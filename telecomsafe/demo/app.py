"""TelecomSafe Baseline Demo v1.

    python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt
    python -m telecomsafe.demo.app --weights ... --examples reports/phase1/demo_examples --open

Three decoupled stages: detect() → judge() → render(). Phase 2 swaps only the weights.
Runs on localhost; no public share link. Styling lives in style.css next to this file.
"""

from __future__ import annotations

import argparse
import html
import re
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from telecomsafe.judge.rules import RuleEngine
from telecomsafe.judge.schema import Detection, RiskResult
from telecomsafe.paths import IMAGE_SUFFIXES

# Per-class box colours (categorical palette slots); red is reserved for boxes that triggered a rule.
CLASSES = {  # name: (display label, colour)
    "person": ("Person", "#2a78d6"),
    "helmet": ("Helmet", "#1baf7a"),
    "vest": ("Hi-vis vest", "#008300"),
    "harness": ("Harness", "#e87ba4"),
    "no_helmet": ("No helmet", "#eb6834"),
    "no_vest": ("No vest", "#eda100"),
    "machinery": ("Machinery", "#4a3aa7"),
    "vehicle": ("Vehicle", "#6b6a66"),
    "tower": ("Tower", "#52514e"),
}
HIT_COLOR = "#d03b3b"
_CLASS_PATTERN = re.compile(r"\b(" + "|".join(sorted(CLASSES, key=len, reverse=True)) + r")\b")
LEVELS = {  # level: (label, icon)
    "low": ("Low risk", "✓"),
    "medium": ("Medium risk", "!"),
    "high": ("High risk", "⛔"),
}
EXAMPLE_LABELS = {  # file-name prefix → example caption
    "1_": "Compliant crew", "2_": "No helmet", "3_": "Near machinery", "4_": "Pole work", "5_": "Failure case",
}
STYLE = (Path(__file__).with_name("style.css")).read_text(encoding="utf-8")
# Gradio translates its built-in texts (upload hints) to the browser language. The UI is English-only, so
# map those keys back to English for the Chinese locales (the ones this team's browsers use).
BUILTIN_EN = {"upload_text.drop_image": "Drop image here", "upload_text.click_to_upload": "Click to upload",
              "common.or": "or"}


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


# ---------------------------------------------------------------- render
def _font(size: int):
    for name in ("seguisb.ttf", "arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_boxes(image: Image.Image, dets: list[Detection], flagged: set[int]) -> Image.Image:
    im = image.convert("RGB").copy()
    draw = ImageDraw.Draw(im)
    scale = max(im.size) / 640
    lw = max(2, round(2.5 * scale))
    font = _font(max(12, round(13 * scale)))
    pad = max(3, round(3 * scale))
    # Draw unflagged first so boxes that triggered a rule stay on top.
    for i in sorted(range(len(dets)), key=lambda k: k in flagged):
        d = dets[i]
        hit = i in flagged
        color = HIT_COLOR if hit else CLASSES.get(d.cls, ("", "#52514e"))[1]
        draw.rectangle(d.box, outline=color, width=lw * 2 if hit else lw)
        label = f"{'! ' if hit else ''}{d.cls} {d.conf:.2f}"
        x0, y0, _, _ = d.box
        tw, th = draw.textbbox((0, 0), label, font=font)[2:]
        top = y0 - th - 2 * pad if y0 - th - 2 * pad >= 0 else y0
        draw.rounded_rectangle((x0, top, x0 + tw + 2 * pad, top + th + 2 * pad), radius=pad, fill=color)
        draw.text((x0 + pad, top + pad - 1), label, fill="#ffffff", font=font)
    return im


def _n(count: int, noun: str) -> str:
    return f"{count} {noun}{'' if count == 1 else 's'}"


def risk_card(result: RiskResult | None, n_dets: int = 0) -> str:
    if result is None:
        return ('<div class="ts-risk idle"><div class="ts-risk-icon">?</div><div>'
                '<div class="ts-risk-label">Risk level</div><div class="ts-risk-level">Awaiting image</div>'
                '<div class="ts-risk-summary">Upload a photo or pick an example on the left</div></div></div>')
    label, icon = LEVELS[result.level]
    n_rules = len({h.rule_id for h in result.hits})
    summary = (f"{_n(n_rules, 'rule')} triggered · {_n(len(result.hits), 'violation')} · {_n(n_dets, 'object')} detected"
               if result.hits else f"No violations · {_n(n_dets, 'object')} detected")
    return (f'<div class="ts-risk {result.level}"><div class="ts-risk-icon">{icon}</div><div>'
            f'<div class="ts-risk-label">Risk level</div><div class="ts-risk-level">{label}</div>'
            f'<div class="ts-risk-summary">{summary}</div></div></div>')


def readable(text: str) -> str:
    """Replace class names in rule details with display labels, in one pass so "No helmet" is not re-replaced."""
    return _CLASS_PATTERN.sub(lambda m: CLASSES[m.group(0)][0], text)


def rules_list(result: RiskResult | None, urls: dict[str, str], names: dict[str, str] | None = None) -> str:
    if result is None:
        return '<div class="ts-empty">Triggered safety rules and their regulatory sources appear here</div>'
    if not result.hits:
        return '<div class="ts-empty">✓ No safety rule triggered</div>'
    groups: dict[str, list] = {}
    for h in result.hits:
        groups.setdefault(h.rule_id, []).append(h)
    items = []
    for rule_id, hits in groups.items():
        h = hits[0]
        label, _ = LEVELS[h.level]
        details = "; ".join(dict.fromkeys(readable(x.detail) for x in hits))
        source = html.escape(h.source)
        if urls.get(rule_id):
            source = f'<a href="{html.escape(urls[rule_id])}" target="_blank" rel="noopener">{source} ↗</a>'
        count = f" ×{len(hits)}" if len(hits) > 1 else ""
        items.append(
            f'<div class="ts-rule"><div class="ts-rule-id">{html.escape(rule_id)}</div>'
            f'<div class="ts-rule-name">{html.escape((names or {}).get(rule_id, h.name))}{count}</div>'
            f'<div class="ts-level {h.level}">{label}</div>'
            f'<div class="ts-rule-meta">{html.escape(details)} · {source}</div></div>'
        )
    return f'<div class="ts-rules">{"".join(items)}</div>'


def detection_chips(dets: list[Detection] | None, flagged: set[int] | None = None) -> str:
    if dets is None:
        return legend()
    if not dets:
        return '<div class="ts-empty">Nothing detected — try a lower confidence threshold</div>'
    counts: dict[str, int] = {}
    hit_classes = {dets[i].cls for i in (flagged or set())}
    for d in dets:
        counts[d.cls] = counts.get(d.cls, 0) + 1
    order = [c for c in CLASSES if c in counts] + [c for c in counts if c not in CLASSES]
    chips = []
    for c in order:
        label, color = CLASSES.get(c, (c, "#52514e"))
        cls = " flagged" if c in hit_classes else ""
        chips.append(f'<span class="ts-chip{cls}"><span class="ts-dot" style="background:{color}"></span>'
                     f'{label} <b>×{counts[c]}</b></span>')
    return f'<div class="ts-chips">{"".join(chips)}</div>'


def legend() -> str:
    chips = [f'<span class="ts-chip"><span class="ts-dot" style="background:{color}"></span>{label}</span>'
             for name, (label, color) in CLASSES.items() if name != "tower"]
    chips.append(f'<span class="ts-chip"><span class="ts-dot" style="background:{HIT_COLOR}"></span>Triggered a rule</span>')
    return f'<div class="ts-chips">{"".join(chips)}</div>'


def render(image: Image.Image, dets: list[Detection], result: RiskResult,
           rule_urls: dict[str, str] | None = None,
           rule_names: dict[str, str] | None = None) -> tuple[Image.Image, str, str, str]:
    flagged = {i for h in result.hits for i in h.detections}
    return (draw_boxes(image, dets, flagged), risk_card(result, len(dets)),
            rules_list(result, rule_urls or {}, rule_names), detection_chips(dets, flagged))


# ---------------------------------------------------------------- UI
def model_name(weights: str) -> str:
    """e.g. "E2 · YOLO11s": run folder name plus the architecture stored in the checkpoint."""
    parts = Path(weights).parts
    run = parts[-3] if len(parts) >= 3 and parts[-2] == "weights" else Path(weights).stem
    arch = Path(str((getattr(load_model(weights), "ckpt", None) or {}).get("train_args", {}).get("model", ""))).stem
    arch = arch.replace("yolo", "YOLO") if arch else ""
    return f"{run.upper() if len(run) <= 3 else run} · {arch}" if arch else run


def header(weights: str, n_classes: int, n_rules: int) -> str:
    model = model_name(weights)
    return f"""
<div class="ts-header">
  <div class="ts-brand">
    <div class="ts-logo">📡</div>
    <div>
      <h1 class="ts-title">TelecomSafe · Construction Safety Risk Detection</h1>
      <p class="ts-subtitle">Object detection → safety rules → risk level · telecom construction sites · Baseline Demo v1</p>
    </div>
  </div>
  <div class="ts-badges">
    <span class="ts-badge">Model {html.escape(model)}</span>
    <span class="ts-badge">{n_classes} classes</span>
    <span class="ts-badge">{n_rules} safety rules</span>
  </div>
</div>"""


FOOTER = """
<div class="ts-footer">
  <b>Note</b>: phase 1 baseline (YOLO11s trained on public datasets), validation mAP50 = 0.756; the telecom test set
  (TelecomEval) is still being built. Harness, vehicle and no-helmet detection remain weak and are the focus of
  phase 2 generative augmentation. Person–machine distance is estimated from the person's box height and is indicative only.
</div>"""


def example_label(path: str) -> str:
    return next((v for k, v in EXAMPLE_LABELS.items() if Path(path).name.startswith(k)), Path(path).stem)


def section(step: int, title: str) -> str:
    return f'<div class="ts-section-title"><span class="ts-step">{step}</span>{title}</div>'


def build_ui(weights: str, examples: list[str]):
    import gradio as gr

    engine = RuleEngine.from_yaml()
    rule_urls = {r["id"]: r.get("source_url", "") for r in engine.rules}
    rule_names = {r["id"]: r.get("name_en", r["name"]) for r in engine.rules}
    detect(Image.new("RGB", (640, 640)), weights, 0.5)  # warm up: the first real request is then as fast as the rest
    n_classes = len(load_model(weights).names)

    def run(image, conf):
        if image is None:
            return None, risk_card(None), rules_list(None, rule_urls, rule_names), detection_chips(None)
        dets = detect(image, weights, conf)
        return render(image, dets, judge(dets, engine), rule_urls, rule_names)

    with gr.Blocks(title="TelecomSafe · Construction Safety Risk Detection") as ui:
        gr.HTML(header(weights, n_classes, len(engine.rules)))
        with gr.Row(equal_height=False):
            with gr.Column(scale=5, elem_classes="ts-panel"):
                gr.HTML(section(1, "Upload a site photo"))
                image = gr.Image(type="pil", label="Input image", show_label=False, height=380, sources=["upload", "clipboard"],
                                 buttons=["fullscreen"])
                conf = gr.Slider(0.05, 0.9, value=0.35, step=0.05, label="Confidence threshold",
                                 info="Lower finds more objects; higher gives fewer false alarms")
                btn = gr.Button("Analyse", variant="primary", size="lg")
                if examples:
                    gr.HTML(section(0, "Examples — click to analyse (none used in training)").replace(">0<", ">★<"))
                    gallery = gr.Gallery(
                        value=[(e, example_label(e)) for e in examples], columns=3, height="auto",
                        allow_preview=False, show_label=False, object_fit="cover", elem_classes="ts-examples",
                    )
            with gr.Column(scale=7, elem_classes="ts-panel"):
                gr.HTML(section(2, "Result"))
                risk = gr.HTML(risk_card(None))
                out_image = gr.Image(type="pil", label="Detections", show_label=False, height=420, interactive=False,
                                     buttons=["fullscreen", "download"])
                gr.HTML(section(3, "Triggered safety rules"))
                rules = gr.HTML(rules_list(None, rule_urls, rule_names))
                gr.HTML(section(4, "Detected objects"))
                chips = gr.HTML(detection_chips(None))
        outputs = [out_image, risk, rules, chips]
        gr.HTML(FOOTER)

        if examples:
            def pick(conf_value, evt):
                img = Image.open(examples[evt.index]).convert("RGB")
                return (img, *run(img, conf_value))
            # Gradio finds the event argument by its annotation; with postponed annotations
            # (from __future__ import annotations) it must be a real class, not a string.
            pick.__annotations__["evt"] = gr.SelectData
            gallery.select(pick, [conf], [image, *outputs], api_visibility="undocumented")

        btn.click(run, [image, conf], outputs, api_name="run")
        image.upload(run, [image, conf], outputs, api_visibility="undocumented")
        conf.release(run, [image, conf], outputs, api_visibility="undocumented")
        image.clear(lambda: run(None, 0), None, outputs, api_visibility="undocumented")
    return ui


def english_builtins():
    import gradio as gr

    return gr.I18n(**{loc: BUILTIN_EN for loc in ("zh-CN", "zh-TW", "zh")})


def theme():
    import gradio as gr

    return gr.themes.Soft(
        primary_hue=gr.themes.colors.blue, neutral_hue=gr.themes.colors.slate, radius_size="lg",
        font=["Microsoft YaHei UI", "PingFang SC", "Noto Sans SC", "Segoe UI", "sans-serif"],
    ).set(
        button_primary_background_fill="#1c5cab", button_primary_background_fill_hover="#184f95",
        button_primary_text_color="#ffffff", body_background_fill="#f5f5f2",
        body_background_fill_dark="#1a1a19", block_border_width="0px", block_shadow="none",
    )


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
    build_ui(args.weights, examples).launch(
        server_name="127.0.0.1", server_port=args.port, share=False, inbrowser=args.open,
        theme=theme(), css=STYLE, footer_links=[], i18n=english_builtins(),
    )


if __name__ == "__main__":
    main()
