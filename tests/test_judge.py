import pytest

from telecomsafe.judge import geometry as geo
from telecomsafe.judge.rules import RuleEngine
from telecomsafe.judge.schema import Detection, RiskResult, RuleHit

PERSON = Detection("person", 0.9, (100, 100, 150, 270))  # 170 px tall → 1 px ≈ 1 cm


def engine(**enable):
    rules = [
        {"id": "R1", "name": "no helmet", "type": "ppe_violation", "level": "medium",
         "params": {"negative_class": "no_helmet", "min_conf": 0.3}},
        {"id": "R3", "name": "tower", "type": "on_structure_without_ppe", "level": "high",
         "params": {"structure_class": "tower", "ppe_class": "harness", "min_overlap": 0.3}},
        {"id": "R4", "name": "near machine", "type": "proximity", "level": "high",
         "params": {"targets": ["machinery"], "max_distance_m": 2.0}},
    ]
    return RuleEngine({"person_height_m": 1.7, "rules": rules})


def test_geometry():
    a, b = (0, 0, 10, 10), (5, 5, 15, 15)
    assert geo.iou(a, b) == pytest.approx(25 / 175)
    assert geo.ioa((0, 0, 10, 10), (0, 0, 5, 10)) == 0.5
    assert geo.gap((0, 0, 10, 10), (13, 14, 20, 20)) == 5.0
    assert geo.gap(a, b) == 0.0
    assert geo.metric_gap(PERSON.box, (250, 100, 400, 270)) == pytest.approx(1.0)


def test_compliant_scene_is_low():
    result = engine().judge([PERSON, Detection("helmet", 0.9, (110, 100, 140, 120))])
    assert result.level == "low" and result.hits == []


def test_no_helmet_is_medium_and_respects_confidence():
    e = engine()
    assert e.judge([PERSON, Detection("no_helmet", 0.8, (110, 100, 140, 120))]).level == "medium"
    assert e.judge([PERSON, Detection("no_helmet", 0.1, (110, 100, 140, 120))]).level == "low"


def test_proximity_threshold():
    e = engine()
    near = e.judge([PERSON, Detection("machinery", 0.9, (250, 100, 400, 270))])  # ≈1.0 m
    far = e.judge([PERSON, Detection("machinery", 0.9, (500, 100, 650, 270))])   # ≈3.5 m
    assert near.level == "high" and near.hits[0].detections == [0, 1]
    assert far.level == "low"


def test_operator_in_cab_is_not_a_proximity_hit():
    machine = Detection("machinery", 0.9, (0, 0, 400, 300))
    in_cab = Detection("person", 0.9, (150, 40, 200, 120))       # feet 180 px above the machine base
    on_ground = Detection("person", 0.9, (150, 150, 200, 295))   # inside the box, feet at ground level
    assert geo.is_operator(in_cab.box, machine.box) and not geo.is_operator(on_ground.box, machine.box)
    assert engine().judge([in_cab, machine]).level == "low"
    assert engine().judge([on_ground, machine]).level == "high"


def test_on_tower_without_harness():
    tower = Detection("tower", 0.9, (50, 0, 300, 400))
    harness = Detection("harness", 0.9, (105, 150, 145, 220))
    assert engine().judge([PERSON, tower]).level == "high"
    assert engine().judge([PERSON, tower, harness]).level == "low"


def test_result_level_is_the_highest_hit():
    hits = [RuleHit("R1", "a", "medium", ""), RuleHit("R4", "b", "high", "")]
    result = RiskResult.from_hits(hits)
    assert result.level == "high" and result.hits[0].rule_id == "R4"


def test_unknown_rule_type_fails():
    with pytest.raises(ValueError):
        RuleEngine({"rules": [{"id": "X", "name": "x", "type": "magic", "level": "low", "params": {}}]})


def test_shipped_rules_yaml_loads():
    e = RuleEngine.from_yaml()
    assert {r["id"] for r in e.rules} >= {"R1", "R2", "R4"}
