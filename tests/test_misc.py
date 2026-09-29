from telecomsafe.data import catalog, freeze_eval
from telecomsafe.paths import class_names, load_sources
from telecomsafe.train import NO_AUGMENTATION, train_args

from conftest import make_image


def test_freeze_detects_changes(tmp_path):
    root, out = tmp_path / "eval", tmp_path / "splits"
    make_image(root / "images" / "a.jpg", pattern=1)
    (root / "labels").mkdir()
    (root / "labels" / "a.txt").write_text("0 0.5 0.5 0.1 0.1")
    freeze_eval.create(root, out)
    assert freeze_eval.check(root, out) == []
    assert (out / "telecom_eval.txt").read_text().strip().endswith("a.jpg")

    (root / "labels" / "a.txt").write_text("1 0.5 0.5 0.1 0.1")  # re-labelling counts as a change
    assert any(p.startswith("changed:") for p in freeze_eval.check(root, out))
    make_image(root / "images" / "b.jpg", pattern=2)
    assert any(p.startswith("added:") for p in freeze_eval.check(root, out))


def test_e1_turns_off_augmentation_and_e2_keeps_defaults():
    e1 = train_args("e1", "d.yaml", {})
    e2 = train_args("e2", "d.yaml", {"epochs": 1})
    assert all(e1[k] == 0.0 for k in NO_AUGMENTATION)
    assert not any(k in e2 for k in NO_AUGMENTATION)
    assert e2["epochs"] == 1 and e1["model"] == e2["model"] and e1["name"] == "e1"


def test_shipped_configs_are_consistent():
    targets = set(class_names())
    for src in load_sources():
        cm = src.get("class_map")
        if isinstance(cm, dict):
            assert set(v for v in cm.values() if v) <= targets | {"tower"}, src["name"]
        for c in src.get("annotates") or []:
            assert c in targets | {"tower"}, (src["name"], c)


def test_catalog_renders_every_source():
    sources = load_sources()
    text = catalog.render(sources, [{"name": "person", "dimension": "workers", "description": "d"}], catalog.Counter())
    for src in sources:
        assert src["title"] in text
    assert "请勿手动编辑" in text
