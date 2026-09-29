"""Draw the (mapped) labels of random samples per source for a manual check.

    python -m telecomsafe.data.audit                     # 50 images per enabled source
    python -m telecomsafe.data.audit --sources chv -n 20

Output: runs/audit/<source>/*.jpg. Thick boxes are real labels; thin boxes tagged
"(pseudo)" are teacher pseudo labels. Look for wrong mappings (e.g. a helmet labelled as head),
missing boxes and boxes on the wrong object; fix class_map or disable the source.
"""

from __future__ import annotations

import argparse
import json
import random

from PIL import Image, ImageDraw

from telecomsafe.data.build import map_classes, merge_pseudo, pseudo_path
from telecomsafe.data.readers import read_source
from telecomsafe.paths import ROOT, class_names, load_sources, resolve

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948", "#52514e"]


def draw(sample, targets: list[str]) -> Image.Image:
    im = Image.open(sample.image).convert("RGB")
    d = ImageDraw.Draw(im)
    lw = max(2, round(max(im.size) / 400))
    for b in sample.boxes:
        color = PALETTE[targets.index(b.cls) % len(PALETTE)]
        d.rectangle((b.x1, b.y1, b.x2, b.y2), outline=color, width=1 if b.pseudo else lw)
        d.text((b.x1 + 2, max(0, b.y1 - 12)), b.cls + (" (pseudo)" if b.pseudo else ""), fill=color)
    return im


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", nargs="*")
    ap.add_argument("-n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    targets = class_names()

    for cfg in load_sources():
        if not cfg.get("enabled") or cfg.get("role") == "unused":
            continue
        if args.sources and cfg["name"] not in args.sources:
            continue
        root = resolve(cfg["path"])
        if not root.exists():
            continue
        samples = read_source(cfg["format"], root, cfg.get("names"))
        map_classes(samples, cfg.get("class_map") or {}, targets, cfg["name"])
        if pseudo_path(cfg["name"]).exists():
            merge_pseudo(samples, json.loads(pseudo_path(cfg["name"]).read_text(encoding="utf-8")), set(cfg.get("annotates") or []))
        out = ROOT / "runs" / "audit" / cfg["name"]
        out.mkdir(parents=True, exist_ok=True)
        for s in random.Random(args.seed).sample(samples, min(args.n, len(samples))):
            draw(s, targets).save(out / f"{s.image.stem}.jpg", quality=85)
        print(f"  {cfg['name']}: {min(args.n, len(samples))} images → {out}")


if __name__ == "__main__":
    main()
