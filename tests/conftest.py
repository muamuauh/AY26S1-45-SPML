import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def make_image(path: Path, size=(100, 80), pattern: int = 0) -> Path:
    """Seeded random-noise image: different `pattern`s give clearly different perceptual hashes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(pattern)
    Image.fromarray(rng.integers(0, 256, (size[1], size[0], 3), dtype=np.uint8)).save(path, quality=95)
    return path


@pytest.fixture
def yolo_dataset(tmp_path):
    """Roboflow-style layout: train/images + train/labels + data.yaml."""
    root = tmp_path / "yolo_src"
    make_image(root / "train" / "images" / "a.jpg", pattern=1)
    make_image(root / "train" / "images" / "bg.jpg", pattern=2)  # background image: no label file
    (root / "train" / "labels").mkdir(parents=True)
    (root / "train" / "labels" / "a.txt").write_text("0 0.5 0.5 0.2 0.25\n1 0.25 0.25 0.1 0.1\n")
    (root / "data.yaml").write_text("names: ['Hardhat', 'NO-Hardhat']\n")
    return root


@pytest.fixture
def coco_dataset(tmp_path):
    root = tmp_path / "coco_src"
    make_image(root / "images" / "c.jpg", size=(200, 100), pattern=3)
    (root / "ann.json").write_text(json.dumps({
        "images": [{"id": 1, "file_name": "images/c.jpg", "width": 200, "height": 100}],
        "annotations": [{"id": 1, "image_id": 1, "category_id": 7, "bbox": [10, 20, 30, 40]}],
        "categories": [{"id": 7, "name": "worker"}],
    }))
    return root


@pytest.fixture
def voc_dataset(tmp_path):
    root = tmp_path / "voc_src"
    make_image(root / "JPEGImages" / "v.jpg", size=(120, 90), pattern=4)
    (root / "Annotations").mkdir(parents=True)
    (root / "Annotations" / "v.xml").write_text(
        "<annotation><filename>v.jpg</filename><size><width>120</width><height>90</height></size>"
        "<object><name>head</name><bndbox><xmin>1</xmin><ymin>2</ymin><xmax>31</xmax><ymax>42</ymax></bndbox></object>"
        "</annotation>"
    )
    return root
