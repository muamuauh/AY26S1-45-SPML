"""TelecomEval candidates from Creative Commons videos (YouTube, CC BY filter).

    python -m telecomsafe.data.collect_video                       # all queries
    python -m telecomsafe.data.collect_video --videos-per-query 4 --frames-per-video 3

Climbing and installation footage is mostly helmet-cam or third-person video of
exactly the scenes TelecomEval needs. For each video whose licence reads Creative
Commons (YouTube's CC option is CC BY 3.0), a frame is sampled every --every seconds;
the E2 detector keeps frames that show a whole person (a person box with a head
inside it, so helmet-cam shots of hands and feet are dropped), blurred frames are dropped, and
at most --frames-per-video visually distinct frames are kept so a few long videos
cannot dominate the test set. Frames go to data/raw/t3_candidates/images/ and are
recorded in data/licence_manifest.csv with the video's creator, licence and a
timestamped link. Videos are deleted after extraction.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import cv2

from telecomsafe.data.collect_open import OUT, _phash, read_manifest, write_manifest
from telecomsafe.paths import INTERIM, ROOT

VIDEO_QUERIES = {  # query → domain
    "cell tower climb": "telecom", "tower climber": "telecom", "tower technician": "telecom",
    "cell tower antenna installation": "telecom", "microwave dish installation tower": "telecom",
    "fiber optic installation": "telecom", "fiber optic splicing": "telecom", "fiber cable laying": "telecom",
    "telecom tower construction": "telecom", "radio tower work": "telecom",
    "torre de telecomunicaciones subida": "telecom", "通信铁塔 攀爬": "telecom", "鉄塔 作業": "telecom",
    "lineman pole climbing": "near", "bucket truck lineman": "near",
}
CC_FILTER = "EgIwAQ%3D%3D"  # YouTube search filter "Creative Commons"
SEEN = INTERIM / "videos_seen.txt"
TMP = INTERIM / "videos"
WEIGHTS = ROOT / "runs/phase1/e2/weights/best.pt"


def search(query: str, n: int) -> list[dict]:
    import yt_dlp

    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp={CC_FILTER}"
    with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "playlistend": n, "no_warnings": True}) as y:
        return [e for e in (y.extract_info(url, download=False).get("entries") or []) if e.get("id")]


def fetch(video_id: str) -> tuple[dict, Path] | None:
    """Metadata always; the file only if the licence is Creative Commons."""
    import yt_dlp

    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "outtmpl": str(TMP / "%(id)s.%(ext)s"),
            # video-only mp4 needs no ffmpeg merge, and OpenCV reads it directly
            "format": "bv*[height<=720][ext=mp4]/b[height<=720][ext=mp4]/bv*[height<=720]",
            "js_runtimes": {"node": {}}}
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(opts) as y:
        info = y.extract_info(url, download=False)
        if "creative commons" not in (info.get("license") or "").lower():
            return None
        info = y.extract_info(url, download=True)
    return info, Path(y.prepare_filename(info))


HEADS = {"helmet", "no_helmet"}


def visible_people(result, height: int, min_height: float = 0.08) -> int:
    """People whose box is at least min_height of the frame and has a head (helmet or bare) in its top half.

    The head requirement rejects the hands and legs that helmet-cam footage is full of."""
    boxes = [(result.names[int(c)], b) for c, b in zip(result.boxes.cls.tolist(), result.boxes.xyxy.tolist())]
    heads = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for n, b in boxes if n in HEADS]
    count = 0
    for n, (x1, y1, x2, y2) in boxes:
        if n == "person" and (y2 - y1) >= min_height * height and any(
                x1 <= hx <= x2 and y1 <= hy <= (y1 + y2) / 2 for hx, hy in heads):
            count += 1
    return count


def sharpness(frame) -> float:
    gray = cv2.cvtColor(cv2.resize(frame, (640, 360)), cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def sample(path: Path, every: float, skip: float = 3.0):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    t = skip
    while t < total - skip:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        yield t, frame
        t += every
    cap.release()


def pick_frames(model, path: Path, every: float, k: int, min_sharpness: float, known: list[int]) -> list[tuple]:
    """(seconds, frame, persons) for at most k sharp, distinct frames that show a person."""
    import imagehash
    from PIL import Image

    scored = []
    frames = list(sample(path, every))
    for i in range(0, len(frames), 32):
        chunk = frames[i : i + 32]
        for (t, frame), r in zip(chunk, model.predict([f for _, f in chunk], conf=0.3, verbose=False)):
            persons = visible_people(r, frame.shape[0])
            if persons:
                s = sharpness(frame)
                if s >= min_sharpness:
                    scored.append((persons, s, t, frame))
    picked, hashes = [], list(known)
    for persons, s, t, frame in sorted(scored, key=lambda x: (-x[0], -x[1])):
        ph = int(str(imagehash.phash(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))), 16)
        if any(bin(ph ^ o).count("1") < 14 for o in hashes) or any(abs(t - p[0]) < 8 for p in picked):
            continue
        picked.append((t, frame, persons))
        hashes.append(ph)
        if len(picked) == k:
            break
    known[:] = hashes
    return picked


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--videos-per-query", type=int, default=8)
    ap.add_argument("--frames-per-video", type=int, default=4)
    ap.add_argument("--every", type=float, default=2.0, help="seconds between sampled frames")
    ap.add_argument("--max-minutes", type=float, default=20)
    ap.add_argument("--min-sharpness", type=float, default=60, help="variance of the Laplacian; lower = blurrier")
    ap.add_argument("--weights", default=str(WEIGHTS))
    args = ap.parse_args(argv)
    if not Path(args.weights).exists():
        sys.exit(f"{args.weights} not found — run  python -m telecomsafe.weights e2")
    from ultralytics import YOLO

    model = YOLO(args.weights)
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    seen = set(SEEN.read_text(encoding="utf-8").split()) if SEEN.exists() else set()
    rows = read_manifest()
    known = [h for r in rows if r["status"] == "candidate" and (h := _phash(OUT / r["file"])) is not None]
    for query, domain in VIDEO_QUERIES.items():
        try:
            entries = search(query, args.videos_per_query * 2)
        except Exception as e:  # yt-dlp raises many error types
            print(f"  ✗ search {query!r}: {e}", file=sys.stderr)
            continue
        entries = [e for e in entries if e["id"] not in seen
                   and 10 <= (e.get("duration") or 0) <= args.max_minutes * 60][: args.videos_per_query]
        print(f"  {query!r}: {len(entries)} new videos")
        for e in entries:
            vid = e["id"]
            seen.add(vid)
            try:
                got = fetch(vid)
            except Exception as err:
                print(f"    ✗ {vid}: {err}", file=sys.stderr)
                continue
            if got is None:
                print(f"    - {vid}: not Creative Commons, skipped")
                continue
            info, path = got
            frames = pick_frames(model, path, args.every, args.frames_per_video, args.min_sharpness, known)
            path.unlink(missing_ok=True)
            creator = info.get("uploader") or info.get("channel") or ""
            for t, frame, persons in frames:
                sec = int(t)
                name = f"youtube_{vid}_t{sec:04d}.jpg"
                cv2.imwrite(str(OUT / name), frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
                stamp = f"{sec // 60}:{sec % 60:02d}"
                rows.append({
                    "file": name, "provider": "youtube", "source_id": f"{vid}_t{sec}", "title": info.get("title", ""),
                    "creator": creator, "licence": "by", "licence_version": "3.0",
                    "licence_url": "https://creativecommons.org/licenses/by/3.0/",
                    "landing_url": f"https://www.youtube.com/watch?v={vid}&t={sec}s", "image_url": "",
                    "attribution": f'Frame at {stamp} from "{info.get("title", "")}" by {creator}, CC BY 3.0, via YouTube',
                    "query": query, "domain": domain, "status": "candidate",
                    "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                })
            print(f"    ✓ {vid}: {len(frames)} frames  ({info.get('title', '')[:60]})")
            write_manifest(rows)
            SEEN.write_text("\n".join(sorted(seen)), encoding="utf-8")
    SEEN.write_text("\n".join(sorted(seen)), encoding="utf-8")
    shutil.rmtree(TMP, ignore_errors=True)
    print(f"{sum(r['status'] == 'candidate' for r in rows)} candidates in {OUT}")


if __name__ == "__main__":
    main()
