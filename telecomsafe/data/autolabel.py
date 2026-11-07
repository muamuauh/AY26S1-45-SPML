"""Label generated images automatically: detectors draw the boxes, a vision-language model decides the classes.

    python -m telecomsafe.data.autolabel <folder>                 # <folder>/images → <folder>/labels + autolabel.jsonl
    python -m telecomsafe.data.autolabel <folder> --only a.png b.png

Boxes come from detectors, because chat VLMs are poor at coordinates:
  people      E2 person ∪ COCO person (YOLO11x), merged
  head/torso  E2's helmet / no_helmet / vest / no_vest box on that person when there is one, else YOLO11-pose
              keypoints (head from nose/eyes/ears, torso from shoulders to hips)
  harness     E2's harness box when there is one, else shoulders to upper thighs from the pose keypoints
  vehicles    E2 machinery / vehicle ∪ COCO car / truck / bus
The VLM (VLM_API_BASE / VLM_API_MODEL / VLM_API_KEY in .env, any OpenAI-compatible chat endpoint) sees the image
with numbered boxes plus a crop of every person, and answers per box: is it a person; helmet, hi-vis and harness
(or not visible); machinery, ordinary vehicle or neither; and how many people / vehicles were missed. Its answers
pick the classes: a head gets helmet or no_helmet, a torso vest or no_vest, a harness box only when it says
harness. Everything it said is kept in autolabel.jsonl, and images it reports missed objects in are flagged for
the human spot check (telecomsafe.data.synth expects a person to check a sample of every submission).
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont

from telecomsafe.env import load_env
from telecomsafe.paths import IMAGE_SUFFIXES, INTERIM, ROOT, class_names

E2_WEIGHTS = ROOT / "runs" / "phase1" / "e2" / "weights" / "best.pt"
POSE_WEIGHTS = INTERIM / "models" / "yolo11n-pose.pt"
PROMPT = """You check labels for a construction-safety dataset. Image 1 is a photo with numbered boxes:
P1, P2, ... are candidate people; V1, V2, ... are candidate vehicles. Image 2 shows a crop of every P box, labelled with its number.
Answer only with JSON of this form:
{"people": [{"id": 1, "person": true, "role": "worker" | "bystander", "helmet": "safety_helmet" | "none" | "not_visible",
             "hi_vis": "yes" | "no" | "not_visible", "harness": "yes" | "no" | "not_visible"}],
 "vehicles": [{"id": 1, "kind": "machinery" | "vehicle" | "neither"}],
 "missed_people": 0, "missed_vehicles": 0}
Rules: person = a real human (not a statue, poster or reflection). role: "worker" for anyone doing, helping with or
supervising the job (climbing, on the structure or roof, at the truck, holding a rope, standing by with tools);
"bystander" for passers-by who are not part of the job (pedestrians, cyclists, drivers, people on a distant street).
helmet: "safety_helmet" for a hard hat or climbing helmet
worn on the head; "none" for a bare head, cap, hood or headscarf; "not_visible" if the head cannot be seen.
hi_vis: "yes" only for a high-visibility vest or jacket with reflective strips. harness: "yes" for a full-body safety
harness worn on the body (shoulder, chest and leg straps). vehicles: "machinery" for bucket trucks, cranes, aerial work
platforms, excavators, cable-drum trailers and similar; "vehicle" for ordinary cars, vans, pickups and plain trucks.
missed_people / missed_vehicles: how many clearly visible people / vehicles have no box at all."""
COCO_VEHICLES = {"car", "truck", "bus"}


def iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    return i / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i + 1e-9)


def inside(pt, b, margin: float = 0.0) -> bool:
    return b[0] - margin <= pt[0] <= b[2] + margin and b[1] - margin <= pt[1] <= b[3] + margin


def centre(b):
    return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def same_object(a, b, thr: float = 0.5, contain: float = 0.8) -> bool:
    """Overlapping boxes, or one mostly inside the other (a partial box of the same person)."""
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    small = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return iou(a, b) >= thr or ix * iy / (small + 1e-9) >= contain


def merge(primary: list, extra: list) -> list:
    """Boxes in priority order (primary, then extra; each by confidence), dropping repeats of a kept box."""
    kept = []
    for b in list(primary) + list(extra):
        if not any(same_object(b, k) for k in kept):
            kept.append(b)
    return kept


# ---------------------------------------------------------------- geometry (pure, tested)
def head_box(person, kp=None, conf=None):
    x1, y1, x2, y2 = person
    w, h = x2 - x1, y2 - y1
    if kp is not None:
        pts = [kp[k] for k in range(5) if conf[k] > 0.4]
        if pts:
            # fitted to E2's head boxes (328 people): a square of side ~ face-keypoint spread and person height,
            # centred 0.35 of its side above the face keypoints (the box takes in hair and helmet)
            pts = np.array(pts)
            size = 1.125 * np.ptp(pts[:, 0]) + 0.0875 * h
            cx, cy = pts[:, 0].mean(), pts[:, 1].mean() - 0.35 * size
            return [max(x1, cx - size / 2), max(y1, cy - size / 2), min(x2, cx + size / 2), min(y2, cy + size / 2)]
    return [x1 + 0.28 * w, y1, x2 - 0.28 * w, y1 + 0.17 * h]


def torso_box(person, kp=None, conf=None):
    x1, y1, x2, y2 = person
    w, h = x2 - x1, y2 - y1
    if kp is not None:
        sh = [kp[k] for k in (5, 6) if conf[k] > 0.4]
        hp = [kp[k] for k in (11, 12) if conf[k] > 0.4]
        if sh:
            pts = np.array(sh + hp)
            top = min(p[1] for p in sh)
            bottom = max(p[1] for p in hp) if hp else top + 0.35 * h
            pad = max(0.12 * np.ptp(pts[:, 0]), 0.06 * w)
            return [max(x1, pts[:, 0].min() - pad), max(y1, top - 0.03 * h), min(x2, pts[:, 0].max() + pad), min(y2, bottom + 0.02 * h)]
    return [x1 + 0.08 * w, y1 + 0.17 * h, x2 - 0.08 * w, y1 + 0.55 * h]


def harness_box(person, kp=None, conf=None):
    """Shoulder straps to leg loops: the torso box stretched down to the upper thighs."""
    t = torso_box(person, kp, conf)
    x1, y1, x2, y2 = person
    knees = [kp[k] for k in (13, 14) if kp is not None and conf[k] > 0.4]
    thigh = (t[3] + 0.4 * (max(k[1] for k in knees) - t[3])) if knees else t[3] + 0.12 * (y2 - y1)
    return [t[0], t[1], t[2], min(y2, thigh)]


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON in: {text[:200]}")
    return json.loads(m.group(0))


def to_labels(people: list, heads: list, torsos: list, harnesses: list, vehicles: list, answer: dict) -> list[tuple[str, list]]:
    """Turn the VLM's answers into (class, box) labels. Bystanders get a person box only: the PPE classes describe
    the workers (phase 2 rule, docs/guides/Phase2-Synth-Task-EN.md)."""
    by_p = {int(p.get("id", 0)): p for p in answer.get("people", [])}
    by_v = {int(v.get("id", 0)): v for v in answer.get("vehicles", [])}
    out = []
    for i, box in enumerate(people, 1):
        a = by_p.get(i)
        if not a or not a.get("person", False):
            continue
        out.append(("person", box))
        if a.get("role") == "bystander":
            continue
        if a.get("helmet") in ("safety_helmet", "none"):
            out.append(("helmet" if a["helmet"] == "safety_helmet" else "no_helmet", heads[i - 1]))
        if a.get("hi_vis") in ("yes", "no"):
            out.append(("vest" if a["hi_vis"] == "yes" else "no_vest", torsos[i - 1]))
        if a.get("harness") == "yes":
            out.append(("harness", harnesses[i - 1]))
    for i, box in enumerate(vehicles, 1):
        kind = by_v.get(i, {}).get("kind")
        if kind in ("machinery", "vehicle"):
            out.append((kind, box))
    return out


# ---------------------------------------------------------------- models and the VLM
class Labeller:
    def __init__(self):
        from ultralytics import YOLO

        load_env()
        self.e2 = YOLO(str(E2_WEIGHTS))
        self.coco = YOLO("yolo11x.pt")
        self.pose = YOLO(str(POSE_WEIGHTS) if POSE_WEIGHTS.exists() else "yolo11n-pose.pt")
        base = os.environ.get("VLM_API_BASE", "").rstrip("/")
        self.url = base if base.endswith("/chat/completions") else base + "/chat/completions"
        self.model, self.key = os.environ.get("VLM_API_MODEL"), os.environ.get("VLM_API_KEY")
        if not (base and self.model and self.key):
            sys.exit("set VLM_API_BASE / VLM_API_MODEL / VLM_API_KEY in .env")
        self.s = requests.Session()
        try:
            self.font = ImageFont.truetype("arialbd.ttf", 28)
        except OSError:
            self.font = ImageFont.load_default()

    def detect(self, im):
        def run(model, conf):
            r = model.predict(im, conf=conf, verbose=False)[0]
            return [(r.names[int(c)], b, float(s)) for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]
        e2 = run(self.e2, 0.25)
        e2_low = run(self.e2, 0.1)  # head and torso boxes: E2 places them well even when unsure of the class
        coco = run(self.coco, 0.3)
        people = merge([b for c, b, _ in e2 if c == "person"], [b for c, b, _ in coco if c == "person"])
        vehicles = merge([b for c, b, _ in e2 if c in ("machinery", "vehicle")], [b for c, b, _ in coco if c in COCO_VEHICLES])
        pose = self.pose.predict(im, verbose=False)[0].keypoints
        figs = list(zip(pose.xy.cpu().numpy(), pose.conf.cpu().numpy())) if pose is not None and pose.conf is not None else []
        heads, torsos, harnesses = [], [], []
        for p in people:
            fig = max(figs, key=lambda f: sum(c for (x, y), c in zip(f[0], f[1]) if c > 0.3 and inside((x, y), p)), default=None)
            kp, cf = fig if fig is not None and sum(c > 0.3 and inside(xy, p) for xy, c in zip(fig[0], fig[1])) >= 4 else (None, None)
            own = lambda names, dets=e2: [b for c, b, _ in dets if c in names and inside(centre(b), p)]  # noqa: E731
            h = own(("helmet", "no_helmet"), e2_low)
            t = own(("vest", "no_vest"), e2_low)
            hz = own(("harness",))
            heads.append(min(h, key=lambda b: b[1]) if h else head_box(p, kp, cf))
            torsos.append(max(t, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if t else torso_box(p, kp, cf))
            harnesses.append(max(hz, key=lambda b: (b[2] - b[0]) * (b[3] - b[1])) if hz else harness_box(p, kp, cf))
        return people, heads, torsos, harnesses, vehicles

    def sheets(self, im, people, vehicles) -> list[str]:
        """Image 1: the photo with numbered boxes; image 2: the person crops. Base64 JPEGs."""
        a = im.copy()
        d = ImageDraw.Draw(a)
        lw = max(3, a.width // 300)
        for i, b in enumerate(people, 1):
            d.rectangle(b, outline=(0, 160, 255), width=lw)
            d.text((b[0] + 4, b[1] + 2), f"P{i}", fill=(0, 160, 255), font=self.font, stroke_width=3, stroke_fill="black")
        for i, b in enumerate(vehicles, 1):
            d.rectangle(b, outline=(255, 140, 0), width=lw)
            d.text((b[0] + 4, b[1] + 2), f"V{i}", fill=(255, 140, 0), font=self.font, stroke_width=3, stroke_fill="black")
        a.thumbnail((1280, 1280))
        crops = []
        for i, b in enumerate(people, 1):
            pad = 0.15 * (b[3] - b[1])
            c = im.crop((max(0, b[0] - pad), max(0, b[1] - pad), min(im.width, b[2] + pad), min(im.height, b[3] + pad)))
            c = c.resize((max(1, round(c.width * 320 / c.height)), 320))
            crops.append((i, c))
        sheet = Image.new("RGB", (max(1, sum(c.width + 10 for _, c in crops)), 360), "white")
        x = 0
        for i, c in crops:
            sheet.paste(c, (x, 36))
            ImageDraw.Draw(sheet).text((x + 4, 2), f"P{i}", fill="black", font=self.font)
            x += c.width + 10
        out = []
        for img in (a, sheet):
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=88)
            out.append(base64.b64encode(buf.getvalue()).decode())
        return out

    def ask(self, images: list[str]) -> tuple[dict, dict]:
        content = [{"type": "text", "text": PROMPT}] + [
            {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b}} for b in images]
        for attempt in range(3):
            try:
                r = self.s.post(self.url, headers={"Authorization": f"Bearer {self.key}"}, timeout=300,
                                json={"model": self.model, "temperature": 0, "messages": [{"role": "user", "content": content}]})
                j = r.json()
                return parse_json(j["choices"][0]["message"]["content"]), j.get("usage", {})
            except (requests.RequestException, KeyError, IndexError, ValueError) as e:
                last = e
                time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"VLM failed: {last!r}")


def write_yolo(path: Path, labels: list, w: int, h: int) -> None:
    names = class_names()
    lines = []
    for c, (x1, y1, x2, y2) in labels:
        x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, x2), min(h, y2)
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        lines.append(f"{names.index(c)} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(folder: Path, only: list[str] | None = None, workers: int = 4) -> None:
    lab = Labeller()
    (folder / "labels").mkdir(exist_ok=True)
    log = folder / "autolabel.jsonl"
    done = set()
    if log.exists() and not only:
        done = {json.loads(l)["file"] for l in log.read_text(encoding="utf-8").splitlines() if l.strip()}
    imgs = [p for p in sorted((folder / "images").iterdir()) if p.suffix.lower() in IMAGE_SUFFIXES
            and p.name not in done and (not only or p.name in only)]
    print(f"{len(imgs)} images to label ({len(done)} done) with {lab.model}", flush=True)
    t0 = time.time()
    lock = threading.Lock()
    finished = [0]

    def label(p: Path, size: tuple, boxes: tuple, sheets: list[str]) -> None:  # the VLM call runs in a worker thread
        people, heads, torsos, harnesses, vehicles = boxes
        try:
            answer, usage = lab.ask(sheets)
        except RuntimeError as e:
            print(f"  ✗ {p.name}: {e}", file=sys.stderr, flush=True)
            return
        labels = to_labels(people, heads, torsos, harnesses, vehicles, answer)
        write_yolo(folder / "labels" / f"{p.stem}.txt", labels, *size)
        flag = bool(answer.get("missed_people") or answer.get("missed_vehicles"))
        with lock:
            f.write(json.dumps({"file": p.name, "people": len(people), "vehicles": len(vehicles), "answer": answer,
                                "labels": [[c, [round(float(v), 1) for v in b]] for c, b in labels], "flag_missed": flag,
                                "usage": usage}, ensure_ascii=False) + "\n")
            f.flush()
            finished[0] += 1
            print(f"  {finished[0]}/{len(imgs)} {p.name}: {len(labels)} boxes{'  ⚑ missed objects' if flag else ''}"
                  f" ({time.time() - t0:.0f}s)", flush=True)

    with open(log, "a", encoding="utf-8") as f, ThreadPoolExecutor(workers) as pool:
        pending = []
        for p in imgs:  # detection stays on the main thread (one GPU); at most 2 x workers images wait for the VLM
            im = Image.open(p).convert("RGB")
            boxes = lab.detect(im)
            pending.append(pool.submit(label, p, im.size, boxes, lab.sheets(im, boxes[0], boxes[4])))
            while len([x for x in pending if not x.done()]) >= 2 * workers:
                time.sleep(0.2)
        for x in pending:
            x.result()


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--workers", type=int, default=4, help="VLM calls in flight at once")
    args = ap.parse_args(argv)
    run(args.folder.resolve(), args.only, args.workers)


if __name__ == "__main__":
    main()
