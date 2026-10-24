"""Phase 2 synthetic training data (TelecomSynth): each member generates images for one weak class.

    python -m telecomsafe.data.synth prelabel <folder>                     # optional: E2 pre-labels in <folder>/labels/
    python -m telecomsafe.data.synth check <folder> --target no_helmet
    python -m telecomsafe.data.synth intake <folder> --contributor <name> --target no_helmet
    python -m telecomsafe.data.synth dataset [--max N]                     # data/processed/e3/dataset.yaml for E3

A submission uses the TelecomEval contribution format (images/, labels/, sources.csv; see
docs/guides/Phase2-Synth-Task-EN.md) with every image generated: method = generated, licence = GENERATED,
the model in `creator` and the full prompt in `notes`. On top of the contribution checks, `check` requires:

  - a short side of at least MIN_SIDE px (no crops from grids, no stretched or upscaled exports),
  - the target class in at least TARGET_SHARE of the images,
  - no near-duplicates inside the submission (pHash), and none of TelecomEval (the test set must stay unseen),
  - every visible instance of all 8 classes labelled (warned per image, as for TelecomEval).

`intake` copies a passing submission into data/synth/telecomsynth/ as <stem>__<contributor>.<ext> and records
contributor, target class and original name in its sources.csv; handing in again replaces that contributor's
images for that target only. `dataset` writes the E3 training set: the frozen training split plus TelecomSynth
(or N of its images), with the unchanged validation split.
"""

from __future__ import annotations

import argparse
import csv
import random
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

from telecomsafe.data import contrib
from telecomsafe.paths import IMAGE_SUFFIXES, PROCESSED, RAW, ROOT, class_names

SYNTH_DIR = ROOT / "data" / "synth" / "telecomsynth"
E3_DIR = PROCESSED / "e3"
TARGETS = ("no_helmet", "vehicle", "machinery", "harness", "no_vest")
MIN_SIDE = 1024
TARGET_SHARE = 0.8
DUP_DIST = 8
FIELDS = contrib.FIELDS + ["contributor", "target", "original_file"]


# ---------------------------------------------------------------- checks
def images_of(folder: Path) -> list[Path]:
    d = folder / "images"
    return sorted(p for p in d.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES) if d.is_dir() else []


def near_pairs(hashes: dict[str, int], others: dict[str, int] | None = None, dist: int = DUP_DIST) -> list[tuple[str, str]]:
    """Pairs of near-identical images: inside `hashes`, or between `hashes` and `others`."""
    items = list(hashes.items())
    if others is None:
        return [(a, b) for i, (a, x) in enumerate(items) for b, y in items[i + 1:] if bin(x ^ y).count("1") <= dist]
    return [(a, b) for a, x in items for b, y in others.items() if bin(x ^ y).count("1") <= dist]


def check(folder: Path, target: str, eval_dir: Path = RAW / "telecom_eval") -> tuple[list[str], list[str], Counter]:
    from PIL import Image

    if target not in TARGETS:
        return [f"target must be one of {', '.join(TARGETS)}"], [], Counter()
    errors, warnings, counts, rows = contrib.check(folder)
    names = class_names()
    tid = names.index(target)
    with_target = 0
    for row in rows:
        f = row.get("file", "")
        if row.get("method") != "generated":
            errors.append(f"{f}: every TelecomSynth image is generated (method = generated)")
        if not row.get("creator", "").strip():
            errors.append(f"{f}: put the image model in `creator`")
        if not row.get("notes", "").strip():
            errors.append(f"{f}: put the full prompt in `notes`")
    for img in images_of(folder):
        try:
            with Image.open(img) as im:
                side = min(im.size)
        except OSError:
            continue  # contrib.check already reported it
        if side < MIN_SIDE:
            errors.append(f"{img.name}: short side {side} px; generate at least {MIN_SIDE} px (no crops or upscaling)")
        label = folder / "labels" / f"{img.stem}.txt"
        if label.exists() and any(l.split()[0] == str(tid) for l in label.read_text(encoding="utf-8").splitlines() if l.strip()):
            with_target += 1
    n = len(images_of(folder))
    if n and with_target / n < TARGET_SHARE:
        errors.append(f"only {with_target}/{n} images contain a {target} box (at least {TARGET_SHARE:.0%} must)")
    mine = contrib.phashes(images_of(folder))
    for a, b in near_pairs(mine):
        errors.append(f"{Path(a).name} and {Path(b).name} are near-identical — keep one")
    if (eval_dir / "images").is_dir():
        for a, b in near_pairs(mine, contrib.phashes((eval_dir / "images").iterdir())):
            errors.append(f"{Path(a).name} is near-identical to TelecomEval's {Path(b).name} — the test set must stay unseen")
    return errors, [w for w in warnings if "recommended" not in w], counts


def report(folder: Path, target: str) -> bool:
    errors, warnings, counts = check(folder, target)
    names = class_names()
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"{len(images_of(folder))} images, target {target}; instances:", {names[k]: counts[k] for k in range(len(names))})
    print("✓ All checks passed" if not errors else f"✗ {len(errors)} errors")
    return not errors


# ---------------------------------------------------------------- optional pre-labels
def prelabel(folder: Path) -> None:
    """E2 (people and PPE) + a COCO model (vehicles) → <folder>/labels/, and a sources.csv to fill in."""
    from telecomsafe.data import pseudo_label

    imgs = images_of(folder)
    if not imgs:
        sys.exit(f"put the images in {folder / 'images'} first")
    pseudo_label.main(["--weights", str(ROOT / "runs" / "phase1" / "e2" / "weights" / "best.pt"),
                       "--images", str(folder / "images"), "--yolo-out", str(folder / "labels"), "--conf", "0.35"])
    sources = folder / "sources.csv"
    if not sources.exists():
        with open(sources, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=contrib.FIELDS)
            w.writeheader()
            w.writerows({"file": p.name, "subset": "telecom", "method": "generated", "licence": "GENERATED",
                         "creator": "", "notes": ""} for p in imgs)
    print(f"pre-labels for {len(imgs)} images in {folder / 'labels'} — check and correct every box;"
          f" fill creator (model) and notes (prompt) in {sources}")


# ---------------------------------------------------------------- intake
def read_sources(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def intake(folder: Path, contributor: str, target: str) -> None:
    if not report(folder, target):
        sys.exit("fix the errors above first")
    who = re.sub(r"[^A-Za-z0-9]+", "_", contributor).strip("_")
    rows = read_sources(folder / "sources.csv")
    old = read_sources(SYNTH_DIR / "sources.csv")
    replaced = [r for r in old if r["contributor"] == who and r["target"] == target]
    keep = [r for r in old if r not in replaced]
    for sub in ("images", "labels"):
        (SYNTH_DIR / sub).mkdir(parents=True, exist_ok=True)
    for r in replaced:  # handing in again replaces this contributor's images for this target
        (SYNTH_DIR / "images" / r["file"]).unlink(missing_ok=True)
        (SYNTH_DIR / "labels" / f"{Path(r['file']).stem}.txt").unlink(missing_ok=True)
    taken = {r["file"] for r in keep}
    new = []
    for r in rows:
        name = contrib.eval_name(r["file"], who)
        if name in taken:  # same file name already used by this contributor for another target
            name = contrib.eval_name(f"{target}_{r['file']}", who)
        shutil.copy2(folder / "images" / r["file"], SYNTH_DIR / "images" / name)
        shutil.copy2(folder / "labels" / f"{Path(r['file']).stem}.txt", SYNTH_DIR / "labels" / f"{Path(name).stem}.txt")
        new.append({**{k: r.get(k, "") for k in contrib.FIELDS}, "file": name, "contributor": who, "target": target,
                    "original_file": r.get("original_file") or r["file"]})
    allrows = sorted(keep + new, key=lambda r: (r["target"], r["contributor"], r["file"]))
    with open(SYNTH_DIR / "sources.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    by_target = Counter(r["target"] for r in allrows)
    print(f"merged {len(new)} {target} images from {who} → {SYNTH_DIR}  (TelecomSynth now: {dict(by_target)})")


# ---------------------------------------------------------------- E3 training set
def dataset(max_images: int | None = None, seed: int = 0, out: Path = E3_DIR) -> Path:
    """E3 = the frozen training split + TelecomSynth (or `max_images` of it, for the mix-ratio ablation)."""
    train = sorted((PROCESSED / "yolo" / "images" / "train").iterdir())
    synth = sorted(p for p in (SYNTH_DIR / "images").iterdir() if p.suffix.lower() in IMAGE_SUFFIXES) \
        if (SYNTH_DIR / "images").is_dir() else []
    if not synth:
        sys.exit(f"TelecomSynth is empty — intake some submissions into {SYNTH_DIR} first")
    if max_images is not None and max_images < len(synth):
        synth = sorted(random.Random(seed).sample(synth, max_images))
    out.mkdir(parents=True, exist_ok=True)
    name = "dataset.yaml" if max_images is None else f"dataset_synth{max_images}.yaml"
    lst = out / name.replace(".yaml", "_train.txt")
    lst.write_text("\n".join(str(p.resolve()) for p in train + synth) + "\n", encoding="utf-8")
    val = (PROCESSED / "yolo" / "images" / "val").resolve().as_posix()
    names = "\n".join(f"  {i}: {n}" for i, n in enumerate(class_names()))
    y = out / name
    y.write_text(f"train: {lst.resolve().as_posix()}\nval: {val}\nnames:\n{names}\n", encoding="utf-8")
    print(f"E3 training set: {len(train)} real + {len(synth)} synthetic images → {y}")
    return y


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["prelabel", "check", "intake", "dataset"])
    ap.add_argument("folder", type=Path, nargs="?")
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--contributor")
    ap.add_argument("--max", type=int, help="dataset: use only this many synthetic images (mix-ratio ablation)")
    args = ap.parse_args(argv)
    if args.command == "dataset":
        dataset(args.max)
        return
    if args.folder is None:
        ap.error(f"{args.command} needs a folder")
    folder = args.folder.resolve()
    if args.command == "prelabel":
        prelabel(folder)
    elif args.command == "check":
        if not args.target:
            ap.error("check needs --target")
        sys.exit(0 if report(folder, args.target) else 1)
    else:
        if not (args.target and args.contributor):
            ap.error("intake needs --target and --contributor")
        intake(folder, args.contributor, args.target)


if __name__ == "__main__":
    main()
