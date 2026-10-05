"""Task packages: zips, the collection checker and both intakes (temporary folders only)."""

import csv
import json
import zipfile

import numpy as np
import pytest
from PIL import Image

from telecomsafe.data import collect_open, package

HEADER = ["file", "source_url", "title", "creator", "licence", "licence_version", "licence_url", "scene", "notes"]


def _image(path, seed, size=(640, 640)):
    rng = np.random.default_rng(seed)
    Image.fromarray(rng.integers(0, 255, (size[1] // 16, size[0] // 16, 3), dtype=np.uint8)).resize(size).save(path)


def _submission(root, rows, images):
    (root / "images").mkdir(parents=True)
    for name, seed in images.items():
        _image(root / "images" / name, seed)
    with open(root / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    return root


@pytest.fixture
def project(tmp_path, monkeypatch):
    """An empty project: candidates folder, rejected folder, manifest, interim and eval folders."""
    out, rejected = tmp_path / "t3" / "images", tmp_path / "t3" / "rejected"
    out.mkdir(parents=True)
    for mod in (collect_open, package):
        monkeypatch.setattr(mod, "OUT", out)
    monkeypatch.setattr(collect_open, "MANIFEST", tmp_path / "manifest.csv")
    monkeypatch.setattr(package, "REJECTED", rejected)
    monkeypatch.setattr(package, "INTERIM", tmp_path / "interim")
    monkeypatch.setattr(package, "EVAL_DIR", tmp_path / "telecom_eval")
    return tmp_path


def test_zip_keeps_scripts_executable(tmp_path):
    folder = tmp_path / "pkg"
    folder.mkdir()
    (folder / "start.command").write_text("#!/bin/bash\n")
    (folder / "README.md").write_text("x")
    with zipfile.ZipFile(package.make_zip(folder)) as z:
        modes = {i.filename.split("/")[-1]: (i.external_attr >> 16) & 0o777 for i in z.infolist()}
    assert modes == {"start.command": 0o755, "README.md": 0o644}


def test_checker_rejects_bad_licences_and_duplicates(tmp_path):
    chk = package.check_module()
    sub = _submission(tmp_path / "sub", [
        ["a.jpg", "https://x.org/1", "t", "Ann", "CC-BY", "4.0", "https://creativecommons.org/licenses/by/4.0/", "tower", ""],
        ["b.jpg", "https://x.org/2", "t", "Ann", "CC-BY-NC", "4.0", "https://creativecommons.org/licenses/by-nc/4.0/", "tower", ""],
        ["c.jpg", "https://x.org/3", "t", "", "CC-BY", "", "", "tower", ""],
        ["d.jpg", "https://seen.org/photo/", "t", "", "CC0", "", "", "rooftop", ""],
        ["e.jpg", "https://x.org/5", "t", "", "PDM", "", "", "beach", ""],
    ], {"a.jpg": 1, "b.jpg": 2, "c.jpg": 3, "d.jpg": 4, "e.jpg": 1})
    errors, warnings, rows = chk.check_submission(sub, {chk.normalise_url("http://www.seen.org/photo")}, [], ["tower", "rooftop"])
    bad = {r["file"] for r in rows if r.get("_bad")}
    assert bad == {"b.jpg", "c.jpg", "d.jpg", "e.jpg"}  # e.jpg is the same photo as a.jpg
    assert any("CC-BY-NC" in e for e in errors) and any("needs the creator" in e for e in errors)
    assert any("already in the project" in e for e in errors) and any("duplicate of another" in e for e in errors)
    assert warnings == ["line 6 (e.jpg): scene 'beach' is not one of tower, rooftop"]


def test_collection_intake_adds_candidates_once(project):
    sub = _submission(project / "sub", [
        ["a.jpg", "https://x.org/1", "Crew", "Ann Lee", "CC-BY-SA", "4.0", "https://creativecommons.org/licenses/by-sa/4.0/", "tower", ""],
        ["b.jpg", "https://dvidshub.net/image/2", "Mast", "Spc. Doe", "US-GOV", "", "", "tower", ""],
    ], {"a.jpg": 1, "b.jpg": 2})
    package.intake_collection(sub, "telecom", "Ann Lee", skip_bad=False)
    rows = {r["file"]: r for r in collect_open.read_manifest()}
    assert set(rows) == {"contrib_ann_lee_a.jpg", "contrib_ann_lee_b.jpg"}
    a, b = rows["contrib_ann_lee_a.jpg"], rows["contrib_ann_lee_b.jpg"]
    assert (a["provider"], a["licence"], a["licence_version"], a["domain"], a["status"]) == ("contrib:ann_lee", "by-sa", "4.0", "telecom", "candidate")
    assert b["licence"] == "Public domain (US federal government work)"
    assert (package.OUT / "contrib_ann_lee_a.jpg").exists()
    with pytest.raises(SystemExit):  # the same submission again: every image is now known
        package.intake_collection(sub, "telecom", "Ann Lee", skip_bad=False)


def test_annotation_intake_maps_package_paths_to_project_images(project):
    for name, seed in (("a.jpg", 1), ("b.jpg", 2)):
        _image(package.OUT / name, seed)
    collect_open.write_manifest([{"file": "a.jpg", "status": "candidate", "subset": "near"},
                                 {"file": "b.jpg", "status": "candidate", "subset": "telecom"}])
    box = {"type": "rectanglelabels", "value": {"x": 10, "y": 10, "width": 20, "height": 40, "rectanglelabels": ["person"]}}
    tower = {"type": "rectanglelabels", "value": {"x": 0, "y": 0, "width": 5, "height": 5, "rectanglelabels": ["tower"]}}
    tasks = [
        {"data": {"image": "/data/local-files/?d=data/images/a.jpg", "file": "a.jpg"},
         "annotations": [{"result": [box, tower], "updated_at": "2026-10-05"}]},
        {"data": {"image": "/data/local-files/?d=data/images/b.jpg", "file": "b.jpg"},
         "annotations": [{"result": [], "was_cancelled": True}]},
    ]
    export = project / "annotations.json"
    export.write_text(json.dumps(tasks), encoding="utf-8")
    package.intake_annotations(export, allow_incomplete=False)
    eval_dir = package.EVAL_DIR
    assert sorted(p.name for p in (eval_dir / "images").iterdir()) == ["a.jpg"]  # b.jpg was skipped
    assert (eval_dir / "labels" / "a.txt").read_text().split() == ["0", "0.200000", "0.300000", "0.200000", "0.400000"]
    assert (eval_dir / "subsets.csv").read_text().splitlines() == ["file,subset", "a.jpg,near"]
    assert (package.INTERIM / "telecom_eval_spot_check.jpg").exists()


def test_annotation_intake_refuses_unfinished_work(project):
    _image(package.OUT / "a.jpg", 1)
    export = project / "annotations.json"
    export.write_text(json.dumps([{"data": {"image": "x", "file": "a.jpg"}, "annotations": []}]), encoding="utf-8")
    with pytest.raises(SystemExit):
        package.intake_annotations(export, allow_incomplete=False)
