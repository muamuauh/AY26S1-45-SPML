"""Collect openly licensed candidate images for TelecomEval (tier T3).

    python -m telecomsafe.data.collect_open                   # Openverse + Wikimedia Commons
    python -m telecomsafe.data.collect_open --per-query 40 --providers wikimedia
    python -m telecomsafe.data.collect_open --sync            # after deleting rejected images by hand

Images go to data/raw/t3_candidates/images/; every download is recorded in
data/licence_manifest.csv with creator, licence and landing page, as CC BY /
CC BY-SA attribution requires. By default only licences that allow redistribution
of the annotated set are fetched: CC0, public domain, CC BY, CC BY-SA.

Workflow: collect → delete everything that is not people working in a telecom
setting → --sync (marks deleted rows as rejected) → pre-label → annotate → export
to data/raw/telecom_eval/ → freeze_eval --create.
"""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

from telecomsafe.paths import DATA, RAW

USER_AGENT = "TelecomSafe/0.1 (research dataset collection; https://github.com/muamuauh/AY26S1-45-SPML)"
OUT = RAW / "t3_candidates" / "images"
MANIFEST = DATA / "licence_manifest.csv"
FIELDS = ["file", "provider", "source_id", "title", "creator", "licence", "licence_version", "licence_url",
          "landing_url", "image_url", "attribution", "query", "downloaded_at", "status"]

QUERIES = [
    "tower climber", "cell tower technician", "telecommunication tower worker", "antenna installation worker",
    "telecom mast construction", "cell site maintenance", "fiber optic cable installation", "rooftop antenna installation",
    "lineman telecommunication", "radio tower climbing",
]
WIKIMEDIA_CATEGORIES = [
    "Telecom towers", "Communications towers", "Antenna towers", "Telecommunications infrastructure",
    "Tower climbers", "Telecommunications workers",
]
OPENVERSE_LICENCES = "cc0,pdm,by,by-sa"
WIKIMEDIA_OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? [\d.]+)", re.I)


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


def _wikimedia_titles(s: requests.Session, query: str | None, category: str | None, limit: int) -> list[str]:
    api = "https://commons.wikimedia.org/w/api.php"
    if category:
        params = {"action": "query", "list": "categorymembers", "cmtitle": f"Category:{category}",
                  "cmtype": "file", "cmlimit": min(limit, 500), "format": "json"}
        return [m["title"] for m in get_json(s, api, params).get("query", {}).get("categorymembers", [])]
    params = {"action": "query", "list": "search", "srsearch": query, "srnamespace": 6,
              "srlimit": min(limit, 500), "format": "json"}
    return [m["title"] for m in get_json(s, api, params).get("query", {}).get("search", [])]


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


# ---------------------------------------------------------------- manifest
def read_manifest() -> list[dict]:
    if not MANIFEST.exists():
        return []
    with open(MANIFEST, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_manifest(rows: list[dict]) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
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


def collect(providers: list[str], per_query: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read_manifest()
    seen = {(r["provider"], r["source_id"]) for r in rows}
    # Openverse also indexes Wikimedia/Flickr, so the same photo arrives under different ids.
    hashes = {h for r in rows if r["status"] == "candidate" and (h := _phash(OUT / r["file"])) is not None}
    s = session()
    jobs = []
    if "openverse" in providers:
        jobs += [("openverse", q, None) for q in QUERIES]
    if "wikimedia" in providers:
        jobs += [("wikimedia", q, None) for q in QUERIES] + [("wikimedia", None, c) for c in WIKIMEDIA_CATEGORIES]
    for provider, query, category in jobs:
        label = query or f"Category:{category}"
        try:
            items = openverse(s, query, per_query) if provider == "openverse" else wikimedia(s, query, category, per_query)
        except (requests.RequestException, RuntimeError) as e:
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
            rows.append({**it, "file": path.name, "status": status,
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
    ap.add_argument("--providers", nargs="+", default=["openverse", "wikimedia"], choices=["openverse", "wikimedia"])
    ap.add_argument("--per-query", type=int, default=40)
    ap.add_argument("--sync", action="store_true")
    args = ap.parse_args(argv)
    sync() if args.sync else collect(args.providers, args.per_query)


if __name__ == "__main__":
    main()
