"""TelecomSafe Baseline Demo v1.

    python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt
    python -m telecomsafe.demo.app --weights ... --examples reports/phase1/demo_examples

Three decoupled stages: detect() → judge() → render(). Phase 2 swaps only the weights.
Runs on localhost; no public share link.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from telecomsafe.judge.rules import RuleEngine
from telecomsafe.judge.schema import Detection, RiskResult
from telecomsafe.paths import IMAGE_SUFFIXES

LEVEL_STYLE = {  # label, background, ink
    "low": ("低风险", "#0ca30c", "#ffffff"),
    "medium": ("中风险", "#fab219", "#0b0b0b"),
    "high": ("高风险", "#d03b3b", "#ffffff"),
}
BOX_COLORS = {"person": "#2a78d6", "helmet": "#1baf7a", "vest": "#1baf7a", "harness": "#1baf7a",
              "no_helmet": "#eb6834", "no_vest": "#eb6834", "machinery": "#4a3aa7", "vehicle": "#4a3aa7", "tower": "#52514e"}
HIT_COLOR = "#d03b3b"


@lru_cache(maxsize=2)
def load_model(weights: str):
    from ultralytics import YOLO
    return YOLO(weights)


def detect(image: Image.Image, weights: str, conf: float) -> list[Detection]:
    r = load_model(weights).predict(image, conf=conf, verbose=False)[0]
    return [
        Detection(r.names[int(c)], float(s), tuple(map(float, xyxy)))
        for xyxy, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())
    ]


def judge(dets: list[Detection], engine: RuleEngine) -> RiskResult:
    return engine.judge(dets)


def render(image: Image.Image, dets: list[Detection], result: RiskResult) -> tuple[Image.Image, str, list[list[str]], str]:
    im = image.convert("RGB").copy()
    draw = ImageDraw.Draw(im)
    lw = max(2, round(max(im.size) / 300))
    try:
        font = ImageFont.truetype("arial.ttf", max(12, lw * 6))
    except OSError:
        font = ImageFont.load_default()
    flagged = {i for h in result.hits for i in h.detections}
    for i, d in enumerate(dets):
        color = HIT_COLOR if i in flagged else BOX_COLORS.get(d.cls, "#52514e")
        draw.rectangle(d.box, outline=color, width=lw * 2 if i in flagged else lw)
        label = f"{d.cls} {d.conf:.2f}"
        x, y = d.box[0], max(0, d.box[1] - font.size - 4)
        tb = draw.textbbox((x, y), label, font=font)
        draw.rectangle((tb[0] - 2, tb[1] - 2, tb[2] + 2, tb[3] + 2), fill=color)
        draw.text((x, y), label, fill="#ffffff", font=font)

    text, bg, ink = LEVEL_STYLE[result.level]
    if not result.hits:
        text += " · 未发现违规"
    card =(f'<div style="padding:18px;border-radius:8px;background:{bg};color:{ink};'
            f'font-size:26px;font-weight:600;text-align:center">风险等级：{text}</div>')
    rows = [[h.rule_id, h.name, {"low": "低", "medium": "中", "high": "高"}[h.level], h.detail, h.source] for h in result.hits]
    counts: dict[str, int] = {}
    for d in dets:
        counts[d.cls] = counts.get(d.cls, 0) + 1
    summary = "检测统计：" + (" · ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "无检测结果")
    return im, card, rows, summary


def build_ui(weights: str, examples: list[str]):
    import gradio as gr

    engine = RuleEngine.from_yaml()
    detect(Image.new("RGB", (640, 640)), weights, 0.5)  # warm up: the first real request is then as fast as the rest

    def run(image, conf):
        if image is None:
            return None, "", [], ""
        dets = detect(image, weights, conf)
        return render(image, dets, judge(dets, engine))

    with gr.Blocks(title="TelecomSafe · Baseline Demo v1") as ui:
        gr.Markdown("## TelecomSafe · Baseline Demo v1\n电信施工安全风险识别：检测 → 规则判断 → 风险等级")
        with gr.Row():
            with gr.Column(scale=3):
                image = gr.Image(type="pil", label="上传图片")
                conf = gr.Slider(0.05, 0.9, value=0.35, step=0.05, label="置信度阈值")
                btn = gr.Button("识别", variant="primary")
                if examples:
                    gr.Examples(examples=[[e] for e in examples], inputs=[image], label="示例")
            with gr.Column(scale=4):
                out_image = gr.Image(type="pil", label="检测结果")
                card = gr.HTML()
                table = gr.Dataframe(headers=["规则", "名称", "等级", "依据", "法规出处"], label="触发规则", wrap=True)
                summary = gr.Markdown()
        btn.click(run, [image, conf], [out_image, card, table, summary])
        image.upload(run, [image, conf], [out_image, card, table, summary])
    return ui


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--examples", default="reports/phase1/demo_examples", help="folder of example images")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--open", action="store_true", help="open the browser once the server is ready")
    args = ap.parse_args(argv)
    if not Path(args.weights).exists():
        raise SystemExit(f"weights not found: {args.weights}")
    ex_dir = Path(args.examples)
    examples = sorted(str(p) for p in ex_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES) if ex_dir.exists() else []
    build_ui(args.weights, examples).launch(server_name="127.0.0.1", server_port=args.port, share=False, inbrowser=args.open)


if __name__ == "__main__":
    main()
