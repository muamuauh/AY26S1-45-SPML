"""Download released model weights (see configs/weights.yaml).

    python -m telecomsafe.weights          # every released model
    python -m telecomsafe.weights e2       # only E2 (the demo model)
    python -m telecomsafe.weights --check  # verify local files, download nothing

Files already present with the right sha256 are skipped.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import requests

from telecomsafe.paths import CONFIGS, load_yaml, resolve


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r    {done / total:6.1%} of {total / 1e6:.0f} MB", end="", flush=True)
    print()
    tmp.replace(dest)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help="model names from configs/weights.yaml (default: all)")
    ap.add_argument("--check", action="store_true", help="only verify local files")
    args = ap.parse_args(argv)

    cfg = load_yaml(CONFIGS / "weights.yaml")
    names = args.names or list(cfg["weights"])
    unknown = set(names) - set(cfg["weights"])
    if unknown:
        sys.exit(f"unknown model(s): {sorted(unknown)}; available: {sorted(cfg['weights'])}")

    failed = False
    for name in names:
        w = cfg["weights"][name]
        dest = resolve(w["path"])
        if dest.exists() and sha256(dest) == w["sha256"]:
            print(f"  ✓ {name}: {dest} (sha256 ok)")
            continue
        if args.check:
            print(f"  ✗ {name}: {'missing' if not dest.exists() else 'sha256 mismatch'} — {dest}")
            failed = True
            continue
        url = f"{cfg['url']}/{w['asset']}"
        print(f"  ↓ {name}: {url}")
        try:
            fetch(url, dest)
        except requests.RequestException as e:
            print(f"    ✗ download failed: {e}", file=sys.stderr)
            failed = True
            continue
        if sha256(dest) != w["sha256"]:
            dest.unlink()
            print(f"    ✗ sha256 mismatch — file removed; the release asset differs from configs/weights.yaml", file=sys.stderr)
            failed = True
        else:
            print(f"    ✓ saved to {dest}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
