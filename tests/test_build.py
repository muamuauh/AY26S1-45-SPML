import shutil

import numpy as np
import pytest

from telecomsafe.data.build import (
    ConfigError, apply_filter, build, duplicates, leaks, map_classes, merge_pseudo,
    split_train_val, write_dataset, yolo_lines,
)
from telecomsafe.data.readers import Box, Sample, read_yolo

TARGETS = ["person", "helmet", "no_helmet"]


def cfg(name, root, **kw):
    return {"name": name, "role": "train", "enabled": True, "format": "yolo", "path": str(root),
            "class_map": {"Hardhat": "helmet", "NO-Hardhat": "no_helmet"}, "annotates": ["helmet", "no_helmet"], **kw}


def test_map_classes_renames_and_drops(yolo_dataset):
    samples = read_yolo(yolo_dataset)
    dropped = map_classes(samples, {"Hardhat": "helmet", "NO-Hardhat": None}, TARGETS, "src")
    assert [b.cls for s in samples for b in s.boxes] == ["helmet"]
    assert dropped == {"NO-Hardhat": 1}
    assert all(s.source == "src" for s in samples)


def test_map_classes_rejects_undeclared_class(yolo_dataset):
    with pytest.raises(ConfigError, match="NO-Hardhat"):
        map_classes(read_yolo(yolo_dataset), {"Hardhat": "helmet"}, TARGETS, "src")


def test_map_classes_drops_classes_outside_phase1(yolo_dataset):
    samples = read_yolo(yolo_dataset)
    map_classes(samples, {"Hardhat": "tower", "NO-Hardhat": "no_helmet"}, TARGETS, "src")
    assert [b.cls for s in samples for b in s.boxes] == ["no_helmet"]


def test_merge_pseudo_only_adds_unannotated_classes(tmp_path):
    s = Sample(tmp_path / "x.jpg", 100, 100, [Box("helmet", 0, 0, 10, 10)])
    added = merge_pseudo([s], {str(s.image): [["person", 0, 0, 50, 90, 0.9], ["helmet", 1, 1, 9, 9, 0.8]]}, {"helmet"})
    assert added == 1
    assert [(b.cls, b.pseudo) for b in s.boxes] == [("helmet", False), ("person", True)]


def test_filter_no_person(tmp_path):
    a = Sample(tmp_path / "a.jpg", 1, 1, [Box("person", 0, 0, 1, 1)])
    b = Sample(tmp_path / "b.jpg", 1, 1, [Box("machinery", 0, 0, 1, 1)])
    assert apply_filter([a, b], "no_person") == [b]
    with pytest.raises(ConfigError):
        apply_filter([a], "no_cats")


def test_hash_helpers():
    hashes = np.array([0b0000, 0b0001, 0b1111_0000, 0b0000], dtype=np.uint64)
    assert duplicates(hashes, threshold=1).tolist() == [False, True, False, True]
    assert leaks(hashes, np.array([0b1111_0000], dtype=np.uint64), threshold=0).tolist() == [False, False, True, False]


def test_split_is_deterministic_and_stratified(tmp_path):
    samples = [Sample(tmp_path / f"{src}{i}.jpg", 1, 1, source=src) for src in "ab" for i in range(10)]
    s1, s2 = split_train_val(samples, 0.2, seed=0), split_train_val(samples, 0.2, seed=0)
    assert [x.image for x in s1["val"]] == [x.image for x in s2["val"]]
    assert sorted(x.source for x in s1["val"]) == ["a", "a", "b", "b"]


def test_yolo_lines_clamps_and_skips_degenerate(tmp_path):
    s = Sample(tmp_path / "x.jpg", 100, 100, [Box("helmet", -10, -10, 50, 50), Box("person", 5, 5, 5.5, 60)])
    assert yolo_lines(s, TARGETS) == ["1 0.250000 0.250000 0.500000 0.500000"]


def test_build_removes_eval_leaks_and_duplicates(yolo_dataset, tmp_path):
    copy = tmp_path / "copy_src"
    shutil.copytree(yolo_dataset, copy)  # the same images again → cross-source duplicates
    eval_root = tmp_path / "eval"
    shutil.copytree(yolo_dataset, eval_root)
    (eval_root / "train" / "images" / "bg.jpg").unlink()  # eval contains only a.jpg
    cfgs = [cfg("s1", yolo_dataset), cfg("s2", copy),
            {**cfg("ev", eval_root), "role": "eval"}]
    result, roots = build(cfgs, TARGETS, use_pseudo=False)
    kept = result.splits["train"] + result.splits["val"]
    assert [s.image.name for s in kept] == ["bg.jpg"]
    assert result.removed == {"eval_leak": 2, "duplicate": 1}
    assert [s.image.name for s in result.splits["test"]] == ["a.jpg"]
    assert result.coverage["s1"] == {"person": "missing", "helmet": "labeled", "no_helmet": "labeled"}


def test_write_dataset(yolo_dataset, tmp_path):
    samples = read_yolo(yolo_dataset)
    map_classes(samples, {"Hardhat": "helmet", "NO-Hardhat": "no_helmet"}, TARGETS, "s1")
    out = tmp_path / "out"
    yaml_path = write_dataset({"train": samples, "val": []}, {"s1": yolo_dataset}, out, TARGETS)
    assert "test:" not in yaml_path.read_text()
    labels = sorted((out / "labels" / "train").iterdir())
    assert [p.name.split("_")[:3] for p in labels] == [["s1", "", "a"], ["s1", "", "bg"]]
    assert all(len(p.stem) <= len("s1__") + 40 + 9 for p in labels)
    assert labels[0].read_text().splitlines()[0].startswith("1 ")
    images = sorted((out / "images" / "train").iterdir())
    assert [p.stem for p in images] == [p.stem for p in labels]
