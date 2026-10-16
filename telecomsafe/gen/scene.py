"""Route ④ — move real workers into telecom scenes (telecom_scene_transfer).

    python -m telecomsafe.gen.scene backgrounds            # build / refresh the background pool
    python -m telecomsafe.gen.scene telecom_scene_transfer --n 50

The training data is almost all building sites while TelecomEval is telecom work; this route keeps the
real worker (and therefore every PPE label) and changes the setting.

Background pool (TelecomSeed): candidate images rejected in the TelecomEval review that show no person.
They must look like an outdoor telecom scene to CLIP, be a wide view (not a close-up of cables or kit),
show ground in the lower quarter (where the feet go),
contain no object of a target class according to E2
(otherwise the composite would have unlabelled objects), and pass G0 against TelecomEval. The pool is
cached in data/synth/backgrounds.json with each image's licence and attribution.

Cut-outs: training images with one or two people, the person not cut by the frame, not overlapping
another person, and a whole standing figure (YOLO11-pose: nose and both ankles visible); SAM 2 segments
the person. The person is scaled to 18–38% of the background height with
the feet in the lower part of the frame, recoloured halfway towards the background's statistics, pasted,
and only a ring along the outline plus the ground under the feet are repainted with SDXL inpainting (edges
and a contact shadow). The person's labels (person and the PPE boxes inside it) move with it.
Gates: G3 — E2 still finds the person where it was pasted; G1 — CLIP sees a photograph of a worker
outdoors rather than a pasted cut-out.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from telecomsafe.gen.common import (SYNTH, TRAIN_LABELS, Label, done_bases, iou, read_labels, scenario, select_bases,
                                    shuffled, write_record)
from telecomsafe.gen.gates import g0_leak_mask
from telecomsafe.gen.inpaint import Models, crop_square, region
from telecomsafe.gen.insert import GROUND, NOT_GROUND

BACKGROUNDS = SYNTH / "backgrounds.json"
POSE_WEIGHTS = SYNTH.parent / "interim" / "models" / "yolo11n-pose.pt"
TELECOM_SCENE = ["a photo of an outdoor telecom tower or antenna mast", "a photo of a street with a utility pole or telecom cabinet",
                 "a photo of a roadside cable trench or manhole", "a photo of rooftop antennas"]
NOT_TELECOM_SCENE = ["a diagram, map or illustration", "a photo of an indoor room", "a close-up photo of electronic equipment",
                     "a photo of the night sky", "a landscape photo without any structures"]
WIDE = ["a wide outdoor photo of a street, field or site", "a photo of a landscape with a tower in the distance",
        "a photo of a building with a yard or road in front"]
CLOSE_UP = ["a close-up photo of cables or cable reels", "a close-up photo of a piece of equipment",
            "a photo looking up at a mast from below", "a close-up photo of a wall or fence",
            "an aerial photo taken from high above", "a drone photo looking down on a street"]
REAL_WORKER = ["a photo of a worker standing outdoors"]
PASTED = ["a cut-out figure pasted onto a photo", "a photo collage", "a cartoon figure"]


# ---------------------------------------------------------------- geometry (pure, tested)
def person_parts(labels: list[Label], person: Label) -> list[Label]:
    """The person and the labels that belong to them (box centre inside the person box)."""
    out = [person]
    for lb in labels:
        if lb is person or lb.cls == "person":
            continue
        cx, cy = (lb.x1 + lb.x2) / 2, (lb.y1 + lb.y2) / 2
        if person.x1 <= cx <= person.x2 and person.y1 <= cy <= person.y2:
            out.append(lb)
    return out


def standalone_people(labels: list[Label], width: int, height: int, margin: float = 0.01) -> list[Label]:
    """People not cut by the frame and not overlapping anyone else (clean cut-outs)."""
    people = [lb for lb in labels if lb.cls == "person"]
    out = []
    for p in people:
        inside = p.x1 > margin * width and p.y1 > margin * height and p.x2 < (1 - margin) * width and p.y2 < (1 - margin) * height
        alone = all(q is p or iou(p.box, q.box) == 0 for q in people)
        if inside and alone:
            out.append(p)
    return out


def placement(person: Label, bg_size: tuple[int, int], rng: random.Random,
              height_range: tuple[float, float] = (0.18, 0.38)) -> tuple[float, float, float]:
    """(scale, dx, dy) moving the person box into the background: height_range of its height (smaller looks far
    more natural than large), feet low in the frame."""
    bw, bh = bg_size
    target_h = bh * rng.uniform(*height_range)
    scale = target_h / person.h
    feet = bh * rng.uniform(0.78, 0.97)
    new_w = person.w * scale
    x1 = rng.uniform(0.02 * bw, max(0.02 * bw, 0.98 * bw - new_w))
    return scale, x1 - person.x1 * scale, feet - person.y2 * scale


def feet_strip(person: Label, size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Box of the background around and just above the moved person's feet (where they would stand)."""
    bw, bh = size
    x1, x2 = person.x1 - 0.25 * person.w, person.x2 + 0.25 * person.w
    y1, y2 = person.y2 - 0.12 * person.h, person.y2 + 0.04 * person.h
    return int(max(0, x1)), int(max(0, y1)), int(min(bw, x2)), int(min(bh, y2))


def move(lb: Label, scale: float, dx: float, dy: float) -> Label:
    return Label(lb.cls, lb.x1 * scale + dx, lb.y1 * scale + dy, lb.x2 * scale + dx, lb.y2 * scale + dy)


def recolor(fg: np.ndarray, mask: np.ndarray, ref: np.ndarray, amount: float = 0.5) -> np.ndarray:
    """Shift the masked pixels' per-channel mean / std part of the way towards ref's."""
    m = mask > 0
    if m.sum() < 10:
        return fg
    f = fg.astype(np.float32)
    mu, sd = f[m].mean(0), f[m].std(0) + 1e-6
    rmu, rsd = ref.reshape(-1, 3).mean(0), ref.reshape(-1, 3).std(0) + 1e-6
    target = (f - mu) / sd * (sd + amount * (rsd - sd)) + (mu + amount * (rmu - mu))
    out = f.copy()
    out[m] = target[m]
    return np.clip(out, 0, 255).astype(np.uint8)


def is_grayscale(img: Image.Image, max_saturation: float = 20.0) -> bool:
    """Black-and-white (or nearly) photo: a colour worker pasted in looks obviously wrong."""
    return float(np.asarray(img.convert("HSV"))[..., 1].mean()) < max_saturation


def full_body(keypoints: np.ndarray, conf: np.ndarray, box, min_conf: float = 0.5) -> bool:
    """COCO keypoints of one person: nose and both ankles confidently visible inside the box — a whole,
    unoccluded standing figure (half bodies and hands make floating cut-outs)."""
    x1, y1, x2, y2 = box
    for k in (0, 15, 16):  # nose, left ankle, right ankle
        x, y = keypoints[k]
        if conf[k] < min_conf or not (x1 <= x <= x2 and y1 <= y <= y2):
            return False
    return True


# ---------------------------------------------------------------- background pool
def build_backgrounds(models: Models, limit: int | None = None) -> list[dict]:
    from telecomsafe.data.collect_open import OUT, read_manifest

    rejected = OUT.parent / "rejected"
    rows = [r for r in read_manifest() if r["status"] == "rejected" and r.get("scene") not in (None, "", "unreadable")
            and int(r.get("persons") or 0) == 0 and (rejected / r["file"]).exists()]
    rows = rows[:limit] if limit else rows
    leak = g0_leak_mask([rejected / r["file"] for r in rows])
    pool = []
    for r, bad in zip(rows, leak):
        if bad:
            continue
        img = Image.open(rejected / r["file"]).convert("RGB")
        if min(img.size) < 480 or is_grayscale(img):
            continue
        tele = models.clip.share(img, TELECOM_SCENE, NOT_TELECOM_SCENE)
        if tele < 0.5 or models.clip.is_photo(img) < 0.5:
            continue
        # the feet go in the lower quarter, so that band must be ground (not sky, a mast seen from below, water...)
        ground = models.clip.share(img.crop((0, int(0.75 * img.height), img.width, img.height)), GROUND, NOT_GROUND)
        if ground < 0.5:
            continue
        # a person 18–45% of the frame high needs a wide view; close-ups of cable reels make giants or dwarfs
        wide = models.clip.share(img, WIDE, CLOSE_UP)
        if wide < 0.5:
            continue
        found = [d for d in models.detector.detect(img) if d[2] >= 0.35]
        if found:
            continue
        pool.append({"file": str((rejected / r["file"]).relative_to(SYNTH.parents[1])), "scene": r["scene"],
                     "telecom": round(tele, 3), "ground": round(ground, 3), "wide": round(wide, 3), "licence": r["licence"], "creator": r["creator"],
                     "landing_url": r["landing_url"], "attribution": r["attribution"]})
    BACKGROUNDS.parent.mkdir(parents=True, exist_ok=True)
    BACKGROUNDS.write_text(json.dumps(pool, indent=1, ensure_ascii=False), encoding="utf-8")
    return pool


# ---------------------------------------------------------------- composite
def composite(fg: Image.Image, labels: list[Label], person: Label, bg: Image.Image, models: Models, cfg: dict,
              seed: int) -> tuple:
    rng = random.Random(seed)
    mask = np.asarray(models.sam_mask(fg, person.box)) > 127
    fill = mask.sum() / max(1.0, person.w * person.h)
    entry = {"fill": round(float(fill), 3)}
    if fill < cfg.get("min_fill", 0.3):
        entry["skipped"] = "person mask too small"
        return None, None, entry
    # the feet must land on ground (not on a mast, a car roof or in the air): try several placements
    ground = 0.0
    for _ in range(cfg.get("placements", 10)):
        scale, dx, dy = placement(person, bg.size, rng, tuple(cfg.get("person_height", (0.18, 0.38))))
        cand = move(person, scale, dx, dy)
        ground = models.clip.share(bg.crop(feet_strip(cand, bg.size)), GROUND, NOT_GROUND)
        if ground >= cfg.get("ground_min", 0.5):
            break
    else:
        entry["skipped"] = "no ground for the feet"
        entry["ground"] = round(ground, 3)
        return None, None, entry
    entry["ground"] = round(ground, 3)
    if scale > cfg.get("max_upscale", 2.5):  # a small person blown up comes out blurred
        entry.update(skipped="person upscaled too much", scale=round(scale, 3))
        return None, None, entry
    parts = [move(lb, scale, dx, dy) for lb in person_parts(labels, person)]
    new_person = parts[0]
    # cut out the person's bounding box, scaled
    x1, y1, x2, y2 = (int(v) for v in person.box)
    cut = fg.crop((x1, y1, x2, y2))
    cmask = Image.fromarray((mask[y1:y2, x1:x2] * 255).astype(np.uint8))
    size = (max(1, round(cut.width * scale)), max(1, round(cut.height * scale)))
    cut, cmask = cut.resize(size, Image.LANCZOS), cmask.resize(size, Image.LANCZOS)
    px, py = round(x1 * scale + dx), round(y1 * scale + dy)
    ref = np.asarray(bg.crop((max(0, px), max(0, py), min(bg.width, px + size[0]), min(bg.height, py + size[1]))))
    cut = Image.fromarray(recolor(np.asarray(cut), np.asarray(cmask), ref if ref.size else np.asarray(bg),
                                  cfg.get("recolor", 0.5)))
    out = bg.copy()
    out.paste(cut, (px, py), cmask.filter(ImageFilter.GaussianBlur(1)))
    # repaint a ring along the outline and the ground under the feet (edges, contact shadow)
    full = Image.new("L", bg.size, 0)
    full.paste(cmask, (px, py))
    r = max(3, int(0.02 * new_person.h))  # ring width along the outline
    ring = np.asarray(full.filter(ImageFilter.MaxFilter(2 * r + 1))) > 127
    ring &= ~(np.asarray(full.filter(ImageFilter.MinFilter(2 * (r // 2) + 1))) > 127)
    ring_img = Image.fromarray((ring * 255).astype(np.uint8))
    fw = new_person.w
    ImageDraw.Draw(ring_img).ellipse((new_person.x1 - 0.1 * fw, new_person.y2 - 0.04 * new_person.h,
                                      new_person.x2 + 0.3 * fw, new_person.y2 + 0.04 * new_person.h), fill=255)
    box = crop_square(new_person.box, *bg.size, cfg.get("crop_scale", 1.3), 0.0)
    crop, mcrop = out.crop(box), ring_img.crop(box)
    gen = models.inpaint(crop, mcrop, {**cfg, "strength": cfg.get("harmonize_strength", 0.55)}, seed,
                         cfg["prompt"].strip())
    out.paste(Image.composite(gen, crop, mcrop.filter(ImageFilter.GaussianBlur(2))), box)
    entry.update(scale=round(scale, 3), person=[round(v, 1) for v in new_person.box])
    return out, parts, entry


def run(sid: str, n: int, seed: int) -> None:
    cfg = scenario(sid)
    out_ok, out_bad = SYNTH / "filtered" / sid, SYNTH / "rejected" / sid
    if not BACKGROUNDS.exists():
        raise SystemExit("no background pool — run: python -m telecomsafe.gen.scene backgrounds")
    pool = json.loads(BACKGROUNDS.read_text(encoding="utf-8"))
    done = done_bases(out_ok, out_bad)
    bases = [b for b in shuffled(select_bases(cfg), seed) if b.name not in done][:n]
    print(f"{sid}: {len(bases)} bases, {len(pool)} backgrounds, {len(done)} already done", flush=True)
    models = Models(cfg)
    from ultralytics import YOLO

    POSE_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    pose_model = YOLO(str(POSE_WEIGHTS) if POSE_WEIGHTS.exists() else "yolo11n-pose.pt")
    rng = random.Random(seed)
    stats = {"passed": 0, "rejected": 0}
    t0 = time.time()
    root = SYNTH.parents[1]
    for k, base in enumerate(bases):
        fg = Image.open(base).convert("RGB")
        labels = read_labels(TRAIN_LABELS / f"{base.stem}.txt", *fg.size)
        people = standalone_people(labels, *fg.size)
        meta = {"scenario": sid, "base": base.name, "seed": seed}
        if people:  # keep only whole, unoccluded standing figures
            pose = pose_model.predict(fg, verbose=False)[0]
            kps = pose.keypoints
            figures = [] if kps is None or kps.conf is None else list(zip(kps.xy.cpu().numpy(), kps.conf.cpu().numpy()))
            people = [p for p in people if any(full_body(xy, c, p.box) for xy, c in figures)]
        if not people:
            meta["reason"] = "base: no whole standing person"
            write_record(out_bad / base.stem, fg, labels, meta)
            stats["rejected"] += 1
            continue
        person = max(people, key=lambda p: p.h)
        bgr = rng.choice(pool)
        bg = Image.open(root / bgr["file"]).convert("RGB")
        result, parts, entry = composite(fg, labels, person, bg, models, cfg, seed * 10000 + k)
        meta.update(edit=entry, background={k_: bgr[k_] for k_ in ("file", "scene", "licence", "creator", "landing_url", "attribution")})
        ok = False
        if result is not None:
            dets = models.detector.detect(result)
            g3 = bool(models.detector.found(dets, "person", parts[0].box, min_iou=0.5))
            g1_photo = models.clip.is_photo(result)
            g1_real = models.clip.share(region(result, parts[0].box, 0.3), REAL_WORKER, PASTED)
            entry.update(g3=g3, g1_photo=round(g1_photo, 3), g1_real=round(g1_real, 3))
            ok = g3 and g1_photo >= 0.5 and g1_real >= cfg.get("g1_min", 0.5)
            if not ok:
                meta["reason"] = "gates"
        else:
            meta["reason"] = entry.get("skipped", "composite failed")
        write_record((out_ok if ok else out_bad) / base.stem, result if result is not None else fg,
                     parts if ok else labels, meta)
        stats["passed" if ok else "rejected"] += 1
        print(f"  {k + 1}/{len(bases)} {base.name[:44]} + {Path(bgr['file']).name[:24]} → {'ok' if ok else 'rejected'}"
              f" ({time.time() - t0:.0f}s)", flush=True)
    (SYNTH / f"{sid}_last_run.json").write_text(
        json.dumps({**stats, "bases": len(bases), "seconds": round(time.time() - t0)}), encoding="utf-8")
    print(f"{sid}: {stats} in {time.time() - t0:.0f}s → {out_ok}", flush=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["backgrounds", "telecom_scene_transfer"])
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    if args.command == "backgrounds":
        pool = build_backgrounds(Models(scenario("telecom_scene_transfer")))
        print(f"{len(pool)} backgrounds → {BACKGROUNDS}")
    else:
        run(args.command, args.n, args.seed)


if __name__ == "__main__":
    main()
