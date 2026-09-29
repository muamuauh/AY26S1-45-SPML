"""Perception → judgement interface (I5 in docs/06 §6).

Phase 1 perception emits boxes only. Phase 2 may add fields (masks, attributes)
but must not change the existing ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LEVELS = ("low", "medium", "high")


@dataclass(frozen=True)
class Detection:
    cls: str
    conf: float
    box: tuple[float, float, float, float]  # x1, y1, x2, y2 in pixels


@dataclass
class RuleHit:
    rule_id: str
    name: str
    level: str
    source: str
    detections: list[int] = field(default_factory=list)  # indices into the detection list
    detail: str = ""


@dataclass
class RiskResult:
    level: str
    hits: list[RuleHit] = field(default_factory=list)

    @staticmethod
    def from_hits(hits: list[RuleHit]) -> RiskResult:
        level = max((h.level for h in hits), key=LEVELS.index, default="low")
        return RiskResult(level, sorted(hits, key=lambda h: -LEVELS.index(h.level)))
