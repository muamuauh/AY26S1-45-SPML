"""Teacher pseudo-labels for classes a source does not annotate.

    python -m telecomsafe.data.pseudo_label --weights runs/phase1/teacher/weights/best.pt
    python -m telecomsafe.data.pseudo_label --weights ... --images data/raw/t3_candidates/images \
        --yolo-out data/raw/t3_candidates/prelabels      # pre-annotation for Label Studio

Mode 1 writes data/interim/pseudo/<source>.json, merged by build.py. Only classes
outside the source's `annotates` list are kept, so real labels are never overridden.
Mode 2 writes YOLO txt files (+ classes.txt) for importing into Label Studio.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from telecomsafe.data.build import map_classes, pseudo_path
from telecomsafe.data.readers import read_source
from telecomsafe.paths import IMAGE_SUFFIXES, class_names, load_sources, resolve


def predict(model, images: list[Path], conf: float, batch: int = 16):
    for i in range(0, len(images), batch):
        chunk = images[i : i + batch]
        for path, r in zip(chunk, model.predict([str(p) for p in chunk], conf=conf, verbose=False)):
            names = r.names
            yield path, r, [
                (names[int(c)], *map(float, xyxy), float(s))
                for xyxy, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())
            ]


def label_sources(model, sources: list[str] | None, conf: float) -> None:
    targets = class_names()
    for cfg in load_sources():
        if not cfg.get("enabled") or cfg.get("role") != "train":
            continue
        if sources and cfg["name"] not in sources:
            continue
        missing = set(targets) - set(cfg.get("annotates") or [])
        if not missing:
            continue
        root = resolve(cfg["path"])
        if not root.exists():
            print(f"  ! {cfg['name']}: not downloaded, skipped")
            continue
        samples = read_source(cfg["format"], root, cfg.get("names"))
        map_classes(samples, cfg.get("class_map") or {}, targets, cfg["name"])
        out: dict[str, list] = {}
        n = 0
        for path, _, dets in predict(model, [s.image for s in samples], conf):
            keep = [list(d) for d in dets if d[0] in missing]
            if keep:
                out[str(path)] = keep
                n += len(keep)
        dst = pseudo_path(cfg["name"])
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(out), encoding="utf-8")
        print(f"  {cfg['name']}: {n} pseudo boxes for {sorted(missing)} → {dst}")


# COCO classes a stock COCO-pretrained YOLO detects reliably, mapped to target classes.
COCO_MAP = {"car": "vehicle", "truck": "vehicle", "bus": "vehicle", "motorcycle": "vehicle"}


def label_folder(model, folder: Path, out: Path, conf: float, coco_model=None) -> dict[str, list]:
    """Pre-label every image in `folder`; writes YOLO txt files and returns {image: [(cls, x1, y1, x2, y2, conf)]}.

    `coco_model` (optional) adds classes the teacher does not know (see COCO_MAP).
    """
    targets = class_names()
    out.mkdir(parents=True, exist_ok=True)
    (out / "classes.txt").write_text("\n".join(targets) + "\n", encoding="utf-8")
    images = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    teacher_classes = set(model.names.values())
    extra: dict[Path, list] = {}
    if coco_model is not None:
        for path, _, dets in predict(coco_model, images, conf):
            extra[path] = [(COCO_MAP[d[0]], *d[1:]) for d in dets
                           if d[0] in COCO_MAP and COCO_MAP[d[0]] not in teacher_classes]
    labels: dict[str, list] = {}
    for path, r, dets in predict(model, images, conf):
        h, w = r.orig_shape
        dets = [d for d in dets if d[0] in targets] + extra.get(path, [])
        labels[str(path)] = dets
        lines = [
            f"{targets.index(c)} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} {(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}"
            for c, x1, y1, x2, y2, _ in dets
        ]
        (out / f"{path.stem}.txt").write_text("\n".join(lines), encoding="utf-8")
    print(f"pre-labels for {len(images)} images → {out}")
    return labels


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--sources", nargs="*", help="limit to these sources (mode 1)")
    ap.add_argument("--images", help="folder of images to pre-label (mode 2)")
    ap.add_argument("--yolo-out", help="output folder for YOLO pre-labels (mode 2)")
    ap.add_argument("--coco-weights", default="yolo11x.pt",
                    help="COCO-pretrained model adding vehicle boxes in mode 2 ('' to disable)")
    args = ap.parse_args(argv)

    from ultralytics import YOLO

    model = YOLO(args.weights)
    if args.images:
        coco = YOLO(args.coco_weights) if args.coco_weights else None
        label_folder(model, Path(args.images), Path(args.yolo_out or Path(args.images).parent / "prelabels"), args.conf, coco)
    else:
        label_sources(model, args.sources, args.conf)


if __name__ == "__main__":
    main()
