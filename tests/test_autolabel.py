"""Auto-labelling and the phase 2 prompt bank (no GPU, no models, no API calls)."""

import numpy as np

from telecomsafe.data.autolabel import harness_box, head_box, merge, parse_json, same_object, to_labels, torso_box, write_yolo
from telecomsafe.data.generate_synth import BANKS, prompt_bank

PERSON = [100, 100, 200, 400]
BOX = [10, 10, 20, 20]


def labels_for(answer, people=(PERSON,), vehicles=()):
    n = len(people)
    return to_labels(list(people), [BOX] * n, [BOX] * n, [BOX] * n, list(vehicles), answer)


def test_same_object_catches_overlaps_and_partial_boxes():
    assert same_object([0, 0, 100, 100], [5, 5, 100, 100])
    assert same_object([0, 0, 100, 200], [10, 10, 60, 80])  # a partial box inside a whole person, low IoU
    assert not same_object([0, 0, 100, 100], [200, 200, 300, 300])


def test_merge_keeps_the_primary_box_of_each_object():
    a, part, other = [0, 0, 100, 200], [10, 10, 60, 80], [300, 0, 400, 200]
    assert merge([a], [part, other]) == [a, other]


def test_worker_gets_ppe_labels():
    answer = {"people": [{"id": 1, "person": True, "role": "worker", "helmet": "none", "hi_vis": "no", "harness": "yes"}]}
    assert [c for c, _ in labels_for(answer)] == ["person", "no_helmet", "no_vest", "harness"]


def test_bystander_gets_a_person_box_only():
    answer = {"people": [{"id": 1, "person": True, "role": "bystander", "helmet": "none", "hi_vis": "no", "harness": "no"}]}
    assert [c for c, _ in labels_for(answer)] == ["person"]


def test_not_visible_and_rejected_people_get_no_class():
    answer = {"people": [{"id": 1, "person": True, "role": "worker", "helmet": "not_visible", "hi_vis": "not_visible", "harness": "not_visible"},
                         {"id": 2, "person": False}]}
    assert [c for c, _ in labels_for(answer, people=(PERSON, [300, 100, 400, 400]))] == ["person"]


def test_vehicle_kinds():
    answer = {"people": [], "vehicles": [{"id": 1, "kind": "machinery"}, {"id": 2, "kind": "vehicle"}, {"id": 3, "kind": "neither"}]}
    assert [c for c, _ in labels_for(answer, people=(), vehicles=(BOX, BOX, BOX))] == ["machinery", "vehicle"]


def test_person_fractions_without_pose():
    x1, y1, x2, y2 = head_box(PERSON)
    assert y1 == 100 and y2 < 200 and x1 > 100 and x2 < 200  # top of the person box
    t, h = torso_box(PERSON), harness_box(PERSON)
    assert t[1] > y1 and h[3] > t[3]  # the harness reaches below the torso, to the thighs


def test_head_box_sits_above_the_face_keypoints():
    kp, conf = np.zeros((17, 2)), np.zeros(17)
    kp[:5] = [[150, 150], [145, 148], [155, 148], [140, 150], [160, 150]]
    conf[:5] = 0.9
    x1, y1, x2, y2 = head_box(PERSON, kp, conf)
    assert y1 < 150 and (y1 + y2) / 2 < 150 and x1 < 140 and x2 > 160


def test_parse_json_ignores_surrounding_text():
    assert parse_json('Here it is:\n```json\n{"people": []}\n```') == {"people": []}


def test_write_yolo_clips_and_drops_tiny_boxes(tmp_path):
    path = tmp_path / "a.txt"
    write_yolo(path, [("person", [-10, 0, 50, 100]), ("vehicle", [5, 5, 5.5, 5.5])], 100, 100)
    assert path.read_text(encoding="utf-8") == "0 0.250000 0.500000 0.500000 1.000000"


def test_prompt_bank_is_unique_and_cycles_the_scene_families():
    for target, bank in BANKS.items():
        scenes = bank[0]
        prompts = prompt_bank(target, 2 * len(scenes))
        assert len({p["prompt"] for p in prompts}) == len(prompts)
        assert [p["family"] for p in prompts[: len(scenes)]] == [s[0] for s in scenes]
        assert prompt_bank(target, 5) == prompts[:5]  # resuming a run sees the same prompts
