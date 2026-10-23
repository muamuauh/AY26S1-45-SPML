"""Shortlist the best TelecomEval candidates, then turn the ones you pick into your contribution.

    python -m telecomsafe.data.shortlist                       # top 100 → data/interim/telecomeval_shortlist/
    python -m telecomsafe.data.shortlist --apply <decisions.json> --contributor <name>

Every candidate in data/licence_manifest.csv that shows a person in a work scene is scored:

    score = 0.5 · CLIP work-scene score + 0.25 · person size + 0.25 · class variety

  person size    tallest person box found by the E2 detector / image height, full marks at 30 %
  class variety  distinct phase-1 classes E2 finds (conf ≥ 0.35), full marks at 4; no_helmet, harness,
                 machinery and vehicle (rare in TelecomEval candidates) count double

Picks go best-first, skipping near-duplicates (pHash), a third photo from the same event (same title
without its trailing number) and anything over SCENE_CAP per scene, so the list is varied.
The shortlist folder has the images, shortlist.csv (scores, licence) and review.html: mark telecom (1),
near (2) or reject (X) and export. --apply copies the telecom / near picks into
data/raw/telecomeval_contrib/<name>/ (images + sources.csv, the contribution format of
docs/guides/TelecomEval-Contribution-EN.md), fetching Wikimedia images again at full resolution.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from telecomsafe.data import screen
from telecomsafe.data.collect_open import OUT, read_manifest, session
from telecomsafe.paths import INTERIM, RAW, class_names

SHORTLIST = INTERIM / "telecomeval_shortlist"
CONTRIB = RAW / "telecomeval_contrib"  # under data/raw/ so the local Label Studio can serve the images
WORK_SCENES = {"tower", "rooftop", "trench", "manhole", "cabinet", "splicing", "pole", "bucket_truck"}
RARE = {"no_helmet", "harness", "machinery", "vehicle"}
MIN_SIDE = 720       # files on disk; Wikimedia picks are fetched again at full size by --apply
SCENE_CAP = 25
PER_EVENT = 2
FULL_RES = 2048      # long side requested from Wikimedia for the picks
SOURCE_FIELDS = ["file", "subset", "method", "source_url", "title", "creator", "licence", "licence_version",
                 "licence_url", "notes"]


# ---------------------------------------------------------------- scoring (pure, tested)
def person_size(dets: list, height: int) -> float:
    tallest = max((d[1][3] - d[1][1] for d in dets if d[0] == "person"), default=0.0)
    return min(1.0, tallest / height / 0.3)


def class_variety(dets: list) -> float:
    found = {d[0] for d in dets}
    return min(1.0, sum(2 if c in RARE else 1 for c in found) / 4)


def score(clip: float, size: float, variety: float) -> float:
    return 0.5 * clip + 0.25 * size + 0.25 * variety


def event_key(title: str) -> str:
    """'File:1-91 CAV PLT LFX (6568779).jpg' → '1-91 cav plt lfx': photos of one event share it."""
    t = re.sub(r"^File:", "", title)
    t = re.sub(r"\.(jpe?g|png|webp)$", "", t, flags=re.I)
    t = re.sub(r"[\s_-]*[(\[]?\d+[)\]]?$", "", t)
    return t.strip().lower()


def pick(cands: list[dict], n: int, hashes: dict[str, int], max_dist: int = 10) -> list[dict]:
    """Best first, with no near-duplicates, at most PER_EVENT per event and SCENE_CAP per scene."""
    chosen, events, scenes = [], {}, {}
    for c in sorted(cands, key=lambda c: -c["score"]):
        if len(chosen) == n:
            break
        h = hashes.get(c["file"])
        if h is not None and any(bin(h ^ hashes[o["file"]]).count("1") <= max_dist
                                 for o in chosen if hashes.get(o["file"]) is not None):
            continue
        ev = event_key(c.get("title", ""))
        if (ev and events.get(ev, 0) >= PER_EVENT) or scenes.get(c["scene"], 0) >= SCENE_CAP:
            continue
        chosen.append(c)
        events[ev] = events.get(ev, 0) + 1
        scenes[c["scene"]] = scenes.get(c["scene"], 0) + 1
    return chosen


# ---------------------------------------------------------------- shortlist
def build(n: int) -> Path:
    import imagehash
    from ultralytics import YOLO

    from telecomsafe.data.collect_video import WEIGHTS

    rows = [r for r in read_manifest() if r["status"] == "candidate" and (OUT / r["file"]).exists()
            and int(r.get("persons") or 0) >= 1 and r.get("scene") in WORK_SCENES]
    model = YOLO(str(WEIGHTS))
    names = set(class_names())
    cands, hashes = [], {}
    for i, r in enumerate(rows):
        with Image.open(OUT / r["file"]) as im:
            im = im.convert("RGB")
        if min(im.size) < MIN_SIDE:
            continue
        res = model.predict(im, conf=0.35, verbose=False)[0]
        dets = [(res.names[int(c)], tuple(b), float(s)) for b, c, s in
                zip(res.boxes.xyxy.tolist(), res.boxes.cls.tolist(), res.boxes.conf.tolist()) if res.names[int(c)] in names]
        size, variety = person_size(dets, im.height), class_variety(dets)
        cands.append({**r, "size_score": round(size, 3), "variety": round(variety, 3),
                      "classes": " ".join(sorted({d[0] for d in dets})), "wh": f"{im.width}x{im.height}",
                      "score": round(score(float(r["clip_score"]), size, variety), 4)})
        hashes[r["file"]] = int(str(imagehash.phash(im)), 16)
        if (i + 1) % 100 == 0:
            print(f"  scored {i + 1}/{len(rows)}", flush=True)
    chosen = pick(cands, n, hashes)
    if SHORTLIST.exists():
        shutil.rmtree(SHORTLIST)
    (SHORTLIST / "images").mkdir(parents=True)
    for c in chosen:
        shutil.copy2(OUT / c["file"], SHORTLIST / "images" / c["file"])
    fields = ["rank", "file", "score", "clip_score", "size_score", "variety", "classes", "scene", "domain", "subset",
              "wh", "provider", "title", "creator", "licence", "landing_url"]
    with open(SHORTLIST / "shortlist.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows({**c, "rank": k} for k, c in enumerate(chosen, 1))
    # the review page, in shortlist order, with nothing decided yet
    by_file = {c["file"]: c for c in chosen}
    items = screen.review_items(chosen)
    for it in items:
        c = by_file[it["file"]]
        it.update(state="", auto=False, decided=False, prev=c.get("subset") or "", score=c["score"],
                  scene=f"{c['scene']} · {c['classes'] or 'no PPE found'}")
    items.sort(key=lambda it: -it["score"])
    (SHORTLIST / "review.html").write_text(screen.page_html(
        items, key="telecomeval-shortlist", export="shortlist_decisions.json",
        after="Then run <code>python -m telecomsafe.data.shortlist --apply &lt;file&gt; --contributor &lt;name&gt;</code>."),
        encoding="utf-8")
    print(f"{len(cands)} scored, {len(chosen)} shortlisted → {SHORTLIST}")
    print("  scenes:", {s: sum(c['scene'] == s for c in chosen) for s in sorted({c['scene'] for c in chosen})})
    return SHORTLIST


# ---------------------------------------------------------------- picks → contribution
def full_resolution(s, title: str) -> bytes | None:
    """The Wikimedia file at up to FULL_RES px on its long side (the candidates were fetched at 1280)."""
    from telecomsafe.data.collect_open import get_json

    pages = get_json(s, "https://commons.wikimedia.org/w/api.php", {
        "action": "query", "titles": title, "prop": "imageinfo", "iiprop": "url|size",
        "iiurlwidth": FULL_RES, "format": "json"}).get("query", {}).get("pages", {})
    info = (next(iter(pages.values()), {}).get("imageinfo") or [{}])[0]
    url = info.get("thumburl") or info.get("url")
    if not url:
        return None
    r = s.get(url, timeout=180)
    r.raise_for_status()
    return r.content


def apply(path: Path, contributor: str) -> Path:
    decisions = json.loads(path.read_text(encoding="utf-8"))
    picks = {f: d for f, d in decisions.items() if d in ("telecom", "near")}
    rows = {r["file"]: r for r in read_manifest()}
    folder = CONTRIB / re.sub(r"[^A-Za-z0-9]+", "_", contributor).strip("_").lower()
    (folder / "images").mkdir(parents=True, exist_ok=True)
    s = session()

    def fetch(f: str) -> bytes | None:
        if rows[f]["provider"] != "wikimedia":
            return None
        try:
            return full_resolution(s, rows[f]["title"])
        except Exception as e:  # keep the 1280 px copy rather than lose the pick
            print(f"  ! {f}: full-resolution download failed ({e}); using the copy on disk")
            return None

    with ThreadPoolExecutor(4) as pool:  # Commons is slow per connection from here
        fetched = dict(zip(picks, pool.map(fetch, picks)))
    out = []
    for f, subset in picks.items():
        r = rows[f]
        data = fetched[f]
        dst = folder / "images" / f
        if data:
            dst.write_bytes(data)
        else:
            shutil.copy2(OUT / f, dst)
        out.append({"file": f, "subset": subset, "method": "collected", "source_url": r["landing_url"],
                    "title": r["title"], "creator": r["creator"], "licence": r["licence"],
                    "licence_version": r["licence_version"], "licence_url": r["licence_url"],
                    "notes": f"from the project candidates ({r['provider']})"})
        print(f"  {f}: {subset}", flush=True)
    sources = folder / "sources.csv"
    existing = []
    if sources.exists():
        with open(sources, encoding="utf-8-sig") as fh:
            existing = [x for x in csv.DictReader(fh) if x["file"] not in picks]
    with open(sources, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerows(existing + out)
    print(f"{len(out)} picks ({sum(o['subset'] == 'telecom' for o in out)} telecom) → {folder}")
    return folder


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--apply", type=Path, help="decisions exported from the shortlist page")
    ap.add_argument("--contributor", help="your name (folder under data/raw/telecomeval_contrib/)")
    args = ap.parse_args(argv)
    if args.apply:
        if not args.contributor:
            ap.error("--apply needs --contributor")
        apply(args.apply, args.contributor)
    else:
        build(args.n)


if __name__ == "__main__":
    main()
