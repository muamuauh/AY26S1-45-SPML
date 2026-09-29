"""Box geometry used by the rules. Boxes are (x1, y1, x2, y2) in pixels."""

from __future__ import annotations

Box = tuple[float, float, float, float]


def area(b: Box) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def intersection(a: Box, b: Box) -> float:
    return area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


def iou(a: Box, b: Box) -> float:
    inter = intersection(a, b)
    union = area(a) + area(b) - inter
    return inter / union if union > 0 else 0.0


def ioa(inner: Box, outer: Box) -> float:
    """Share of `inner` covered by `outer`."""
    a = area(inner)
    return intersection(inner, outer) / a if a > 0 else 0.0


def gap(a: Box, b: Box) -> float:
    """Shortest edge-to-edge distance in pixels (0 when the boxes overlap)."""
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return (dx * dx + dy * dy) ** 0.5


def is_operator(person: Box, machine: Box, min_inside: float = 0.9, ground_band: float = 0.25) -> bool:
    """A person inside a machine's box whose feet are well above the machine's base is its operator (in the cab).

    Workers standing next to the machine have their feet within the bottom `ground_band` of the machine box.
    """
    if ioa(person, machine) < min_inside:
        return False
    machine_h = machine[3] - machine[1]
    return machine[3] - person[3] > ground_band * machine_h


def metric_gap(person: Box, other: Box, person_height_m: float = 1.7) -> float:
    """Approximate real-world gap in metres, using the person box height as scale.

    A monocular estimate: it ignores depth, so it is only meaningful for objects at a
    similar distance from the camera. Good enough to flag 'suspiciously close'.
    """
    h = person[3] - person[1]
    return gap(person, other) / h * person_height_m if h > 0 else float("inf")
