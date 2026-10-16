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


def test_place_box_stands_with_a_person_and_covers_no_label():
    import random
    from telecomsafe.gen.insert import covered, place_box
    person = Label("person", 100, 200, 140, 400)        # 200 px tall, feet at y=400
    helmet = Label("helmet", 105, 200, 135, 230)
    for seed in range(20):
        box = place_box([person, helmet], 1000, 600, (1.0, 3.0), random.Random(seed))
        assert box is not None
        assert abs(box[3] - 400) <= 0.05 * 200 + 1e-6      # bottom at the person's feet
        assert 0.9 * 200 - 1e-6 <= box[3] - box[1] <= 1.1 * 200 + 1e-6
        inside = min(box[2], 1000) - max(box[0], 0)
        assert inside >= 0.5 * (box[2] - box[0]) - 1e-6  # at most half beyond the frame
        assert covered(box, person.box) <= 0.05 and covered(box, helmet.box) <= 0.05


def test_place_box_needs_a_usable_reference_person():
    import random
    from telecomsafe.gen.insert import place_box
    assert place_box([Label("vest", 0, 0, 10, 10)], 640, 640, (1, 3), random.Random(0)) is None
    cut_off = Label("person", 10, 300, 60, 640)          # feet outside the frame: no ground reference
    assert place_box([cut_off], 640, 640, (1, 3), random.Random(0)) is None
    huge = Label("person", 10, 10, 200, 600)              # a truck 3 persons long would not fit even cut off
    assert place_box([huge], 640, 640, (1.0, 3.0), random.Random(0)) is None


def test_tight_box():
    from telecomsafe.gen.insert import tight_box
    m = np.zeros((50, 80), bool)
    m[10:20, 30:45] = True
    assert tight_box(m) == (30, 10, 45, 20) and tight_box(np.zeros((5, 5), bool)) is None


def test_place_box_ignores_people_who_are_not_on_the_ground():
    import random
    from telecomsafe.gen.insert import place_box
    on_scaffold = Label("person", 100, 50, 140, 250)     # feet at 250 of 600: up on a structure
    assert place_box([on_scaffold], 1000, 600, (1.0, 3.0), random.Random(0)) is None
    on_ground = Label("person", 100, 300, 140, 500)
    assert place_box([on_scaffold, on_ground], 1000, 600, (1.0, 3.0), random.Random(0))[3] > 450


def test_select_bases_can_exclude_sources_from_the_scenario(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "class_names", lambda: NAMES)
    images, labels = tmp_path / "images", tmp_path / "labels"
    images.mkdir()
    labels.mkdir()
    sizes = {}
    for stem in ("work_at_height__a", "apd__b"):
        p = images / f"{stem}.jpg"
        p.write_bytes(b"x")
        sizes[p] = (100, 100)
        (labels / f"{stem}.txt").write_text("0 0.5 0.5 0.1 0.3\n")
    cfg = {"base": {"require": ["person"], "exclude_sources": ["work_at_height"]}}
    assert [p.stem for p in select_bases(cfg, images, labels, sizes=sizes)] == ["apd__b"]


def test_person_parts_and_standalone_people():
    from telecomsafe.gen.scene import person_parts, standalone_people
    a = Label("person", 100, 100, 200, 400)
    b = Label("person", 150, 120, 260, 420)               # overlaps a
    c = Label("person", 500, 100, 600, 400)
    edge = Label("person", 0, 100, 60, 400)               # cut by the left edge
    helmet_a, vest_c = Label("helmet", 130, 100, 170, 130), Label("vest", 520, 180, 580, 280)
    labels = [a, b, c, edge, helmet_a, vest_c]
    assert standalone_people(labels, 800, 600) == [c]
    assert [lb.cls for lb in person_parts(labels, c)] == ["person", "vest"]
    assert helmet_a in person_parts(labels, a) and vest_c not in person_parts(labels, a)


def test_placement_and_move_keep_the_person_low_and_in_scale():
    import random
    from telecomsafe.gen.scene import move, placement
    p = Label("person", 50, 40, 110, 240)                  # 200 px tall
    for seed in range(20):
        s, dx, dy = placement(p, (1000, 800), random.Random(seed))
        q = move(p, s, dx, dy)
        assert 0.18 * 800 - 1e-6 <= q.h <= 0.38 * 800 + 1e-6
        assert 0.78 * 800 - 1e-6 <= q.y2 <= 0.97 * 800 + 1e-6
        assert q.x1 >= 0 and q.x2 <= 1000
        assert abs(q.w / q.h - p.w / p.h) < 1e-9          # aspect ratio kept


def test_recolor_moves_only_the_masked_pixels_halfway():
    from telecomsafe.gen.scene import recolor
    fg = np.full((10, 10, 3), 200, np.uint8)
    mask = np.zeros((10, 10), np.uint8)
    mask[2:8, 2:8] = 255
    ref = np.full((5, 5, 3), 100, np.uint8)
    out = recolor(fg, mask, ref, amount=0.5)
    assert abs(int(out[5, 5, 0]) - 150) <= 1 and out[0, 0, 0] == 200


def test_full_body_needs_nose_and_both_ankles_inside_the_box():
    from telecomsafe.gen.scene import full_body
    kp = np.zeros((17, 2))
    conf = np.zeros(17)
    kp[0], kp[15], kp[16] = (50, 20), (40, 190), (60, 190)
    conf[[0, 15, 16]] = 0.9
    assert full_body(kp, conf, (0, 0, 100, 200))
    conf[16] = 0.2                                       # an ankle hidden: half body or occluded
    assert not full_body(kp, conf, (0, 0, 100, 200))
    conf[16] = 0.9
    assert not full_body(kp, conf, (0, 0, 100, 150))     # ankles outside the box: another person's pose


def test_feet_strip_sits_at_the_feet_and_stays_in_the_frame():
    from telecomsafe.gen.scene import feet_strip
    p = Label("person", 100, 100, 140, 300)
    x1, y1, x2, y2 = feet_strip(p, (1000, 1000))
    assert x1 < 100 and x2 > 140 and y1 < 300 < y2 and y2 - y1 < 0.2 * p.h
    s = feet_strip(Label("person", 0, 800, 40, 1000), (1000, 1000))
    assert s[0] == 0 and s[3] == 1000


def test_is_grayscale_tells_black_and_white_photos_apart():
    from telecomsafe.gen.scene import is_grayscale
    rng = np.random.default_rng(0)
    gray = rng.integers(0, 255, (64, 64), dtype=np.uint8)
    assert is_grayscale(Image.fromarray(np.stack([gray] * 3, -1)))
    assert not is_grayscale(Image.fromarray(rng.integers(0, 255, (64, 64, 3), dtype=np.uint8)))


def test_reject_record_moves_all_three_files_and_notes_the_reason(tmp_path):
    from telecomsafe.gen.common import reject_record, write_record
    ok, bad = tmp_path / "filtered", tmp_path / "rejected"
    write_record(ok / "a.rf.1", Image.new("RGB", (8, 8)), [], {"base": "a.jpg"})
    reject_record(ok / "a.rf.1", bad, "g4: unnatural")
    assert not list(ok.iterdir())
    assert sorted(p.name for p in bad.iterdir()) == ["a.rf.1.jpg", "a.rf.1.json", "a.rf.1.txt"]
    assert json.loads((bad / "a.rf.1.json").read_text(encoding="utf-8"))["reason"] == "g4: unnatural"


def test_wilson_interval():
    from telecomsafe.gen.g4 import wilson
    lo, hi = wilson(75, 100)
    assert 0.65 < lo < 0.75 < hi < 0.83
    assert wilson(0, 0) == (0.0, 1.0)
    assert wilson(10, 10)[1] == 1.0


def test_coco_to_openpose_builds_the_neck_and_drops_hidden_points():
    from telecomsafe.gen.scene_gen import coco_to_openpose
    xy = np.arange(34, dtype=float).reshape(17, 2)
    conf = np.ones(17)
    conf[3] = 0.1                                          # left ear hidden
    pts = coco_to_openpose(xy, conf)
    assert len(pts) == 18 and pts[0] == list(xy[0])
    assert pts[1] == [(xy[5][0] + xy[6][0]) / 2, (xy[5][1] + xy[6][1]) / 2]
    assert pts[2] == list(xy[6]) and pts[17] is None      # right shoulder; left ear


def test_pose_normalise_and_place_round_trip():
    from telecomsafe.gen.scene_gen import normalise_pose, place_pose
    pts = [[15.0, 30.0], None]
    n = normalise_pose(pts, (10, 20, 30, 60))
    assert n == [[0.25, 0.25], None]
    assert place_pose(n, (100, 200, 140, 280)) == [[110.0, 220.0], None]


def test_person_height_and_focal():
    from telecomsafe.gen.scene_gen import focal_px, person_height_px
    assert person_height_px(1000, 10, 1.75) == pytest.approx(175)
    f = focal_px(Image.new("RGB", (1200, 800)), fov_deg=90)
    assert f == pytest.approx(600)


def test_ppe_matches_needs_the_prompted_classes_and_not_their_opposites():
    from telecomsafe.gen.scene_gen import ppe_matches
    person = (0, 0, 100, 200)
    dets = [("helmet", (30, 0, 70, 30), 0.8), ("no_vest", (20, 50, 80, 120), 0.6)]
    ok, labels = ppe_matches(dets, person, {"helmet": True, "vest": False})
    assert ok and [lb.cls for lb in labels] == ["helmet", "no_vest"]
    assert not ppe_matches(dets, person, {"helmet": True, "vest": True})[0]
    assert not ppe_matches(dets + [("no_helmet", (30, 0, 70, 30), 0.5)], person, {"helmet": True, "vest": False})[0]
    assert not ppe_matches([("helmet", (300, 0, 340, 30), 0.9)], person, {"helmet": True, "vest": False})[0]


def test_draw_pose_draws_on_black():
    from telecomsafe.gen.scene_gen import draw_pose
    pts = [None] * 18
    pts[1], pts[2] = [50, 50], [80, 50]
    img = np.asarray(draw_pose(pts, (128, 128), 4))
    assert img[50, 65].any() and not img[10, 10].any()


def test_ppe_matches_falls_back_to_low_threshold_boxes_for_the_wanted_class():
    from telecomsafe.gen.scene_gen import ppe_matches
    person = (0, 0, 100, 200)
    dets = [("no_vest", (20, 50, 80, 120), 0.5)]
    low = [("no_helmet", (30, 0, 70, 30), 0.08)]
    ok, labels = ppe_matches(dets, person, {"helmet": False, "vest": False}, low)
    assert ok and [lb.cls for lb in labels] == ["no_helmet", "no_vest"]
    assert not ppe_matches(dets, person, {"helmet": False, "vest": False})[0]
