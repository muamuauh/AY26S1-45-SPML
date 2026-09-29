"""Annotate TelecomEval in a local Label Studio.

    python -m telecomsafe.data.labelstudio serve    # start Label Studio (own conda env "labelstudio")
    python -m telecomsafe.data.labelstudio push     # create the project, import images + pre-labels
    python -m telecomsafe.data.labelstudio pull     # export finished annotations → data/raw/telecom_eval/

Credentials (LABEL_STUDIO_*) come from .env; `serve` creates that account on first start.
Pre-labels are read from data/raw/t3_candidates/prelabels/ (see telecomsafe.data.pseudo_label).
Images are served from disk (local-files storage), nothing is uploaded or copied.

Annotation rules: follow the criteria in configs/taxonomy.yaml (also in data/README.md).
Every pre-label must be checked; add missing boxes (harness and machinery are never
pre-labelled). "Skip" an image that turns out to be unusable — skipped images are
left out of TelecomEval.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from xml.sax.saxutils import quoteattr

import requests
from PIL import Image

from telecomsafe.env import load_env
from telecomsafe.paths import IMAGE_SUFFIXES, INTERIM, RAW, class_names, load_taxonomy

CANDIDATES = RAW / "t3_candidates"
EVAL_DIR = RAW / "telecom_eval"
STATE = INTERIM / "labelstudio_project.json"
LS_DATA = INTERIM / "labelstudio"
PROJECT_TITLE = "TelecomEval"
COLORS = ["#2a78d6", "#1baf7a", "#eb6834", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948", "#52514e"]


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"{name} is empty — fill it in .env (template: .env.example)")
    return value


def label_config() -> str:
    labels = "\n".join(
        f'    <Label value="{c["name"]}" background="{COLORS[i % len(COLORS)]}" hint={quoteattr(c.get("criterion", ""))}/>'
        for i, c in enumerate(load_taxonomy())
    )
    return (
        "<View>\n"
        '  <Image name="image" value="$image" zoom="true" zoomControl="true"/>\n'
        '  <RectangleLabels name="label" toName="image" strokeWidth="2">\n'
        f"{labels}\n"
        "  </RectangleLabels>\n"
        "</View>"
    )


class Client:
    def __init__(self):
        self.url = os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080").rstrip("/")
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Token {env('LABEL_STUDIO_TOKEN')}"

    def call(self, method: str, path: str, **kw):
        try:
            r = self.s.request(method, f"{self.url}{path}", timeout=120, **kw)
        except requests.ConnectionError:
            sys.exit(f"Label Studio is not running at {self.url} — start it with: python -m telecomsafe.data.labelstudio serve")
        if not r.ok:
            sys.exit(f"{method} {path} → HTTP {r.status_code}: {r.text[:300]}")
        return r.json() if r.content else None


# ---------------------------------------------------------------- serve
def label_studio_exe() -> Path:
    exe = Path.home() / ".conda" / "envs" / "labelstudio" / "Scripts" / "label-studio.exe"
    if not exe.exists():
        sys.exit("Label Studio not installed. Run:\n  conda create -n labelstudio python=3.12 -y\n"
                 "  conda run -n labelstudio pip install label-studio")
    return exe


def serve() -> None:
    port = urlparse(os.environ.get("LABEL_STUDIO_URL", "http://localhost:8080")).port or 8080
    child_env = {
        **os.environ,
        "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED": "true",
        "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT": str(RAW),
        "LABEL_STUDIO_BASE_DATA_DIR": str(LS_DATA),
        "LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN": "true",
        "PYTHONIOENCODING": "utf-8",
    }
    LS_DATA.mkdir(parents=True, exist_ok=True)
    cmd = [str(label_studio_exe()), "start", "--no-browser", "--port", str(port),
           "--username", env("LABEL_STUDIO_USERNAME"), "--password", env("LABEL_STUDIO_PASSWORD"),
           "--user-token", env("LABEL_STUDIO_TOKEN")]
    print(f"Label Studio → http://localhost:{port}  (log in with LABEL_STUDIO_USERNAME / PASSWORD from .env; Ctrl+C to stop)")
    subprocess.run(cmd, env=child_env, check=False)


# ---------------------------------------------------------------- push
def to_prediction(dets: list, w: int, h: int) -> dict:
    result = [{
        "from_name": "label", "to_name": "image", "type": "rectanglelabels",
        "original_width": w, "original_height": h, "image_rotation": 0,
        "value": {"x": 100 * x1 / w, "y": 100 * y1 / h, "width": 100 * (x2 - x1) / w,
                  "height": 100 * (y2 - y1) / h, "rotation": 0, "rectanglelabels": [cls]},
        "score": conf,
    } for cls, x1, y1, x2, y2, conf in dets]
    return {"model_version": "prelabel", "score": min((r["score"] for r in result), default=0), "result": result}


def read_prelabels(image: Path, w: int, h: int) -> list:
    txt = CANDIDATES / "prelabels" / f"{image.stem}.txt"
    if not txt.exists():
        return []
    names = class_names()
    dets = []
    for line in txt.read_text(encoding="utf-8").splitlines():
        cid, cx, cy, bw, bh = line.split()[:5]
        cx, cy, bw, bh = float(cx) * w, float(cy) * h, float(bw) * w, float(bh) * h
        dets.append((names[int(cid)], cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, 1.0))
    return dets


def push() -> None:
    if STATE.exists():
        sys.exit(f"project already pushed ({STATE}); delete that file only if you want a second project")
    images = sorted(p for p in (CANDIDATES / "images").iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    if not images:
        sys.exit("no candidate images — run telecomsafe.data.collect_open first")
    c = Client()
    project = c.call("POST", "/api/projects", json={
        "title": PROJECT_TITLE, "label_config": label_config(),
        "description": "TelecomEval: annotate by the criteria in configs/taxonomy.yaml; skip unusable images.",
        "show_skip_button": True,
    })
    c.call("POST", "/api/storages/localfiles", json={
        "project": project["id"], "title": "t3 candidates", "path": str(CANDIDATES / "images"),
        "regex_filter": r".*\.(jpe?g|png|webp)$", "use_blob_urls": True,
    })
    tasks, n_boxes = [], 0
    for img in images:
        with Image.open(img) as im:
            w, h = im.size
        rel = img.relative_to(RAW).as_posix()
        dets = read_prelabels(img, w, h)
        n_boxes += len(dets)
        task = {"data": {"image": f"/data/local-files/?d={quote(rel)}"}}
        if dets:
            task["predictions"] = [to_prediction(dets, w, h)]
        tasks.append(task)
    c.call("POST", f"/api/projects/{project['id']}/import", json=tasks)
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({"project_id": project["id"]}), encoding="utf-8")
    print(f"project {project['id']}: {len(tasks)} images, {n_boxes} pre-label boxes → {c.url}/projects/{project['id']}")


# ---------------------------------------------------------------- pull
def yolo_line(value: dict, names: list[str]) -> str | None:
    label = value["rectanglelabels"][0]
    if label not in names:
        return None
    x, y, w, h = (value[k] / 100 for k in ("x", "y", "width", "height"))
    return f"{names.index(label)} {x + w / 2:.6f} {y + h / 2:.6f} {w:.6f} {h:.6f}"


def convert(tasks: list[dict], names: list[str], out: Path) -> dict[str, int]:
    """Write finished annotations as YOLO; returns counts. Skipped/unannotated tasks are left out."""
    counts = {"images": 0, "boxes": 0, "skipped": 0, "unannotated": 0}
    if out.exists():
        shutil.rmtree(out)
    (out / "images").mkdir(parents=True)
    (out / "labels").mkdir(parents=True)
    for t in tasks:
        done = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if not done:
            counts["skipped" if t.get("annotations") else "unannotated"] += 1
            continue
        latest = max(done, key=lambda a: a.get("updated_at") or a.get("created_at") or "")
        rel = parse_qs(urlparse(t["data"]["image"]).query)["d"][0]
        src = RAW / rel
        shutil.copy2(src, out / "images" / src.name)
        lines = [ln for r in latest["result"] if r.get("type") == "rectanglelabels" and (ln := yolo_line(r["value"], names))]
        (out / "labels" / f"{src.stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        counts["images"] += 1
        counts["boxes"] += len(lines)
    return counts


def pull() -> None:
    if not STATE.exists():
        sys.exit("no project yet — run push first")
    pid = json.loads(STATE.read_text(encoding="utf-8"))["project_id"]
    tasks = Client().call("GET", f"/api/projects/{pid}/export", params={"exportType": "JSON", "download_all_tasks": "true"})
    counts = convert(tasks, class_names(), EVAL_DIR)
    print(f"TelecomEval → {EVAL_DIR}: {counts}")
    if counts["unannotated"]:
        print(f"  ! {counts['unannotated']} images are not annotated yet — finish them before freezing")
    else:
        print("  next: review, then  python -m telecomsafe.data.freeze_eval --create")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["serve", "push", "pull", "config"])
    args = ap.parse_args(argv)
    load_env()
    {"serve": serve, "push": push, "pull": pull, "config": lambda: print(label_config())}[args.command]()


if __name__ == "__main__":
    main()
