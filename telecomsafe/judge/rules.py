"""Rule-based risk judgement (levels 1–2 of the fusion design; no learnable layer).

Rules are declared in configs/rules.yaml; each `type` below is one predicate.

    ppe_violation            a negative PPE class was detected (e.g. no_helmet)
                             params: negative_class, min_conf
    proximity                a person is within max_distance_m of a target class
                             params: targets, max_distance_m, min_conf,
                             exclude_operators (default true: people in the cab are not "near" their machine)
    on_structure_without_ppe a person overlaps a structure (tower) and has no PPE box
                             params: structure_class, ppe_class, min_overlap, min_conf
"""

from __future__ import annotations

from pathlib import Path

from telecomsafe.judge import geometry as geo
from telecomsafe.judge.schema import Detection, RiskResult, RuleHit
from telecomsafe.paths import CONFIGS, load_yaml


def _of(dets: list[Detection], cls: str, min_conf: float) -> list[int]:
    return [i for i, d in enumerate(dets) if d.cls == cls and d.conf >= min_conf]


def ppe_violation(rule: dict, dets: list[Detection], ctx: dict) -> list[RuleHit]:
    p = rule["params"]
    return [_hit(rule, [i], f"{p['negative_class']} · confidence {dets[i].conf:.2f}") for i in _of(dets, p["negative_class"], p.get("min_conf", 0))]


def proximity(rule: dict, dets: list[Detection], ctx: dict) -> list[RuleHit]:
    p = rule["params"]
    min_conf = p.get("min_conf", 0)
    hits = []
    for pi in _of(dets, "person", min_conf):
        for cls in p["targets"]:
            for ti in _of(dets, cls, min_conf):
                if p.get("exclude_operators", True) and geo.is_operator(dets[pi].box, dets[ti].box):
                    continue
                d = geo.metric_gap(dets[pi].box, dets[ti].box, ctx["person_height_m"])
                if d < p["max_distance_m"]:
                    hits.append(_hit(rule, [pi, ti], f"≈{d:.1f} m from {cls}"))
    return hits


def on_structure_without_ppe(rule: dict, dets: list[Detection], ctx: dict) -> list[RuleHit]:
    p = rule["params"]
    min_conf = p.get("min_conf", 0)
    structures = _of(dets, p["structure_class"], min_conf)
    ppe = _of(dets, p["ppe_class"], min_conf)
    hits = []
    for pi in _of(dets, "person", min_conf):
        person = dets[pi].box
        on = [si for si in structures if geo.ioa(person, dets[si].box) >= p.get("min_overlap", 0.3)]
        wearing = any(geo.ioa(dets[k].box, person) >= 0.5 for k in ppe)
        if on and not wearing:
            hits.append(_hit(rule, [pi, on[0]], f"on {p['structure_class']}, no {p['ppe_class']} detected"))
    return hits


PREDICATES = {
    "ppe_violation": ppe_violation,
    "proximity": proximity,
    "on_structure_without_ppe": on_structure_without_ppe,
}


def _hit(rule: dict, detections: list[int], detail: str) -> RuleHit:
    return RuleHit(rule["id"], rule["name"], rule["level"], rule.get("source", ""), detections, detail)


class RuleEngine:
    def __init__(self, config: dict):
        self.rules = [r for r in config["rules"] if r.get("enabled", True)]
        self.ctx = {"person_height_m": config.get("person_height_m", 1.7)}
        unknown = {r["type"] for r in self.rules} - set(PREDICATES)
        if unknown:
            raise ValueError(f"unknown rule types in rules.yaml: {sorted(unknown)}")

    @classmethod
    def from_yaml(cls, path: Path = CONFIGS / "rules.yaml") -> RuleEngine:
        return cls(load_yaml(path))

    def judge(self, dets: list[Detection]) -> RiskResult:
        hits = [h for r in self.rules for h in PREDICATES[r["type"]](r, dets, self.ctx)]
        return RiskResult.from_hits(hits)
