"""Label Studio helper shipped in the TelecomEval annotation package.

    python tools/ls_tool.py start     # start Label Studio, create the project on first run, open the browser
    python tools/ls_tool.py export    # write deliverable/annotations.json and print progress

Run through start.bat / start.command and export.bat / export.command, which set up
the Python environment first. Everything (database, login) stays inside this folder.
"""

from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import time
import webbrowser
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests

PKG = Path(__file__).resolve().parents[1]
DATA = PKG / "data"
LS_DATA = PKG / "ls_data"
STATE = LS_DATA / "package_state.json"
DELIVERABLE = PKG / "deliverable"
PORT = int(os.environ.get("TELECOMEVAL_PORT", "8089"))
URL = f"http://localhost:{PORT}"


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    state = {"username": "annotator@telecomsafe.local", "password": secrets.token_urlsafe(9),
             "token": secrets.token_hex(20), "project_id": None}
    save_state(state)
    return state


def save_state(state: dict) -> None:
    LS_DATA.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")


def api(state: dict, method: str, path: str, **kw):
    r = requests.request(method, URL + path, headers={"Authorization": f"Token {state['token']}"}, timeout=300, **kw)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json() if r.content else {}


def is_up() -> bool:
    try:
        return requests.get(URL + "/health", timeout=3).ok
    except requests.RequestException:
        return False


def launch(state: dict) -> subprocess.Popen:
    exe = Path(sys.executable).parent / ("label-studio.exe" if os.name == "nt" else "label-studio")
    env = {**os.environ,
           "LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED": "true",
           "LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT": str(PKG),
           "LABEL_STUDIO_BASE_DATA_DIR": str(LS_DATA),
           "LABEL_STUDIO_ENABLE_LEGACY_API_TOKEN": "true",
           "PYTHONIOENCODING": "utf-8"}
    LS_DATA.mkdir(parents=True, exist_ok=True)
    log = open(LS_DATA / "label_studio.log", "a", encoding="utf-8")
    proc = subprocess.Popen([str(exe), "start", "--no-browser", "--port", str(PORT),
                             "--username", state["username"], "--password", state["password"],
                             "--user-token", state["token"]], env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f"Starting Label Studio on {URL} (the first start takes a minute or two) ...", flush=True)
    for _ in range(300):
        if proc.poll() is not None:
            sys.exit(f"Label Studio stopped unexpectedly — see {LS_DATA / 'label_studio.log'}")
        if is_up():
            return proc
        time.sleep(1)
    proc.terminate()
    sys.exit(f"Label Studio did not start within 5 minutes — see {LS_DATA / 'label_studio.log'}")


def ensure_project(state: dict) -> int:
    pid = state.get("project_id")
    if pid and api(state, "GET", f"/api/projects/{pid}"):
        return pid
    meta = json.loads((DATA / "package.json").read_text(encoding="utf-8"))
    project = api(state, "POST", "/api/projects", json={
        "title": meta["title"], "description": meta["description"],
        "label_config": (DATA / "label_config.xml").read_text(encoding="utf-8"),
        "show_skip_button": True, "show_collab_predictions": True, "model_version": "prelabel",
    })
    api(state, "POST", "/api/storages/localfiles", json={
        "project": project["id"], "title": "package images", "path": str(DATA / "images"),
        "regex_filter": r".*\.(jpe?g|png|webp)$", "use_blob_urls": True,
    })
    tasks = json.loads((DATA / "tasks.json").read_text(encoding="utf-8"))
    api(state, "POST", f"/api/projects/{project['id']}/import", json=tasks)
    state["project_id"] = project["id"]
    save_state(state)
    print(f"Created the project and imported {len(tasks)} images.", flush=True)
    return project["id"]


def banner(state: dict, pid: int) -> None:
    line = "=" * 64
    print(f"\n{line}\n  Label Studio: {URL}/projects/{pid}/data\n"
          f"  Email / 邮箱:       {state['username']}\n"
          f"  Password / 密码:    {state['password']}\n"
          f"  Keep this window open while annotating; close it to stop.\n"
          f"  标注期间不要关闭本窗口；关闭即停止。\n{line}\n", flush=True)


def start() -> None:
    state = load_state()
    proc = None if is_up() else launch(state)
    pid = ensure_project(state)
    banner(state, pid)
    if not os.environ.get("TELECOMEVAL_NO_BROWSER"):
        webbrowser.open(f"{URL}/user/login/?next=/projects/{pid}/data")
    if proc is None:
        print("Label Studio was already running (another window?). This window can be closed.")
        return
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


def export() -> None:
    state = load_state()
    if not state.get("project_id"):
        sys.exit("Nothing to export yet — run start first.")
    proc = None if is_up() else launch(state)
    try:
        tasks = api(state, "GET", f"/api/projects/{state['project_id']}/export",
                    params={"exportType": "JSON", "download_all_tasks": "true"})
    finally:
        if proc is not None:
            proc.terminate()
    classes = json.loads((DATA / "package.json").read_text(encoding="utf-8"))["classes"]
    allowed = set(classes)
    status, boxes, unknown = Counter(), Counter(), Counter()
    for t in tasks:
        done = [a for a in t.get("annotations", []) if not a.get("was_cancelled")]
        if done:
            status["annotated"] += 1
            latest = max(done, key=lambda a: a.get("updated_at") or a.get("created_at") or "")
            for r in latest.get("result", []):
                for label in r.get("value", {}).get("rectanglelabels", []):
                    (boxes if label in allowed else unknown)[label] += 1
        else:
            status["skipped" if t.get("annotations") else "not done"] += 1
    DELIVERABLE.mkdir(exist_ok=True)
    out = DELIVERABLE / "annotations.json"
    text = json.dumps(tasks, ensure_ascii=False)
    out.write_text(text, encoding="utf-8")
    (DELIVERABLE / f"annotations_{datetime.now():%Y%m%d_%H%M}.json").write_text(text, encoding="utf-8")
    print(f"\nImages: {len(tasks)}  annotated {status['annotated']} · skipped {status['skipped']} · "
          f"not done {status['not done']}")
    print("Boxes per class: " + ", ".join(f"{c} {boxes[c]}" for c in classes))
    if unknown:
        print(f"!! Labels outside the guidelines: {dict(unknown)}")
    print(f"\nSaved {out}")
    if status["not done"]:
        print(f"{status['not done']} images are not done yet / 还有 {status['not done']} 张没有完成。")
    else:
        print("All images are done. Hand in deliverable/annotations.json / 全部完成，请提交 deliverable/annotations.json")


if __name__ == "__main__":
    {"start": start, "export": export}[sys.argv[1] if len(sys.argv) > 1 else "start"]()
