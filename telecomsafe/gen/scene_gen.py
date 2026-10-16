"""Route ④ (generative): paint a worker into a telecom background, sized by the scene's depth.

    python -m telecomsafe.gen.scene_gen poses                                 # build the pose library
    python -m telecomsafe.gen.scene_gen telecom_scene_generate --n 12 --seed 0

Why: pasting real workers into backgrounds (telecomsafe.gen.scene) was rated natural for only 9 of 99
images in G4 — the person's size / perspective and lighting did not match the scene. Here the person is
painted by SDXL inpainting with the whole surroundings as context (light, colour and shadow come from the
model), the pose comes from a real worker in the training set (OpenPose ControlNet), and the size from
the background's metric depth: a person of height H whose feet are at depth Z is f·H/Z pixels tall
(f = focal length in pixels, from EXIF when present, else a 65° field of view).

Labels: the PPE state is set in the prompt (hard hat or not, safety vest or not); the E2 detector then
boxes the painted person and their PPE, and the image is kept only if what it finds matches the prompt
and the person's size matches the planned box. Backgrounds: the pool of telecom.gen.scene (person-free
telecom scenes, G0-checked, licences recorded).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from telecomsafe.gen.common import SYNTH, TRAIN_LABELS, Label, done_bases, iou, read_labels, scenario, select_bases, shuffled, write_record
from telecomsafe.gen.inpaint import SAM_WEIGHTS, crop_square
from telecomsafe.gen.insert import GROUND, NOT_GROUND
from telecomsafe.gen.scene import BACKGROUNDS, POSE_WEIGHTS, feet_strip, full_body, standalone_people

POSES = SYNTH / "poses.json"
MODELS = SYNTH.parent / "interim" / "models"
DEPTH_MODEL = MODELS / "depth-anything-v2-metric-outdoor-base"
CONTROLNET = MODELS / "controlnet-openpose-sdxl"

# OpenPose body-18 order, built from COCO-17 (None: the neck, the shoulders' midpoint)
OPENPOSE_FROM_COCO = [0, None, 6, 8, 10, 5, 7, 9, 12, 14, 16, 11, 13, 15, 2, 1, 4, 3]
LIMBS = [(1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
         (1, 0), (0, 14), (14, 16), (0, 15), (15, 17)]
COLORS = [(255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
          (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
          (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85)]


# ---------------------------------------------------------------- geometry (pure, tested)
def coco_to_openpose(xy: np.ndarray, conf: np.ndarray, min_conf: float = 0.3) -> list:
    """17 COCO keypoints → 18 OpenPose keypoints ([x, y] or None when not visible)."""
    out = []
    for c in OPENPOSE_FROM_COCO:
        if c is None:  # neck
            ok = conf[5] >= min_conf and conf[6] >= min_conf
            out.append([float((xy[5][0] + xy[6][0]) / 2), float((xy[5][1] + xy[6][1]) / 2)] if ok else None)
        else:
            out.append([float(xy[c][0]), float(xy[c][1])] if conf[c] >= min_conf else None)
    return out


def normalise_pose(points: list, box) -> list:
    """Keypoints relative to the person box: (0, 0) top-left, (1, 1) bottom-right."""
    x1, y1, x2, y2 = box
    return [None if p is None else [(p[0] - x1) / (x2 - x1), (p[1] - y1) / (y2 - y1)] for p in points]


def place_pose(pose: list, box) -> list:
    x1, y1, x2, y2 = box
    return [None if p is None else [x1 + p[0] * (x2 - x1), y1 + p[1] * (y2 - y1)] for p in pose]


def draw_pose(points: list, size: tuple[int, int], width: float) -> Image.Image:
    """OpenPose-style skeleton on black (the ControlNet's conditioning image)."""
    canvas = Image.new("RGB", size, 0)
    d = ImageDraw.Draw(canvas)
    for i, (a, b) in enumerate(LIMBS):
        if points[a] is not None and points[b] is not None:
            colour = tuple(int(0.6 * c) for c in COLORS[i])
            d.line([tuple(points[a]), tuple(points[b])], fill=colour, width=max(1, int(width)))
    r = max(1.0, width * 0.8)
    for i, p in enumerate(points):
        if p is not None:
            d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=COLORS[i])
    return canvas


def focal_px(image: Image.Image, fov_deg: float = 65.0) -> float:
    """Focal length in pixels: from the EXIF 35 mm-equivalent focal length when present (36 mm across the
    long side), else from a horizontal field of view typical of phone and compact cameras."""
    long_side = max(image.size)
    try:
        f35 = image.getexif().get_ifd(0x8769).get(41989)
        if f35 and 10 <= float(f35) <= 300:
            return float(f35) * long_side / 36.0
    except Exception:
        pass
    return long_side / (2 * math.tan(math.radians(fov_deg) / 2))


def person_height_px(focal: float, depth_m: float, height_m: float) -> float:
    """Pinhole camera: an upright person of height_m at distance depth_m is focal·H/Z pixels tall."""
    return focal * height_m / max(depth_m, 0.1)


def ppe_matches(dets: list, person_box, wants: dict, low_dets: list | None = None) -> tuple[bool, list[Label]]:
    """The E2 detections on the painted person agree with the prompt's PPE (hard hat yes / no, vest yes / no):
    the wanted class is found and its opposite is not. no_helmet is a weak class for E2, so a wanted class
    missing at the normal threshold may come from low_dets (a low-threshold pass; the caller corroborates it
    with CLIP). Returns (ok, the PPE labels)."""
    x1, y1, x2, y2 = person_box

    def on_person(ds):
        return [d for d in ds if x1 <= (d[1][0] + d[1][2]) / 2 <= x2 and y1 <= (d[1][1] + d[1][3]) / 2 <= y2]

    inside, low = on_person(dets), on_person(low_dets or [])
    labels = []
    for yes, no, want in (("helmet", "no_helmet", wants["helmet"]), ("vest", "no_vest", wants["vest"])):
        cls, other = (yes, no) if want else (no, yes)
        found = [d for d in inside if d[0] == cls] or [d for d in low if d[0] == cls]
        if not found or any(d[0] == other for d in inside):
            return False, []
        best = max(found, key=lambda d: d[2])
        labels.append(Label(cls, *best[1]))
    if any(d[0] == "harness" for d in inside):  # never prompted
        return False, []
    return True, labels


# ---------------------------------------------------------------- pose library
def build_poses(limit: int = 1500, seed: int = 0, min_aspect: float = 1.6) -> list[dict]:
    """Whole standing people from the training set (YOLO11-pose), as box-relative OpenPose keypoints."""
    from ultralytics import YOLO

    cfg = scenario("telecom_scene_transfer")  # same base rules: one or two clean, whole people
    bases = shuffled(select_bases(cfg), seed)[:limit]
    model = YOLO(str(POSE_WEIGHTS) if POSE_WEIGHTS.exists() else "yolo11n-pose.pt")
    poses = []
    for base in bases:
        img = Image.open(base).convert("RGB")
        people = standalone_people(read_labels(TRAIN_LABELS / f"{base.stem}.txt", *img.size), *img.size)
        if not people:
            continue
        kps = model.predict(img, verbose=False)[0].keypoints
        if kps is None or kps.conf is None:
            continue
        for xy, c in zip(kps.xy.cpu().numpy(), kps.conf.cpu().numpy()):
            for p in people:
                if full_body(xy, c, p.box) and p.h / p.w >= min_aspect and min(c[5], c[6], c[11], c[12]) >= 0.5:
                    poses.append({"base": base.name, "aspect": round(p.h / p.w, 3),
                                  "points": normalise_pose(coco_to_openpose(xy, c), p.box)})
    POSES.parent.mkdir(parents=True, exist_ok=True)
    POSES.write_text(json.dumps(poses), encoding="utf-8")
    return poses


# ---------------------------------------------------------------- models
class GenModels:
    def __init__(self, cfg: dict):
        import torch
        from diffusers import AutoencoderKL, ControlNetModel, StableDiffusionXLControlNetInpaintPipeline
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation
        from ultralytics import SAM

        from telecomsafe.gen.gates import Clip, Detector

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        vae = AutoencoderKL.from_pretrained(cfg["vae"], dtype=torch.float16)
        controlnet = ControlNetModel.from_pretrained(str(CONTROLNET), dtype=torch.float16)
        self.pipe = StableDiffusionXLControlNetInpaintPipeline.from_pretrained(
            cfg["model"], vae=vae, controlnet=controlnet, dtype=torch.float16, variant="fp16").to("cuda")
        self.pipe.set_progress_bar_config(disable=True)
        self.depth_proc = AutoImageProcessor.from_pretrained(str(DEPTH_MODEL))
        # on the CPU: once per background, and SDXL + ControlNet already fill a 12 GB card
        self.depth_model = AutoModelForDepthEstimation.from_pretrained(str(DEPTH_MODEL)).eval()
        self.sam = SAM(str(SAM_WEIGHTS) if SAM_WEIGHTS.exists() else "sam2.1_b.pt")
        self.detector = Detector()
        self.low_detector = Detector(conf=cfg.get("low_conf", 0.05))
        self.clip = Clip()
        self.torch = torch

    def sam_mask(self, image: Image.Image, box) -> np.ndarray:
        r = self.sam(image, bboxes=[list(box)], verbose=False)[0].masks
        if r is None:
            return np.zeros(image.size[::-1], bool)
        return np.asarray(Image.fromarray((r.data[0].cpu().numpy() * 255).astype(np.uint8)).resize(image.size)) > 127

    def depth(self, image: Image.Image) -> np.ndarray:
        """Metric depth (metres) at the image's resolution."""
        torch = self.torch
        inputs = self.depth_proc(images=image, return_tensors="pt")
        with torch.no_grad():
            pred = self.depth_model(**inputs).predicted_depth
        pred = torch.nn.functional.interpolate(pred[:, None], size=image.size[::-1], mode="bicubic", align_corners=False)
        return pred[0, 0].float().cpu().numpy()

    def paint(self, crop: Image.Image, mask: Image.Image, control: Image.Image, cfg: dict, seed: int,
              prompt: str, negative: str) -> Image.Image:
        g = self.torch.Generator("cuda").manual_seed(seed)
        out = self.pipe(prompt=prompt, negative_prompt=negative, image=crop.resize((1024, 1024), Image.LANCZOS),
                        mask_image=mask.resize((1024, 1024)), control_image=control.resize((1024, 1024)),
                        controlnet_conditioning_scale=cfg.get("control_scale", 0.8), strength=cfg.get("strength", 1.0),
                        guidance_scale=cfg.get("guidance", 7.0), num_inference_steps=cfg.get("steps", 30),
                        generator=g).images[0]
        return out.resize(crop.size, Image.LANCZOS)


# ---------------------------------------------------------------- one image
def plan(bg: Image.Image, depth: np.ndarray, pose: dict, models: GenModels, cfg: dict, rng: random.Random):
    """A box for the new person: feet on visible ground, height from the depth there."""
    w, h = bg.size
    f = focal_px(bg, cfg.get("fov", 65.0))
    lo, hi = cfg.get("person_height", [0.08, 0.6])
    last = "no placement"
    for _ in range(cfg.get("placements", 30)):
        fx, fy = rng.uniform(0.08, 0.92) * w, rng.uniform(0.55, 0.97) * h
        patch = depth[max(0, int(fy) - 3):int(fy) + 4, max(0, int(fx) - 3):int(fx) + 4]
        z = float(np.median(patch))
        ph = person_height_px(f, z, rng.uniform(1.6, 1.85))
        if not lo * h <= ph <= hi * h:
            last = "person would be too small or too large there"
            continue
        pw = ph / pose["aspect"]
        box = (fx - pw / 2, fy - ph, fx + pw / 2, fy)
        if box[0] < 0 or box[2] > w or box[1] < 0.02 * h:
            last = "person would leave the frame"
            continue
        ground = models.clip.share(bg.crop(feet_strip(Label("person", *box), bg.size)), GROUND, NOT_GROUND)
        if ground < cfg.get("ground_min", 0.5):
            last = "no ground under the feet"
            continue
        return box, {"depth_m": round(z, 2), "focal_px": round(f, 1), "ground": round(ground, 3)}
    return None, {"skipped": last}


def generate(bg: Image.Image, depth: np.ndarray, pose: dict, models: GenModels, cfg: dict, seed: int):
    rng = random.Random(seed)
    box, entry = plan(bg, depth, pose, models, cfg, rng)
    if box is None:
        return None, None, entry
    w, h = bg.size
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    side_box = crop_square(box, w, h, cfg.get("crop_scale", 2.0), 0.0)
    side = side_box[2] - side_box[0]
    min_side = min(cfg.get("min_crop", 512), w, h)
    if side < min_side:  # small people: keep enough context around them
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        left = int(min(max(0, cx - min_side / 2), w - min_side))
        top = int(min(max(0, cy - min_side / 2), h - min_side))
        side_box = (left, top, left + min_side, top + min_side)
    crop = bg.crop(side_box)
    ox, oy = side_box[0], side_box[1]
    # mask: the box widened for arms and a contact shadow, feathered
    mask = Image.new("L", bg.size, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((x1 - 0.2 * bw, y1 - 0.05 * bh, x2 + 0.2 * bw, y2 + 0.04 * bh), radius=0.15 * bw, fill=255)
    md.ellipse((x1 - 0.3 * bw, y2 - 0.04 * bh, x2 + 0.5 * bw, y2 + 0.06 * bh), fill=255)
    mcrop = mask.crop(side_box)
    scale = 1024 / side
    pts = [None if p is None else [(p[0] - ox) * scale, (p[1] - oy) * scale] for p in place_pose(pose["points"], box)]
    control = draw_pose(pts, (1024, 1024), width=max(3.0, bh * scale / 40))
    ppe = rng.choice(cfg["ppe"])
    prompt = cfg["prompt"].strip().format(ppe=ppe["text"])
    negative = ", ".join(x for x in (ppe.get("negative"), cfg["negative"]) if x)
    gen = models.paint(crop, mcrop, control, cfg, seed, prompt, negative)
    out = bg.copy()
    out.paste(Image.composite(gen, crop, mcrop.filter(ImageFilter.GaussianBlur(max(2, int(0.02 * side))))), side_box[:2])
    entry.update(box=[round(v, 1) for v in box], crop=list(side_box), ppe=ppe["text"], prompt=prompt,
                 wants={"helmet": ppe["helmet"], "vest": ppe["vest"]})
    return out, box, entry


def keep_person_only(bg: Image.Image, painted: Image.Image, person_box, models: GenModels) -> Image.Image:
    """Inpainting repaints the whole mask and leaves a smudged patch around the person: put back only the
    painted person (SAM) and a thin contact shadow under the feet onto the untouched background."""
    keep = models.sam_mask(painted, person_box)
    x1, y1, x2, y2 = person_box
    pw, ph = x2 - x1, y2 - y1
    grow = max(1, int(0.01 * ph))
    keep_img = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(2 * grow + 1))
    shadow = Image.new("L", bg.size, 0)
    ImageDraw.Draw(shadow).ellipse((x1 - 0.15 * pw, y2 - 0.03 * ph, x2 + 0.25 * pw, y2 + 0.025 * ph), fill=160)
    alpha = Image.fromarray(np.maximum(np.asarray(keep_img), np.asarray(shadow)))
    return Image.composite(painted, bg, alpha.filter(ImageFilter.GaussianBlur(max(1, grow))))


def check(bg: Image.Image, painted: Image.Image, box, entry: dict, models: GenModels, cfg: dict):
    """(image, labels, reason): the person found where planned, cleaned up, sized and dressed as asked."""
    people = [d for d in models.detector.detect(painted) if d[0] == "person" and iou(d[1], box) >= 0.4]
    if not people:
        return None, [], "g3: painted person not detected where planned"
    p = max(people, key=lambda d: iou(d[1], box))
    result = keep_person_only(bg, painted, p[1], models)
    dets = models.detector.detect(result)
    people = [d for d in dets if d[0] == "person" and iou(d[1], p[1]) >= 0.5]
    if not people:
        return None, [], "g3: person lost after clean-up"
    p = max(people, key=lambda d: iou(d[1], box))
    ratio = (p[1][3] - p[1][1]) / (box[3] - box[1])
    ppe_ok, ppe_labels = ppe_matches(dets, p[1], entry["wants"], models.low_detector.detect(result))
    # CLIP must agree with the prompt on the head and the torso (corroborates low-threshold boxes)
    x1, y1, x2, y2 = p[1]
    ph = y2 - y1
    head = result.crop((int(x1), int(y1), int(x2), int(y1 + 0.2 * ph)))
    torso = result.crop((int(x1), int(y1 + 0.18 * ph), int(x2), int(y1 + 0.6 * ph)))
    bare, plain = models.clip.bare_head(head), models.clip.ordinary_clothes(torso)
    wants = entry["wants"]
    clip_ok = (bare < 0.5) == wants["helmet"] and (plain < 0.5) == wants["vest"]
    g1 = models.clip.is_photo(result)
    entry.update(height_ratio=round(ratio, 3), g1_photo=round(g1, 3), clip_bare_head=round(bare, 3),
                 clip_plain_clothes=round(plain, 3),
                 dets=[[d[0], [round(v, 1) for v in d[1]], round(d[2], 3)] for d in dets])
    if not cfg.get("min_height_ratio", 0.75) <= ratio <= cfg.get("max_height_ratio", 1.25):
        return result, [], "g3: painted person's size differs from the plan"
    if not ppe_ok:
        return result, [], "g3: detected PPE does not match the prompt"
    if not clip_ok:
        return result, [], "g1: CLIP sees other PPE than prompted"
    if g1 < 0.5:
        return result, [], "g1: not photo-like"
    return result, [Label("person", *p[1])] + ppe_labels, ""


def run(sid: str, n: int, seed: int) -> None:
    cfg = scenario(sid)
    out_ok, out_bad = SYNTH / "filtered" / sid, SYNTH / "rejected" / sid
    if not BACKGROUNDS.exists() or not POSES.exists():
        raise SystemExit("needs the background pool and pose library: python -m telecomsafe.gen.scene backgrounds; "
                         "python -m telecomsafe.gen.scene_gen poses")
    pool = json.loads(BACKGROUNDS.read_text(encoding="utf-8"))
    poses = json.loads(POSES.read_text(encoding="utf-8"))
    done = done_bases(out_ok, out_bad)
    jobs = [k for k in range(n) if f"{seed}:{k}" not in done]
    order = shuffled(range(len(pool)), seed)
    print(f"{sid}: {len(jobs)} images to make, {len(pool)} backgrounds, {len(poses)} poses", flush=True)
    models = GenModels(cfg)
    root = SYNTH.parents[1]
    depth_cache: dict[str, np.ndarray] = {}
    stats = {"passed": 0, "rejected": 0}
    t0 = time.time()
    for k in jobs:
        rng = random.Random(seed * 100003 + k)
        bgr = pool[order[k % len(pool)]]
        pose = rng.choice(poses)
        bg = Image.open(root / bgr["file"]).convert("RGB")
        if bgr["file"] not in depth_cache:
            depth_cache = {bgr["file"]: models.depth(bg)}  # one at a time: backgrounds cycle in order
        meta = {"scenario": sid, "base": f"{seed}:{k}", "seed": seed, "pose_from": pose["base"],
                "background": {k_: bgr[k_] for k_ in ("file", "scene", "licence", "creator", "landing_url", "attribution")}}
        stem = f"{Path(bgr['file']).stem}__s{seed}_{k:05d}"
        ok, labels, result, entry = False, [], None, {}
        for attempt in range(cfg.get("retries", 2)):  # a new seed (placement, PPE, noise) when one fails
            painted, box, entry = generate(bg, depth_cache[bgr["file"]], pose, models, cfg,
                                           seed * 100003 + k + 7919 * attempt)
            entry["attempt"] = attempt
            if painted is None:
                meta["reason"] = entry.get("skipped", "generation failed")
                break
            out, labels, reason = check(bg, painted, box, entry, models, cfg)
            result = out if out is not None else painted
            meta["reason"] = reason
            if not reason:
                ok = True
                del meta["reason"]
                break
        meta["edit"] = entry
        write_record((out_ok if ok else out_bad) / stem, result if result is not None else bg, labels, meta)
        stats["passed" if ok else "rejected"] += 1
        print(f"  {k + 1}/{n} {Path(bgr['file']).name[:28]} → {'ok' if ok else meta['reason']} ({time.time() - t0:.0f}s)",
              flush=True)
    (SYNTH / f"{sid}_last_run.json").write_text(
        json.dumps({**stats, "jobs": len(jobs), "seconds": round(time.time() - t0)}), encoding="utf-8")
    print(f"{sid}: {stats} in {time.time() - t0:.0f}s → {out_ok}", flush=True)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["poses", "telecom_scene_generate"])
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--limit", type=int, default=1500, help="poses: base images to scan")
    args = ap.parse_args(argv)
    if args.command == "poses":
        print(f"{len(build_poses(args.limit, args.seed))} poses → {POSES}")
    else:
        run(args.command, args.n, args.seed)


if __name__ == "__main__":
    main()
