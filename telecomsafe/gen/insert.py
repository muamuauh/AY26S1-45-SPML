"""Route ③ — insert vehicles and telecom machinery into real training images (SDXL inpainting).

    python -m telecomsafe.gen.insert add_vehicle --n 50
    python -m telecomsafe.gen.insert add_telecom_machinery --n 50

Placement uses a person in the image as the scale and depth reference: the object's bottom edge sits at
that person's feet (same ground depth) and its size follows the object's height and length in person
heights (configs/scenarios.yaml → objects), with a random narrowing for oblique views. A placement may not
cover any labelled object, so the existing labels stay valid.

The placed box is repainted with "a <object> parked on the ground ..." on an upscaled crop. The label is
the tight box of what was painted (SAM 2 prompted with the placed box), not an E2 detection: E2 is weak on
vehicles, and keeping only what it already detects would bias the data towards easy cases (document 03 §7).
G1: CLIP must see the object in the region, and the base must be an outdoor photo. E2's verdict is only
recorded (g3_detected) for analysis.

Outputs and records as in telecomsafe.gen.inpaint (data/synth/{filtered,rejected}/<scenario>/).
"""

from __future__ import annotations

import argparse
import json
import random
import time

import numpy as np
from PIL import Image, ImageFilter

from telecomsafe.gen.common import (SYNTH, TRAIN_LABELS, Label, done_bases, iou, read_labels, scenario, select_bases,
                                    shuffled, write_record)
from telecomsafe.gen.gates import g0_leak_mask
from telecomsafe.gen.inpaint import Models, crop_square, match_colors, region

OUTDOOR = ["a photo of an outdoor construction site", "a photo of an outdoor street or yard"]
NOT_OUTDOOR = ["a photo of an indoor room or warehouse", "a close-up portrait photo", "a studio photo on a plain background"]
NOT_OBJECT = ["a photo of empty ground or pavement", "a photo of a wall or building", "a distorted blurry blob",
              "a toy model", "a photo of a person"]
GROUND = ["a photo of the ground: a road, pavement, dirt or gravel", "a photo of a paved yard or parking area"]
NOT_GROUND = ["a photo of the sky", "a photo of steel beams or scaffolding", "a photo of a building wall",
              "a photo of a roof or solar panels", "a photo of a person", "a photo of trees or bushes"]


# ---------------------------------------------------------------- placement (pure, tested)
def covered(box, other) -> float:
    """Share of `other` that `box` covers."""
    ix = max(0.0, min(box[2], other[2]) - max(box[0], other[0]))
    iy = max(0.0, min(box[3], other[3]) - max(box[1], other[1]))
    area = (other[2] - other[0]) * (other[3] - other[1])
    return ix * iy / area if area > 0 else 0.0


def place_box(labels: list[Label], width: int, height: int, size: tuple[float, float], rng: random.Random,
              tries: int = 60, max_cover: float = 0.05, max_outside: float = 0.5,
              min_feet: float = 0.5) -> tuple[float, float, float, float] | None:
    """A box for an object `size` = (height, length) in person heights, standing where a reference person
    stands, covering no labelled object by more than max_cover. Up to max_outside of its length may lie
    beyond the left or right edge (vehicles cut off by the frame are common in real photos); the caller
    clips it to the image. Only people whose feet are in the lower part of the frame (below min_feet of
    the height) count as standing on the ground; people on scaffolds or platforms would put the object in the
    air. None if no such place is found."""
    people = [lb for lb in labels if lb.cls == "person" and lb.h >= 0.08 * height
              and min_feet * height <= lb.y2 <= 0.98 * height]
    if not people:
        return None
    for _ in range(tries):
        p = rng.choice(people)
        bh = p.h * size[0] * rng.uniform(0.9, 1.1)
        bw = p.h * size[1] * rng.uniform(0.35, 1.0)  # narrower at an angle; ~0.35 when seen head-on
        if bh > 0.7 * height or (1 - max_outside) * bw > width:
            continue
        bottom = min(height - 1.0, p.y2 + rng.uniform(-0.05, 0.05) * p.h)
        if bottom - bh < 0:
            continue
        x1 = rng.uniform(-max_outside * bw, width - (1 - max_outside) * bw)
        box = (x1, bottom - bh, x1 + bw, bottom)
        if all(covered(box, lb.box) <= max_cover for lb in labels):
            return box
    return None


def ground_strip(image: Image.Image, box) -> Image.Image:
    """The band of the original image where the object's wheels would stand (lower part of the box)."""
    x1, y1, x2, y2 = box
    bh = y2 - y1
    return image.crop((int(x1), int(max(0, y2 - 0.3 * bh)), int(x2), int(min(image.height, y2 + 0.1 * bh))))


def tight_box(mask: np.ndarray) -> tuple[float, float, float, float] | None:
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return None
    return float(xs.min()), float(ys.min()), float(xs.max() + 1), float(ys.max() + 1)


# ---------------------------------------------------------------- generation
def insert_object(image: Image.Image, labels: list[Label], models: Models, cfg: dict, seed: int) -> tuple:
    rng = random.Random(seed)
    w, h = image.size
    entry = {"attempts": 0, "inserted": False}
    for attempt in range(cfg.get("retries", 3)):
        obj = rng.choice(cfg["objects"])
        box, ground = None, 0.0
        for _ in range(10):  # a placement whose wheels would stand on visible ground
            cand_box = place_box(labels, w, h, (obj["h"], obj["w"]), rng)
            if cand_box is None:
                break
            cand_box = (max(0.0, cand_box[0]), cand_box[1], min(float(w), cand_box[2]), cand_box[3])
            ground = models.clip.share(ground_strip(image, cand_box), GROUND, NOT_GROUND)
            if ground >= cfg.get("ground_min", 0.5):
                box = cand_box
                break
        if box is None:
            entry["skipped"] = "no place for the object" if ground == 0.0 else "no ground under the placement"
            return image, labels, entry
        entry["ground"] = round(ground, 3)
        s = seed * 10 + attempt
        prompt = cfg["prompt"].strip().format(object=obj["name"])
        grow = max(4, int(0.04 * max(box[2] - box[0], box[3] - box[1])))
        mask = Image.new("L", image.size, 0)
        mask.paste(255, tuple(int(v) for v in (box[0] - grow, box[1] - grow, box[2] + grow, box[3] + grow // 2)))
        crop_box = crop_square(box, w, h, cfg.get("crop_scale", 1.6), 0.0)
        crop, mcrop = image.crop(crop_box), mask.crop(crop_box)
        gen = models.inpaint(crop, mcrop, cfg, s, prompt)
        if cfg.get("color_match"):
            gen = match_colors(gen, crop, mcrop, max(3, grow))
        cand = image.copy()
        cand.paste(Image.composite(gen, crop, mcrop.filter(ImageFilter.GaussianBlur(max(2, grow // 2)))), crop_box)
        entry.update(attempts=attempt + 1, seed=s, object=obj["name"], placed=[round(v, 1) for v in box])
        g1 = models.clip.share(region(cand, box, 0.1), [f"a photo of a {obj['name']}"], NOT_OBJECT)
        seg = np.asarray(models.sam_mask(cand, box)) > 127
        seg &= np.asarray(mask) > 127  # what SAM finds inside the painted area
        tb = tight_box(seg)
        fill = seg.sum() / max(1.0, (box[2] - box[0]) * (box[3] - box[1]))
        dets = models.detector.detect(cand)
        entry.update(g1=round(g1, 3), fill=round(float(fill), 3),
                     g3_detected=bool(models.detector.found(dets, cfg["targets"][0], box, min_iou=0.3)))
        if g1 >= cfg.get("g1_min", 0.5) and tb is not None and fill >= cfg.get("min_fill", 0.25) and iou(tb, box) >= 0.35:
            entry.update(inserted=True, box=[round(v, 1) for v in tb])
            return cand, labels + [Label(cfg["targets"][0], *tb)], entry
    return image, labels, entry


def run(sid: str, n: int, seed: int) -> None:
    cfg = scenario(sid)
    out_ok, out_bad = SYNTH / "filtered" / sid, SYNTH / "rejected" / sid
    done = done_bases(out_ok, out_bad)
    bases = [b for b in shuffled(select_bases(cfg), seed) if b.name not in done]
    leak = g0_leak_mask(bases[: n * 2])
    bases = [b for b, bad in zip(bases[: n * 2], leak) if not bad][:n]
    print(f"{sid}: {len(bases)} bases (G0 removed {sum(leak)}), {len(done)} already done", flush=True)
    models = Models(cfg)
    stats = {"passed": 0, "rejected": 0}
    t0 = time.time()
    for k, base in enumerate(bases):
        img = Image.open(base).convert("RGB")
        labels = read_labels(TRAIN_LABELS / f"{base.stem}.txt", *img.size)
        meta = {"scenario": sid, "base": base.name, "seed": seed}
        photo, outdoor = models.clip.is_photo(img), models.clip.share(img, OUTDOOR, NOT_OUTDOOR)
        meta.update(g1_photo=round(photo, 3), g1_outdoor=round(outdoor, 3))
        if photo < 0.5 or outdoor < 0.5:
            meta["reason"] = "base: not a photo" if photo < 0.5 else "base: not outdoors"
            write_record(out_bad / base.stem, img, labels, meta)
            stats["rejected"] += 1
            continue
        result, new, entry = insert_object(img, labels, models, cfg, seed * 10000 + k)
        meta["edit"] = entry
        ok = entry["inserted"]
        if not ok:
            meta["reason"] = entry.get("skipped", "object not convincing")
        write_record((out_ok if ok else out_bad) / base.stem, result, new, meta)
        stats["passed" if ok else "rejected"] += 1
        print(f"  {k + 1}/{len(bases)} {base.name[:44]} → {'ok ' + entry.get('object', '') if ok else 'rejected'}"
              f" ({time.time() - t0:.0f}s)", flush=True)
    (SYNTH / f"{sid}_last_run.json").write_text(
        json.dumps({**stats, "bases": len(bases), "seconds": round(time.time() - t0)}), encoding="utf-8")
    print(f"{sid}: {stats} in {time.time() - t0:.0f}s → {out_ok}", flush=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", choices=["add_vehicle", "add_telecom_machinery"])
    ap.add_argument("--n", type=int, default=20, help="number of base images to process")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    run(args.scenario, args.n, args.seed)


if __name__ == "__main__":
    main()
