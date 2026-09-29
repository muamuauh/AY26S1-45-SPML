"""Read YOLO / COCO / VOC datasets into one in-memory representation.

Boxes are absolute pixel coordinates (x1, y1, x2, y2) with the dataset's own
class names; mapping to the project's target classes happens in build.py.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from PIL import Image

from telecomsafe.paths import IMAGE_SUFFIXES


@dataclass
class Box:
    cls: str
    x1: float
    y1: float
    x2: float
    y2: float
    conf: float = 1.0
    pseudo: bool = False


@dataclass
class Sample:
    image: Path
    width: int
    height: int
    boxes: list[Box] = field(default_factory=list)
    source: str = ""


def image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as im:  # reads the header only
        return im.size


def _find_yolo_names(root: Path) -> list[str] | None:
    for cfg in sorted(root.rglob("*.yaml")):
        try:
            data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError):
            continue
        names = data.get("names") if isinstance(data, dict) else None
        if isinstance(names, dict):
            return [names[k] for k in sorted(names)]
        if isinstance(names, list):
            return names
    return None


def read_yolo(root: Path, names: list[str] | None = None) -> list[Sample]:
    """Every image under an ``images`` directory whose sibling ``labels`` directory exists.

    An image without a label file is a background image (no objects), as in YOLO.
    Class names come from a data.yaml inside the dataset, falling back to ``names``.
    """
    found = _find_yolo_names(root)
    names = found or names
    if not names:
        raise ValueError(f"{root}: no data.yaml with 'names' found and no names given in sources.yaml")

    samples = []
    for img in sorted(p for p in root.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES):
        parts = list(img.parts)
        if "images" not in parts:
            continue
        i = len(parts) - 1 - parts[::-1].index("images")
        labels_dir = Path(*parts[:i], "labels", *parts[i + 1 : -1])
        if not labels_dir.is_dir():
            continue
        w, h = image_size(img)
        boxes = []
        label = labels_dir / (img.stem + ".txt")
        if label.exists():
            for line in label.read_text(encoding="utf-8").splitlines():
                vals = line.split()
                if len(vals) < 5:
                    continue
                cid, cx, cy, bw, bh = int(vals[0]), *map(float, vals[1:5])
                boxes.append(Box(names[cid], (cx - bw / 2) * w, (cy - bh / 2) * h, (cx + bw / 2) * w, (cy + bh / 2) * h))
        samples.append(Sample(img, w, h, boxes))
    return samples


def read_coco(root: Path) -> list[Sample]:
    samples = []
    for ann_file in sorted(root.rglob("*.json")):
        data = json.loads(ann_file.read_text(encoding="utf-8"))
        if not all(k in data for k in ("images", "annotations", "categories")):
            continue
        cats = {c["id"]: c["name"] for c in data["categories"]}
        by_image: dict[int, list[Box]] = {}
        for a in data["annotations"]:
            x, y, bw, bh = a["bbox"]
            by_image.setdefault(a["image_id"], []).append(Box(cats[a["category_id"]], x, y, x + bw, y + bh))
        for im in data["images"]:
            path = _locate(ann_file.parent, im["file_name"])
            if path is None:
                continue
            samples.append(Sample(path, im["width"], im["height"], by_image.get(im["id"], [])))
    return samples


def read_voc(root: Path) -> list[Sample]:
    samples = []
    for xml_file in sorted(root.rglob("*.xml")):
        tree = ET.parse(xml_file).getroot()
        if tree.tag != "annotation":
            continue
        filename = tree.findtext("filename") or (xml_file.stem + ".jpg")
        path = _locate(xml_file.parent.parent, filename) or _locate(xml_file.parent, filename)
        if path is None:
            continue
        size = tree.find("size")
        if size is not None and int(size.findtext("width", "0")) > 0:
            w, h = int(size.findtext("width")), int(size.findtext("height"))
        else:
            w, h = image_size(path)
        boxes = []
        for obj in tree.iter("object"):
            bb = obj.find("bndbox")
            boxes.append(Box(obj.findtext("name").strip(), *(float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))))
        samples.append(Sample(path, w, h, boxes))
    return samples


def _locate(base: Path, file_name: str) -> Path | None:
    direct = base / file_name
    if direct.exists():
        return direct
    matches = list(base.rglob(Path(file_name).name))
    return matches[0] if matches else None


def read_source(fmt: str, root: Path, names: list[str] | None = None) -> list[Sample]:
    if fmt == "yolo":
        return read_yolo(root, names)
    if fmt == "coco":
        return read_coco(root)
    if fmt == "voc":
        return read_voc(root)
    raise ValueError(f"unknown format {fmt!r}; expected yolo, coco or voc")
