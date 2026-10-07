"""Route ③ — local edits of real training images with SDXL inpainting.

    python -m telecomsafe.gen.inpaint remove_helmet --n 50          # 50 base images
    python -m telecomsafe.gen.inpaint remove_helmet --n 50 --seed 1 # a different sample of bases
    python -m telecomsafe.gen.inpaint remove_vest --n 50

Both scenarios remove a piece of PPE (remove_ppe). For each target box a mask (SAM 2, for helmets widened
with an ellipse slightly larger than the box — otherwise the model paints the helmet's shape back) is
repainted on a square crop upscaled to 1024 px, colours are matched on a ring outside the mask before
pasting back (no halo), and the edit is kept only if G3 (the E2 detector no longer finds the target there)
and G1 (CLIP sees a bare head / ordinary clothes) both pass; up to `retries` seeds are tried.

remove_helmet: the helmet box becomes a no_helmet head box (E2's box when it finds one, else an estimate).
remove_vest:   the vest box becomes a no_vest box; the garment comes from the scenario's variables.

Outputs: data/synth/filtered/<scenario>/ (passed) and data/synth/rejected/<scenario>/ (with the reason),
each image with a YOLO .txt and a .json record. Bases already processed are skipped, so runs can resume.
Models load offline from the Hugging Face cache (HF_HUB_OFFLINE=1); see environment-gen.yml.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from telecomsafe.gen.common import (SYNTH, TRAIN_LABELS, Label, done_bases, read_labels, scenario, select_bases,
                                    shuffled, write_record)
from telecomsafe.gen.gates import Clip, Detector, g0_leak_mask
from telecomsafe.paths import INTERIM

SAM_WEIGHTS = INTERIM / "models" / "sam2.1_b.pt"  # downloaded by ultralytics on first use if missing


# ---------------------------------------------------------------- geometry (pure, tested)
def crop_square(box, width: int, height: int, scale: float, shift_down: float = 0.3) -> tuple[int, int, int, int]:
    """A square of side scale × the box's longer side around the box (shifted down to include the face),
    kept inside the image."""
    x1, y1, x2, y2 = box
    side = int(max(x2 - x1, y2 - y1) * scale)
    side = min(side, width, height)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2 + shift_down * (y2 - y1)
    left = int(min(max(0, cx - side / 2), width - side))
    top = int(min(max(0, cy - side / 2), height - side))
    return left, top, left + side, top + side


def head_box(helmet: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    """Estimated head box once the helmet is gone: the helmet box's width, from just below its top to
    roughly the chin."""
    x1, y1, x2, y2 = helmet
    w, h = x2 - x1, y2 - y1
    return x1 + 0.05 * w, y1 + 0.1 * h, x2 - 0.05 * w, y2 + 0.45 * h


def ellipse_mask(size: tuple[int, int], box, pad=(0.12, 0.08, 0.12, 0.05)) -> Image.Image:
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse((x1 - pad[0] * w, y1 - pad[1] * h, x2 + pad[2] * w, y2 + pad[3] * h), fill=255)
    return m


def region(image: Image.Image, box, pad: float, below: float | None = None) -> Image.Image:
    """The box plus padding (and optionally extra room below, for a head's face), clipped to the image."""
    x1, y1, x2, y2 = box
    w, h = x2 - x1, y2 - y1
    below = pad if below is None else below
    return image.crop((max(0, x1 - pad * w), max(0, y1 - pad * h), min(image.width, x2 + pad * w),
                       min(image.height, y2 + below * h)))


def match_colors(gen: Image.Image, ref: Image.Image, mask: Image.Image, ring: int) -> Image.Image:
    """Shift gen's colour statistics so that, on a ring just outside the mask, they match ref."""
    m = np.asarray(mask) > 127
    outer = np.asarray(mask.filter(ImageFilter.MaxFilter(2 * ring + 1))) > 127
    band = outer & ~m
    if band.sum() < 50:
        return gen
    g, r = np.asarray(gen, dtype=np.float32), np.asarray(ref, dtype=np.float32)
    out = (g - g[band].mean(0)) / (g[band].std(0) + 1e-6) * r[band].std(0) + r[band].mean(0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def fill_prompt(cfg: dict, seed: int) -> str:
    """Fill {variables} in the scenario prompt, one choice per seed (variety across images)."""
    rng = random.Random(seed)
    return cfg["prompt"].strip().format(**{k: rng.choice(v) for k, v in (cfg.get("variables") or {}).items()})


# ---------------------------------------------------------------- scenarios
@dataclass(frozen=True)
class Removal:
    """What a PPE-removal scenario paints away and how its result is checked and labelled."""
    target: str              # class painted away
    replacement: str         # class its box becomes
    add_ellipse: bool        # widen the SAM mask with an ellipse
    crop_scale: float
    shift_down: float
    judge: str               # Clip method scoring the edited region (G1)
    region_pad: float        # padding of the region shown to G1
    region_below: float      # extra room below the box in that region


REMOVALS = {
    "remove_helmet": Removal("helmet", "no_helmet", True, 4.0, 0.3, "bare_head", 0.6, 1.2),
    "remove_vest": Removal("vest", "no_vest", False, 2.0, 0.0, "ordinary_clothes", 0.2, 0.2),
}


# ---------------------------------------------------------------- models
class Models:
    def __init__(self, cfg: dict):
        import torch
        from diffusers import AutoencoderKL, AutoPipelineForInpainting
        from ultralytics import SAM

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        vae = AutoencoderKL.from_pretrained(cfg["vae"], dtype=torch.float16)
        self.pipe = AutoPipelineForInpainting.from_pretrained(cfg["model"], vae=vae, dtype=torch.float16,
                                                              variant="fp16").to("cuda")
        self.pipe.set_progress_bar_config(disable=True)
        SAM_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
        self.sam = SAM(str(SAM_WEIGHTS) if SAM_WEIGHTS.exists() else "sam2.1_b.pt")
        self.detector = Detector()
        self.clip = Clip()
        self.torch = torch

    def sam_mask(self, image: Image.Image, box) -> Image.Image:
        r = self.sam(image, bboxes=[list(box)], verbose=False)[0].masks
        if r is None:
            return Image.new("L", image.size, 0)
        return Image.fromarray((r.data[0].cpu().numpy() * 255).astype(np.uint8)).resize(image.size)

    def inpaint(self, crop: Image.Image, mask: Image.Image, cfg: dict, seed: int, prompt: str) -> Image.Image:
        g = self.torch.Generator("cuda").manual_seed(seed)
        out = self.pipe(prompt=prompt, negative_prompt=cfg["negative"], image=crop.resize((1024, 1024), Image.LANCZOS),
                        mask_image=mask.resize((1024, 1024)), strength=cfg.get("strength", 1.0),
                        guidance_scale=cfg.get("guidance", 7.0), num_inference_steps=cfg.get("steps", 30),
                        generator=g).images[0]
        return out.resize(crop.size, Image.LANCZOS)


# ---------------------------------------------------------------- PPE removal
def remove_ppe(image: Image.Image, labels: list[Label], models: Models, cfg: dict, spec: Removal, seed: int) -> tuple:
    result = image.copy()
    w, h = image.size
    targets = [lb for lb in labels if lb.cls == spec.target]
    report = []
    for j, lb in enumerate(targets):
        entry = {spec.target: [round(v, 1) for v in lb.box], "attempts": 0, "removed": False}
        report.append(entry)
        if lb.h < cfg.get(f"min_{spec.target}_px", 0):
            entry["skipped"] = "too small"
            continue
        mask = models.sam_mask(result, lb.box)
        if spec.add_ellipse:
            mask.paste(255, mask=ellipse_mask(image.size, lb.box, cfg["mask"].get("ellipse_pad", (0.12, 0.08, 0.12, 0.05))))
        elif np.asarray(mask).max() == 0:  # SAM found nothing: fall back to the box itself
            ImageDraw.Draw(mask).rectangle(lb.box, fill=255)
        grow = max(5, int(cfg["mask"].get("grow", 0.1) * max(lb.w, lb.h)))
        mask = mask.filter(ImageFilter.MaxFilter(2 * (grow // 2) + 1))
        box = crop_square(lb.box, w, h, cfg.get("crop_scale", spec.crop_scale), spec.shift_down)
        crop, mcrop = result.crop(box), mask.crop(box)
        feather = mcrop.filter(ImageFilter.GaussianBlur(max(2, grow // 4)))
        for attempt in range(cfg.get("retries", 3)):
            s = seed * 100 + j * 10 + attempt
            prompt = fill_prompt(cfg, s)
            gen = models.inpaint(crop, mcrop, cfg, s, prompt)
            if cfg.get("color_match"):
                gen = match_colors(gen, crop, mcrop, max(3, grow))
            cand = result.copy()
            cand.paste(Image.composite(gen, crop, feather), box)
            entry["attempts"] = attempt + 1
            g3 = not models.detector.found(models.detector.detect(cand), spec.target, lb.box)
            g1 = getattr(models.clip, spec.judge)(region(cand, lb.box, spec.region_pad, spec.region_below))
            entry.update(seed=s, prompt=prompt, g3=g3, g1=round(g1, 3))
            if g3 and g1 >= cfg.get("g1_min", 0.5):
                result, entry["removed"] = cand, True
                break
    new = [lb for lb in labels if lb.cls != spec.target]
    dets = models.detector.detect(result) if spec.target == "helmet" else []
    for lb, entry in zip(targets, report):
        if not entry["removed"]:
            new.append(lb)
        elif spec.target == "helmet":  # a no_helmet box covers the head, not the old helmet
            guess = head_box(lb.box)
            near = models.detector.found(dets, "no_helmet", guess, min_iou=0.2)
            entry["new_box"] = "detector" if near else "estimated"
            new.append(Label("no_helmet", *(max(near, key=lambda d: d[2])[1] if near else guess)))
        else:  # the torso box stays where the vest was
            entry["new_box"] = "same"
            new.append(Label(spec.replacement, *lb.box))
    return result, new, report


def run(sid: str, n: int, seed: int) -> None:
    cfg, spec = scenario(sid), REMOVALS[sid]
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
        photo = models.clip.is_photo(img)
        meta["g1_photo"] = round(photo, 3)
        if photo < 0.5:
            meta["reason"] = "base: not a photo"
            write_record(out_bad / base.stem, img, labels, meta)
            stats["rejected"] += 1
            continue
        result, new, report = remove_ppe(img, labels, models, cfg, spec, seed * 10000 + k)
        meta["edits"] = report
        ok = any(e["removed"] for e in report)
        if not ok:
            meta["reason"] = f"no {spec.target} removed"
        write_record((out_ok if ok else out_bad) / base.stem, result, new, meta)
        stats["passed" if ok else "rejected"] += 1
        print(f"  {k + 1}/{len(bases)} {base.name[:48]} → {'ok' if ok else 'rejected'} ({time.time() - t0:.0f}s)", flush=True)
    (SYNTH / f"{sid}_last_run.json").write_text(
        json.dumps({**stats, "bases": len(bases), "seconds": round(time.time() - t0)}), encoding="utf-8")
    print(f"{sid}: {stats} in {time.time() - t0:.0f}s → {out_ok}", flush=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenario", choices=sorted(REMOVALS))
    ap.add_argument("--n", type=int, default=20, help="number of base images to process")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    run(args.scenario, args.n, args.seed)


if __name__ == "__main__":
    main()
