"""Freeze TelecomEval and verify it has not changed.

    python -m telecomsafe.data.freeze_eval --create   # write splits/telecom_eval.txt + .sha256
    python -m telecomsafe.data.freeze_eval --check    # exit 1 if any image or label changed

Both images and label files are hashed: re-labelling the test set is as damaging
to the phase 1 / phase 2 comparison as swapping images.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from telecomsafe.paths import IMAGE_SUFFIXES, ROOT, SPLITS, load_sources, resolve


def eval_root() -> Path:
    cfg = next(c for c in load_sources() if c["name"] == "telecom_eval")
    return resolve(cfg["path"])


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(root: Path) -> dict[str, str]:
    """relative path -> sha256 for every image and label file under root."""
    files = [p for p in root.rglob("*") if p.is_file() and (p.suffix.lower() in IMAGE_SUFFIXES or p.suffix == ".txt")]
    return {p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else p.as_posix(): file_sha256(p) for p in sorted(files)}


def digest(entries: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{k}\t{v}\n" for k, v in sorted(entries.items())).encode()).hexdigest()


def create(root: Path, out_dir: Path = SPLITS) -> str:
    entries = manifest(root)
    if not entries:
        raise SystemExit(f"{root} has no images — build TelecomEval first")
    images = [k for k in entries if Path(k).suffix.lower() in IMAGE_SUFFIXES]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "telecom_eval.txt").write_text("\n".join(images) + "\n", encoding="utf-8")
    total = digest(entries)
    lines = [f"# TelecomEval frozen manifest — {len(images)} images, {len(entries) - len(images)} label files",
             f"# total {total}"] + [f"{v}  {k}" for k, v in entries.items()]
    (out_dir / "telecom_eval.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return total


def check(root: Path, out_dir: Path = SPLITS) -> list[str]:
    """Return a list of problems (empty = frozen set intact)."""
    frozen_file = out_dir / "telecom_eval.sha256"
    if not frozen_file.exists():
        return [f"{frozen_file} missing — run with --create first"]
    frozen = {}
    for line in frozen_file.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#"):
            sha, path = line.split("  ", 1)
            frozen[path] = sha
    current = manifest(root)
    problems = [f"missing: {p}" for p in frozen if p not in current]
    problems += [f"added: {p}" for p in current if p not in frozen]
    problems += [f"changed: {p}" for p in frozen if p in current and current[p] != frozen[p]]
    return problems


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--create", action="store_true")
    g.add_argument("--check", action="store_true")
    ap.add_argument("--root", help="TelecomEval directory (default: path in sources.yaml)")
    args = ap.parse_args(argv)
    root = Path(args.root) if args.root else eval_root()

    if args.create:
        if (SPLITS / "telecom_eval.sha256").exists():
            sys.exit("TelecomEval is already frozen. Unfreezing breaks phase 1 / phase 2 comparability; "
                     "delete splits/telecom_eval.* by hand only if you really mean it.")
        print(f"frozen: {create(root)}")
        return
    problems = check(root)
    if problems:
        print("TelecomEval has changed since it was frozen:", *problems[:20], sep="\n  ", file=sys.stderr)
        sys.exit(1)
    print("TelecomEval intact")


if __name__ == "__main__":
    main()
