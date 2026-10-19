"""Generate a small synthetic part of TelecomEval with an image model, then turn the picks into your contribution.

    python -m telecomsafe.data.generate_eval --dry-run              # print the prompts and the cost estimate
    python -m telecomsafe.data.generate_eval                        # → data/interim/telecomeval_generated/
    python -m telecomsafe.data.generate_eval --apply <decisions.json> --contributor <name>

Needs the image API in .env (never commit it), as a triple for any OpenAI-compatible endpoint or relay:
IMAGE_API_BASE (base URL ending in /v1; default https://api.openai.com/v1), IMAGE_API_MODEL (default
gpt-image-2; --model overrides it) and IMAGE_API_KEY. Each scenario is one whole-scene photo request, written
for evaluation and deliberately unlike phase 2: phase 2 repaints parts of real training photos (inpainting
a person, a helmet, a vest), whereas these are complete telecom scenes from text, with every phase-1 class
and both PPE states covered across the set, and camera, light and region varied per scenario. The expected
classes listed with each scenario only guide annotation — every image is still labelled by hand.

These images are reported as their own subset (method = generated in sources.csv), never mixed silently
with real photos: a detector can do better or worse on generated images than on real sites.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import shutil
import sys
import time
from datetime import date
from pathlib import Path

import requests

from telecomsafe.data import screen
from telecomsafe.data.shortlist import CONTRIB, SOURCE_FIELDS
from telecomsafe.env import load_env
from telecomsafe.paths import INTERIM

OUT_DIR = INTERIM / "telecomeval_generated"
DEFAULT_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-image-2"


def endpoint(base: str | None) -> str:
    """…/v1 → …/v1/images/generations (a full …/images/generations URL is kept as it is)."""
    base = (base or DEFAULT_BASE).strip().rstrip("/")
    return base if base.endswith("/images/generations") else f"{base}/images/generations"


def image_bytes(item: dict, s: requests.Session) -> bytes:
    """One image from the response: base64 (OpenAI) or a URL (what some relays return)."""
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    r = s.get(item["url"], timeout=300)
    r.raise_for_status()
    return r.content
PRICE = {"low": 0.005, "medium": 0.041, "high": 0.165}   # USD per 1536×1024 image, gpt-image-2 (Oct 2026)

STYLE = ("Candid documentary photograph, realistic and unstaged: people are busy with the work and do not look at "
         "the camera, natural imperfections, real equipment wear and dirt, no text, no logos, no watermark.")
CAMERAS = ["shot on a phone from across the street", "telephoto from about 30 metres away",
           "wide-angle from ground level looking up", "eye-level from about 10 metres away",
           "slightly elevated view from a nearby balcony", "handheld from behind a parked vehicle"]
CONDITIONS = ["overcast morning light", "harsh midday sun with hard shadows", "warm late-afternoon light",
              "light rain, wet surfaces", "after rain, puddles on the ground", "hazy humid air"]
REGIONS = ["a Southeast Asian city", "a European suburb", "a rural village in East Africa", "a small town in India",
           "a North American roadside", "a Chinese residential district", "a hillside town in Latin America",
           "the outskirts of a Middle Eastern city"]

# (id, subset, scene, expected classes, what happens)
SCENARIOS = [
    ("tower_climb_mixed", "telecom", "tower", "person helmet no_helmet harness vehicle",
     "two technicians climbing a lattice telecom tower; the upper one wears a white hard hat and a full-body harness "
     "clipped to the tower, the lower one has no helmet; a white van is parked at the base"),
    ("tower_platform_three", "telecom", "tower", "person helmet harness vest",
     "three riggers on a platform high on a telecom tower fitting panel antennas, all in harnesses, two in hi-vis vests"),
    ("tower_base_crew", "telecom", "tower", "person helmet no_helmet vest no_vest vehicle",
     "a crew at the fenced base of a monopole tower unloading antenna parts from a pickup truck; some in hi-vis vests "
     "and hard hats, one in a plain t-shirt and baseball cap"),
    ("tower_crane_lift", "telecom", "tower", "person helmet vest machinery",
     "a mobile crane lifting an antenna mount up a telecom tower while two workers in hard hats and hi-vis vests "
     "guide the tag line"),
    ("monopole_bucket", "telecom", "tower", "person helmet harness machinery",
     "a technician in a bucket truck basket working on equipment halfway up a monopole, wearing a harness and hard hat"),
    ("tower_no_ppe", "telecom", "tower", "person no_helmet no_vest",
     "a man climbing the ladder of a small rooftop telecom mast with no helmet, no harness, ordinary clothes"),
    ("rooftop_antennas", "telecom", "rooftop", "person helmet no_helmet vest no_vest",
     "two technicians installing sector antennas on a flat building roof; one in a hard hat and hi-vis vest, the "
     "other bareheaded in a dark polo shirt"),
    ("rooftop_dish_edge", "telecom", "rooftop", "person no_helmet no_vest harness",
     "a technician aligning a microwave dish near the edge of a roof, wearing a harness tied to an anchor but no "
     "helmet and no vest"),
    ("rooftop_cable_tray", "telecom", "rooftop", "person helmet vest",
     "workers pulling coaxial and fibre cable along a rooftop cable tray between equipment cabinets"),
    ("cabinet_kneel", "telecom", "cabinet", "person no_helmet no_vest vehicle",
     "a technician kneeling at an open green roadside fibre cabinet, wearing a cap and a plain jacket, a small van "
     "with its doors open behind him"),
    ("cabinet_two_vests", "telecom", "cabinet", "person no_helmet vest vehicle",
     "two technicians in hi-vis vests, no helmets, testing fibre connections inside a grey street cabinet on a busy "
     "pavement with cars passing"),
    ("cabinet_new_install", "telecom", "cabinet", "person helmet vest machinery",
     "a small crane truck lowering a new telecom cabinet onto a concrete base while workers in hard hats steady it"),
    ("trench_excavator", "telecom", "trench", "person helmet vest machinery",
     "a mini excavator digging a narrow trench along a road edge while workers lay orange fibre ducts; hard hats and "
     "hi-vis vests"),
    ("trench_hand_dig", "telecom", "trench", "person no_helmet no_vest helmet vest",
     "a crew hand-digging a shallow cable trench beside a sidewalk; some wear hard hats and vests, two do not"),
    ("trench_drum_trailer", "telecom", "trench", "person helmet vest machinery vehicle",
     "a cable drum trailer feeding fibre cable into a roadside duct, a pickup towing it, two workers guiding the cable"),
    ("manhole_tripod", "telecom", "manhole", "person helmet vest vehicle",
     "a worker climbing down into an underground cable manhole beside a rescue tripod and traffic cones, a colleague "
     "watching; a utility van parked nearby"),
    ("manhole_splice_tent", "telecom", "manhole", "person no_helmet no_vest vehicle",
     "a fibre splicing tent over an open manhole on a residential street, a technician without helmet working "
     "inside, a van beside it"),
    ("manhole_pulling", "telecom", "manhole", "person helmet no_helmet vest no_vest machinery",
     "workers pulling cable out of a manhole with a cable-pulling winch truck; mixed PPE"),
    ("aerial_cable_ladder", "telecom", "aerial_cable", "person no_helmet no_vest",
     "a technician on a ladder leaning against a wooden pole fixing a black telecom drop cable, no helmet, no harness"),
    ("aerial_cable_crew", "telecom", "aerial_cable", "person helmet vest machinery vehicle",
     "a crew stringing new aerial fibre cable along a street from a bucket truck, cars parked along the road"),
    ("aerial_cable_tangle", "telecom", "aerial_cable", "person no_helmet vest",
     "a worker in a hi-vis vest but no helmet untangling a dense bundle of overhead telecom cables from a ladder in a "
     "crowded market street"),
    ("fibre_van_splice", "telecom", "cabinet", "person no_helmet no_vest vehicle",
     "a fibre technician splicing cable at a fold-out table at the back of a service van on a quiet street"),
    ("small_cell_pole", "telecom", "tower", "person helmet harness machinery vehicle",
     "a technician in an aerial work platform installing a small-cell antenna on a street light pole, traffic cones "
     "and a parked car nearby"),
    ("rooftop_rain", "telecom", "rooftop", "person helmet vest harness",
     "two riggers in rain jackets with hi-vis stripes working on a rooftop telecom mast in the rain, harnesses on"),
    ("tower_night", "telecom", "tower", "person helmet harness",
     "a tower climber with a head torch working on a lit telecom tower at dusk, harness and hard hat"),
    ("tower_far_small", "telecom", "tower", "person helmet harness vehicle",
     "a tall lattice tower in open countryside with two small figures climbing it and a 4x4 vehicle at the base"),
    ("pole_climb_gaffs", "near", "pole", "person helmet harness",
     "a lineworker climbing a wooden utility pole with climbing spikes and a pole strap, hard hat on"),
    ("bucket_truck_lineman", "near", "bucket_truck", "person helmet vest machinery vehicle",
     "a lineman in the bucket of a utility truck working on power lines above a road, a colleague in a vest on the "
     "ground, cars waiting"),
    ("pole_crew_no_ppe", "near", "pole", "person no_helmet no_vest machinery",
     "an informal crew replacing a concrete electricity pole with a small crane truck; most wear no helmets or vests"),
    ("transmission_tower", "near", "overhead_line", "person helmet harness",
     "line workers in harnesses climbing a steel high-voltage transmission tower"),
    ("substation_edge", "near", "overhead_line", "person helmet no_helmet vest vehicle",
     "workers unloading equipment beside a rural electricity line from a pickup; one bareheaded"),
    ("storm_repair", "near", "pole", "person helmet vest machinery",
     "a storm-damage repair crew at a leaning utility pole with downed lines, bucket truck and digger derrick"),
]


def prompt_for(k: int, scenario: tuple) -> str:
    _, _, _, _, action = scenario
    return (f"{STYLE} {action[0].upper()}{action[1:]}. Setting: {REGIONS[k % len(REGIONS)]}. "
            f"{CONDITIONS[(k * 5) % len(CONDITIONS)].capitalize()}, {CAMERAS[(k * 7) % len(CAMERAS)]}.")


def coverage(scenarios=SCENARIOS) -> dict[str, int]:
    """How many scenarios are meant to contain each phase-1 class."""
    out: dict[str, int] = {}
    for s in scenarios:
        for c in s[3].split():
            out[c] = out.get(c, 0) + 1
    return out


def generate(model: str | None, quality: str, size: str, only: list[str] | None) -> None:
    load_env()
    key = os.environ.get("IMAGE_API_KEY")
    if not key:
        sys.exit("IMAGE_API_KEY is not set — fill IMAGE_API_BASE / IMAGE_API_MODEL / IMAGE_API_KEY in .env "
                 "(never commit .env)")
    url = endpoint(os.environ.get("IMAGE_API_BASE"))
    model = model or os.environ.get("IMAGE_API_MODEL") or DEFAULT_MODEL
    s = requests.Session()
    print(f"model {model}, endpoint {url.split('//')[-1].split('/')[0]}", flush=True)
    (OUT_DIR / "images").mkdir(parents=True, exist_ok=True)
    log = OUT_DIR / "prompts.csv"
    done = set()
    if log.exists():
        with open(log, encoding="utf-8-sig") as f:
            done = {r["id"] for r in csv.DictReader(f)}
    new = not log.exists()
    with open(log, "a", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["id", "file", "subset", "scene", "expected", "model", "quality", "size",
                                          "date", "prompt", "usage"])
        if new:
            w.writeheader()
        for k, sc in enumerate(SCENARIOS):
            sid = sc[0]
            if sid in done or (only and sid not in only):
                continue
            prompt = prompt_for(k, sc)
            t0 = time.time()
            try:
                r = s.post(url, headers={"Authorization": f"Bearer {key}"}, timeout=600,
                           json={"model": model, "prompt": prompt, "size": size, "quality": quality, "n": 1})
                if r.status_code != 200:
                    print(f"  ✗ {sid}: HTTP {r.status_code} {r.text[:200]}", file=sys.stderr)
                    continue
                body = r.json()
                data = image_bytes(body["data"][0], s)
            except (requests.RequestException, KeyError, IndexError, ValueError) as e:
                print(f"  ✗ {sid}: {e!r}"[:300], file=sys.stderr)
                continue
            file = f"gen_{sid}.png"
            (OUT_DIR / "images" / file).write_bytes(data)
            w.writerow({"id": sid, "file": file, "subset": sc[1], "scene": sc[2], "expected": sc[3], "model": model,
                        "quality": quality, "size": size, "date": f"{date.today():%Y-%m-%d}", "prompt": prompt,
                        "usage": json.dumps(body.get("usage", {}))})
            f.flush()
            print(f"  ✓ {sid} ({time.time() - t0:.0f}s)", flush=True)
    write_review()


def write_review() -> None:
    with open(OUT_DIR / "prompts.csv", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    items = [{"file": r["file"], "title": r["prompt"][:120], "provider": r["model"], "licence": "generated",
              "landing": "", "domain": r["subset"], "persons": 0, "scene": f"{r['scene']} · expect {r['expected']}",
              "score": 1.0, "state": "", "auto": False, "decided": False,
              "size": screen.image_size(OUT_DIR / "images" / r["file"])}
             for r in rows if (OUT_DIR / "images" / r["file"]).exists()]
    (OUT_DIR / "review.html").write_text(screen.page_html(
        items, key="telecomeval-generated", export="generated_decisions.json",
        after="Then run <code>python -m telecomsafe.data.generate_eval --apply &lt;file&gt; --contributor &lt;name&gt;</code>."),
        encoding="utf-8")
    print(f"{len(items)} generated images → open {OUT_DIR / 'review.html'}")


def apply(path: Path, contributor: str) -> Path:
    decisions = json.loads(path.read_text(encoding="utf-8"))
    with open(OUT_DIR / "prompts.csv", encoding="utf-8-sig") as f:
        rows = {r["file"]: r for r in csv.DictReader(f)}
    folder = CONTRIB / re.sub(r"[^A-Za-z0-9]+", "_", contributor).strip("_").lower()
    (folder / "images").mkdir(parents=True, exist_ok=True)
    picks = {f: d for f, d in decisions.items() if d in ("telecom", "near") and f in rows}
    out = []
    for f, subset in picks.items():
        r = rows[f]
        shutil.copy2(OUT_DIR / "images" / f, folder / "images" / f)
        out.append({"file": f, "subset": subset, "method": "generated", "source_url": f"openai:{r['model']}",
                    "title": r["id"], "creator": f"{r['model']} ({r['quality']}, {r['date']})", "licence": "GENERATED",
                    "licence_version": "", "licence_url": "", "notes": r["prompt"]})
    sources = folder / "sources.csv"
    existing = []
    if sources.exists():
        with open(sources, encoding="utf-8-sig") as fh:
            existing = [x for x in csv.DictReader(fh) if x["file"] not in picks]
    with open(sources, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=SOURCE_FIELDS)
        w.writeheader()
        w.writerows(existing + out)
    print(f"{len(out)} generated picks → {folder}")
    return folder


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", help="overrides IMAGE_API_MODEL from .env")
    ap.add_argument("--quality", default="medium", choices=list(PRICE))
    ap.add_argument("--size", default="1536x1024")
    ap.add_argument("--only", nargs="*", help="scenario ids")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", type=Path)
    ap.add_argument("--contributor")
    args = ap.parse_args(argv)
    if args.apply:
        if not args.contributor:
            ap.error("--apply needs --contributor")
        apply(args.apply, args.contributor)
        return
    if args.dry_run:
        for k, sc in enumerate(SCENARIOS):
            print(f"[{sc[0]}] ({sc[1]}, expect {sc[3]})\n  {prompt_for(k, sc)}\n")
        print(f"{len(SCENARIOS)} scenarios; class coverage: {coverage()}")
        print(f"estimated cost at {args.quality}: ~${len(SCENARIOS) * PRICE[args.quality]:.2f} (one image each)")
        return
    generate(args.model, args.quality, args.size, args.only)


if __name__ == "__main__":
    main()
