"""Generate phase 2 training images (TelecomSynth) for one weak class with an image model.

    python -m telecomsafe.data.generate_synth harness --dry-run          # the prompt bank and cost estimate
    python -m telecomsafe.data.generate_synth harness --n 20             # a pilot
    python -m telecomsafe.data.generate_synth harness --n 450 --workers 4
    python -m telecomsafe.data.generate_synth no_vest --n 360 --workers 4

Uses the same image API settings as generate_eval (IMAGE_API_BASE / IMAGE_API_MODEL / IMAGE_API_KEY in .env).
Prompts are combined from a per-class bank — scene x people and PPE x equipment look x camera x region x
light — so every prompt is different and each scene family is spread over many settings. The wording is
deliberately unlike the prompts behind TelecomEval's generated images (generate_eval), which must stay unseen.

Images go to data/synth/work/<class>/images/ with prompts.csv (model, size, full prompt, the people and PPE the
prompt asked for); a run resumes where it stopped. The kept images are then labelled and handed in through
telecomsafe.data.synth.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import requests

from telecomsafe.data.generate_eval import DEFAULT_MODEL, PRICE, endpoint, image_bytes
from telecomsafe.env import load_env
from telecomsafe.paths import ROOT

WORK = ROOT / "data" / "synth" / "work"
TEMPLATE = ("Real-world photo taken by a site safety officer during routine telecom maintenance. {action} "
            "{people}. {gear}. Location: {region}. {light}. {camera}. Natural colours, sharp focus, believable "
            "anatomy and equipment, nobody posing for the camera, no text, no logos, no watermark.")

# ---- harness: (family, subset, orientation, people: "one" | "group", action)
HARNESS_SCENES = [
    ("lattice_climb", "telecom", "portrait", "one", "A technician climbs the steel lattice of a mobile-phone tower, clipped in with a twin lanyard"),
    ("lattice_platform", "telecom", "landscape", "group", "Riggers stand on a narrow platform high on a lattice telecom tower, fixing panel antennas"),
    ("monopole", "telecom", "portrait", "one", "A worker on the step bolts of a slim monopole cell tower, tied off with a lanyard, adjusting a radio unit"),
    ("wood_pole", "telecom", "portrait", "one", "A line technician works on a wooden telephone pole using climbing spikes and a pole strap around the pole"),
    ("concrete_pole", "telecom", "portrait", "one", "A fibre technician on a concrete utility pole splices an aerial fibre cable, secured by a positioning lanyard"),
    ("rooftop_edge", "telecom", "landscape", "group", "Workers install antennas at the edge of a flat building roof, their harnesses tied to an anchor rail"),
    ("ladder_pole", "telecom", "portrait", "one", "A technician on an extension ladder leaning against a pole fixes a drop cable, tied off to the pole"),
    ("water_tower", "telecom", "landscape", "group", "A crew mounts small antennas on a water tower's catwalk railing, clipped to the handrail"),
    ("tower_rescue_drill", "telecom", "portrait", "group", "Climbers practise a controlled descent on a telecom tower, one lowering another on a rope"),
    ("transmission", "near", "portrait", "group", "Line workers climb a high-voltage transmission pylon, clipped to the steel members"),
    ("bucket", "near", "landscape", "one", "A lineman in the bucket of a boom truck works on overhead lines, the harness lanyard clipped to the boom"),
]
PEOPLE = {
    "one": [
        "The worker wears a white hard hat and an orange hi-vis vest",
        "The worker wears a yellow hard hat and a dark work jacket without hi-vis",
        "The worker wears a climbing helmet and a plain grey T-shirt",
        "The worker has no helmet, short hair and a navy work shirt",
        "The worker wears a baseball cap and a hoodie, no hi-vis",
        "The worker wears a red climbing helmet and a lime hi-vis shirt",
    ],
    "group": [
        "Two workers: one in a hard hat and hi-vis vest, the other bareheaded in a dark jacket",
        "Two workers in red climbing helmets, one in a lime hi-vis shirt and one in a plain blue shirt",
        "Three workers at different heights, all in hard hats, only one wearing a hi-vis vest",
        "Two workers, one in a cap and one in a white hard hat, both in plain work clothes",
        "Three workers in orange hi-vis jackets, one of them without a helmet",
    ],
}
GEAR = [
    "Each wears a full-body harness with orange straps over the shoulders, chest and thighs",
    "Each wears a full-body harness with yellow webbing and a tool pouch on the hip",
    "Each wears a black full-body harness with a red shock-absorbing lanyard",
    "Each wears a red and black harness with leg loops and a positioning belt",
    "Each wears a worn grey harness with a rope grab on the chest",
]
CAMERAS = [  # distant views twice: small far-away workers are what the detector misses on TelecomEval
    "Shot from the ground looking up with a wide-angle lens",
    "Shot from a neighbouring rooftop at the same height",
    "Telephoto shot from about 40 metres away",
    "Wide shot from across the street, the workers small in the frame",
    "Close shot from slightly below showing the waist and chest",
    "Shot from a drone hovering beside the structure",
    "Distant shot from a hillside, the structure and its climbers small in the frame",
]
REGIONS = ["a hillside town in southern China", "a dusty suburb in Kenya", "an industrial estate in Germany",
           "a coastal village in Vietnam", "a highway roadside in Texas", "a mountain pass in Peru",
           "a dense city block in Mumbai", "farmland in rural France"]
LIGHT = ["Bright midday sun with hard shadows", "Grey overcast sky", "Early morning haze", "Wet surfaces after rain",
         "Golden evening light", "Windy day with dark clouds"]

# ---- no_vest: more scene families than harness, on the ground as well as up high, so poses and framings repeat less
NO_VEST_SCENES = [
    ("cabinet", "telecom", "landscape", "one", "A technician crouches at an open roadside fibre cabinet, testing connections with a handheld meter"),
    ("manhole", "telecom", "landscape", "group", "A crew feeds fibre cable from a drum into an open manhole beside the road"),
    ("trench", "telecom", "landscape", "group", "Workers lay orange fibre ducts by hand in a shallow trench along a street"),
    ("ladder", "telecom", "portrait", "one", "A technician halfway up a ladder against a utility pole fixes a drop cable to a house"),
    ("rooftop_carry", "telecom", "landscape", "group", "Riggers carry antenna panels across a flat roof towards a small mast"),
    ("tower_base", "telecom", "landscape", "group", "A crew unpacks radio units and coils of cable inside the fenced base of a lattice cell tower"),
    ("tower_climb", "telecom", "portrait", "one", "A climber high on a mobile-phone tower bolts a microwave dish to the steel"),
    ("shelter", "telecom", "landscape", "one", "A technician carries a battery pack into an outdoor equipment shelter beside a monopole"),
    ("van_unload", "telecom", "landscape", "group", "Workers unload cable reels and tool cases from the back of a parked van next to a street cabinet"),
    ("survey", "telecom", "portrait", "one", "A field engineer walks along a village lane with a tablet, checking the overhead cables"),
    ("splice_table", "telecom", "landscape", "group", "Fibre splicers work at a folding table under a small tent by the roadside"),
    ("power_line", "near", "landscape", "group", "Line workers pull overhead cable between concrete poles along a country road"),
    ("transformer", "near", "portrait", "group", "Electricians service a pole-mounted transformer, one on a ladder and one passing tools from the ground"),
]
NO_VEST_PEOPLE = {
    "one": [
        "The worker wears a white hard hat and a plain navy work jacket, no hi-vis clothing",
        "The worker wears a yellow hard hat and a grey T-shirt, no hi-vis clothing",
        "The worker wears a baseball cap and an olive camouflage jacket",
        "The worker has no helmet and wears a checked flannel shirt",
        "The worker wears a red hard hat and a dark rain jacket with no reflective strips",
        "The worker wears a hooded sweatshirt and cargo trousers",
        "The worker wears a blue hard hat and a plain blue boiler suit with no reflective strips",
    ],
    "group": [
        "Two workers in plain dark work jackets and no hi-vis clothing, one in a hard hat and one bareheaded",
        "Three workers in ordinary T-shirts and jeans, all in white hard hats",
        "Two workers in camouflage jackets, one in a cap and one in a hard hat",
        "Three workers in rain jackets with no reflective strips, two of them in hard hats",
        "Two workers in plain blue boiler suits and yellow hard hats",
        "Three workers: two in plain work shirts and one supervisor in an orange hi-vis vest",
        "Four workers in ordinary work clothes, only one of them wearing a yellow hi-vis vest",
    ],
}
NO_VEST_DETAILS = [
    "Tool bags and coils of black cable lie on the ground nearby",
    "Traffic cones mark off the work area",
    "A dusty pickup is parked a short way off",
    "Their clothes are worn and dirty from a long day of work",
    "A wheelbarrow and a few cut lengths of duct stand to one side",
]
NO_VEST_REGIONS = REGIONS + ["a market town in Nigeria", "a favela hillside in Brazil", "a rice-growing village in Indonesia",
                             "a housing estate in Poland"]
BANKS = {"harness": (HARNESS_SCENES, PEOPLE, GEAR, CAMERAS, REGIONS, LIGHT),
         "no_vest": (NO_VEST_SCENES, NO_VEST_PEOPLE, NO_VEST_DETAILS, CAMERAS, NO_VEST_REGIONS, LIGHT)}
SIZES = {"portrait": "1024x1536", "landscape": "1536x1024"}


def prompt_bank(target: str, n: int, seed: int = 0) -> list[dict]:
    """n different prompts; scene families in turn, the other parts drawn without repeating a combination."""
    scenes, people, gear, cameras, regions, light = BANKS[target]
    rng = random.Random(seed)
    combos = {kind: list(itertools.product(range(len(opts)), range(len(gear)), range(len(cameras)),
                                           range(len(regions)), range(len(light)))) for kind, opts in people.items()}
    for c in combos.values():
        rng.shuffle(c)
    used = {kind: 0 for kind in people}
    out = []
    for k in range(n):
        family, subset, orient, kind, action = scenes[k % len(scenes)]
        p, g, c, r, li = combos[kind][used[kind] % len(combos[kind])]
        used[kind] += 1
        out.append({"id": f"{target}_{k:04d}", "family": family, "subset": subset, "size": SIZES[orient],
                    "people": people[kind][p],
                    "prompt": TEMPLATE.format(action=action + ".", people=people[kind][p], gear=gear[g], region=regions[r],
                                              light=light[li], camera=cameras[c])})
    return out


FIELDS = ["id", "file", "family", "subset", "people", "model", "quality", "size", "date", "seconds", "prompt", "usage"]


def generate(target: str, n: int, quality: str, workers: int, model: str | None) -> None:
    load_env()
    key = os.environ.get("IMAGE_API_KEY")
    if not key:
        sys.exit("IMAGE_API_KEY is not set in .env")
    url = endpoint(os.environ.get("IMAGE_API_BASE"))
    model = model or os.environ.get("IMAGE_API_MODEL") or DEFAULT_MODEL
    out = WORK / target
    (out / "images").mkdir(parents=True, exist_ok=True)
    log = out / "prompts.csv"
    done = set()
    if log.exists():
        with open(log, encoding="utf-8-sig") as f:
            done = {r["id"] for r in csv.DictReader(f)}
    todo = [p for p in prompt_bank(target, n) if p["id"] not in done]
    print(f"{target}: {len(todo)} to generate ({len(done)} done) with {model}, {workers} at a time", flush=True)
    lock = threading.Lock()
    new = not log.exists()
    f = open(log, "a", newline="", encoding="utf-8-sig")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        w.writeheader()
    s = requests.Session()

    def one(p: dict) -> None:
        t0 = time.time()
        for attempt in range(3):
            try:
                r = s.post(url, headers={"Authorization": f"Bearer {key}"}, timeout=600,
                           json={"model": model, "prompt": p["prompt"], "size": p["size"], "quality": quality, "n": 1})
                if r.status_code == 200:
                    body = r.json()
                    data = image_bytes(body["data"][0], s)
                    break
                msg = f"HTTP {r.status_code} {r.text[:150]}"
            except (requests.RequestException, KeyError, IndexError, ValueError) as e:
                msg = repr(e)[:200]
            time.sleep(5 * (attempt + 1))
        else:
            print(f"  ✗ {p['id']}: {msg}", file=sys.stderr, flush=True)
            return
        file = f"{p['id']}.png"
        (out / "images" / file).write_bytes(data)
        with lock:
            w.writerow({**{k: p[k] for k in ("id", "family", "subset", "people", "size", "prompt")}, "file": file,
                        "model": model, "quality": quality, "date": f"{date.today():%Y-%m-%d}",
                        "seconds": round(time.time() - t0), "usage": json.dumps(body.get("usage", {}))})
            f.flush()
        print(f"  ✓ {p['id']} {p['family']} ({time.time() - t0:.0f}s)", flush=True)

    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(one, todo))
    f.close()
    print(f"done → {out}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", choices=list(BANKS))
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--quality", default="medium", choices=list(PRICE))
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--model", help="overrides IMAGE_API_MODEL")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.dry_run:
        bank = prompt_bank(args.target, args.n)
        for p in bank[:6]:
            print(f"[{p['id']} {p['family']} {p['size']}]\n  {p['prompt']}\n")
        print(f"{len(bank)} prompts, {len({p['prompt'] for p in bank})} unique; "
              f"~${len(bank) * PRICE[args.quality]:.2f} at {args.quality} (gpt-image-2 list price)")
        return
    generate(args.target, args.n, args.quality, args.workers, args.model)


if __name__ == "__main__":
    main()
