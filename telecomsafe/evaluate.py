"""Evaluate E1/E2 on TelecomEval and write the phase 1 reports.

    python -m telecomsafe.evaluate                 # runs/phase1/{e1,e2,e2_s1,e2_s2}/weights/best.pt
    python -m telecomsafe.evaluate --exps e1 e2 e2_s1 e2_s2 --split val --skip-check --out <folder>

Runs named <exp>_s<k> are further seeds of <exp>: they are grouped with it and every
table and chart reports the mean over seeds (± standard deviation when there are several).

Refuses to run if TelecomEval changed since it was frozen (use --skip-check only
while TelecomEval does not exist yet, e.g. to evaluate on val during development).

Outputs in reports/phase1/: <run>_metrics.csv, summary.csv (mean ± std per experiment),
<exp>_confusion_matrix.png, per_class_ap.csv, per_class_ap.png, class_distribution.png, weak_classes.md
(weak_classes.md is written only if absent — its "reason" column is filled by hand;
pass --rewrite-weak-classes to regenerate it).
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import statistics
import sys
from pathlib import Path

from telecomsafe.paths import PROCESSED, REPORTS, RUNS

# Categorical palette in fixed slot order (validated default palette, light surface).
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
# Known experiments keep their slot whatever else is plotted with them (colour follows the entity).
SLOTS = {"e1": 0, "e2": 1, "v1_e2_yolov8s": 2, "v1_e2_yolo11m": 3, "e3": 4}
LABELS = {"e1": "E1 · YOLO11s, no augmentation", "e2": "E2 · YOLO11s, default augmentation",
          "v1_e2_yolov8s": "E2 · YOLOv8s (v1 data)", "v1_e2_yolo11m": "E2 · YOLO11m (v1 data)",
          "e3": "E3 · + generative augmentation"}
SURFACE, INK, MUTED = "#fcfcfb", "#0b0b0b", "#52514e"


def exp_color(exp: str, order: list[str]) -> str:
    if exp in SLOTS:
        return PALETTE[SLOTS[exp]]
    free = [i for i in range(len(PALETTE)) if i not in SLOTS.values()]
    return PALETTE[free[[e for e in order if e not in SLOTS].index(exp) % len(free)]]


def group_of(run: str) -> str:
    """e2_s1 → e2: further seeds of an experiment share its name."""
    return re.sub(r"_s\d+$", "", run)


def aggregate(runs: dict[str, dict]) -> dict[str, dict]:
    """Group runs by experiment; metrics become means, with *_std when an experiment has several seeds."""
    groups: dict[str, list[dict]] = {}
    for run, r in runs.items():
        groups.setdefault(group_of(run), []).append(r)
    out = {}
    for g, rs in groups.items():
        def mean_std(values: list[float]) -> tuple[float, float | None]:
            return statistics.fmean(values), (statistics.stdev(values) if len(values) > 1 else None)

        overall = {"exp": g, "runs": len(rs), "split": rs[0]["overall"]["split"]}
        for key in ("mAP50", "mAP50-95", "precision", "recall"):
            overall[key], overall[f"{key}_std"] = mean_std([float(r["overall"][key]) for r in rs])
        per_class = {}
        for c in {c for r in rs for c in r["per_class"]}:
            vals = [r["per_class"][c] for r in rs if c in r["per_class"]]
            ap50, ap50_std = mean_std([v["ap50"] for v in vals])
            ap, ap_std = mean_std([v["ap50_95"] for v in vals])
            per_class[c] = {"ap50": ap50, "ap50_std": ap50_std, "ap50_95": ap, "ap50_95_std": ap_std}
        out[g] = {"overall": overall, "per_class": per_class, "names": rs[0]["names"], "runs": len(rs)}
    return out


def fmt(v: float | None) -> str:
    return "" if v is None else f"{v:.4f}"


def evaluate(exp: str, data: str, split: str, out: Path = REPORTS) -> dict | None:
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
    if cm.exists() and group_of(exp) == exp:  # one confusion matrix per experiment (its first seed)
        shutil.copy2(cm, out / f"{exp}_confusion_matrix.png")
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

    exps = list(results)
    fig, ax = plt.subplots(figsize=(10, 4.4), facecolor=SURFACE)
    width = 0.8 / len(exps)
    for j, exp in enumerate(exps):
        vals = [results[exp]["per_class"].get(c, {}).get("ap50", 0.0) for c in classes]
        errs = [results[exp]["per_class"].get(c, {}).get("ap50_std") or 0.0 for c in classes]
        xs = [i + (j - (len(exps) - 1) / 2) * width for i in range(len(classes))]
        n = results[exp].get("runs", 1)
        label = LABELS.get(exp, exp) + (f" — mean of {n} seeds" if n > 1 else "")
        ax.bar(xs, vals, width=width - 0.03, color=exp_color(exp, exps), label=label, edgecolor=SURFACE, linewidth=2,
               yerr=errs if n > 1 else None, error_kw={"ecolor": INK, "elinewidth": 1, "capsize": 2})
    for i, c in enumerate(classes):  # distinguish "AP 0" from "class absent from the evaluation set"
        if not any(c in results[e]["per_class"] for e in exps):
            ax.text(i, 0.02, "no samples", ha="center", va="bottom", rotation=90, color=MUTED, fontsize=8)
    ax.set_xticks(range(len(classes)), classes)
    ax.set_ylim(0, 1)
    ax.set_ylabel(f"AP50 on {eval_name}", color=MUTED)
    _style(ax, "Per-class AP50 by experiment")
    # Below the axes: bars can reach 1.0 in any class, so no spot inside the plot is guaranteed free.
    ax.legend(frameon=False, labelcolor=INK, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=min(len(exps), 3))
    fig.tight_layout()
    fig.savefig(out, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def plot_distribution(counts: dict[str, int], out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    items = sorted(counts.items(), key=lambda kv: kv[1])
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(items) + 1.2), facecolor=SURFACE)
    ax.barh([k for k, _ in items], [v for _, v in items], color=PALETTE[0], height=0.6)
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
        f"按 {exp.upper()}{'（' + str(results[exp].get('runs', 1)) + ' 个种子的均值）' if results[exp].get('runs', 1) > 1 else ''}"
        f" 在 {eval_name} 上的 AP50 从低到高取前 {k} 类。阶段二（M3）的风险场景规格库优先覆盖这些类别。",
        "",
        "| 排名 | 类别 | AP50 | 训练实例数 | 可能原因（人工填写） |",
        "|---|---|---|---|---|",
    ]
    for i, c in enumerate(ranked[:k], 1):
        pc = results[exp]["per_class"].get(c, {})
        ap, sd = pc.get("ap50"), pc.get("ap50_std")
        shown = "—" if ap is None else f"{ap:.3f}" + (f" ± {sd:.3f}" if sd is not None else "")
        lines.append(f"| {i} | {c} | {shown} | {counts.get(c, '—')} | |")
    if absent:
        lines += ["", f"⚠️ {eval_name} 中没有样本、因而无法评估的类别：{', '.join(absent)}。"
                  "它们不参与排名；需要时补充测试样本，否则在报告中说明。"]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exps", nargs="+", default=["e1", "e2", "e2_s1", "e2_s2"])
    ap.add_argument("--data", default=str(PROCESSED / "yolo" / "dataset.yaml"))
    ap.add_argument("--split", default="test", help="test = TelecomEval; val only for development")
    ap.add_argument("--top-k", type=int, default=4)
    ap.add_argument("--out", type=Path, default=REPORTS, help="report folder (default reports/phase1)")
    ap.add_argument("--skip-check", action="store_true")
    ap.add_argument("--rewrite-weak-classes", action="store_true",
                    help="regenerate weak_classes.md (overwrites the hand-written reasons)")
    args = ap.parse_args(argv)

    if args.split == "test" and not args.skip_check:
        from telecomsafe.data.freeze_eval import check, eval_root
        problems = check(eval_root())
        if problems:
            sys.exit("TelecomEval is not frozen or has changed:\n  " + "\n  ".join(problems[:10]))

    args.out.mkdir(parents=True, exist_ok=True)
    runs = {e: r for e in args.exps if (r := evaluate(e, args.data, args.split, args.out))}
    if not runs:
        sys.exit("no trained runs found")

    for run, r in runs.items():
        write_rows(args.out / f"{run}_metrics.csv", [r["overall"]])
    results = aggregate(runs)
    write_rows(args.out / "summary.csv", [{k: (fmt(v) if isinstance(v, float) or v is None else v)
                                           for k, v in r["overall"].items()} for r in results.values()])
    classes = next(iter(results.values()))["names"]
    counts = train_instances()
    rows = []
    for c in classes:
        row = {"class": c, "train_instances": counts.get(c, "")}
        for exp in results:
            pc = results[exp]["per_class"].get(c, {})
            row[f"{exp}_ap50"] = fmt(pc.get("ap50"))
            if results[exp]["runs"] > 1:
                row[f"{exp}_ap50_std"] = fmt(pc.get("ap50_std"))
            row[f"{exp}_ap50_95"] = fmt(pc.get("ap50_95"))
        if row.get("e1_ap50") and row.get("e2_ap50"):
            row["delta_ap50"] = f"{float(row['e2_ap50']) - float(row['e1_ap50']):+.4f}"
        else:
            row["delta_ap50"] = ""
        rows.append(row)
    write_rows(args.out / "per_class_ap.csv", rows)
    eval_name = "TelecomEval" if args.split == "test" else args.split
    plot_per_class(results, classes, args.out / "per_class_ap.png", eval_name)
    if counts:
        plot_distribution({c: counts.get(c, 0) for c in classes}, args.out / "class_distribution.png")
    weak = args.out / "weak_classes.md"
    if args.rewrite_weak_classes or not weak.exists():
        weak.write_text(weak_classes_md(results, classes, counts, args.top_k, eval_name), encoding="utf-8")
    else:
        print(f"  kept {weak.name} (hand-written reasons); use --rewrite-weak-classes to regenerate")

    for exp, r in results.items():
        o = r["overall"]
        sd = (lambda k: f" ± {o[k + '_std']:.4f}" if o.get(k + "_std") is not None else "")
        print(f"{exp} ({o['runs']} run{'s' if o['runs'] > 1 else ''}): mAP50={o['mAP50']:.4f}{sd('mAP50')}  "
              f"mAP50-95={o['mAP50-95']:.4f}{sd('mAP50-95')}  P={o['precision']:.3f}  R={o['recall']:.3f}")
    print(f"reports written to {args.out}")


if __name__ == "__main__":
    main()
