import pytest

from telecomsafe.data.readers import read_coco, read_source, read_voc, read_yolo


def test_yolo_denormalises_and_keeps_background(yolo_dataset):
    samples = {s.image.name: s for s in read_yolo(yolo_dataset)}
    assert set(samples) == {"a.jpg", "bg.jpg"}
    assert samples["bg.jpg"].boxes == []
    first, second = samples["a.jpg"].boxes
    assert first.cls == "Hardhat"
    assert (first.x1, first.y1, first.x2, first.y2) == pytest.approx((40, 30, 60, 50))
    assert second.cls == "NO-Hardhat"


def test_yolo_uses_fallback_names_without_data_yaml(yolo_dataset):
    (yolo_dataset / "data.yaml").unlink()
    samples = read_yolo(yolo_dataset, names=["x", "y"])
    assert {b.cls for s in samples for b in s.boxes} == {"x", "y"}


def test_yolo_without_any_names_fails(yolo_dataset):
    (yolo_dataset / "data.yaml").unlink()
    with pytest.raises(ValueError):
        read_yolo(yolo_dataset)


def test_coco(coco_dataset):
    (s,) = read_coco(coco_dataset)
    (b,) = s.boxes
    assert (s.width, s.height) == (200, 100)
    assert (b.cls, b.x1, b.y1, b.x2, b.y2) == ("worker", 10, 20, 40, 60)


def test_voc(voc_dataset):
    (s,) = read_voc(voc_dataset)
    (b,) = s.boxes
    assert s.image.name == "v.jpg"
    assert (b.cls, b.x1, b.y2) == ("head", 1, 42)


def test_unknown_format(tmp_path):
    with pytest.raises(ValueError):
        read_source("kitti", tmp_path)
