"""Download the datasets registered in configs/sources.yaml into data/raw/<name>/.

    python -m telecomsafe.data.download --list          # what is registered and what is present
    python -m telecomsafe.data.download                 # every enabled source that can be scripted
    python -m telecomsafe.data.download --only construction_ppe --force

Credentials are read from the repository's .env file (template: .env.example; never commit .env):
  Kaggle    KAGGLE_API_TOKEN, or legacy KAGGLE_USERNAME + KAGGLE_KEY
            (kaggle.com → Settings → API → Generate New Token)
  Roboflow  ROBOFLOW_API_KEY (app.roboflow.com → Settings → API Keys)

Sources with `method: manual` only print their instructions.
"""

from __future__ import annotations

import argparse
import os
import sys
import zipfile
from pathlib import Path

import requests
import yaml

from telecomsafe.env import load_env
from telecomsafe.paths import load_sources, resolve


def is_present(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def fetch_zip(url: str, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / "_download.zip"
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with open(archive, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r    {done / total:6.1%} of {total / 1e6:.0f} MB", end="", flush=True)
    print()
    with zipfile.ZipFile(archive) as z:
        z.extractall(dest)
    archive.unlink()


def via_kaggle(spec: dict, dest: Path) -> None:
    if not (os.environ.get("KAGGLE_API_TOKEN") or os.environ.get("KAGGLE_KEY")
            or (Path.home() / ".kaggle" / "kaggle.json").exists() or (Path.home() / ".kaggle" / "access_token").exists()):
        raise RuntimeError("Kaggle key missing: fill KAGGLE_API_TOKEN (or KAGGLE_USERNAME + KAGGLE_KEY) in .env")
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
    except (Exception, SystemExit) as e:  # kaggle calls exit(1) when authentication fails
        raise RuntimeError(f"Kaggle authentication failed ({e!r}); check the key in .env") from e
    dest.mkdir(parents=True, exist_ok=True)
    api.dataset_download_files(spec["ref"], path=str(dest), unzip=True, quiet=False)


def via_roboflow(spec: dict, dest: Path) -> None:
    key = os.environ.get("ROBOFLOW_API_KEY")
    if not key:
        raise RuntimeError("ROBOFLOW_API_KEY is not set. See the module docstring.")
    from roboflow import Roboflow

    project = Roboflow(api_key=key).workspace(spec["workspace"]).project(spec["project"])
    version = spec.get("version") or max(int(v.version.split("/")[-1]) for v in project.versions())
    ds = project.version(version)
    for fmt in ("yolov11", "yolov8"):
        try:
            ds.download(fmt, location=str(dest), overwrite=True)
            return
        except Exception as e:  # older roboflow clients do not know "yolov11"
            last = e
    raise RuntimeError(f"Roboflow download failed: {last}")


def via_ultralytics(spec: dict, dest: Path) -> None:
    from ultralytics.utils import ROOT as ULTRALYTICS_ROOT

    cfg = yaml.safe_load((ULTRALYTICS_ROOT / "cfg" / "datasets" / spec["yaml"]).read_text(encoding="utf-8"))
    url = cfg.get("download")
    if not isinstance(url, str) or not url.startswith("http"):
        raise RuntimeError(f"{spec['yaml']} has no plain download URL")
    fetch_zip(url, dest)


METHODS = {"kaggle": via_kaggle, "roboflow": via_roboflow, "ultralytics": via_ultralytics,
           "url_zip": lambda spec, dest: fetch_zip(spec["url"], dest)}


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", help="source names")
    ap.add_argument("--all", action="store_true", help="include sources with enabled: false")
    ap.add_argument("--force", action="store_true", help="re-download even if the folder is not empty")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    load_env()

    failures = 0
    for cfg in load_sources():
        if cfg.get("role") == "unused" or "download" not in cfg:
            continue
        name, dest, spec = cfg["name"], resolve(cfg["path"]), cfg["download"]
        if args.only and name not in args.only:
            continue
        if not (args.all or args.only or cfg.get("enabled")):
            continue
        present = is_present(dest)
        if args.list:
            print(f"  {'✓' if present else '·'} {name:28s} {spec['method']:12s} {cfg.get('tier', '')}")
            continue
        if present and not args.force:
            print(f"  ✓ {name}: already in {dest}")
            continue
        if spec["method"] == "manual":
            print(f"  ✋ {name}: manual — {spec.get('instructions', '')}\n     {cfg.get('homepage', '')}")
            continue
        print(f"  ↓ {name} via {spec['method']}")
        try:
            METHODS[spec["method"]](spec, dest)
            print(f"    done → {dest}")
        except Exception as e:
            failures += 1
            print(f"    ✗ {e}", file=sys.stderr)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
