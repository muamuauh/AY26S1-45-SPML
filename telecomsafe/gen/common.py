"""Shared pieces of the generation pipeline: labels, scenarios, base images, output records.

Every synthetic image is written with a YOLO label file and a JSON sidecar recording how it was made
(scenario, base image, seed, prompt, gate scores), so any image in a report can be traced and regenerated.
Heavy libraries (torch, diffusers) are imported only where a model is loaded, so these helpers and their
tests run in the training environment too.
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from telecomsafe.paths import CONFIGS, DATA, PROCESSED, class_names, load_yaml

TRAIN_IMAGES = PROCESSED / "yolo" / "images" / "train"
TRAIN_LABELS = PROCESSED / "yolo" / "labels" / "train"
SYNTH = DATA / "synth"


@dataclass
class Label:
    cls: str
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def box(self) -> tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    @property
    def w(self) -> float:
        return self.x2 - self.x1

    @property
    def h(self) -> float:
        return self.y2 - self.y1


def read_labels(path: Path, width: int, height: int, names: list[str] | None = None) -> list[Label]:
    names = names or class_names()
    out = []
    for line in path.read_text(encoding="utf-8").splitlines() if path.exists() else []:
        parts = line.split()
        if len(parts) < 5:
            continue
        c, cx, cy, bw, bh = int(parts[0]), *(float(v) for v in parts[1:5])
        out.append(Label(names[c], (cx - bw / 2) * width, (cy - bh / 2) * height,
                         (cx + bw / 2) * width, (cy + bh / 2) * height))
    return out


def write_labels(path: Path, labels: list[Label], width: int, height: int, names: list[str] | None = None) -> None:
    names = names or class_names()
    lines = []
    for lb in labels:
        x1, y1 = max(0.0, lb.x1), max(0.0, lb.y1)
        x2, y2 = min(float(width), lb.x2), min(float(height), lb.y2)
        if x2 - x1 < 1 or y2 - y1 < 1:
            continue
        lines.append(f"{names.index(lb.cls)} {(x1 + x2) / 2 / width:.6f} {(y1 + y2) / 2 / height:.6f} "
                     f"{(x2 - x1) / width:.6f} {(y2 - y1) / height:.6f}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def iou(a, b) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def load_scenarios(path: Path = CONFIGS / "scenarios.yaml") -> dict:
    return load_yaml(path)


def scenario(sid: str, path: Path = CONFIGS / "scenarios.yaml") -> dict:
    cfg = load_scenarios(path)
    for s in cfg["scenarios"]:
        if s["id"] == sid:
            return {**cfg.get("defaults", {}), **s}
    raise KeyError(f"no scenario {sid!r} in {path}")


def source_of(image: Path) -> str:
    """Build output names start with the source dataset: <source>__<stem>_<hash>.<ext>."""
    return image.name.split("__", 1)[0]


def select_bases(cfg: dict, images: Path = TRAIN_IMAGES, labels: Path = TRAIN_LABELS, sizes=None,
                 exclude_sources: tuple[str, ...] = ()) -> list[Path]:
    """Training images that satisfy the scenario's `base` rules (only training images are ever used).

    `sizes` maps image path → (width, height); by default the size is read from the file."""
    from PIL import Image

    rules = cfg.get("base", {})
    exclude_sources = tuple(exclude_sources) + tuple(rules.get("exclude_sources", []))
    need = set(rules.get("require", []))
    avoid = set(rules.get("exclude", []))
    out = []
    for img in sorted(images.iterdir()):
        if source_of(img) in exclude_sources:
            continue
        if sizes is not None:
            w, h = sizes[img]
        else:
            with Image.open(img) as im:
                w, h = im.size
        lbs = read_labels(labels / f"{img.stem}.txt", w, h)
        present = {lb.cls for lb in lbs}
        if not need <= present or avoid & present:
            continue
        if sum(lb.cls == "person" for lb in lbs) > rules.get("max_people", 99):
            continue
        if not all(_sized(lbs, cls, rules[key], h, cfg.get(f"min_{cls}_px", 0))
                   for key in rules if key.endswith("_height") for cls in [key[: -len("_height")]]):
            continue
        out.append(img)
    return out


def _sized(labels: list[Label], cls: str, bounds, image_height: int, min_px: float) -> bool:
    """Every box of `cls` is between bounds[0] and bounds[1] of the image height and at least min_px tall."""
    lo, hi = bounds
    return all(lo * image_height <= lb.h <= hi * image_height and lb.h >= min_px for lb in labels if lb.cls == cls)


def shuffled(items: list, seed: int) -> list:
    items = list(items)
    random.Random(seed).shuffle(items)
    return items


def record_paths(stem: Path) -> dict[str, Path]:
    """<stem>.jpg / .txt / .json. Suffixes are appended, never substituted: Roboflow stems contain dots
    (IMG_122_jpg.rf.9e7c…), and Path.with_suffix would cut them and make different images collide."""
    return {ext: stem.parent / f"{stem.name}{ext}" for ext in (".jpg", ".txt", ".json")}


def write_record(stem: Path, image, labels: list[Label], meta: dict) -> None:
    """<stem>.jpg + <stem>.txt (YOLO) + <stem>.json (how it was made)."""
    paths = record_paths(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    image.save(paths[".jpg"], quality=95)
    write_labels(paths[".txt"], labels, *image.size)
    meta = {**meta, "labels": [asdict(lb) for lb in labels]}
    paths[".json"].write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")


def reject_record(stem: Path, rejected: Path, reason: str) -> None:
    """Move an accepted record (<stem>.jpg/.txt/.json) to the rejected folder, noting why."""
    rejected.mkdir(parents=True, exist_ok=True)
    for ext, path in record_paths(stem).items():
        if not path.exists():
            continue
        if ext == ".json":
            meta = json.loads(path.read_text(encoding="utf-8"))
            meta["reason"] = reason
            (rejected / path.name).write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")
            path.unlink()
        else:
            path.replace(rejected / path.name)


def done_bases(*folders: Path) -> set[str]:
    """Base image names already processed (from the records' `base` field)."""
    out = set()
    for d in folders:
        for p in d.glob("*.json") if d.exists() else []:
            out.add(json.loads(p.read_text(encoding="utf-8")).get("base", ""))
    return out
