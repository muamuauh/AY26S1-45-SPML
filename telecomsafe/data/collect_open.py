"""Collect openly licensed candidate images for TelecomEval (tier T3).

    python -m telecomsafe.data.collect_open                   # every provider that is set up
    python -m telecomsafe.data.collect_open --per-query 40 --providers wikimedia flickr
    python -m telecomsafe.data.collect_open --sync            # after deleting rejected images by hand

Providers: Openverse and Wikimedia Commons (no key needed), Flickr (FLICKR_API_KEY
in .env) and DVIDS, the US Department of Defense media archive (DVIDS_API_KEY);
a provider without its key is skipped. Wikimedia categories about people at work
are also searched one level of subcategories down. Frames from Creative Commons videos come from
telecomsafe.data.collect_video.

Images go to data/raw/t3_candidates/images/; every download is recorded in
data/licence_manifest.csv with creator, licence and landing page, as CC BY /
CC BY-SA attribution requires. By default only licences that allow redistribution
of the annotated set are fetched: CC0, public domain, CC BY, CC BY-SA.

Each query carries a domain: "telecom", or "near" for the closely related power-line
work (utility poles, bucket trucks), which is reported as a separate subset.

Workflow: collect → python -m telecomsafe.data.screen (score, review, keep / reject)
→ pre-label → annotate → export to data/raw/telecom_eval/ → freeze_eval --create.
"""

from __future__ import annotations

import argparse
import csv
import html
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from telecomsafe.env import load_env
from telecomsafe.paths import DATA, RAW

USER_AGENT = "TelecomSafe/0.1 (research dataset collection; https://github.com/muamuauh/AY26S1-45-SPML)"
OUT = RAW / "t3_candidates" / "images"
MANIFEST = DATA / "licence_manifest.csv"
FIELDS = ["file", "provider", "source_id", "title", "creator", "licence", "licence_version", "licence_url",
          "landing_url", "image_url", "attribution", "query", "domain", "downloaded_at", "status",
          # filled by telecomsafe.data.screen
          "persons", "scene", "clip_score", "subset"]

TELECOM_QUERIES = [
    # English
    "tower climber", "cell tower technician", "telecommunication tower worker", "antenna installation worker",
    "telecom mast construction", "cell site maintenance", "fiber optic cable installation", "rooftop antenna installation",
    "lineman telecommunication", "radio tower climbing", "tower technician harness", "microwave antenna installation",
    "fiber optic splicing", "fiber optic cable trench", "cable laying worker", "telephone line repair",
    "communications cabinet technician", "manhole cable worker", "5G antenna installation", "broadband construction crew",
    "army signal antenna mast", "satellite dish installation worker",
    # Chinese, Japanese, Korean, Spanish, French, German, Portuguese, Indonesian
    "通信铁塔 作业", "铁塔 攀爬 工人", "光缆 敷设", "基站 施工", "天线 安装 工人",
    "鉄塔 作業員", "基地局 工事", "光ファイバー 敷設", "통신탑 작업",
    "torrero telecomunicaciones", "instalación antena trabajador", "tendido fibra óptica",
    "technicien pylône télécom", "installation antenne technicien", "Mobilfunkmast Monteur", "Glasfaser Verlegung",
    "torre de telecomunicações trabalhador", "instalação fibra óptica", "pemasangan menara BTS",
]
NEAR_QUERIES = [  # power-line work: same climbing, harness and bucket-truck hazards, reported separately
    "lineman climbing utility pole", "lineworker bucket truck", "power line maintenance worker", "utility pole climbing",
]
QUERIES = TELECOM_QUERIES + NEAR_QUERIES
WIKIMEDIA_CATEGORIES = {  # category → domain
    "Telecom towers": "telecom", "Communications towers": "telecom", "Antenna towers": "telecom",
    "Telecommunications infrastructure": "telecom", "Telecommunications Tower Technicians at work": "telecom",
    "Mobile phone base stations": "telecom", "Fiber to the x": "telecom", "Optical fiber cables": "telecom",
    "Serving area interface": "telecom", "Climbing towers": "telecom", "Working at height": "telecom",
    "Fall protection harnesses": "telecom",
    "Lineworkers": "near", "Maintenance of overhead power lines": "near", "Aerial work platforms": "near",
}
# Only categories about people at work are searched one level of subcategories down: the subcategories
# of the structure categories (towers at night, aerial photographs, towers in art...) almost never show people.
WIKIMEDIA_RECURSE = {"Telecommunications Tower Technicians at work", "Working at height", "Lineworkers",
                     "Maintenance of overhead power lines", "Fiber to the x"}
PROVIDERS = ["openverse", "wikimedia", "flickr", "dvids"]
OPENVERSE_LICENCES = "cc0,pdm,by,by-sa"
WIKIMEDIA_OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? [\d.]+)", re.I)
# Flickr licence ids are looked up at run time (Flickr has added licences over the years); keep these by name
FLICKR_OK = re.compile(r"^(attribution( |-)?(sharealike)?( license| \d|$)|cc by|public domain|no known copyright"
                       r"|united states government work|cc0)", re.I)
FLICKR_NOT_OK = re.compile(r"noncommercial|non-commercial|noderiv|no deriv|\bnc\b|\bnd\b", re.I)
DVIDS_RESTRICTED = re.compile(r"courtesy|copyright|©|all rights reserved", re.I)


def domain_of(query: str) -> str:
    return "near" if query in NEAR_QUERIES else "telecom"


def session() -> requests.Session:
    s = requests.Session()
    s.headers["User-Agent"] = USER_AGENT
    return s


def get_json(s: requests.Session, url: str, params: dict, retries: int = 4) -> dict:
    for attempt in range(retries):
        r = s.get(url, params=params, timeout=30)
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 30 * (attempt + 1)))
            print(f"    rate limited, waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError(f"gave up after {retries} rate-limited attempts: {url}")


# ---------------------------------------------------------------- providers
def openverse(s: requests.Session, query: str, limit: int) -> list[dict]:
    out, page = [], 1
    while len(out) < limit:
        data = get_json(s, "https://api.openverse.org/v1/images/",
                        {"q": query, "license": OPENVERSE_LICENCES, "page_size": 20, "page": page})
        for r in data.get("results", []):
            out.append({
                "provider": "openverse", "source_id": r["id"], "title": r.get("title") or "",
                "creator": r.get("creator") or "", "licence": r.get("license", ""),
                "licence_version": r.get("license_version") or "", "licence_url": r.get("license_url") or "",
                "landing_url": r.get("foreign_landing_url") or "", "image_url": r["url"],
                "attribution": r.get("attribution") or "", "query": query,
            })
        if page >= data.get("page_count", 1):
            break
        page += 1
        time.sleep(3)  # anonymous rate limit
    return out[:limit]


def _wikimedia_members(s: requests.Session, category: str, kind: str, limit: int) -> list[str]:
    params = {"action": "query", "list": "categorymembers", "cmtitle": f"Category:{category}",
              "cmtype": kind, "cmlimit": min(limit, 500), "format": "json"}
    members = get_json(s, "https://commons.wikimedia.org/w/api.php", params).get("query", {}).get("categorymembers", [])
    return [m["title"] for m in members]


def wikimedia_subcategories(s: requests.Session, category: str) -> list[str]:
    return [t.split(":", 1)[1] for t in _wikimedia_members(s, category, "subcat", 100)]


def _wikimedia_titles(s: requests.Session, query: str | None, category: str | None, limit: int) -> list[str]:
    if category:
        return _wikimedia_members(s, category, "file", limit)
    params = {"action": "query", "list": "search", "srsearch": query, "srnamespace": 6,
              "srlimit": min(limit, 500), "format": "json"}
    return [m["title"] for m in get_json(s, "https://commons.wikimedia.org/w/api.php", params).get("query", {}).get("search", [])]


def wikimedia(s: requests.Session, query: str | None, category: str | None, limit: int) -> list[dict]:
    titles = _wikimedia_titles(s, query, category, limit)
    out = []
    for i in range(0, len(titles), 50):
        params = {"action": "query", "titles": "|".join(titles[i : i + 50]), "prop": "imageinfo",
                  "iiprop": "url|extmetadata|mime", "iiurlwidth": 1600, "format": "json"}
        pages = get_json(s, "https://commons.wikimedia.org/w/api.php", params).get("query", {}).get("pages", {})
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            if not info.get("mime", "").startswith("image/") or info.get("mime") == "image/svg+xml":
                continue
            meta = {k: v.get("value", "") for k, v in info.get("extmetadata", {}).items()}
            licence = meta.get("LicenseShortName", "")
            if not WIKIMEDIA_OK.match(licence):
                continue
            creator = html.unescape(re.sub(r"<[^>]+>", "", meta.get("Artist", ""))).strip()
            out.append({
                "provider": "wikimedia", "source_id": str(page.get("pageid")), "title": page["title"],
                "creator": creator, "licence": licence, "licence_version": "", "licence_url": meta.get("LicenseUrl", ""),
                "landing_url": info.get("descriptionurl", ""), "image_url": info.get("thumburl") or info["url"],
                "attribution": f'"{page["title"]}" by {creator or "unknown"}, {licence}, via Wikimedia Commons',
                "query": category and f"Category:{category}" or query,
            })
        time.sleep(1)
    return out


def flickr_licences(s: requests.Session, key: str) -> dict[str, dict]:
    data = get_json(s, "https://api.flickr.com/services/rest/", {
        "method": "flickr.photos.licenses.getInfo", "api_key": key, "format": "json", "nojsoncallback": 1})
    if data.get("stat") != "ok":
        raise RuntimeError(f"Flickr: {data.get('message', data)}")
    return {str(lic["id"]): lic for lic in data["licenses"]["license"]
            if FLICKR_OK.search(lic["name"]) and not FLICKR_NOT_OK.search(lic["name"])}


def flickr(s: requests.Session, query: str, limit: int, key: str, licences: dict[str, dict]) -> list[dict]:
    data = get_json(s, "https://api.flickr.com/services/rest/", {
        "method": "flickr.photos.search", "api_key": key, "text": query, "license": ",".join(licences),
        "content_types": 0, "media": "photos", "sort": "relevance", "per_page": min(limit, 250),
        "extras": "owner_name,license,url_l,url_c,url_o", "format": "json", "nojsoncallback": 1})
    out = []
    for p in data.get("photos", {}).get("photo", []):
        url = p.get("url_l") or p.get("url_c") or p.get("url_o")
        lic = licences.get(str(p.get("license")))
        if not url or not lic:
            continue
        landing = f"https://www.flickr.com/photos/{p['owner']}/{p['id']}"
        creator = p.get("ownername") or p["owner"]
        out.append({
            "provider": "flickr", "source_id": p["id"], "title": p.get("title") or "", "creator": creator,
            "licence": lic["name"], "licence_version": "", "licence_url": lic.get("url") or "",
            "landing_url": landing, "image_url": url,
            "attribution": f'"{p.get("title") or "Untitled"}" by {creator}, {lic["name"]}, via Flickr ({landing})',
            "query": query,
        })
    return out


def dvids(s: requests.Session, query: str, limit: int, key: str) -> list[dict]:
    """US Department of Defense imagery. Works of federal employees are public domain; anything credited
    to a third party ("courtesy") or carrying a copyright notice is skipped."""
    data = get_json(s, "https://api.dvidshub.net/search",
                    {"api_key": key, "q": query, "type[]": "image", "max_results": min(limit, 50)})
    out = []
    for r in data.get("results", []):
        asset = get_json(s, "https://api.dvidshub.net/asset", {"api_key": key, "id": r["id"]}).get("results", {})
        credit = asset.get("credit") or r.get("credit") or ""
        if isinstance(credit, list):
            credit = "; ".join(" ".join(filter(None, (c.get("rank"), c.get("name")))) for c in credit)
        if DVIDS_RESTRICTED.search(f"{credit} {asset.get('description', '')}") or not asset.get("image"):
            continue
        creator = ", ".join(filter(None, (credit, asset.get("unit_name") or r.get("unit_name"))))
        title = asset.get("title") or r.get("title", "")
        out.append({
            "provider": "dvids", "source_id": str(r["id"]).split(":")[-1], "title": title, "creator": creator,
            "licence": "Public domain (US federal government work)", "licence_version": "",
            "licence_url": "https://www.dvidshub.net/about/copyright", "landing_url": asset.get("url") or r.get("url", ""),
            "image_url": asset["image"], "attribution": f'"{title}" by {creator}, public domain, via DVIDS',
            "query": query,
        })
        time.sleep(0.3)
    return out


# ---------------------------------------------------------------- manifest
def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with open(MANIFEST, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for r in rows:  # rows written before the domain column existed
        r["domain"] = r.get("domain") or "telecom"
    return rows


def write_manifest(rows: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        w.writeheader()
        w.writerows(rows)


def download(s: requests.Session, item: dict) -> Path | None:
    ext = Path(item["image_url"].split("?")[0]).suffix.lower()
    ext = ext if ext in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
    path = OUT / f"{item['provider']}_{re.sub(r'[^A-Za-z0-9_-]', '_', item['source_id'])[:60]}{ext}"
    try:
        r = s.get(item["image_url"], timeout=60)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"    ✗ {item['image_url']}: {e}", file=sys.stderr)
        return None
    path.write_bytes(r.content)
    return path


def _phash(path: Path) -> int | None:
    import imagehash
    from PIL import Image

    try:
        with Image.open(path) as im:
            return int(str(imagehash.phash(im)), 16)
    except OSError:
        return None


def candidate_hashes(rows: list[dict]) -> set[int]:
    return {h for r in rows if r["status"] == "candidate" and (h := _phash(OUT / r["file"])) is not None}


def collect(providers: list[str], per_query: int, depth: int = 1) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    load_env()
    rows = read_manifest()
    seen = {(r["provider"], r["source_id"]) for r in rows}
    # Openverse also indexes Wikimedia/Flickr, so the same photo arrives under different ids.
    hashes = candidate_hashes(rows)
    s = session()
    keys = {"flickr": os.environ.get("FLICKR_API_KEY"), "dvids": os.environ.get("DVIDS_API_KEY")}
    for p in ("flickr", "dvids"):
        if p in providers and not keys[p]:
            print(f"  - {p}: skipped, {p.upper()}_API_KEY is not set in .env")
            providers = [x for x in providers if x != p]
    licences = flickr_licences(s, keys["flickr"]) if "flickr" in providers else {}
    if licences:
        print(f"  flickr licences: {', '.join(lic['name'] for lic in licences.values())}")
    jobs = []  # (provider, query, category, domain)
    for p in ("openverse", "flickr", "dvids", "wikimedia"):
        if p in providers:
            jobs += [(p, q, None, domain_of(q)) for q in QUERIES]
    if "wikimedia" in providers:
        for cat, dom in WIKIMEDIA_CATEGORIES.items():
            subcats = wikimedia_subcategories(s, cat) if depth and cat in WIKIMEDIA_RECURSE else []
            jobs += [("wikimedia", None, c, dom) for c in [cat, *subcats]]
    for provider, query, category, domain in jobs:
        label = query or f"Category:{category}"
        try:
            if provider == "openverse":
                items = openverse(s, query, per_query)
            elif provider == "flickr":
                items = flickr(s, query, per_query, keys["flickr"], licences)
            elif provider == "dvids":
                items = dvids(s, query, per_query, keys["dvids"])
            else:
                items = wikimedia(s, query, category, per_query)
        except (requests.RequestException, RuntimeError, KeyError, ValueError) as e:
            print(f"  ✗ {provider} {label}: {e}", file=sys.stderr)
            continue
        new = [it for it in items if (it["provider"], it["source_id"]) not in seen]
        print(f"  {provider:9s} {label!r}: {len(items)} found, {len(new)} new")
        for it in new:
            path = download(s, it)
            if path is None:
                continue
            seen.add((it["provider"], it["source_id"]))
            h = _phash(path)
            status = "duplicate" if h in hashes else "candidate"
            if status == "duplicate":
                path.unlink()
            elif h is not None:
                hashes.add(h)
            rows.append({**it, "file": path.name, "status": status, "domain": domain,
                         "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            time.sleep(0.5)
        write_manifest(rows)
    print(f"{sum(r['status'] == 'candidate' for r in rows)} candidates in {OUT}; manifest: {MANIFEST}")


def sync() -> None:
    """Mark candidates whose file was deleted as rejected, so the manifest lists exactly what is kept."""
    rows = read_manifest()
    for r in rows:
        if r["status"] == "candidate" and not (OUT / r["file"]).exists():
            r["status"] = "rejected"
    write_manifest(rows)
    kept = sum(r["status"] == "candidate" for r in rows)
    print(f"{kept} kept, {sum(r['status'] == 'rejected' for r in rows)} rejected")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--providers", nargs="+", default=PROVIDERS, choices=PROVIDERS)
    ap.add_argument("--per-query", type=int, default=40)
    ap.add_argument("--depth", type=int, default=1, choices=[0, 1], help="1 = also search subcategories of the work categories")
    ap.add_argument("--sync", action="store_true")
    args = ap.parse_args(argv)
    sync() if args.sync else collect(args.providers, args.per_query, args.depth)


if __name__ == "__main__":
    main()
