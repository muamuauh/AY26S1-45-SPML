"""Check a TelecomEval image submission and pack it for hand-in.

    python tools/check.py                 # checks ./submission, writes deliverable/<zip> when it passes

Run through check.bat / check.command. The project's intake runs the same checks again,
so a submission that passes here will be accepted there. Needs only Pillow.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from PIL import Image

PKG = Path(__file__).resolve().parents[1]
COLUMNS = ["file", "source_url", "title", "creator", "licence", "licence_version", "licence_url", "scene", "notes"]
# licence code → needs version, creator and licence URL (attribution licences)
LICENCES = {"CC0": False, "PDM": False, "US-GOV": False, "CC-BY": True, "CC-BY-SA": True}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
MIN_SIDE = 480
DUP_BITS = 6  # dHash Hamming distance at or below which two images count as the same photo


def dhash(path: Path) -> int:
    with Image.open(path) as im:
        px = list(im.convert("L").resize((9, 8), Image.LANCZOS).tobytes())
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (px[row * 9 + col] > px[row * 9 + col + 1])
    return bits


def normalise_url(url: str) -> str:
    url = url.strip().split("#")[0].lower()
    url = re.sub(r"^https?://(www\.)?", "", url)
    return url.rstrip("/")


def load_seen(path: Path) -> tuple[set[str], list[int]]:
    urls, hashes = set(), []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                url, _, h = line.partition("\t")
                if url:
                    urls.add(normalise_url(url))
                if h:
                    hashes.append(int(h, 16))
    return urls, hashes


def close(h: int, others: list[int]) -> bool:
    return any(bin(h ^ o).count("1") <= DUP_BITS for o in others)


def check_submission(sub: Path, seen_urls: set[str], seen_hashes: list[int], scenes: list[str]) -> tuple[list, list, list]:
    """Returns (errors, warnings, rows). Rows passing every check carry a "dhash" field."""
    errors, warnings = [], []
    manifest = sub / "manifest.csv"
    if not manifest.exists():
        return [f"{manifest} not found — copy manifest_template.csv there and fill it in"], [], []
    with open(manifest, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            return [f"manifest.csv is missing columns: {missing}"], [], []
        rows = [{k: (v or "").strip() for k, v in r.items() if k} for r in reader if any((v or "").strip() for v in r.values())]
    images = sub / "images"
    on_disk = {p.name for p in images.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES} if images.exists() else set()
    listed, hashes = set(), []
    for i, r in enumerate(rows, start=2):  # line 1 is the header
        where = f"line {i} ({r['file'] or 'no file'})"

        def err(msg: str, r=r, where=where) -> None:
            r["_bad"] = True
            errors.append(f"{where}: {msg}")
        if not r["file"]:
            err("file is empty")
            continue
        if r["file"] in listed:
            err("listed twice")
            continue
        listed.add(r["file"])
        if r["file"] not in on_disk:
            err("not found in images/")
            continue
        if not re.match(r"^https?://", r["source_url"]):
            err("source_url must be the page the image came from (http...)")
        elif normalise_url(r["source_url"]) in seen_urls:
            err("already in the project (source_url is in seen.txt)")
        lic = r["licence"].upper()
        if lic not in LICENCES:
            err(f"licence '{r['licence']}' not allowed — use one of {', '.join(LICENCES)}")
        elif LICENCES[lic]:
            if not re.match(r"^\d(\.\d)?$", r["licence_version"]):
                err(f"{lic} needs licence_version, e.g. 4.0")
            if not r["creator"]:
                err(f"{lic} needs the creator's name for attribution")
            if not re.match(r"^https?://", r["licence_url"]):
                err(f"{lic} needs licence_url")
        if scenes and r["scene"] not in scenes:
            warnings.append(f"{where}: scene '{r['scene']}' is not one of {', '.join(scenes)}")
        try:
            with Image.open(images / r["file"]) as im:
                im.verify()
            with Image.open(images / r["file"]) as im:
                w, h = im.size
            if min(w, h) < MIN_SIDE:
                err(f"too small ({w}x{h}); the short side needs at least {MIN_SIDE} px")
                continue
            d = dhash(images / r["file"])
        except Exception as e:  # unreadable or not an image
            err(f"cannot be opened as an image ({e.__class__.__name__})")
            continue
        if close(d, seen_hashes):
            err("the same photo is already in the project")
        elif close(d, hashes):
            err("duplicate of another image in this submission")
        hashes.append(d)
        r["dhash"] = f"{d:016x}"
    for name in sorted(on_disk - listed):
        errors.append(f"images/{name}: not listed in manifest.csv")
    return errors, warnings, rows


def main() -> None:
    meta = json.loads((PKG / "data" / "package.json").read_text(encoding="utf-8"))
    sub = PKG / "submission"
    seen_urls, seen_hashes = load_seen(PKG / "data" / "seen.txt")
    errors, warnings, rows = check_submission(sub, seen_urls, seen_hashes, meta["scenes"])
    ok = sum(not r.get("_bad") for r in rows)
    lines = [f"TelecomEval collection check — {meta['domain']} — {datetime.now():%Y-%m-%d %H:%M}",
             f"images listed: {len(rows)} · passing: {ok} · target: {meta['target']}", ""]
    lines += [f"ERROR   {e}" for e in errors] + [f"WARNING {w}" for w in warnings]
    if len(rows) < meta["target"]:
        lines.append(f"NOTE    {len(rows)} of the {meta['target']} images targeted so far")
    report = "\n".join(lines)
    print(report)
    sub.mkdir(exist_ok=True)
    (sub / "check_report.txt").write_text(report, encoding="utf-8")
    if errors or not rows:
        print(f"\n✗ Fix the errors above and run the check again. / 请修正以上错误后重新检查。")
        sys.exit(1)
    out = PKG / "deliverable" / f"TelecomEval_collect_{meta['domain']}_{datetime.now():%Y%m%d_%H%M}.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(sub / "manifest.csv", "manifest.csv")
        z.write(sub / "check_report.txt", "check_report.txt")
        for r in rows:
            z.write(sub / "images" / r["file"], f"images/{r['file']}")
    print(f"\n✓ All checks passed. Hand in / 检查通过，请提交: {out}")


if __name__ == "__main__":
    main()
