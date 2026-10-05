"""Task packages for teammates: annotate TelecomEval, or collect more candidate images.

    python -m telecomsafe.data.package annotate                         # → dist/packages/TelecomEval_annotate_<date>.zip
    python -m telecomsafe.data.package collect --domain telecom --target 80
    python -m telecomsafe.data.package collect --domain near --target 30
    python -m telecomsafe.data.package intake-annotations <annotations.json>
    python -m telecomsafe.data.package intake-collection <zip or folder> --domain telecom --collector <name>

annotate   packs the candidates kept in review (subset telecom / near) that are not yet in
           data/raw/telecom_eval/, with E2 pre-labels, the guidelines and one-click Label Studio
           scripts for Windows and macOS. The teammate hands in deliverable/annotations.json.
collect    packs instructions, licence rules, accepted / rejected examples, a list of images the
           project already has (seen.txt) and a checker that zips a valid submission.
intake-*   check what comes back with the same rules and merge it: annotations become YOLO labels
           in data/raw/telecom_eval/ (+ subsets.csv and a spot-check sheet); collected images join
           data/raw/t3_candidates/ for the usual screen → review.

Packages contain only openly licensed images with their attribution: never APD, .env or weights.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
import re
import shutil
import sys
import zipfile
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import quote

from PIL import Image, ImageDraw, ImageFont

from telecomsafe.data.collect_open import NEAR_QUERIES, OUT, TELECOM_QUERIES, read_manifest, write_manifest
from telecomsafe.data.labelstudio import EVAL_DIR, convert, label_config, read_prelabels, to_prediction, write_subsets
from telecomsafe.paths import INTERIM, RAW, ROOT, class_names, load_sources, load_taxonomy, resolve

FILES = Path(__file__).parent / "package_files"
DIST = ROOT / "dist" / "packages"
REJECTED = OUT.parent / "rejected"
CRLF = {".bat"}
EXECUTABLE = {".command", ".sh"}

DOMAINS = {
    "telecom": {
        "title_zh": "电信施工作业", "title_en": "telecom construction work",
        "scenes": [
            ("tower", "登塔、塔上作业（角钢塔、单管塔）", "climbing or working on a lattice tower or monopole"),
            ("rooftop", "屋顶天线、设备安装", "installing antennas or equipment on a rooftop"),
            ("trench", "沿路开挖、敷设光缆或管道", "trenching, laying fibre or ducts along a road"),
            ("manhole", "人井、地下线缆井作业", "working in or at a manhole / underground cable vault"),
            ("cabinet", "街边通信机柜维护", "working on a roadside telecom cabinet"),
            ("aerial_cable", "架设或维修架空通信线缆", "stringing or repairing overhead telecom cable"),
            ("other", "其他电信施工", "other telecom construction"),
        ],
        "rule_zh": "架空线路分不清是通信线还是电力线时，交给 near 子集（另一个收集包）。",
        "rule_en": "If you cannot tell telecom cable from power line, it belongs to the near package instead.",
        "categories": ["Telecommunications Tower Technicians at work", "Working at height", "Climbing towers",
                       "Mobile phone base stations", "Fiber to the x"],
    },
    "near": {
        "title_zh": "电力线路作业（相近领域）", "title_en": "power-line work (near domain)",
        "scenes": [
            ("pole", "爬电线杆作业", "climbing and working on a utility pole"),
            ("bucket_truck", "斗臂车、高空作业平台上作业", "working from a bucket truck or aerial work platform"),
            ("overhead_line", "输电塔、高压线路作业", "working on transmission towers or high-voltage lines"),
            ("other", "其他电力线路作业", "other power-line work"),
        ],
        "rule_zh": "明显是通信线缆或天线的，交给 telecom 收集包。",
        "rule_en": "Clearly telecom cable or antennas belong to the telecom package instead.",
        "categories": ["Lineworkers", "Lineworkers in the United States", "Maintenance of overhead power lines",
                       "Aerial work platforms"],
    },
}
EXTRA_KEYWORDS = {
    "telecom": ["tower climber harness", "cell tower crew", "telecom technician ladder", "fiber optic crew street",
                "telephone lineman", "signal soldiers antenna", "通信 施工 安全帽", "光缆 施工", "铁塔 安装"],
    "near": ["lineman", "power line repair", "utility pole worker", "electric line crew", "电力 线路 抢修", "电工 登杆"],
}


# ---------------------------------------------------------------- helpers
def check_module():
    """The collection checker shipped in the package, imported so intake applies exactly the same rules."""
    spec = importlib.util.spec_from_file_location("telecomeval_check", FILES / "collect" / "tools" / "check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copy_template(src: Path, dst: Path, values: dict[str, str] | None = None) -> None:
    """Copy a file, filling {placeholders} in text files and fixing line endings per platform."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.suffix.lower() not in {".bat", ".command", ".sh", ".py", ".md", ".csv", ".txt"}:
        shutil.copy2(src, dst)
        return
    text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    for k, v in (values or {}).items():
        text = text.replace("{" + k + "}", str(v))
    if src.suffix.lower() in CRLF:
        text = text.replace("\n", "\r\n")
    dst.write_bytes(text.encode("utf-8"))


def copy_tree(src: Path, dst: Path, values: dict[str, str] | None = None) -> None:
    for p in src.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            copy_template(p, dst / p.relative_to(src), values)


def make_zip(folder: Path) -> Path:
    out = folder.with_suffix(".zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_dir():
                continue
            info = zipfile.ZipInfo(f"{folder.name}/{p.relative_to(folder).as_posix()}",
                                   date_time=datetime.fromtimestamp(p.stat().st_mtime).timetuple()[:6])
            mode = 0o755 if p.suffix in EXECUTABLE else 0o644
            info.create_system = 3  # Unix, so macOS applies the permissions below
            info.external_attr = (0o100000 | mode) << 16  # regular file + permissions (.command must be executable)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, p.read_bytes())
    return out


def font(size: int):
    for name in ("arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fresh_dir(name: str) -> Path:
    """An empty build folder. Files are removed one by one, so a folder held open elsewhere
    (an editor or Explorer window) does not stop the build."""
    folder = DIST / name
    if folder.exists():
        shutil.rmtree(folder, ignore_errors=True)
        for p in sorted(folder.rglob("*"), reverse=True) if folder.exists() else []:
            if p.is_file():
                p.unlink()
            else:
                try:
                    p.rmdir()
                except OSError:
                    pass
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def attribution_rows(rows: list[dict]) -> list[dict]:
    keys = ["file", "subset", "title", "creator", "licence", "licence_version", "licence_url", "landing_url", "attribution"]
    return [{k: r.get(k, "") for k in keys} for r in rows]


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["file"])
        w.writeheader()
        w.writerows(rows)


# ---------------------------------------------------------------- annotation package
def phase1_classes() -> list[dict]:
    """Phase 1 taxonomy entries with bilingual criteria (used as label hints)."""
    out = []
    for c in load_taxonomy():
        if c.get("phase1"):
            en = c.get("en") or {}
            out.append({**c, "criterion": f"{c.get('criterion', '')} / {en.get('criterion', '')}"})
    return out


def guideline_examples(folder: Path) -> dict[str, str]:
    """examples/<class>.jpg from the hand-picked ground truth in package_files/annotate_examples.json
    (Construction Site Safety v30 and body_harness, CC BY 4.0): the example box in orange, other classes grey."""
    from telecomsafe.data.build import map_classes
    from telecomsafe.data.readers import read_source

    picks = json.loads((FILES / "annotate_examples.json").read_text(encoding="utf-8"))
    sources = {s["name"]: s for s in load_sources()}
    loaded: dict[str, dict[str, object]] = {}
    made = {}
    for cls, items in picks.items():
        tiles = []
        for item in items:
            cfg = sources[item["source"]]
            root = resolve(cfg.get("path", f"data/raw/{cfg['name']}"))
            if item["source"] not in loaded:
                if not root.exists():
                    break
                found = read_source(cfg["format"], root)
                map_classes(found, cfg["class_map"], class_names(), cfg["name"])
                loaded[item["source"]] = {s.image.relative_to(root).as_posix(): s for s in found}
            s = loaded[item["source"]][item["image"]]
            b = s.boxes[item["box"]]
            with Image.open(s.image) as im:
                im = im.convert("RGB")
            d = ImageDraw.Draw(im)
            lw = max(3, im.width // 200)
            for o in s.boxes:
                if o is not b:
                    d.rectangle((o.x1, o.y1, o.x2, o.y2), outline=(170, 170, 170), width=max(2, lw // 2))
            d.rectangle((b.x1, b.y1, b.x2, b.y2), outline=(235, 104, 52), width=lw)
            pad = max(b.x2 - b.x1, b.y2 - b.y1) * 1.2
            tile = im.crop((max(0, b.x1 - pad), max(0, b.y1 - pad), min(im.width, b.x2 + pad), min(im.height, b.y2 + pad)))
            tiles.append(tile.resize((max(1, round(tile.width * 320 / tile.height)), 320)))
        if not tiles:
            continue
        sheet = Image.new("RGB", (sum(t.width for t in tiles) + 12 * (len(tiles) - 1), 360), "white")
        x = 0
        for t in tiles:
            sheet.paste(t, (x, 40))
            x += t.width + 12
        ImageDraw.Draw(sheet).text((4, 6), f"{cls}: orange = {cls}, grey = other classes", fill=(20, 20, 20), font=font(22))
        path = folder / "examples" / f"{cls}.jpg"
        path.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(path, quality=88)
        made[cls] = path.name
    return made


def annotate(name: str | None, include_annotated: bool) -> Path:
    done = set()
    if (EVAL_DIR / "images").exists() and not include_annotated:
        done = {p.name for p in (EVAL_DIR / "images").iterdir()}
    rows = [r for r in read_manifest() if r["status"] == "candidate" and r.get("subset") in {"telecom", "near"}
            and (OUT / r["file"]).exists() and r["file"] not in done]
    if not rows:
        sys.exit("nothing to annotate — review candidates first (python -m telecomsafe.data.screen)")
    folder = fresh_dir(name or f"TelecomEval_annotate_{date.today():%Y%m%d}")
    classes = phase1_classes()
    names = [c["name"] for c in classes]
    tasks, n_boxes = [], 0
    (folder / "data" / "images").mkdir(parents=True, exist_ok=True)
    for r in rows:
        src = OUT / r["file"]
        shutil.copy2(src, folder / "data" / "images" / r["file"])
        with Image.open(src) as im:
            w, h = im.size
        dets = [d for d in read_prelabels(src, w, h) if d[0] in names]
        n_boxes += len(dets)
        task = {"data": {"image": f"/data/local-files/?d=data/images/{quote(r['file'])}", "file": r["file"],
                         "subset": r["subset"]}}
        if dets:
            task["predictions"] = [to_prediction(dets, w, h)]
        tasks.append(task)
    data = folder / "data"
    (data / "tasks.json").write_text(json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")
    (data / "label_config.xml").write_text(label_config(classes, hotkeys=True), encoding="utf-8")
    subsets = Counter(r["subset"] for r in rows)
    meta = {"title": "TelecomEval", "classes": names, "images": len(rows), "subsets": dict(subsets),
            "description": "TelecomEval annotation — follow GUIDELINES.md; Skip unusable images.",
            "built": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (data / "package.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    write_csv(folder / "ATTRIBUTION.csv", attribution_rows(rows))

    examples = guideline_examples(folder)
    rows_md = []
    for i, c in enumerate(classes, 1):
        en = c.get("en") or {}
        rows_md.append(f"| {i} | `{c['name']}` | {c['description']}<br>{en.get('description', '')} "
                       f"| {c.get('criterion', '').split(' / ')[0]}<br>{en.get('criterion', '')} |")
    ex_md = "\n\n".join(f"**{c}**\n\n![{c}](examples/{f})" for c, f in examples.items())
    values = {"n_images": len(rows), "n_telecom": subsets["telecom"], "n_near": subsets["near"],
              "hours": max(1, round(len(rows) * 3 / 60)), "date": f"{date.today():%Y-%m-%d}",
              "class_rows": "\n".join(rows_md), "examples": ex_md}
    copy_tree(FILES / "annotate", folder, values)
    out = make_zip(folder)
    print(f"{len(rows)} images ({dict(subsets)}), {n_boxes} pre-label boxes, {len(examples)} example sheets")
    print(f"→ {out}  ({out.stat().st_size / 1e6:.0f} MB)")
    return out


# ---------------------------------------------------------------- collection package
def seen_lines() -> list[str]:
    """Source URL and dHash of every image the project has seen (kept, rejected or duplicate)."""
    dhash = check_module().dhash
    lines = ["# source_url<TAB>dhash — images already in the TelecomSafe project; do not submit these again"]
    for r in read_manifest():
        path = next((p for p in (OUT / r["file"], REJECTED / r["file"]) if p.exists()), None)
        try:
            h = f"{dhash(path):016x}" if path else ""
        except OSError:
            h = ""
        if r.get("landing_url") or h:
            lines.append(f"{r.get('landing_url', '')}\t{h}")
    return lines


def thumbnail(src: Path, dst: Path, width: int = 480) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((width, width))
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, quality=85)


def pick_examples(domain: str) -> tuple[list[dict], list[tuple[str, str, list[dict]]]]:
    rows = read_manifest()
    kept = [r for r in rows if r["status"] == "candidate" and r.get("subset") == domain and (OUT / r["file"]).exists()]
    accept, seen_scenes = [], set()
    for r in sorted(kept, key=lambda r: -float(r.get("clip_score") or 0)):  # one per scene first, then the best
        if r.get("scene") not in seen_scenes and int(r.get("persons") or 0) > 0:
            accept.append(r)
            seen_scenes.add(r.get("scene"))
    accept += [r for r in sorted(kept, key=lambda r: -float(r.get("clip_score") or 0)) if r not in accept]
    rejected = [r for r in rows if r["status"] == "rejected" and (REJECTED / r["file"]).exists() and r.get("clip_score")]
    rng = random.Random(0)
    groups = [
        ("没有人在作业 / Nobody working", [r for r in rejected if int(r.get("persons") or 0) == 0 and r.get("scene") in {"no_people", "tower", "cabinet"}]),
        ("摆拍、活动或插画 / Posed, events or illustrations", [r for r in rejected if r.get("scene") in {"portrait", "event", "illustration"}]),
        ("场景不对（室内、清洁、其他工种）/ Wrong setting (indoors, cleaning, other trades)",
         [r for r in rejected if int(r.get("persons") or 0) > 0 and float(r.get("clip_score") or 0) > 0.8
          and r.get("scene") not in {"pole", "tower", "bucket_truck"}]),  # those look like valid scenes; confusing as examples
    ]
    return accept[:8], [(title, rng.sample(g, min(4, len(g)))) for title, g in groups]


def image_table(rows: list[dict], folder: Path, prefix: str, cols: int = 4) -> str:
    cells = []
    for i, r in enumerate(rows, 1):
        src = OUT / r["file"] if (OUT / r["file"]).exists() else REJECTED / r["file"]
        name = f"{prefix}_{i}.jpg"
        thumbnail(src, folder / "examples" / name)
        cells.append(f"![{name}](examples/{name})<br>{r.get('scene', '')}")
    lines = ["| " + " | ".join([" "] * cols) + " |", "|" + "---|" * cols]
    for i in range(0, len(cells), cols):
        row = cells[i : i + cols] + [" "] * (cols - len(cells[i : i + cols]))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def collect(domain: str, target: int, name: str | None) -> Path:
    spec = DOMAINS[domain]
    folder = fresh_dir(name or f"TelecomEval_collect_{domain}_{date.today():%Y%m%d}")
    accept, reject_groups = pick_examples(domain)
    used = list(accept)
    accept_md = image_table(accept, folder, "keep")
    reject_md = []
    for i, (title, rows) in enumerate(reject_groups, 1):
        reject_md.append(f"**{title}**\n\n{image_table(rows, folder, f'reject{i}')}")
        used += rows
    write_csv(folder / "examples" / "ATTRIBUTION.csv", attribution_rows(used))
    seen = seen_lines()
    (folder / "data").mkdir(parents=True, exist_ok=True)
    (folder / "data" / "seen.txt").write_text("\n".join(seen) + "\n", encoding="utf-8")
    meta = {"domain": domain, "target": target, "scenes": [s[0] for s in spec["scenes"]],
            "built": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (folder / "data" / "package.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    kept = Counter(r.get("subset") for r in read_manifest() if r["status"] == "candidate")
    queries = (TELECOM_QUERIES if domain == "telecom" else NEAR_QUERIES) + EXTRA_KEYWORDS[domain]
    values = {
        "domain": domain, "target": target, "hours": max(1, round(target * 4 / 60)), "date": f"{date.today():%Y-%m-%d}",
        "title_zh": spec["title_zh"], "title_en": spec["title_en"], "n_seen": len(seen) - 1,
        "have_zh": f"项目已有电信施工 {kept['telecom']} 张、电力线路作业 {kept['near']} 张",
        "have_en": f"the project has {kept['telecom']} telecom and {kept['near']} power-line images",
        "scene_table_zh": "| 代码 | 场景 |\n|---|---|\n" + "\n".join(f"| `{c}` | {zh} |" for c, zh, _ in spec["scenes"]),
        "scene_table_en": "| Code | Scene |\n|---|---|\n" + "\n".join(f"| `{c}` | {en} |" for c, _, en in spec["scenes"]),
        "scene_codes": ", ".join(f"`{c}`" for c, _, _ in spec["scenes"]),
        "domain_rule_zh": spec["rule_zh"], "domain_rule_en": spec["rule_en"],
        "accept_examples": accept_md, "reject_examples": "\n\n".join(reject_md),
        "keywords": "\n".join(f"- {q}" for q in queries),
        "wikimedia_categories": ", ".join(f"[{c}](https://commons.wikimedia.org/wiki/Category:{quote(c.replace(' ', '_'))})"
                                          for c in spec["categories"]),
    }
    copy_tree(FILES / "collect", folder, values)
    (folder / "submission" / "images").mkdir(parents=True, exist_ok=True)
    out = make_zip(folder)
    print(f"{domain}: target {target}, {len(seen) - 1} seen images, {len(used)} examples → {out}  ({out.stat().st_size / 1e6:.1f} MB)")
    return out


# ---------------------------------------------------------------- intake
def task_file(task: dict) -> Path:
    """The project's copy of a packaged task's image (looked up by file name)."""
    name = task["data"].get("file") or Path(task["data"]["image"].split("d=")[-1]).name
    for folder in (OUT, REJECTED):
        if (folder / name).exists():
            return folder / name
    raise FileNotFoundError(f"{name} is not in {OUT} — was it built from this project?")


def spot_check(out: Path, n: int = 15) -> Path:
    names = class_names()
    files = sorted((EVAL_DIR / "images").iterdir())
    pick = random.Random(0).sample(files, min(n, len(files)))
    tiles = []
    for p in pick:
        with Image.open(p) as im:
            im = im.convert("RGB")
        d = ImageDraw.Draw(im)
        lw = max(2, im.width // 300)
        label = EVAL_DIR / "labels" / f"{p.stem}.txt"
        for line in (label.read_text(encoding="utf-8").splitlines() if label.exists() else []):
            c, cx, cy, w, h = line.split()
            cx, cy, w, h = float(cx) * im.width, float(cy) * im.height, float(w) * im.width, float(h) * im.height
            d.rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), outline=(235, 104, 52), width=lw)
            d.text((cx - w / 2 + lw, cy - h / 2 + lw), names[int(c)], fill=(255, 255, 255), font=font(max(14, im.width // 45)))
        im.thumbnail((520, 400))
        tiles.append(im)
    cols = 5
    sheet = Image.new("RGB", (cols * 524, ((len(tiles) + cols - 1) // cols) * 404), "white")
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 524, (i // cols) * 404))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out, quality=88)
    return out


def intake_annotations(path: Path, allow_incomplete: bool) -> None:
    tasks = json.loads(path.read_text(encoding="utf-8"))
    status = Counter("annotated" if any(not a.get("was_cancelled") for a in t.get("annotations", []))
                     else "skipped" if t.get("annotations") else "not done" for t in tasks)
    print(f"{path.name}: {len(tasks)} tasks — {dict(status)}")
    if status["not done"] and not allow_incomplete:
        sys.exit(f"{status['not done']} images are not done — ask for a complete export, or pass --allow-incomplete")
    missing = [t["data"].get("file") for t in tasks if not _exists(t)]
    if missing:
        sys.exit(f"{len(missing)} images are not in this project: {missing[:5]}")
    counts = convert(tasks, class_names(), EVAL_DIR, source=task_file)
    subsets = write_subsets(EVAL_DIR)
    print(f"TelecomEval → {EVAL_DIR}: {counts}  {subsets}")
    if counts["dropped"]:
        print(f"  ! {counts['dropped']} boxes had labels outside the phase 1 classes and were dropped")
    sheet = spot_check(INTERIM / "telecom_eval_spot_check.jpg")
    print(f"  spot-check sheet: {sheet}\n  next: look at it, then  python -m telecomsafe.data.freeze_eval --create")


def _exists(task: dict) -> bool:
    try:
        task_file(task)
        return True
    except FileNotFoundError:
        return False


LICENCE_CODES = {"CC0": ("cc0", ""), "PDM": ("pdm", ""), "US-GOV": ("Public domain (US federal government work)", ""),
                 "CC-BY": ("by", None), "CC-BY-SA": ("by-sa", None)}


def intake_collection(path: Path, domain: str, collector: str, skip_bad: bool) -> None:
    if path.suffix.lower() == ".zip":
        target = INTERIM / "intake" / path.stem
        if target.exists():
            shutil.rmtree(target)
        with zipfile.ZipFile(path) as z:
            z.extractall(target)
        path = next((p.parent for p in target.rglob("manifest.csv")), target)
    chk = check_module()
    seen_urls, seen_hashes = _seen(chk)
    errors, warnings, rows = chk.check_submission(path, seen_urls, seen_hashes, [s[0] for s in DOMAINS[domain]["scenes"]])
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    good = [r for r in rows if not r.get("_bad") and r.get("dhash")]
    if errors and not skip_bad:
        sys.exit(f"{len(errors)} errors — send it back, or pass --skip-bad to import only the {len(good)} passing images")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", collector).strip("_").lower() or "contrib"
    manifest = read_manifest()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    for r in good:
        src = path / "images" / r["file"]
        dst = OUT / f"contrib_{slug}_{Path(r['file']).stem}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        licence, version = LICENCE_CODES[r["licence"].upper()]
        version = r["licence_version"] if version is None else version
        manifest.append({
            "file": dst.name, "provider": f"contrib:{slug}", "source_id": r["file"], "title": r["title"],
            "creator": r["creator"], "licence": licence, "licence_version": version, "licence_url": r["licence_url"],
            "landing_url": r["source_url"], "image_url": "", "query": r["scene"], "domain": domain,
            "attribution": f'"{r["title"] or "Untitled"}" by {r["creator"] or "unknown"}, {r["licence"]} {version}'.strip()
                           + f", {r['source_url']} (collected by {collector})",
            "downloaded_at": now, "status": "candidate",
        })
    write_manifest(manifest)
    print(f"imported {len(good)} images from {collector} into {OUT} as {domain} candidates")
    print("  next: python -m telecomsafe.data.screen  → review → screen --apply → package annotate")


def _seen(chk) -> tuple[set[str], list[int]]:
    urls, hashes = set(), []
    for line in seen_lines()[1:]:
        url, _, h = line.partition("\t")
        if url:
            urls.add(chk.normalise_url(url))
        if h:
            hashes.append(int(h, 16))
    return urls, hashes


# ---------------------------------------------------------------- cli
def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("annotate", help="build the annotation package")
    a.add_argument("--name")
    a.add_argument("--include-annotated", action="store_true", help="also pack images already in data/raw/telecom_eval/")
    c = sub.add_parser("collect", help="build a collection package")
    c.add_argument("--domain", choices=list(DOMAINS), required=True)
    c.add_argument("--target", type=int, default=80)
    c.add_argument("--name")
    ia = sub.add_parser("intake-annotations", help="merge an exported annotations.json")
    ia.add_argument("file", type=Path)
    ia.add_argument("--allow-incomplete", action="store_true")
    ic = sub.add_parser("intake-collection", help="check and import a collection submission (zip or folder)")
    ic.add_argument("path", type=Path)
    ic.add_argument("--domain", choices=list(DOMAINS), required=True)
    ic.add_argument("--collector", required=True)
    ic.add_argument("--skip-bad", action="store_true", help="import the passing images even if others fail")
    args = ap.parse_args(argv)
    if args.cmd == "annotate":
        annotate(args.name, args.include_annotated)
    elif args.cmd == "collect":
        collect(args.domain, args.target, args.name)
    elif args.cmd == "intake-annotations":
        intake_annotations(args.file, args.allow_incomplete)
    else:
        intake_collection(args.path, args.domain, args.collector, args.skip_bad)


if __name__ == "__main__":
    main()
