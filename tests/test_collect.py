"""Candidate collection and screening for TelecomEval (no network, no GPU)."""

import json
from types import SimpleNamespace

import numpy as np
import pytest

from telecomsafe.data import collect_open, screen
from telecomsafe.data.collect_video import visible_people

FLICKR_NAMES = {
    "All Rights Reserved": False,
    "Attribution-NonCommercial-ShareAlike License": False,
    "Attribution-NonCommercial License": False,
    "Attribution-NoDerivs License": False,
    "Attribution License": True,
    "Attribution-ShareAlike License": True,
    "No known copyright restrictions": True,
    "United States Government Work": True,
    "Public Domain Dedication (CC0)": True,
    "Public Domain Mark": True,
    "CC BY 4.0": True,
    "CC BY-SA 4.0": True,
    "CC BY-NC 4.0": False,
    "CC BY-ND 4.0": False,
}


@pytest.mark.parametrize("name,ok", FLICKR_NAMES.items())
def test_flickr_keeps_only_redistributable_licences(name, ok):
    assert bool(collect_open.FLICKR_OK.search(name) and not collect_open.FLICKR_NOT_OK.search(name)) is ok


def test_dvids_skips_third_party_and_copyrighted_images():
    assert collect_open.DVIDS_RESTRICTED.search("Courtesy photo")
    assert collect_open.DVIDS_RESTRICTED.search("© 2024 Example Corp")
    assert not collect_open.DVIDS_RESTRICTED.search("Staff Sgt. Jane Doe 1st Signal Brigade")


def test_queries_carry_a_domain():
    assert collect_open.domain_of("tower climber") == "telecom"
    assert collect_open.domain_of("lineworker bucket truck") == "near"


def _result(boxes):
    names = {0: "person", 1: "helmet", 2: "no_helmet", 3: "vest"}
    ids = {v: k for k, v in names.items()}
    return SimpleNamespace(names=names, boxes=SimpleNamespace(
        cls=np.array([ids[n] for n, _ in boxes]), xyxy=np.array([b for _, b in boxes])))


def test_visible_people_needs_a_head_in_the_person_box():
    # whole person with a helmet on top → counted
    assert visible_people(_result([("person", (100, 100, 200, 500)), ("helmet", (130, 105, 170, 140))]), 1000) == 1
    # helmet-cam: hands detected as a person, no head → not counted
    assert visible_people(_result([("person", (0, 600, 300, 1000))]), 1000) == 0
    # head in the bottom half of the box (someone else's) → not counted
    assert visible_people(_result([("person", (100, 100, 200, 500)), ("no_helmet", (130, 400, 170, 440))]), 1000) == 0
    # tiny person → not counted
    assert visible_people(_result([("person", (100, 100, 120, 150)), ("helmet", (105, 101, 115, 110))]), 1000) == 0


def test_apply_moves_rejected_and_records_subsets(tmp_path, monkeypatch):
    out, rejected, manifest = tmp_path / "images", tmp_path / "rejected", tmp_path / "manifest.csv"
    out.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg", "d.jpg"):
        (out / name).write_bytes(b"x")
    monkeypatch.setattr(collect_open, "MANIFEST", manifest)
    monkeypatch.setattr(collect_open, "OUT", out)
    monkeypatch.setattr(screen, "OUT", out)
    monkeypatch.setattr(screen, "REJECTED", rejected)
    collect_open.write_manifest([{"file": n, "provider": "p", "source_id": n, "status": "candidate"}
                                 for n in ("a.jpg", "b.jpg", "c.jpg", "d.jpg")])
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({"a.jpg": "telecom", "b.jpg": "near", "c.jpg": "reject"}), encoding="utf-8")
    screen.apply(decisions)
    rows = {r["file"]: r for r in collect_open.read_manifest()}
    assert rows["a.jpg"]["subset"] == "telecom" and rows["b.jpg"]["subset"] == "near"
    assert rows["c.jpg"]["status"] == "rejected" and (rejected / "c.jpg").exists() and not (out / "c.jpg").exists()
    assert rows["d.jpg"]["subset"] == "" and rows["d.jpg"]["status"] == "candidate"
    assert rows["a.jpg"]["domain"] == "telecom"  # filled in for rows written without one


def test_review_page_embeds_candidates_safely(tmp_path, monkeypatch):
    out = tmp_path / "images"
    out.mkdir()
    (out / "a.jpg").write_bytes(b"x")
    (out / "b.jpg").write_bytes(b"x")
    monkeypatch.setattr(screen, "OUT", out)
    row = {"status": "candidate", "title": "</script><b>x", "provider": "p", "licence": "by", "landing_url": "u", "persons": "0"}
    page = screen.review_page([{**row, "file": "a.jpg", "clip_score": "0.2"}, {**row, "file": "b.jpg", "clip_score": "0.99"}])
    assert "</script><b>" not in page
    assert page.count('"state": "reject"') == 1  # only the low-scoring image with nobody visible
