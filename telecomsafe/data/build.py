"""Merge the raw datasets in configs/sources.yaml into one YOLO dataset.

    python -m telecomsafe.data.build --dry-run          # print mapping / coverage / dedupe stats only
    python -m telecomsafe.data.build                    # write data/processed/yolo + reports
    python -m telecomsafe.data.build --sources construction_site_safety construction_ppe \
        --out data/processed/teacher --no-eval          # dataset for the pseudo-label teacher

Pipeline: read → map classes → merge pseudo labels → filter → dedupe (and drop
anything near-identical to TelecomEval) → train/val split → write.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from telecomsafe.data.readers import Box, Sample, read_source
from telecomsafe.paths import INTERIM, PROCESSED, REPORTS, class_names, load_sources, resolve


class ConfigError(Exception):
    pass


# ---------------------------------------------------------------- class mapping
def map_classes(samples: list[Sample], class_map: dict | str, targets: list[str], source: str) -> Counter:
    """Rename boxes to target classes in place; returns counts of dropped raw classes.

    Raises ConfigError listing every raw class that class_map does not declare, so a
    new dataset can never lose annotations silently.
    """
    raw_classes = {b.cls for s in samples for b in s.boxes}
    if class_map == "identity":
        class_map = {c: c for c in raw_classes}
    unknown = sorted(raw_classes - set(class_map))
    if unknown:
        raise ConfigError(
            f"[{source}] class_map in configs/sources.yaml does not declare: {unknown}. "
            "Map each to a target class or to null."
        )
    dropped: Counter = Counter()
    for s in samples:
        kept = []
        for b in s.boxes:
            target = class_map[b.cls]
            if target is None or target not in targets:
                dropped[b.cls] += 1
                continue
            b.cls = target
            kept.append(b)
        s.boxes = kept
        s.source = source
    return dropped


# ---------------------------------------------------------------- coverage & pseudo labels
def coverage(cfgs: list[dict], targets: list[str], pseudo_sources: set[str]) -> dict[str, dict[str, str]]:
    """Per source and target class: labeled / pseudo / missing."""
    table = {}
    for cfg in cfgs:
        annotated = set(cfg.get("annotates") or [])
        table[cfg["name"]] = {
            c: "labeled" if c in annotated else ("pseudo" if cfg["name"] in pseudo_sources else "missing") for c in targets
        }
    return table


def pseudo_path(source: str) -> Path:
    return INTERIM / "pseudo" / f"{source}.json"


def merge_pseudo(samples: list[Sample], pseudo: dict[str, list], annotated: set[str]) -> int:
    """Add teacher predictions for classes the source does not annotate. Returns boxes added."""
    added = 0
    for s in samples:
        for cls, x1, y1, x2, y2, conf in pseudo.get(str(s.image), []):
            if cls not in annotated:
                s.boxes.append(Box(cls, x1, y1, x2, y2, conf=conf, pseudo=True))
                added += 1
    return added


def apply_filter(samples: list[Sample], rule: str | None) -> list[Sample]:
    """no_person: images without people; has:<class>: images with at least one box of that target class."""
    if rule is None:
        return samples
    if rule == "no_person":
        return [s for s in samples if not any(b.cls == "person" for b in s.boxes)]
    if rule.startswith("has:"):
        cls = rule.split(":", 1)[1]
        return [s for s in samples if any(b.cls == cls for b in s.boxes)]
    raise ConfigError(f"unknown filter {rule!r}")


def apply_exclude(samples: list[Sample], listing: str | None) -> list[Sample]:
    """Drop images named in a file (one file name per line, # comments), e.g. configs/exclude/<source>.txt."""
    if not listing:
        return samples
    names = {ln.strip() for ln in resolve(listing).read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")}
    return [s for s in samples if s.image.name not in names]


def chosen_eval_images() -> list[Path]:
    """TelecomEval candidates kept in review. Training images are de-duplicated against them even before
    TelecomEval is annotated and frozen, so the training set does not change when it is."""
    from telecomsafe.data.collect_open import OUT, read_manifest

    return [OUT / r["file"] for r in read_manifest()
            if r["status"] == "candidate" and r.get("subset") in {"telecom", "near"} and (OUT / r["file"]).exists()]


# ---------------------------------------------------------------- perceptual-hash dedupe
def phash_all(paths: list[Path], cache_file: Path | None = None) -> np.ndarray:
    import imagehash
    from PIL import Image

    cache = {}
    if cache_file and cache_file.exists():
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    out = np.zeros(len(paths), dtype=np.uint64)
    for i, p in enumerate(paths):
        st = p.stat()
        key, stamp = str(p), f"{st.st_size}:{int(st.st_mtime)}"
        if key in cache and cache[key][0] == stamp:
            h = cache[key][1]
        else:
            with Image.open(p) as im:
                h = str(imagehash.phash(im))
            cache[key] = [stamp, h]
        out[i] = np.uint64(int(h, 16))
    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache), encoding="utf-8")
    return out


def hamming(a: np.uint64, b: np.ndarray) -> np.ndarray:
    return np.bitwise_count(np.bitwise_xor(b, a))


def leaks(train: np.ndarray, evaluation: np.ndarray, threshold: int) -> np.ndarray:
    """Mask of train rows within `threshold` bits of any evaluation image."""
    mask = np.zeros(len(train), dtype=bool)
    for h in evaluation:
        mask |= hamming(h, train) <= threshold
    return mask


def duplicates(hashes: np.ndarray, threshold: int) -> np.ndarray:
    """Mask of rows that duplicate an earlier kept row (first occurrence wins)."""
    dup = np.zeros(len(hashes), dtype=bool)
    for i in range(len(hashes)):
        if dup[i]:
            continue
        rest = hamming(hashes[i], hashes[i + 1 :]) <= threshold
        dup[i + 1 :] |= rest
    return dup


# ---------------------------------------------------------------- split & write
def split_train_val(samples: list[Sample], val_frac: float, seed: int) -> dict[str, list[Sample]]:
    """Stratified by source so every dataset is represented in val."""
    rng = random.Random(seed)
    by_source: dict[str, list[Sample]] = defaultdict(list)
    for s in samples:
        by_source[s.source].append(s)
    out = {"train": [], "val": []}
    for name in sorted(by_source):
        group = sorted(by_source[name], key=lambda s: str(s.image))
        rng.shuffle(group)
        n_val = max(1, round(len(group) * val_frac)) if len(group) > 1 else 0
        out["val"] += group[:n_val]
        out["train"] += group[n_val:]
    return out


def output_name(s: Sample, root: Path) -> str:
    """<source>__<stem, max 40 chars>_<hash of the relative path>.<ext>

    Short enough for Windows' 260-character path limit (Roboflow file names are long),
    unique because the hash covers the full relative path.
    """
    rel = s.image.relative_to(root) if s.image.is_relative_to(root) else Path(s.image.name)
    digest = hashlib.sha1(rel.as_posix().encode()).hexdigest()[:8]
    return f"{s.source}__{s.image.stem[:40]}_{digest}{s.image.suffix.lower()}"


def yolo_lines(s: Sample, targets: list[str]) -> list[str]:
    lines = []
    for b in s.boxes:
        x1, y1 = max(0.0, b.x1), max(0.0, b.y1)
        x2, y2 = min(float(s.width), b.x2), min(float(s.height), b.y2)
        if x2 - x1 < 1 or y2 - y1 < 1:
            continue
        cx, cy = (x1 + x2) / 2 / s.width, (y1 + y2) / 2 / s.height
        w, h = (x2 - x1) / s.width, (y2 - y1) / s.height
        lines.append(f"{targets.index(b.cls)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return lines


def write_dataset(splits: dict[str, list[Sample]], roots: dict[str, Path], out: Path, targets: list[str]) -> Path:
    if out.exists():
        shutil.rmtree(out)
    for split, samples in splits.items():
        img_dir, lbl_dir = out / "images" / split, out / "labels" / split
        img_dir.mkdir(parents=True)
        lbl_dir.mkdir(parents=True)
        for s in samples:
            name = output_name(s, roots[s.source])
            dst = img_dir / name
            try:
                os.link(s.image, dst)
            except OSError:
                shutil.copy2(s.image, dst)
            (lbl_dir / (Path(name).stem + ".txt")).write_text("\n".join(yolo_lines(s, targets)), encoding="utf-8")
    cfg = [f"path: {out.as_posix()}", "train: images/train", "val: images/val"]
    if splits.get("test"):
        cfg.append("test: images/test")
    cfg.append("names:")
    cfg += [f"  {i}: {n}" for i, n in enumerate(targets)]
    yaml_path = out / "dataset.yaml"
    yaml_path.write_text("\n".join(cfg) + "\n", encoding="utf-8")
    return yaml_path


def stats_rows(splits: dict[str, list[Sample]], targets: list[str]) -> list[dict]:
    rows = []
    for split, samples in splits.items():
        by_source: dict[str, list[Sample]] = defaultdict(list)
        for s in samples:
            by_source[s.source].append(s)
        for source in sorted(by_source):
            group = by_source[source]
            labeled = Counter(b.cls for s in group for b in s.boxes if not b.pseudo)
            pseudo = Counter(b.cls for s in group for b in s.boxes if b.pseudo)
            row = {"source": source, "split": split, "images": len(group)}
            row.update({c: labeled[c] for c in targets})
            row["pseudo_boxes"] = sum(pseudo.values())
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- orchestration
@dataclass
class BuildResult:
    splits: dict[str, list[Sample]]
    coverage: dict[str, dict[str, str]]
    dropped: dict[str, Counter]
    removed: dict[str, int]


def build(
    cfgs: list[dict],
    targets: list[str],
    *,
    val_frac: float = 0.1,
    seed: int = 0,
    dup_threshold: int = 4,
    leak_threshold: int = 8,
    use_pseudo: bool = True,
    include_eval: bool = True,
    hash_cache: Path | None = None,
    leak_images: list[Path] | None = None,
) -> tuple[BuildResult, dict[str, Path]]:
    train_cfgs = [c for c in cfgs if c.get("enabled") and c.get("role") == "train"]
    eval_cfgs = [c for c in cfgs if c.get("enabled") and c.get("role") == "eval"] if include_eval else []

    roots: dict[str, Path] = {}
    dropped: dict[str, Counter] = {}
    train: list[Sample] = []
    evaluation: list[Sample] = []
    pseudo_sources: set[str] = set()

    for cfg in train_cfgs + eval_cfgs:
        name, root = cfg["name"], resolve(cfg.get("path", f"data/raw/{cfg['name']}"))
        if not root.exists() or not any(root.iterdir()):
            print(f"  ! {name}: {root} is empty — skipped (run telecomsafe.data.download first)", file=sys.stderr)
            continue
        samples = read_source(cfg["format"], root, cfg.get("names"))
        dropped[name] = map_classes(samples, cfg.get("class_map") or {}, targets, name)
        roots[name] = root
        if cfg["role"] == "eval":
            evaluation += samples
            continue
        pfile = pseudo_path(name)
        if use_pseudo and pfile.exists():
            merge_pseudo(samples, json.loads(pfile.read_text(encoding="utf-8")), set(cfg.get("annotates") or []))
            pseudo_sources.add(name)
        train += apply_exclude(apply_filter(samples, cfg.get("filter")), cfg.get("exclude"))

    removed = {"eval_leak": 0, "duplicate": 0}
    if train:
        train_hashes = phash_all([s.image for s in train], hash_cache)
        keep = np.ones(len(train), dtype=bool)
        held_out = [s.image for s in evaluation] + list(leak_images or [])
        if held_out:
            leak = leaks(train_hashes, phash_all(held_out, hash_cache), leak_threshold)
            removed["eval_leak"] = int(leak.sum())
            keep &= ~leak
        dup = duplicates(train_hashes, dup_threshold) & keep
        removed["duplicate"] = int(dup.sum())
        keep &= ~dup
        train = [s for s, k in zip(train, keep) if k]

    splits = split_train_val(train, val_frac, seed)
    if evaluation:
        splits["test"] = evaluation
    loaded = [c for c in train_cfgs if c["name"] in roots]
    return BuildResult(splits, coverage(loaded, targets, pseudo_sources), dropped, removed), roots


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sources", nargs="*", help="only these source names (default: all enabled)")
    ap.add_argument("--out", default=str(PROCESSED / "yolo"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-pseudo", action="store_true", help="ignore data/interim/pseudo/*.json")
    ap.add_argument("--no-eval", action="store_true", help="do not attach TelecomEval as the test split")
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)

    cfgs = load_sources()
    if args.sources:
        cfgs = [c for c in cfgs if c["name"] in args.sources or c.get("role") == "eval"]
    targets = class_names()

    try:
        result, roots = build(
            cfgs, targets, val_frac=args.val_frac, seed=args.seed,
            use_pseudo=not args.no_pseudo, include_eval=not args.no_eval,
            hash_cache=INTERIM / "phash_cache.json", leak_images=chosen_eval_images(),
        )
    except ConfigError as e:
        sys.exit(f"ConfigError: {e}")

    print("\nDropped raw classes:")
    for name, cnt in result.dropped.items():
        print(f"  {name}: {dict(cnt) if cnt else '-'}")
    print("\nCoverage (source × class):")
    for name, row in result.coverage.items():
        print(f"  {name:28s} " + " ".join(f"{c}={v[0].upper()}" for c, v in row.items()))
    print(f"\nRemoved: {result.removed}")
    for split, samples in result.splits.items():
        print(f"  {split:5s}: {len(samples)} images, {sum(len(s.boxes) for s in samples)} boxes")
    if "test" not in result.splits and not args.no_eval:
        print("  ! TelecomEval not built yet — dataset.yaml will have no test split", file=sys.stderr)

    if args.dry_run or not any(result.splits.values()):
        return
    yaml_path = write_dataset(result.splits, roots, resolve(args.out), targets)
    if resolve(args.out) == PROCESSED / "yolo":
        write_csv(REPORTS / "dataset_stats.csv", stats_rows(result.splits, targets))
        write_csv(REPORTS / "coverage.csv", [{"source": n, **row} for n, row in result.coverage.items()])
    print(f"\nWrote {yaml_path}")


if __name__ == "__main__":
    main()
