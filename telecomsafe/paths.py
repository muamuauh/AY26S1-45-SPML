"""Repository paths and config loading shared by every module."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / "configs"
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
REPORTS = ROOT / "reports" / "phase1"
SPLITS = ROOT / "splits"
RUNS = ROOT / "runs" / "phase1"

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_yaml(path: Path) -> dict | list:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_taxonomy(path: Path = CONFIGS / "taxonomy.yaml") -> list[dict]:
    """Phase 1 classes in YOLO id order."""
    return [c for c in load_yaml(path)["classes"] if c.get("phase1", True)]


def class_names(path: Path = CONFIGS / "taxonomy.yaml") -> list[str]:
    return [c["name"] for c in load_taxonomy(path)]


def load_sources(path: Path = CONFIGS / "sources.yaml") -> list[dict]:
    return load_yaml(path)["sources"]


def resolve(path: str | Path) -> Path:
    """Paths in configs are relative to the repository root."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p
