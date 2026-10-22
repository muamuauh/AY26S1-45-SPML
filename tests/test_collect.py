"""Candidate collection and screening for TelecomEval (no network, no GPU)."""

import json
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

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


def test_wikimedia_drops_small_images_and_unfree_licences(monkeypatch):
    def page(pid, w, h, licence):
        return {"pageid": pid, "title": f"File:{pid}.jpg", "imageinfo": [{
            "mime": "image/jpeg", "width": w, "height": h, "url": f"https://x/{pid}.jpg",
            "descriptionurl": f"https://c/{pid}", "extmetadata": {"LicenseShortName": {"value": licence}}}]}

    pages = {"1": page(1, 3000, 2000, "Public domain"), "2": page(2, 900, 600, "Public domain"),
             "3": page(3, 3000, 2000, "All rights reserved")}
    monkeypatch.setattr(collect_open, "_wikimedia_titles", lambda *a: [p["title"] for p in pages.values()])
    monkeypatch.setattr(collect_open, "get_json", lambda *a: {"query": {"pages": pages}})
    monkeypatch.setattr(collect_open.time, "sleep", lambda s: None)
    kept = collect_open.wikimedia(None, 'insource:"dvidshub" tower', None, 10, min_side=1000)
    assert [it["source_id"] for it in kept] == ["1"]
    assert len(collect_open.wikimedia(None, "tower", None, 10)) == 2   # no size limit by default


def test_shortlist_scores_and_picks_a_varied_list():
    from telecomsafe.data import shortlist as sl
    dets = [("person", (0, 10, 50, 160), 0.9), ("helmet", (10, 10, 30, 30), 0.8), ("harness", (5, 60, 45, 100), 0.6)]
    assert sl.person_size(dets, 500) == pytest.approx(1.0)          # 150 px of 500 = 30 %: full marks
    assert sl.class_variety(dets) == pytest.approx(1.0)             # person + helmet + harness (rare, counts 2)
    assert sl.event_key("File:1-91 CAV PLT LFX (6568780).jpg") == sl.event_key("File:1-91 CAV PLT LFX (6568779).jpg")
    cands = [{"file": f"{i}.jpg", "score": 1 - i / 10, "scene": "tower", "title": t}
             for i, t in enumerate(["File:Climb (1).jpg", "File:Climb (2).jpg", "File:Climb (3).jpg", "File:Mast.jpg", "File:Dup.jpg"])]
    hashes = {"0.jpg": 0, "1.jpg": 0xFFFF, "2.jpg": 0xFFFF0000, "3.jpg": 0xFF00FF00FF, "4.jpg": 1}   # 4 ≈ 0
    picked = [c["file"] for c in sl.pick(cands, 10, hashes)]
    assert picked == ["0.jpg", "1.jpg", "3.jpg"]   # 2: third of one event; 4: near-duplicate of 0


def test_generated_scenarios_cover_every_class_and_vary_the_setting():
    from telecomsafe.data import generate_eval as g
    from telecomsafe.paths import class_names
    cov = g.coverage()
    assert set(cov) == set(class_names()) and min(cov.values()) >= 5
    assert len({s[0] for s in g.SCENARIOS}) == len(g.SCENARIOS)
    prompts = [g.prompt_for(k, s) for k, s in enumerate(g.SCENARIOS)]
    assert len({p.split("Setting: ")[1] for p in prompts}) > len(g.SCENARIOS) // 2   # settings are not all alike
    assert all(p.startswith(g.STYLE) for p in prompts)


@pytest.mark.parametrize("text,code", [
    ("Public domain", "PDM"), ("Public domain (US federal government work)", "US-GOV"), ("by", "CC-BY"),
    ("CC BY-SA 3.0 de", "CC-BY-SA"), ("CC BY 2.0", "CC-BY"), ("cc0", "CC0"), ("GENERATED", "GENERATED"),
    ("own photo", "OWN"), ("CC BY-NC 4.0", None), ("CC BY-ND 2.0", None), ("All rights reserved", None), ("", None)])
def test_contribution_licences(text, code):
    from telecomsafe.data.contrib import licence_code
    assert licence_code(text) == code


def _contribution(root, rows, labels):
    from telecomsafe.data.contrib import FIELDS
    (root / "images").mkdir(parents=True)
    (root / "labels").mkdir()
    for name, text in labels.items():
        Image.fromarray(np.zeros((800, 1200, 3), np.uint8)).save(root / "images" / name)
        (root / "labels" / f"{name.rsplit('.', 1)[0]}.txt").write_text(text)
    import csv
    with open(root / "sources.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows([{k: r.get(k, "") for k in FIELDS} for r in rows])
    return root


def test_contribution_check_finds_format_and_licence_problems(tmp_path):
    from telecomsafe.data.contrib import check
    ok = "0 0.5 0.5 0.2 0.6\n1 0.5 0.25 0.05 0.05\n3 0.5 0.4 0.15 0.2\n"
    folder = _contribution(tmp_path / "c", [
        {"file": "a.jpg", "subset": "telecom", "method": "collected", "licence": "CC0"},
        {"file": "b.jpg", "subset": "telecom", "method": "generated", "licence": "GENERATED"},
        {"file": "c.jpg", "subset": "tower", "method": "collected", "licence": "CC BY-NC 4.0"},
        {"file": "d.jpg", "subset": "near", "method": "collected", "licence": "CC BY 4.0"},
    ], {"a.jpg": ok, "b.jpg": ok, "c.jpg": ok, "d.jpg": "1 0.5 0.5 0.1 0.1\n9 0.5 0.5 0.1 0.1\n"})
    errors, warnings, counts, rows = check(folder)
    text = "\n".join(errors)
    assert "c.jpg: subset must be telecom or near" in text and "c.jpg: licence 'CC BY-NC 4.0' is not allowed" in text
    assert "d.jpg: CC-BY needs the creator" in text and "class id 9" in text
    assert any(w.startswith("d.jpg: no person box") for w in warnings)   # a warning: people may be < half visible
    assert not any(e.startswith(("a.jpg", "b.jpg")) for e in errors)
    assert any("short side 800 px" in w for w in warnings) and any("no harness box" in w for w in warnings)


def test_image_api_endpoint_and_both_response_shapes():
    import base64

    from telecomsafe.data.generate_eval import endpoint, image_bytes
    assert endpoint(None) == "https://api.openai.com/v1/images/generations"
    assert endpoint("https://relay.example.com/v1/") == "https://relay.example.com/v1/images/generations"
    assert endpoint("https://relay.example.com/v1/images/generations") == "https://relay.example.com/v1/images/generations"
    assert image_bytes({"b64_json": base64.b64encode(b"png").decode()}, None) == b"png"

    class S:
        def get(self, url, timeout):
            return SimpleNamespace(content=b"jpg", raise_for_status=lambda: None)
    assert image_bytes({"url": "https://cdn/x.png"}, S()) == b"jpg"


def test_contributor_is_a_traceable_suffix():
    from telecomsafe.data.contrib import eval_name, owned_by
    assert eval_name("tower_01.JPG", "Lu") == "tower_01__Lu.jpg"
    assert owned_by("tower_01__Lu.jpg", "Lu") and not owned_by("tower_01__Lu.jpg", "Lin")
    assert owned_by("tower_01__Lu.txt", "Lu")
