"""Evaluate E1/E2 on TelecomEval and write the phase 1 reports.

    python -m telecomsafe.evaluate                 # runs/phase1/{e1,e2}/weights/best.pt
    python -m telecomsafe.evaluate --exps e2 --top-k 5

Refuses to run if TelecomEval changed since it was frozen (use --skip-check only
while TelecomEval does not exist yet, e.g. to evaluate on val during development).

Outputs in reports/phase1/: <exp>_metrics.csv, <exp>_confusion_matrix.png,
per_class_ap.csv, per_class_ap.png, class_distribution.png, weak_classes.md
"""

from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

from telecomsafe.paths import PROCESSED, REPORTS, RUNS

# Categorical slots 1–2 of the validated default palette (light surface).
COLORS = {"e1": "#2a78d6", "e2": "#eb6834"}
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"


def evaluate(exp: str, data: str, split: str) -> dict | None:
    weights = RUNS / exp / "weights" / "best.pt"
    if not weights.exists():
        print(f"  ! {weights} not found — skipping {exp}", file=sys.stderr)
        return None
    from ultralytics import YOLO

    m = YOLO(str(weights)).val(data=data, split=split, project=str(RUNS / "eval"), name=exp, exist_ok=True, plots=True)
    names = m.names
    per_class = {}
    for i, cid in enumerate(m.ap_class_index):
        per_class[names[int(cid)]] = {"ap50": float(m.box.ap50[i]), "ap50_95": float(m.box.ap[i])}
    cm = Path(m.save_dir) / "confusion_matrix_normalized.png"
    if cm.exists():
        shutil.copy2(cm, REPORTS / f"{exp}_confusion_matrix.png")
    return {
        "overall": {"exp": exp, "split": split, "mAP50": m.box.map50, "mAP50-95": m.box.map,
                    "precision": m.box.mp, "recall": m.box.mr},
        "per_class": per_class,
        "names": [names[k] for k in sorted(names)],
    }


def train_instances() -> dict[str, int]:
    path = REPORTS / "dataset_stats.csv"
    if not path.exists():
        return {}
    counts: dict[str, int] = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["split"] != "train":
                continue
            for k, v in row.items():
                if k not in ("source", "split", "images", "pseudo_boxes"):
                    counts[k] = counts.get(k, 0) + int(v)
    return counts


def write_rows(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _style(ax, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=12)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.grid(axis="x" if ax.get_xlabel() else "y", color="#e4e3df", linewidth=0.8)
    ax.set_axisbelow(True)


def plot_per_class(results: dict[str, dict], classes: list[str], out: Path, eval_name: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    exps = [e for e in ("e1", "e2") if e in results]
    fig, ax = plt.subplots(figsize=(9, 4.2), facecolor=SURFACE)
    width = 0.8 / len(exps)
    for j, exp in enumerate(exps):
        vals = [results[exp]["per_class"].get(c, {}).get("ap50", 0.0) for c in classes]
        xs = [i + (j - (len(exps) - 1) / 2) * width for i in range(len(classes))]
        ax.bar(xs, vals, width=width - 0.03, color=COLORS[exp], label=exp.upper(), edgecolor=SURFACE, linewidth=2)
    for i, c in enumerate(classes):  # distinguish "AP 0" from "class absent from the evaluation set"
        if not any(c in results[e]["per_class"] for e in exps):
            ax.text(i, 0.02, "no samples", ha="center", va="bottom", rotation=90, color=MUTED, fontsize=8)
    ax.set_xticks(range(len(classes)), classes)
    ax.set_ylim(0, 1)
    ax.set_ylabel(f"AP50 on {eval_name}", color=MUTED)
    _style(ax, "Per-class AP50 — E1 (no augmentation) vs E2 (default augmentation)")
    ax.legend(frameon=False, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_distribution(counts: dict[str, int], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    items = sorted(counts.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(items) + 1.2), facecolor=SURFACE)
    ax.barh([k for k, _ in items], [v for _, v in items], color=COLORS["e1"], height=0.6)
    for i, (_, v) in enumerate(items):
        ax.text(v, i, f" {v:,}", va="center", color=MUTED, fontsize=9)
    ax.set_xlabel("instances in train split", color=MUTED)
    _style(ax, "Training instances per class")
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def weak_classes_md(results: dict[str, dict], classes: list[str], counts: dict[str, int], k: int, eval_name: str) -> str:
    exp = "e2" if "e2" in results else next(iter(results))
    present = [c for c in classes if c in results[exp]["per_class"]]
    absent = [c for c in classes if c not in results[exp]["per_class"]]
    ranked = sorted(present, key=lambda c: results[exp]["per_class"][c]["ap50"])
    lines = [
        "# 弱类别清单（阶段二生成目标）",
        "",
        f"按 {exp.upper()} 在 {eval_name} 上的 AP50 从低到高取前 {k} 类。阶段二（M3）的风险场景规格库优先覆盖这些类别。",
        "",
        "| 排名 | 类别 | AP50 | 训练实例数 | 可能原因（人工填写） |",
        "|---|---|---|---|---|",
    ]
    for i, c in enumerate(ranked[:k], 1):
        ap = results[exp]["per_class"].get(c, {}).get("ap50")
        lines.append(f"| {i} | {c} | {'—' if ap is None else f'{ap:.3f}'} | {counts.get(c, '—')} | |")
    if absent:
        lines += ["", f"⚠️ {eval_name} 中没有样本、因而无法评估的类别：{', '.join(absent)}。"
                  "它们不参与排名；需要时补充测试样本，否则在报告中说明。"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exps", nargs="+", default=["e1", "e2"])
    ap.add_argument("--data", default=str(PROCESSED / "yolo" / "dataset.yaml"))
    ap.add_argument("--split", default="test", help="test = TelecomEval; val only for development")
    ap.add_argument("--top-k", type=int, default=4)
    ap.add_argument("--skip-check", action="store_true")
    args = ap.parse_args(argv)

    if args.split == "test" and not args.skip_check:
        from telecomsafe.data.freeze_eval import check, eval_root
        problems = check(eval_root())
        if problems:
            sys.exit("TelecomEval is not frozen or has changed:\n  " + "\n  ".join(problems[:10]))

    REPORTS.mkdir(parents=True, exist_ok=True)
    results = {e: r for e in args.exps if (r := evaluate(e, args.data, args.split))}
    if not results:
        sys.exit("no trained runs found")

    for exp, r in results.items():
        write_rows(REPORTS / f"{exp}_metrics.csv", [r["overall"]])
    classes = next(iter(results.values()))["names"]
    counts = train_instances()
    rows = []
    for c in classes:
        row = {"class": c, "train_instances": counts.get(c, "")}
        for exp in ("e1", "e2"):
            pc = results.get(exp, {}).get("per_class", {}).get(c, {})
            row[f"{exp}_ap50"] = f"{pc['ap50']:.4f}" if pc else ""
            row[f"{exp}_ap50_95"] = f"{pc['ap50_95']:.4f}" if pc else ""
        if row["e1_ap50"] and row["e2_ap50"]:
            row["delta_ap50"] = f"{float(row['e2_ap50']) - float(row['e1_ap50']):+.4f}"
        else:
            row["delta_ap50"] = ""
        rows.append(row)
    write_rows(REPORTS / "per_class_ap.csv", rows)
    eval_name = "TelecomEval" if args.split == "test" else args.split
    plot_per_class(results, classes, REPORTS / "per_class_ap.png", eval_name)
    if counts:
        plot_distribution({c: counts.get(c, 0) for c in classes}, REPORTS / "class_distribution.png")
    (REPORTS / "weak_classes.md").write_text(weak_classes_md(results, classes, counts, args.top_k, eval_name), encoding="utf-8")

    for exp, r in results.items():
        o = r["overall"]
        print(f"{exp}: mAP50={o['mAP50']:.4f}  mAP50-95={o['mAP50-95']:.4f}  P={o['precision']:.3f}  R={o['recall']:.3f}")
    print(f"reports written to {REPORTS}")


if __name__ == "__main__":
    main()
