"""Generation pipeline helpers (no GPU, no models)."""

import json

import numpy as np
import pytest
from PIL import Image

from telecomsafe.gen import common, gates
from telecomsafe.gen.common import Label, iou, read_labels, select_bases, write_labels, write_record
from telecomsafe.gen.inpaint import crop_square, ellipse_mask, head_box, match_colors

NAMES = ["person", "helmet", "no_helmet", "vest", "no_vest", "harness", "machinery", "vehicle"]


def test_labels_roundtrip_and_clipping(tmp_path):
    labels = [Label("helmet", 10, 20, 50, 60), Label("person", -5, 0, 80, 120), Label("vehicle", 99, 99, 99.5, 99.5)]
    write_labels(tmp_path / "a.txt", labels, 100, 100, NAMES)
    back = read_labels(tmp_path / "a.txt", 100, 100, NAMES)
    assert [lb.cls for lb in back] == ["helmet", "person"]  # the sub-pixel box is dropped
    assert [round(v, 3) for v in back[0].box] == [10, 20, 50, 60]
    assert back[1].x1 == 0 and back[1].y2 == 100  # clipped to the image


def test_crop_square_stays_inside_and_covers_the_box():
    box = crop_square((90, 5, 100, 15), 120, 100, 4.0)
    assert box[2] - box[0] == box[3] - box[1] == 40
    assert 0 <= box[0] and box[2] <= 120 and 0 <= box[1] and box[3] <= 100
    assert box[0] <= 90 and box[2] >= 100 and box[1] <= 5
    big = crop_square((0, 0, 200, 200), 100, 80, 4.0)  # never larger than the image
    assert big[2] - big[0] == big[3] - big[1] == 80 and big[0] >= 0 and big[2] <= 100


def test_head_box_extends_below_the_helmet():
    x1, y1, x2, y2 = head_box((100, 100, 140, 130))
    assert 100 < x1 < x2 < 140 and y1 > 100 and y2 > 130


def test_ellipse_mask_is_slightly_larger_than_the_box():
    m = np.asarray(ellipse_mask((200, 200), (80, 80, 120, 120))) > 0
    ys, xs = np.nonzero(m)
    assert xs.min() < 80 and xs.max() > 120 and ys.min() < 80
    assert m[100, 100] and not m[10, 10]


def test_match_colors_removes_a_global_shift():
    rng = np.random.default_rng(0)
    ref = rng.integers(60, 200, (64, 64, 3)).astype(np.uint8)
    gen = np.clip(ref.astype(int) + 40, 0, 255).astype(np.uint8)  # the inpainted crop came back brighter
    mask = Image.new("L", (64, 64), 0)
    mask.paste(255, (24, 24, 40, 40))
    out = np.asarray(match_colors(Image.fromarray(gen), Image.fromarray(ref), mask, 6), dtype=float)
    assert abs(out.mean() - ref.mean()) < 3 < abs(gen.astype(float).mean() - ref.mean())


def test_iou():
    assert iou((0, 0, 10, 10), (0, 0, 10, 10)) == 1
    assert iou((0, 0, 10, 10), (20, 20, 30, 30)) == 0
    assert abs(iou((0, 0, 10, 10), (5, 0, 15, 10)) - 1 / 3) < 1e-9


def test_select_bases_applies_the_scenario_rules(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "class_names", lambda: NAMES)
    images, labels = tmp_path / "images", tmp_path / "labels"
    images.mkdir()
    rows = {
        "construction_ppe__ok": "1 0.5 0.2 0.1 0.10\n0 0.5 0.5 0.3 0.9\n",      # helmet 10% of the height
        "construction_ppe__tiny": "1 0.5 0.2 0.02 0.02\n0 0.5 0.5 0.3 0.9\n",   # helmet too small
        "construction_ppe__crowd": "1 0.5 0.2 0.1 0.10\n" + "0 0.5 0.5 0.1 0.2\n" * 6,
        "construction_ppe__nohelmet": "0 0.5 0.5 0.3 0.9\n",
        "apd__ok": "1 0.5 0.2 0.1 0.10\n0 0.5 0.5 0.3 0.9\n",
    }
    sizes = {}
    for stem, text in rows.items():
        p = images / f"{stem}.jpg"
        p.write_bytes(b"x")
        sizes[p] = (1000, 1000)
        (labels / f"{stem}.txt").parent.mkdir(exist_ok=True)
        (labels / f"{stem}.txt").write_text(text)
    cfg = {"base": {"require": ["helmet"], "helmet_height": [0.04, 0.3], "max_people": 4}, "min_helmet_px": 40}
    got = select_bases(cfg, images, labels, sizes=sizes, exclude_sources=("apd",))
    assert [p.stem for p in got] == ["construction_ppe__ok"]


def test_write_record_keeps_image_labels_and_provenance(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "class_names", lambda: NAMES)
    write_record(tmp_path / "x", Image.new("RGB", (100, 50)), [Label("no_helmet", 10, 10, 30, 30)], {"seed": 7})
    assert (tmp_path / "x.jpg").exists()
    assert (tmp_path / "x.txt").read_text().startswith("2 ")
    meta = json.loads((tmp_path / "x.json").read_text())
    assert meta["seed"] == 7 and meta["labels"][0]["cls"] == "no_helmet"


def test_g0_flags_near_duplicates_of_held_out_images(tmp_path):
    rng = np.random.default_rng(1)
    a = rng.integers(0, 255, (16, 16, 3), dtype=np.uint8)
    b = rng.integers(0, 255, (16, 16, 3), dtype=np.uint8)
    Image.fromarray(a).resize((128, 128)).save(tmp_path / "held.png")
    Image.fromarray(a).resize((128, 128)).save(tmp_path / "copy.png")
    Image.fromarray(b).resize((128, 128)).save(tmp_path / "other.png")
    assert gates.g0_leak_mask([tmp_path / "copy.png", tmp_path / "other.png"], [tmp_path / "held.png"]) == [True, False]


def test_kid_is_near_zero_for_the_same_distribution():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(300, 16))
    assert abs(gates.kid(x, rng.normal(size=(300, 16)))) < 0.05
    assert gates.kid(x, rng.normal(2.0, 1.0, size=(300, 16))) > 0.5


@pytest.mark.parametrize("sid", ["remove_helmet", "remove_vest", "add_harness", "telecom_scene_transfer"])
def test_scenarios_have_what_the_pipeline_needs(sid):
    cfg = common.scenario(sid)
    assert cfg["target"] > 0 and cfg["route"] and cfg["model"] and cfg["seed"] == 0


def test_record_names_keep_dotted_stems_apart(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "class_names", lambda: NAMES)
    for stem in ("wah__IMG_122_jpg.rf.aaaa_1", "wah__IMG_122_jpg.rf.bbbb_2"):
        write_record(tmp_path / stem, Image.new("RGB", (10, 10)), [], {"base": stem + ".jpg"})
    assert len(list(tmp_path.glob("*.jpg"))) == 2 and len(list(tmp_path.glob("*.json"))) == 2
    assert common.done_bases(tmp_path) == {"wah__IMG_122_jpg.rf.aaaa_1.jpg", "wah__IMG_122_jpg.rf.bbbb_2.jpg"}


def test_fill_prompt_varies_with_the_seed_and_is_reproducible():
    from telecomsafe.gen.inpaint import fill_prompt
    cfg = {"prompt": "worker wearing a {garment}", "variables": {"garment": ["red shirt", "blue jacket", "grey hoodie"]}}
    picks = {fill_prompt(cfg, s) for s in range(30)}
    assert len(picks) == 3 and fill_prompt(cfg, 7) == fill_prompt(cfg, 7)
    assert fill_prompt({"prompt": "  plain  "}, 0) == "plain"


def test_select_bases_size_rules_work_for_any_class(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "class_names", lambda: NAMES)
    images, labels = tmp_path / "images", tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    sizes = {}
    for stem, text in {"src__big": "3 0.5 0.5 0.3 0.4\n", "src__small": "3 0.5 0.5 0.1 0.05\n",
                       "src__harness": "3 0.5 0.5 0.3 0.4\n5 0.5 0.5 0.3 0.4\n"}.items():
        p = images / f"{stem}.jpg"
        p.write_bytes(b"x")
        sizes[p] = (1000, 1000)
        (labels / f"{stem}.txt").write_text(text)
    cfg = {"base": {"require": ["vest"], "exclude": ["harness"], "vest_height": [0.12, 0.7]}, "min_vest_px": 60}
    assert [p.stem for p in select_bases(cfg, images, labels, sizes=sizes)] == ["src__big"]
