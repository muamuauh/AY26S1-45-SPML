"""TelecomEval contributions: everyone hands in ~50 labelled images in one folder format; merge them here.

    python -m telecomsafe.data.contrib check  <folder>                     # validate a contribution
    python -m telecomsafe.data.contrib annotate <folder>                   # pre-label + Label Studio project
    python -m telecomsafe.data.contrib export <folder>                     # Label Studio → <folder>/labels/
    python -m telecomsafe.data.contrib intake <folder> --contributor <name>    # merge into data/raw/telecom_eval/

A contribution folder (format: docs/TelecomEval-Contribution-EN.md):

    images/        the photos (jpg / png / webp)
    labels/        one YOLO file per image, class ids in configs/taxonomy.yaml order (0 person ... 7 vehicle)
    sources.csv    file, subset (telecom | near), method (collected | own_photo | generated), source_url,
                   title, creator, licence, licence_version, licence_url, notes

`annotate` / `export` are for contributors who use this project's Label Studio (`labelstudio serve` must be
running); anyone else can label with any tool that writes YOLO files. `intake` re-runs `check`, refuses
images that are near-duplicates of the training data (they would leak) or of images already merged,
copies everything into data/raw/telecom_eval/ as <file stem>__<contributor>.<ext>, and rewrites
sources.csv / subsets.csv there. Nothing can be merged once TelecomEval is frozen.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

from PIL import Image

from telecomsafe.env import load_env
from telecomsafe.paths import IMAGE_SUFFIXES, PROCESSED, RAW, ROOT, class_names

EVAL_DIR = RAW / "telecom_eval"
FROZEN = ROOT / "splits" / "telecom_eval.sha256"
FIELDS = ["file", "subset", "method", "source_url", "title", "creator", "licence", "licence_version", "licence_url",
          "notes"]
SUBSETS = {"telecom", "near"}
METHODS = {"collected", "own_photo", "generated"}
MIN_SIDE = 640        # below the detector's input size the image is useless for evaluation
GOOD_SIDE = 1000      # recommended; smaller images only warn
LEAK_DIST = 8         # pHash distance that counts as the same photo (as in the training-set de-duplication)


# ---------------------------------------------------------------- rules (pure, tested)
def licence_code(text: str) -> str | None:
    """Normalise a licence string to CC0 / PDM / US-GOV / CC-BY / CC-BY-SA / OWN / GENERATED; None if not allowed."""
    t = (text or "").strip().lower().replace("_", "-")
    if not t or re.search(r"\bnc\b|non-?commercial|\bnd\b|no-?deriv|all rights reserved", t):
        return None
    if t in {"cc0", "cc0 1.0"} or t.startswith("cc0"):
        return "CC0"
    if t in {"pdm", "pd"} or "public domain mark" in t or "no known copyright" in t:
        return "PDM"
    if "us-gov" in t or "government work" in t or "public domain" in t:
        return "US-GOV" if ("gov" in t or "federal" in t) else "PDM"
    if re.match(r"^(cc[ -])?by-sa\b", t):
        return "CC-BY-SA"
    if re.match(r"^(cc[ -])?by\b", t):
        return "CC-BY"
    if t in {"own", "own photo", "own-photo"}:
        return "OWN"
    if t.startswith("generated"):
        return "GENERATED"
    return None


def check_label_file(text: str, n_classes: int) -> tuple[list[str], Counter]:
    errors, counts = [], Counter()
    for k, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"line {k}: expected 5 numbers, got {len(parts)}")
            continue
        try:
            cid, cx, cy, w, h = int(parts[0]), *map(float, parts[1:])
        except ValueError:
            errors.append(f"line {k}: not numbers")
            continue
        if not 0 <= cid < n_classes:
            errors.append(f"line {k}: class id {cid} outside 0–{n_classes - 1}")
        elif not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
            errors.append(f"line {k}: box not normalised to 0–1")
        else:
            counts[cid] += 1
    return errors, counts


def check(folder: Path) -> tuple[list[str], list[str], Counter, list[dict]]:
    """(errors, warnings, instances per class, source rows) for a contribution folder."""
    names = class_names()
    errors, warnings, counts = [], [], Counter()
    images = sorted(p for p in (folder / "images").iterdir() if p.suffix.lower() in IMAGE_SUFFIXES) \
        if (folder / "images").is_dir() else []
    if not images:
        return [f"{folder / 'images'}: no images"], [], counts, []
    sources = folder / "sources.csv"
    if not sources.exists():
        return [f"{sources}: missing"], [], counts, []
    with open(sources, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    missing_cols = [c for c in FIELDS if rows and c not in rows[0]]
    if missing_cols:
        errors.append(f"sources.csv: missing columns {missing_cols}")
    by_file = {r.get("file", ""): r for r in rows}
    for name in sorted(set(by_file) - {p.name for p in images}):
        errors.append(f"sources.csv lists {name}, which is not in images/")
    for img in images:
        where = img.name
        r = by_file.get(img.name)
        if r is None:
            errors.append(f"{where}: no row in sources.csv")
            continue
        if r.get("subset") not in SUBSETS:
            errors.append(f"{where}: subset must be telecom or near, not {r.get('subset')!r}")
        if r.get("method") not in METHODS:
            errors.append(f"{where}: method must be one of {sorted(METHODS)}, not {r.get('method')!r}")
        code = licence_code(r.get("licence", ""))
        if code is None:
            errors.append(f"{where}: licence {r.get('licence')!r} is not allowed")
        elif code in {"CC-BY", "CC-BY-SA"} and not (r.get("creator") and r.get("source_url")):
            errors.append(f"{where}: {code} needs the creator and the source_url")
        if (r.get("method") == "generated") != (code == "GENERATED"):
            errors.append(f"{where}: generated images use licence GENERATED (and only they do)")
        try:
            with Image.open(img) as im:
                side = min(im.size)
        except OSError:
            errors.append(f"{where}: unreadable image")
            continue
        if side < MIN_SIDE:
            errors.append(f"{where}: too small ({side} px short side; at least {MIN_SIDE})")
        elif side < GOOD_SIDE:
            warnings.append(f"{where}: short side {side} px (≥ {GOOD_SIDE} recommended)")
        label = folder / "labels" / f"{img.stem}.txt"
        if not label.exists():
            errors.append(f"{where}: no labels/{label.name}")
            continue
        errs, c = check_label_file(label.read_text(encoding="utf-8"), len(names))
        errors += [f"{where} labels {e}" for e in errs]
        people = c[names.index("person")]
        heads = c[names.index("helmet")] + c[names.index("no_helmet")]
        torsos = c[names.index("vest")] + c[names.index("no_vest")]
        if not people:  # allowed: workers less than half visible are not boxed as person
            warnings.append(f"{where}: no person box — fine only if every worker is less than half visible")
        if people and heads < people:
            warnings.append(f"{where}: {people} people but {heads} helmet / no_helmet — every visible head needs one")
        if people and torsos < people:
            warnings.append(f"{where}: {people} people but {torsos} vest / no_vest — every visible torso needs one")
        counts.update(c)
    for k, n in enumerate(names):
        if not counts[k]:
            warnings.append(f"no {n} box in the whole contribution (every class should appear)")
    return errors, warnings, counts, rows


def report(folder: Path) -> bool:
    errors, warnings, counts, rows = check(folder)
    names = class_names()
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"{len(rows)} images: {dict(Counter(r.get('subset') for r in rows))}, "
          f"methods {dict(Counter(r.get('method') for r in rows))}")
    print("instances:", {names[k]: counts[k] for k in range(len(names))})
    print("✓ All checks passed" if not errors else f"✗ {len(errors)} errors")
    return not errors


# ---------------------------------------------------------------- Label Studio (optional)
def annotate(folder: Path) -> None:
    from telecomsafe.data import labelstudio as ls
    from telecomsafe.data import pseudo_label

    pre = folder / "prelabels"
    images = [p for p in (folder / "images").iterdir() if p.suffix.lower() in IMAGE_SUFFIXES]
    if not all((pre / f"{p.stem}.txt").exists() for p in images):  # pre-label only once
        pseudo_label.main(["--weights", str(ROOT / "runs" / "phase1" / "e2" / "weights" / "best.pt"),
                           "--images", str(folder / "images"), "--yolo-out", str(pre)])
    names = class_names()
    c = ls.Client()
    project = c.call("POST", "/api/projects", json={
        "title": f"TelecomEval – {folder.name}", "label_config": ls.label_config(),
        "description": "Label by docs/TelecomEval-Contribution-EN.md; every image needs its boxes checked.",
        "show_skip_button": False})
    c.call("POST", "/api/storages/localfiles", json={
        "project": project["id"], "title": folder.name, "path": str(folder / "images"),
        "regex_filter": r".*\.(jpe?g|png|webp)$", "use_blob_urls": True})
    tasks = []
    for img in sorted(p for p in (folder / "images").iterdir() if p.suffix.lower() in IMAGE_SUFFIXES):
        with Image.open(img) as im:
            w, h = im.size
        dets = []
        txt = pre / f"{img.stem}.txt"
        for line in (txt.read_text(encoding="utf-8").splitlines() if txt.exists() else []):
            cid, cx, cy, bw, bh = line.split()[:5]
            cx, cy, bw, bh = float(cx) * w, float(cy) * h, float(bw) * w, float(bh) * h
            dets.append((names[int(cid)], cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, 1.0))
        task = {"data": {"image": f"/data/local-files/?d={quote(img.relative_to(RAW).as_posix())}", "file": img.name}}
        if dets:
            task["predictions"] = [ls.to_prediction(dets, w, h)]
        tasks.append(task)
    c.call("POST", f"/api/projects/{project['id']}/import", json=tasks)
    (folder / "labelstudio.json").write_text(json.dumps({"project_id": project["id"]}), encoding="utf-8")
    print(f"{len(tasks)} images → {c.url}/projects/{project['id']}  (then: contrib export {folder})")


def export(folder: Path) -> None:
    from telecomsafe.data import labelstudio as ls

    pid = json.loads((folder / "labelstudio.json").read_text(encoding="utf-8"))["project_id"]
    tasks = ls.Client().call("GET", f"/api/projects/{pid}/export", params={"exportType": "JSON", "download_all_tasks": "true"})
    names = class_names()
    (folder / "labels").mkdir(exist_ok=True)
    done = 0
    for t in tasks:
        ann = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if not ann:
            continue
        latest = max(ann, key=lambda a: a.get("updated_at") or a.get("created_at") or "")
        lines = [ln for r in latest["result"] if r.get("type") == "rectanglelabels" and (ln := ls.yolo_line(r["value"], names))]
        stem = Path(t["data"].get("file") or ls.task_image(t)).stem
        (folder / "labels" / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        done += 1
    print(f"{done}/{len(tasks)} images exported to {folder / 'labels'}")
    report(folder)


# ---------------------------------------------------------------- intake
def phashes(paths) -> dict[str, int]:
    import imagehash

    out = {}
    for p in paths:
        try:
            with Image.open(p) as im:
                out[str(p)] = int(str(imagehash.phash(im.convert("RGB"))), 16)
        except OSError:
            pass
    return out


def near(h: int, others, dist: int = LEAK_DIST) -> bool:
    return any(bin(h ^ o).count("1") <= dist for o in others)


def eval_name(file: str, contributor: str) -> str:
    """The file's name in TelecomEval: the contributor is a suffix, so every image can be traced back."""
    p = Path(file)
    return f"{p.stem}__{contributor}{p.suffix.lower()}"


def owned_by(name: str, contributor: str) -> bool:
    return Path(name).stem.endswith(f"__{contributor}")


def intake(folder: Path, contributor: str) -> None:
    if FROZEN.exists():
        sys.exit(f"TelecomEval is frozen ({FROZEN}); contributions can no longer be merged")
    if not report(folder):
        sys.exit("fix the errors above first")
    who = re.sub(r"[^A-Za-z0-9]+", "_", contributor).strip("_")
    with open(folder / "sources.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    train = phashes(p for split in ("train", "val") for p in (PROCESSED / "yolo" / "images" / split).iterdir())
    others = [p for p in (EVAL_DIR / "images").iterdir() if not owned_by(p.name, who)] \
        if (EVAL_DIR / "images").exists() else []
    merged = phashes(others)
    mine = phashes(folder / "images" / r["file"] for r in rows)
    bad = []
    for r in rows:
        h = mine.get(str(folder / "images" / r["file"]))
        if h is None:
            continue
        if near(h, train.values()):
            bad.append(f"{r['file']}: same photo as a training image — it would leak; replace it")
        elif near(h, merged.values()):
            bad.append(f"{r['file']}: already in TelecomEval (another contribution)")
    if bad:
        print("\n".join(f"ERROR   {b}" for b in bad))
        sys.exit(f"{len(bad)} images refused; nothing was merged")
    for sub in ("images", "labels"):
        (EVAL_DIR / sub).mkdir(parents=True, exist_ok=True)
        for p in (EVAL_DIR / sub).iterdir():  # an earlier intake by the same contributor is replaced
            if owned_by(p.name, who):
                p.unlink()
    out_rows = []
    for r in rows:
        name = eval_name(r["file"], who)
        shutil.copy2(folder / "images" / r["file"], EVAL_DIR / "images" / name)
        shutil.copy2(folder / "labels" / f"{Path(r['file']).stem}.txt", EVAL_DIR / "labels" / f"{Path(name).stem}.txt")
        out_rows.append({**{k: r.get(k, "") for k in FIELDS}, "file": name, "contributor": who,
                         "original_file": r.get("original_file") or r["file"]})
    write_sources(out_rows, who)
    print(f"merged {len(out_rows)} images from {who} → {EVAL_DIR}")


def write_sources(rows: list[dict], contributor: str) -> None:
    """sources.csv (all columns) and subsets.csv (file, subset, method, contributor) for
    data/raw/telecom_eval/; an earlier intake by the same contributor is replaced."""
    path = EVAL_DIR / "sources.csv"
    old = []
    if path.exists():
        with open(path, encoding="utf-8-sig") as f:
            old = [r for r in csv.DictReader(f) if not owned_by(r["file"], contributor)]
    allrows = sorted(old + rows, key=lambda r: (r.get("contributor", ""), r["file"]))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS + ["contributor", "original_file"], extrasaction="ignore")
        w.writeheader()
        w.writerows(allrows)
    (EVAL_DIR / "subsets.csv").write_text(
        "file,subset,method,contributor\n"
        + "".join(f"{r['file']},{r['subset']},{r['method']},{r.get('contributor', '')}\n" for r in allrows),
        encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["check", "annotate", "export", "intake"])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--contributor")
    args = ap.parse_args(argv)
    load_env()  # Label Studio credentials
    args.folder = args.folder.resolve()  # Label Studio needs absolute paths under data/raw/
    if args.command == "check":
        sys.exit(0 if report(args.folder) else 1)
    if args.command == "annotate":
        annotate(args.folder)
    elif args.command == "export":
        export(args.folder)
    else:
        if not args.contributor:
            ap.error("intake needs --contributor")
        intake(args.folder, args.contributor)


if __name__ == "__main__":
    main()
