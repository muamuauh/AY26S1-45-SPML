import xml.etree.ElementTree as ET

import pytest

from telecomsafe.data import labelstudio as ls
from telecomsafe.env import load_env
from telecomsafe.paths import class_names

from conftest import make_image


def test_label_config_is_valid_xml_with_every_class():
    root = ET.fromstring(ls.label_config())
    assert [l.get("value") for l in root.iter("Label")] == class_names()


def test_prediction_roundtrip_to_yolo(tmp_path, monkeypatch):
    monkeypatch.setattr(ls, "RAW", tmp_path)
    make_image(tmp_path / "t3_candidates" / "images" / "a.jpg", size=(200, 100))
    pred = ls.to_prediction([("helmet", 20, 10, 60, 50, 0.9)], 200, 100)
    tasks = [
        {"data": {"image": "/data/local-files/?d=t3_candidates/images/a.jpg"},
         "annotations": [{"result": pred["result"], "was_cancelled": False, "updated_at": "2026-10-01"}]},
        {"data": {"image": "/data/local-files/?d=t3_candidates/images/b.jpg"},
         "annotations": [{"result": [], "was_cancelled": True}]},
        {"data": {"image": "/data/local-files/?d=t3_candidates/images/c.jpg"}, "annotations": []},
    ]
    counts = ls.convert(tasks, class_names(), tmp_path / "eval")
    assert counts == {"images": 1, "boxes": 1, "dropped": 0, "skipped": 1, "unannotated": 1}
    line = (tmp_path / "eval" / "labels" / "a.txt").read_text()
    assert line == f"{class_names().index('helmet')} 0.200000 0.300000 0.200000 0.400000"


def test_load_env_does_not_override_existing(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("# comment\nA_KEY=from_file\nB_KEY=\nexport C_KEY='quoted'\n", encoding="utf-8")
    monkeypatch.setenv("A_KEY", "from_shell")
    monkeypatch.delenv("B_KEY", raising=False)
    monkeypatch.delenv("C_KEY", raising=False)
    assert load_env(f) == ["C_KEY"]
    import os
    assert os.environ["A_KEY"] == "from_shell" and "B_KEY" not in os.environ and os.environ["C_KEY"] == "quoted"
