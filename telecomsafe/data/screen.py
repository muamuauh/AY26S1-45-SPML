"""Score TelecomEval candidates and review them in the browser.

    python -m telecomsafe.data.screen                       # score new candidates, write review.html
    python -m telecomsafe.data.screen --apply <decisions.json>   # file exported from review.html
    python -m telecomsafe.data.screen --summary             # counts per subset and scene

Scoring (written to data/licence_manifest.csv):
  persons     people with a visible head, counted by the E2 detector
  scene       the closest of the CLIP scene prompts below
  clip_score  probability mass CLIP puts on the work scenes (0-1)

review.html (data/raw/t3_candidates/) shows the candidates best first. Mark each one
Telecom (1), Near (2: power-line work, reported as a separate subset) or Reject (X),
then Export and pass the downloaded file to --apply. Rejected images are moved to
data/raw/t3_candidates/rejected/, never deleted. Candidates in which nobody is visible
and that CLIP does not see as a work scene (score < AUTO_REJECT) start out marked Reject;
override them if needed.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from collections import Counter
from pathlib import Path

from telecomsafe.data.collect_open import OUT, read_manifest, write_manifest
from telecomsafe.data.collect_video import WEIGHTS, visible_people

REVIEW = OUT.parent / "review.html"
AUTO_REJECT = 0.5  # every image kept in the first manual screening that had nobody detected scored >= 0.99
REJECTED = OUT.parent / "rejected"
WORK_SCENES = {
    "tower": "a photo of a worker climbing a telecommunication tower",
    "rooftop": "a photo of a technician installing antennas on a rooftop",
    "trench": "a photo of workers laying cables in a trench by the road",
    "manhole": "a photo of a worker in a manhole working on underground cables",
    "cabinet": "a photo of a technician working on a roadside telecom cabinet",
    "splicing": "a photo of a technician splicing fiber optic cables",
    "pole": "a photo of a worker climbing a utility pole",
    "bucket_truck": "a photo of a worker in the bucket of a bucket truck",
}
OTHER_SCENES = {
    "no_people": "a photo of a tower or antenna with no people",
    "illustration": "a diagram, drawing or illustration",
    "portrait": "a portrait photo of a person posing for the camera",
    "event": "a photo of people at a meeting, ceremony or press event",
    "building_site": "a photo of construction workers on a building site",
    "landscape": "a landscape or city skyline",
}


def score(rows: list[dict], rescore: bool = False) -> int:
    import open_clip
    import torch
    from PIL import Image
    from ultralytics import YOLO

    todo = [r for r in rows if r["status"] == "candidate" and (rescore or r.get("clip_score", "") == "")
            and (OUT / r["file"]).exists()]
    if not todo:
        return 0
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k", device=device)
    model.eval()
    names = [*WORK_SCENES, *OTHER_SCENES]
    with torch.no_grad():
        text = model.encode_text(open_clip.get_tokenizer("ViT-B-32")([*WORK_SCENES.values(), *OTHER_SCENES.values()]).to(device))
        text /= text.norm(dim=-1, keepdim=True)
    detector = YOLO(str(WEIGHTS))
    for i in range(0, len(todo), 32):
        chunk, images = [], []
        for r in todo[i : i + 32]:
            try:
                with Image.open(OUT / r["file"]) as im:
                    images.append(im.convert("RGB"))
                chunk.append(r)
            except OSError:  # truncated or not an image: starts out rejected
                r.update(persons=0, scene="unreadable", clip_score="0.000")
        if not chunk:
            continue
        with torch.no_grad():
            feats = model.encode_image(torch.stack([preprocess(im) for im in images]).to(device))
            feats /= feats.norm(dim=-1, keepdim=True)
            probs = (100 * feats @ text.T).softmax(dim=-1).cpu()
        for r, im, p, det in zip(chunk, images, probs, detector.predict(images, conf=0.3, verbose=False)):
            r["persons"] = visible_people(det, im.height)
            r["scene"] = names[int(p.argmax())]
            r["clip_score"] = f"{float(p[: len(WORK_SCENES)].sum()):.3f}"
        print(f"  scored {min(i + 32, len(todo))}/{len(todo)}")
    return len(todo)


def review_page(rows: list[dict]) -> str:
    items = []
    for r in rows:
        if r["status"] != "candidate" or not (OUT / r["file"]).exists():
            continue
        persons = int(r.get("persons") or 0)
        auto = not r.get("subset") and persons == 0 and float(r.get("clip_score") or 0) < AUTO_REJECT
        items.append({
            "file": r["file"], "title": r["title"][:120], "provider": r["provider"], "licence": r["licence"],
            "landing": r["landing_url"], "domain": r.get("domain") or "telecom", "persons": persons,
            "scene": r.get("scene", ""), "score": float(r.get("clip_score") or 0),
            "state": r.get("subset") or ("reject" if auto else ""),
            "auto": auto, "decided": bool(r.get("subset")),
        })
    items.sort(key=lambda x: (x["decided"], x["auto"], -x["score"]))
    data = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    return PAGE.replace("__DATA__", data).replace("__COUNT__", html.escape(str(len(items))))


def apply(path: Path) -> None:
    decisions = json.loads(path.read_text(encoding="utf-8"))
    rows = read_manifest()
    REJECTED.mkdir(parents=True, exist_ok=True)
    n = Counter()
    for r in rows:
        d = decisions.get(r["file"])
        if r["status"] != "candidate" or d not in {"telecom", "near", "reject"}:
            continue
        if d == "reject":
            src = OUT / r["file"]
            if src.exists():
                shutil.move(str(src), REJECTED / r["file"])
            r["status"], r["subset"] = "rejected", ""
        else:
            r["subset"] = d
        n[d] += 1
    write_manifest(rows)
    print(f"applied: {dict(n)}  (rejected images moved to {REJECTED})")
    summary(rows)


def summary(rows: list[dict] | None = None) -> None:
    rows = rows if rows is not None else read_manifest()
    cand = [r for r in rows if r["status"] == "candidate"]
    subsets = Counter(r.get("subset") or "pending" for r in cand)
    print(f"candidates: {len(cand)}  →  telecom {subsets['telecom']} · near {subsets['near']} · not reviewed {subsets['pending']}")
    kept = [r for r in cand if r.get("subset")]
    if kept:
        print("kept by scene:", dict(Counter(r.get("scene") or "?" for r in kept).most_common()))
        print("kept by provider:", dict(Counter(r["provider"] for r in kept).most_common()))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", type=Path, help="decisions JSON exported from review.html")
    ap.add_argument("--rescore", action="store_true", help="score every candidate again")
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args(argv)
    if args.apply:
        return apply(args.apply)
    if args.summary:
        return summary()
    rows = read_manifest()
    n = score(rows, args.rescore)
    if n:
        write_manifest(rows)
    REVIEW.write_text(review_page(rows), encoding="utf-8")
    print(f"scored {n} new candidates; open {REVIEW}")
    summary(rows)


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TelecomEval review</title>
<style>
:root{--bg:#f7f7f5;--card:#fff;--ink:#141413;--muted:#6b6a66;--line:#e3e2de;--tel:#2a78d6;--near:#1baf7a;--rej:#d03b3b;--focus:#eb6834}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#21211f;--ink:#ecebe7;--muted:#9c9b96;--line:#34332f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center}
h1{font-size:16px;margin:0 8px 0 0}.counts span{margin-right:12px;font-variant-numeric:tabular-nums}
.filters button,.export{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer;font:inherit}
.filters button[aria-pressed=true]{border-color:var(--ink)}.export{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.help{color:var(--muted);font-size:12px;flex-basis:100%}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;padding:16px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;overflow:hidden;display:flex;flex-direction:column}
.card.focus{border-color:var(--focus)}.card[data-state=telecom]{border-color:var(--tel)}.card[data-state=near]{border-color:var(--near)}.card[data-state=reject]{opacity:.55}
.card.focus[data-state]{outline:3px solid var(--focus);outline-offset:-3px}
.card img{width:100%;aspect-ratio:4/3;object-fit:contain;background:#0001;cursor:zoom-in}
.meta{padding:8px 10px;font-size:12px;color:var(--muted);flex:1}.meta b{color:var(--ink);font-weight:600}
.meta a{color:inherit}.title{color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.btns{display:grid;grid-template-columns:1fr 1fr 1fr;border-top:1px solid var(--line)}
.btns button{border:0;background:none;color:var(--ink);padding:8px;cursor:pointer;font:inherit}
.btns button+button{border-left:1px solid var(--line)}
.btns button.on[data-v=telecom]{background:var(--tel);color:#fff}.btns button.on[data-v=near]{background:var(--near);color:#fff}.btns button.on[data-v=reject]{background:var(--rej);color:#fff}
.tag{display:inline-block;padding:0 6px;border-radius:4px;border:1px solid var(--line);margin-right:4px}
dialog{border:0;padding:0;background:#000;max-width:96vw;max-height:96vh}dialog img{max-width:96vw;max-height:96vh;display:block}
</style></head><body>
<header>
  <h1>TelecomEval review · __COUNT__ candidates</h1>
  <div class="counts" id="counts"></div>
  <div class="filters" id="filters"></div>
  <button class="export" id="export">Export decisions</button>
  <div class="help"><b>Telecom</b>: people working on a telecom site — tower, rooftop antennas, trench, manhole, street cabinet, aerial cable. <b>Near</b>: power-line work (poles, bucket trucks). <b>Reject</b>: no one working, indoor labs / offices / classrooms, posed portraits, illustrations, near-duplicates. Keys: ← → move · 1 Telecom · 2 Near · X Reject · 0 clear · Space enlarge. Decisions are kept in this browser until exported; then run <code>python -m telecomsafe.data.screen --apply &lt;file&gt;</code>.</div>
</header>
<main id="grid"></main>
<dialog id="zoom"><img alt=""></dialog>
<script>
const items = __DATA__;
const KEY = "telecomeval-review";
let saved = {}; try { saved = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
for (const it of items) if (it.file in saved) it.state = saved[it.file];
const LABEL = {telecom: "Telecom", near: "Near", reject: "Reject"};
let filter = "pending", focus = 0, visible = [];
const grid = document.getElementById("grid");
function persist() { const o = {}; for (const it of items) if (it.state) o[it.file] = it.state; try { localStorage.setItem(KEY, JSON.stringify(o)); } catch (e) {} }
function counts() {
  const c = {pending: 0, telecom: 0, near: 0, reject: 0, all: items.length};
  for (const it of items) c[it.state || "pending"]++;
  document.getElementById("counts").innerHTML = `<span>Telecom <b>${c.telecom}</b></span><span>Near <b>${c.near}</b></span><span>Reject <b>${c.reject}</b></span><span>Pending <b>${c.pending}</b></span>`;
  document.getElementById("filters").innerHTML = ["pending", "telecom", "near", "reject", "all"].map(f =>
    `<button data-f="${f}" aria-pressed="${f === filter}">${f[0].toUpperCase() + f.slice(1)} (${c[f]})</button>`).join(" ");
}
function esc(s) { return String(s).replace(/[&<>"]/g, ch => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[ch])); }
function card(it, i) {
  return `<article class="card" data-i="${i}" data-state="${it.state || ""}">
    <img loading="lazy" src="images/${encodeURIComponent(it.file)}" alt="">
    <div class="meta"><div class="title" title="${esc(it.title)}">${esc(it.title) || "(untitled)"}</div>
      <span class="tag" title="people whose head is visible, counted by the E2 detector">${it.persons} with head</span><span class="tag">${esc(it.scene)}</span><span class="tag">score ${it.score.toFixed(2)}</span>${it.domain === "near" ? '<span class="tag">near query</span>' : ""}${it.auto && it.state === "reject" ? '<span class="tag">auto: no person, low score</span>' : ""}
      <div>${esc(it.provider)} · ${esc(it.licence)} · <a href="${esc(it.landing)}" target="_blank" rel="noopener">source</a></div></div>
    <div class="btns">${["telecom", "near", "reject"].map(v => `<button data-v="${v}" class="${it.state === v ? "on" : ""}">${LABEL[v]}</button>`).join("")}</div>
  </article>`;
}
function render() {
  visible = items.map((it, i) => [it, i]).filter(([it]) => filter === "all" || (it.state || "pending") === filter);
  grid.innerHTML = visible.map(([it, i]) => card(it, i)).join("") || "<p>Nothing here.</p>";
  focus = Math.min(focus, Math.max(visible.length - 1, 0)); mark(); counts();
}
function mark() { grid.querySelectorAll(".card").forEach((c, k) => c.classList.toggle("focus", k === focus)); }
function set(i, v) {
  const it = items[i]; it.state = it.state === v ? "" : v; it.auto = false; persist();
  const el = grid.querySelector(`.card[data-i="${i}"]`);
  if (el) { el.dataset.state = it.state; el.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === it.state)); }
  counts();
}
grid.addEventListener("click", e => {
  const c = e.target.closest(".card"); if (!c) return;
  focus = [...grid.children].indexOf(c); mark();
  if (e.target.dataset.v) set(+c.dataset.i, e.target.dataset.v);
  else if (e.target.tagName === "IMG") zoom(e.target.src);
});
document.getElementById("filters").addEventListener("click", e => { if (e.target.dataset.f) { filter = e.target.dataset.f; focus = 0; render(); } });
const dlg = document.getElementById("zoom");
function zoom(src) { dlg.querySelector("img").src = src; dlg.showModal(); }
dlg.addEventListener("click", () => dlg.close());
document.addEventListener("keydown", e => {
  if (dlg.open) { if (e.key === " " || e.key === "Escape") { e.preventDefault(); dlg.close(); } return; }
  const cards = grid.querySelectorAll(".card"); if (!cards.length) return;
  const i = +cards[focus].dataset.i, map = {"1": "telecom", "2": "near", "x": "reject", "X": "reject"};
  if (e.key === "ArrowRight" || e.key === "ArrowDown") focus = Math.min(focus + 1, cards.length - 1);
  else if (e.key === "ArrowLeft" || e.key === "ArrowUp") focus = Math.max(focus - 1, 0);
  else if (map[e.key]) { set(i, map[e.key]); if (items[i].state) focus = Math.min(focus + 1, cards.length - 1); }
  else if (e.key === "0") { items[i].state = ""; persist(); render(); return; }
  else if (e.key === " ") { e.preventDefault(); zoom(cards[focus].querySelector("img").src); return; }
  else return;
  e.preventDefault(); mark(); cards[focus].scrollIntoView({block: "nearest"});
});
document.getElementById("export").addEventListener("click", () => {
  const o = {}; for (const it of items) if (it.state) o[it.file] = it.state;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(o, null, 1)], {type: "application/json"}));
  a.download = "telecom_eval_decisions.json"; a.click();
});
render();
</script></body></html>
"""

if __name__ == "__main__":
    main()
