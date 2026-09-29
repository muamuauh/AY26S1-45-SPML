"""Generate data/README.md (and reports/phase1/dataset_licences.csv) from configs/sources.yaml.

    python -m telecomsafe.data.catalog

Never edit data/README.md by hand — change configs/sources.yaml and re-run. Re-run
after downloading and after building so the "actual" counts are current.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from telecomsafe.paths import DATA, IMAGE_SUFFIXES, REPORTS, SPLITS, load_sources, load_taxonomy, resolve

ROLE = {"A": "训练 · A 核心", "B": "训练 · B 补充", "optional": "训练 · 可选", "eval": "测试（TelecomEval）", "unused": "未使用"}


def raw_count(cfg: dict) -> int | None:
    path = resolve(cfg.get("path", f"data/raw/{cfg['name']}"))
    if not path.exists():
        return None
    return sum(1 for p in path.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES)


def built_counts(stats: Path = REPORTS / "dataset_stats.csv") -> Counter:
    counts: Counter = Counter()
    if stats.exists():
        with open(stats, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                counts[row["source"]] += int(row["images"])
    return counts


def fmt_count(n: int | None) -> str:
    return "未下载" if n is None else f"{n:,}"


def class_map_text(cfg: dict) -> str:
    cm = cfg.get("class_map")
    if cm == "identity":
        return "直接按目标类别标注"
    if not cm:
        return "待填写（下载后按数据集自带的类别表补全）"
    return ", ".join(f"{k}→{v if v is not None else '丢弃'}" for k, v in cm.items())


def download_text(cfg: dict) -> str:
    d = cfg.get("download") or {}
    m = d.get("method")
    if m == "kaggle":
        return f"`kaggle datasets download -d {d['ref']}`（或 `python -m telecomsafe.data.download --only {cfg['name']}`）"
    if m == "roboflow":
        return f"Roboflow API：workspace `{d['workspace']}` / project `{d['project']}`（`python -m telecomsafe.data.download --only {cfg['name']}`）"
    if m == "ultralytics":
        return f"随 Ultralytics 的 `{d['yaml']}` 自动下载（`python -m telecomsafe.data.download --only {cfg['name']}`）"
    if m == "manual":
        return f"手动：{d.get('instructions', '')}"
    return "—"


def eval_status() -> list[str]:
    lines = []
    sha = SPLITS / "telecom_eval.sha256"
    if sha.exists():
        head = sha.read_text(encoding="utf-8").splitlines()[:2]
        lines.append(f"- **冻结状态**：已冻结。{head[0].lstrip('# ')}；{head[1].lstrip('# ')}")
    else:
        lines.append("- **冻结状态**：尚未冻结（标注完成后运行 `python -m telecomsafe.data.freeze_eval --create`）")
    manifest = DATA / "licence_manifest.csv"
    if manifest.exists():
        with open(manifest, encoding="utf-8-sig") as f:
            status = Counter(r["status"] for r in csv.DictReader(f))
        lines.append(f"- **候选图**：保留 {status.get('candidate', 0)} 张，剔除 {status.get('rejected', 0)} 张（逐图许可见 `data/licence_manifest.csv`）")
    return lines


def render(sources: list[dict], taxonomy: list[dict], built: Counter) -> str:
    used = [c for c in sources if c.get("role") != "unused"]
    unused = [c for c in sources if c.get("role") == "unused"]
    out = [
        "# 数据集说明 / Dataset Catalogue",
        "",
        "> 本文件由 `python -m telecomsafe.data.catalog` 根据 `configs/sources.yaml` 自动生成，**请勿手动编辑**。",
        "> 数据本身不入库（见 `.gitignore`），按下文的获取方式下载到 `data/raw/<名称>/`。",
        "",
        "## 总览",
        "",
        "| 数据集 | 用途 | 参与构建 | 计划规模 | 本地原始张数 | 构建后张数 | 许可 | 链接 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for c in used:
        link = f"[主页]({c['homepage']})" if c.get("homepage") else "—"
        out.append(
            f"| `{c['name']}` {c['title']} | {ROLE.get(c.get('tier'), c.get('tier', ''))} | {'是' if c.get('enabled') else '否'} "
            f"| {c.get('planned_size', '—')} | {fmt_count(raw_count(c))} | {built.get(c['name'], '—')} | {c.get('licence', '—')} | {link} |"
        )

    out += ["", "## 目标类别（阶段一）", "", "| id | 类别 | 维度 | 含义 | 判定标准 |", "|---|---|---|---|---|"]
    for i, t in enumerate(taxonomy):
        out.append(f"| {i} | `{t['name']}` | {t['dimension']} | {t['description']} | {t.get('criterion', '')} |")

    out += ["", "## 各数据集详情"]
    for c in used:
        out += [
            "",
            f"### `{c['name']}` — {c['title']}",
            "",
            f"- **来源**：{c.get('homepage') or ('自建' if c.get('role') == 'eval' else '无公开页面（见获取方式）')}",
        ]
        if c.get("paper"):
            out.append(f"- **论文**：{c['paper']}")
        out += [
            f"- **简介**：{c.get('description', '').strip()}",
            f"- **规模**：计划 {c.get('planned_size', '—')} ｜ 本地原始 {fmt_count(raw_count(c))} ｜ 构建后 {built.get(c['name'], '—')}",
            f"- **格式 / 本地路径**：{c.get('format', '—')} ｜ `{c.get('path', '')}`",
            f"- **类别映射**：{class_map_text(c)}",
            f"- **完整标注的目标类别**：{', '.join(c.get('annotates') or []) or '—'}"
            + ("（其余类别由 teacher 补伪标签）" if c.get("role") == "train" else ""),
            f"- **许可**：{c.get('licence', '—')}",
            f"- **引用**：{c.get('citation', '—')}",
            f"- **获取方式**：{download_text(c)}",
            f"- **用途**：{ROLE.get(c.get('tier'), '')}{'' if c.get('enabled') else '（当前未参与构建）'}",
        ]
        if c.get("filter"):
            out.append(f"- **过滤**：{c['filter']}")
        if c.get("notes"):
            out.append(f"- **备注**：{c['notes']}")
        if not c.get("verified"):
            out.append("- ⚠️ 类别表与规模尚未按下载后的实际文件核对")
        if c.get("role") == "eval":
            out += eval_status()

    out += ["", "## 调研过但阶段一未使用", "", "| 数据集 | 规模 | 许可 | 未使用原因 |", "|---|---|---|---|"]
    for c in unused:
        out.append(f"| [{c['title']}]({c['homepage']}) | {c.get('planned_size', '—')} | {c.get('licence', '—')} | {c.get('reason', '')} |")

    out += [
        "",
        "## TelecomEval 建立流程",
        "",
        "1. `python -m telecomsafe.data.collect_open` —— 从 Openverse 与 Wikimedia Commons 检索开放许可（CC0 / PD / CC BY / CC BY-SA）候选图，自动记录署名",
        "2. 人工筛选：只保留**有人在电信场景作业**的照片，其余直接删除；然后 `python -m telecomsafe.data.collect_open --sync`",
        "3. `python -m telecomsafe.data.pseudo_label --weights <teacher> --images data/raw/t3_candidates/images` —— 生成预标注（teacher 标人员与 PPE，COCO 模型补车辆）",
        "4. `python -m telecomsafe.data.labelstudio serve` 启动 Label Studio（账号见 `.env`），另开终端 `python -m telecomsafe.data.labelstudio push` 导入图片与预标注",
        "5. 在 http://localhost:8080 逐张按上方「判定标准」修正：检查每个预标注框，补画漏标（安全带、机械没有预标注，必须手画）；不可用的图点 Skip",
        "6. `python -m telecomsafe.data.labelstudio pull` —— 导出为 YOLO 格式到 `data/raw/telecom_eval/`",
        "7. `python -m telecomsafe.data.freeze_eval --create` —— 冻结；此后只读，两个阶段共用",
        "",
    ]
    return "\n".join(out)


def write_licences(sources: list[dict], path: Path = REPORTS / "dataset_licences.csv") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["name", "title", "tier", "enabled", "licence", "homepage", "citation"])
        for c in sources:
            w.writerow([c["name"], c["title"], c.get("tier"), c.get("enabled"), c.get("licence"), c.get("homepage"), c.get("citation", "")])


def main() -> None:
    sources = load_sources()
    text = render(sources, load_taxonomy(), built_counts())
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "README.md").write_text(text, encoding="utf-8")
    write_licences(sources)
    print(f"wrote {DATA / 'README.md'} and {REPORTS / 'dataset_licences.csv'}")


if __name__ == "__main__":
    main()
