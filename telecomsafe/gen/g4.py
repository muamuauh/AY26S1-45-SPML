"""G4: human spot check of a generated batch in the browser.

    python -m telecomsafe.gen.g4 page telecom_scene_transfer [--n 100] [--seed 0]   # writes data/synth/g4/<id>.html
    python -m telecomsafe.gen.g4 apply telecom_scene_transfer <decisions.json>      # file exported from the page

The page shows a random sample of the accepted images (data/synth/filtered/<id>/) with their labels
drawn on top (B toggles them). Mark each image Natural (1) or Unnatural (2): unnatural means a person
looks pasted, floats, has the wrong size for the scene, or is blurred or deformed, or a box no longer fits.
Export the decisions and pass the file to `apply`: it reports the share rated natural with a 95% Wilson
interval, writes data/synth/g4/<id>_ratings.json, and moves the unnatural images to
data/synth/rejected/<id>/ (reason "g4: unnatural"); they are never deleted.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from datetime import date
from pathlib import Path

from telecomsafe.gen.common import SYNTH, record_paths, reject_record

G4 = SYNTH / "g4"


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k successes out of n."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def sample(sid: str, n: int, seed: int) -> list[Path]:
    """n random accepted records (their stems) of a scenario, reproducible for a seed."""
    stems = sorted(p.with_name(p.name[:-len(".json")]) for p in (SYNTH / "filtered" / sid).glob("*.json"))
    return random.Random(seed).sample(stems, min(n, len(stems)))


def items(sid: str, stems: list[Path]) -> list[dict]:
    from PIL import Image

    out = []
    for stem in stems:
        paths = record_paths(stem)
        meta = json.loads(paths[".json"].read_text(encoding="utf-8"))
        with Image.open(paths[".jpg"]) as im:
            w, h = im.size
        out.append({"name": stem.name, "src": f"../filtered/{sid}/{paths['.jpg'].name}", "w": w, "h": h,
                    "base": meta.get("base", ""), "background": Path(meta.get("background", {}).get("file", "")).name,
                    "labels": [[lb["cls"], lb["x1"], lb["y1"], lb["x2"], lb["y2"]] for lb in meta.get("labels", [])]})
    return out


def page(sid: str, n: int, seed: int) -> Path:
    stems = sample(sid, n, seed)
    G4.mkdir(parents=True, exist_ok=True)
    out = G4 / f"{sid}.html"
    data = json.dumps(items(sid, stems), ensure_ascii=False)
    out.write_text(PAGE.replace("__SID__", sid).replace("__COUNT__", str(len(stems))).replace("__DATA__", data),
                   encoding="utf-8")
    (G4 / f"{sid}_sample.json").write_text(json.dumps({"seed": seed, "names": [s.name for s in stems]}, indent=1),
                                           encoding="utf-8")
    return out


def apply(sid: str, decisions_file: Path) -> dict:
    decisions = json.loads(decisions_file.read_text(encoding="utf-8"))
    rated = {k: v for k, v in decisions.items() if v in ("natural", "unnatural")}
    k = sum(v == "natural" for v in rated.values())
    lo, hi = wilson(k, len(rated))
    filtered, rejected = SYNTH / "filtered" / sid, SYNTH / "rejected" / sid
    moved = 0
    for name, v in rated.items():
        if v == "unnatural" and record_paths(filtered / name)[".json"].exists():
            reject_record(filtered / name, rejected, "g4: unnatural")
            moved += 1
    remaining = len(list(filtered.glob("*.json")))
    result = {"scenario": sid, "date": date.today().isoformat(), "rated": len(rated), "natural": k,
              "rate": round(k / len(rated), 3) if rated else None, "ci95": [round(lo, 3), round(hi, 3)],
              "moved_to_rejected": moved, "remaining_accepted": remaining, "decisions": rated}
    G4.mkdir(parents=True, exist_ok=True)
    (G4 / f"{sid}_ratings.json").write_text(json.dumps(result, indent=1, ensure_ascii=False), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["page", "apply"])
    ap.add_argument("scenario")
    ap.add_argument("decisions", nargs="?", type=Path)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args(argv)
    if args.command == "page":
        print(f"open {page(args.scenario, args.n, args.seed)}")
        return
    if args.decisions is None:
        ap.error("apply needs the decisions file exported from the page")
    r = apply(args.scenario, args.decisions)
    print(f"{r['scenario']}: {r['natural']}/{r['rated']} natural = {r['rate']:.0%} "
          f"(95% CI {r['ci95'][0]:.0%}–{r['ci95'][1]:.0%}); {r['moved_to_rejected']} moved to rejected, "
          f"{r['remaining_accepted']} accepted remain")


PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>G4 · __SID__</title>
<style>
:root{--bg:#f7f7f5;--card:#fff;--ink:#141413;--muted:#6b6a66;--line:#e3e2de;--ok:#1baf7a;--bad:#d03b3b;--focus:#eb6834}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#21211f;--ink:#ecebe7;--muted:#9c9b96;--line:#34332f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center}
h1{font-size:16px;margin:0 8px 0 0}.counts span{margin-right:12px;font-variant-numeric:tabular-nums}
button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:6px;padding:4px 10px;cursor:pointer;font:inherit}
.export{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.help{color:var(--muted);font-size:12px;flex-basis:100%}
main{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;padding:16px}
.card{background:var(--card);border:2px solid var(--line);border-radius:8px;overflow:hidden;display:flex;flex-direction:column}
.card[data-state=natural]{border-color:var(--ok)}.card[data-state=unnatural]{border-color:var(--bad)}
.card.focus{outline:3px solid var(--focus);outline-offset:-3px}
.pic{position:relative;cursor:zoom-in;background:#0001}.pic img{width:100%;display:block}
.pic svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}
body.nobox .pic svg{display:none}
.meta{padding:6px 10px;font-size:12px;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.btns{display:grid;grid-template-columns:1fr 1fr;border-top:1px solid var(--line)}
.btns button{border:0;border-radius:0;background:none;padding:8px}.btns button+button{border-left:1px solid var(--line)}
.btns button.on[data-v=natural]{background:var(--ok);color:#fff}.btns button.on[data-v=unnatural]{background:var(--bad);color:#fff}
dialog{border:0;padding:0;background:#000;max-width:96vw;max-height:96vh}dialog .pic{cursor:zoom-out}dialog img{max-width:96vw;max-height:96vh;width:auto}
</style></head><body>
<header>
  <h1>G4 spot check · __SID__ · __COUNT__ images</h1>
  <div class="counts" id="counts"></div>
  <button id="boxes">Hide boxes (B)</button>
  <button class="export" id="export">Export decisions</button>
  <div class="help"><b>Natural</b>: could pass for a real photo at a glance. <b>Unnatural</b>: the person looks pasted or floats, is the wrong size for the scene, is blurred or deformed, or a box no longer fits the person or their PPE. Keys: ← → move · 1 Natural · 2 Unnatural · 0 clear · Space enlarge · B boxes. Decisions stay in this browser until exported; then run <code>python -m telecomsafe.gen.g4 apply __SID__ &lt;file&gt;</code>.</div>
</header>
<main id="grid"></main>
<dialog id="zoom"></dialog>
<script>
const items = __DATA__;
const KEY = "g4-__SID__";
const COLORS = {person: "#2a78d6", helmet: "#1baf7a", no_helmet: "#d03b3b", vest: "#e8a10c", no_vest: "#c2410c", harness: "#8b5cf6"};
let saved = {}; try { saved = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) {}
for (const it of items) it.state = saved[it.name] || "";
let focus = 0;
const grid = document.getElementById("grid"), dlg = document.getElementById("zoom");
function persist() { const o = {}; for (const it of items) if (it.state) o[it.name] = it.state; try { localStorage.setItem(KEY, JSON.stringify(o)); } catch (e) {} }
function esc(s) { return String(s).replace(/[&<>"]/g, ch => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[ch])); }
function pic(it) {
  const sw = Math.max(2, it.h / 300);
  const boxes = it.labels.map(([c, x1, y1, x2, y2]) => `<rect x="${x1}" y="${y1}" width="${x2 - x1}" height="${y2 - y1}" fill="none" stroke="${COLORS[c] || "#fff"}" stroke-width="${sw}"><title>${c}</title></rect>`).join("");
  return `<div class="pic"><img loading="lazy" src="${esc(it.src)}" alt=""><svg viewBox="0 0 ${it.w} ${it.h}" preserveAspectRatio="none">${boxes}</svg></div>`;
}
function counts() {
  const c = {natural: 0, unnatural: 0, pending: 0};
  for (const it of items) c[it.state || "pending"]++;
  const rated = c.natural + c.unnatural;
  document.getElementById("counts").innerHTML = `<span>Natural <b>${c.natural}</b></span><span>Unnatural <b>${c.unnatural}</b></span><span>Pending <b>${c.pending}</b></span>` + (rated ? `<span>Natural rate <b>${Math.round(100 * c.natural / rated)}%</b></span>` : "");
}
function render() {
  grid.innerHTML = items.map((it, i) => `<article class="card" data-i="${i}" data-state="${it.state}">${pic(it)}
    <div class="meta" title="${esc(it.name)}">${i + 1}. ${esc(it.base)} → ${esc(it.background)}</div>
    <div class="btns">${["natural", "unnatural"].map(v => `<button data-v="${v}" class="${it.state === v ? "on" : ""}">${v[0].toUpperCase() + v.slice(1)}</button>`).join("")}</div></article>`).join("");
  mark(); counts();
}
function mark() { grid.querySelectorAll(".card").forEach((c, k) => c.classList.toggle("focus", k === focus)); }
function set(i, v) {
  const it = items[i]; it.state = it.state === v ? "" : v; persist();
  const el = grid.children[i]; el.dataset.state = it.state;
  el.querySelectorAll(".btns button").forEach(b => b.classList.toggle("on", b.dataset.v === it.state)); counts();
}
function zoom(i) { dlg.innerHTML = pic(items[i]); dlg.showModal(); }
grid.addEventListener("click", e => {
  const c = e.target.closest(".card"); if (!c) return;
  focus = +c.dataset.i; mark();
  if (e.target.dataset.v) set(focus, e.target.dataset.v); else if (e.target.closest(".pic")) zoom(focus);
});
dlg.addEventListener("click", () => dlg.close());
function toggleBoxes() { document.body.classList.toggle("nobox"); document.getElementById("boxes").textContent = (document.body.classList.contains("nobox") ? "Show" : "Hide") + " boxes (B)"; }
document.getElementById("boxes").addEventListener("click", toggleBoxes);
document.addEventListener("keydown", e => {
  if (e.key === "b" || e.key === "B") { toggleBoxes(); return; }
  if (dlg.open) { if (e.key === " " || e.key === "Escape") { e.preventDefault(); dlg.close(); } return; }
  const map = {"1": "natural", "2": "unnatural"};
  if (e.key === "ArrowRight" || e.key === "ArrowDown") focus = Math.min(focus + 1, items.length - 1);
  else if (e.key === "ArrowLeft" || e.key === "ArrowUp") focus = Math.max(focus - 1, 0);
  else if (map[e.key]) { set(focus, map[e.key]); if (items[focus].state) focus = Math.min(focus + 1, items.length - 1); }
  else if (e.key === "0") { items[focus].state = ""; persist(); render(); return; }
  else if (e.key === " ") { e.preventDefault(); zoom(focus); return; }
  else return;
  e.preventDefault(); mark(); grid.children[focus].scrollIntoView({block: "nearest"});
});
document.getElementById("export").addEventListener("click", () => {
  const o = {}; for (const it of items) if (it.state) o[it.name] = it.state;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(o, null, 1)], {type: "application/json"}));
  a.download = "g4___SID__.json"; a.click();
});
render();
</script></body></html>
"""

if __name__ == "__main__":
    main()
