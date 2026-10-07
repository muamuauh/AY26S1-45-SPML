"""Quality gates for synthetic images (document 03 §7; thresholds in configs/scenarios.yaml → gates).

G0 leak      — no image used by generation may nearly duplicate a TelecomEval image (pHash).
G1 semantic  — CLIP zero-shot: the base must be a photograph, and the edited region must show what the
               scenario asked for (e.g. a bare head, not a cap or a distorted blob).
G3 detector  — the E2 detector, used only to reject extreme failures (here: the helmet is still detected).
G2 (batch distribution) and G4 (human spot check) are run per batch, not per image.
"""

from __future__ import annotations

from functools import cached_property
from pathlib import Path

import numpy as np

from telecomsafe.gen.common import iou
from telecomsafe.paths import RUNS

E2_WEIGHTS = RUNS / "e2" / "weights" / "best.pt"

# CLIP prompts. Index 0.. of POSITIVE count as a pass; the rest are the failure modes seen in the pre-study.
PHOTO = ["a photograph of a real scene", "a photograph of workers on a construction site"]
NOT_PHOTO = ["a diagram with text labels", "an illustration or drawing", "a screenshot of a document"]
BARE_HEAD = ["a photo of a person's bare head with hair", "a photo of a person's bald head"]
NOT_BARE_HEAD = ["a photo of a person wearing a hard hat", "a photo of a person wearing a cap, beanie or hood",
                 "a photo of a person wearing a face mask", "a distorted blurry blob", "a painted cartoon face"]
ORDINARY_CLOTHES = ["a photo of a person wearing an ordinary shirt or jacket", "a photo of a person wearing a plain t-shirt"]
NOT_ORDINARY_CLOTHES = ["a photo of a person wearing a high-visibility safety vest with reflective strips",
                        "a photo of a person wearing a neon yellow or orange vest", "a distorted blurry blob",
                        "a painted cartoon figure"]


def g0_leak_mask(paths: list[Path], held_out: list[Path] | None = None, threshold: int = 8) -> list[bool]:
    """True for each path that nearly duplicates a held-out (TelecomEval) image and must not be used."""
    from telecomsafe.data.build import chosen_eval_images, hamming, phash_all

    held_out = chosen_eval_images() if held_out is None else held_out
    if not held_out or not paths:
        return [False] * len(paths)
    ev = phash_all(held_out)
    return [bool((hamming(h, ev) <= threshold).any()) for h in phash_all(paths)]


class Clip:
    """Zero-shot CLIP scores (open_clip ViT-B-32, the same model as the screening step)."""

    def __init__(self, device: str | None = None):
        import torch

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

    @cached_property
    def _model(self):
        import open_clip

        model, _, preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="laion2b_s34b_b79k",
                                                                     device=self.device)
        model.eval()
        return model, preprocess, open_clip.get_tokenizer("ViT-B-32")

    def share(self, image, positive: list[str], negative: list[str]) -> float:
        """Probability mass CLIP puts on the positive prompts (softmax over positive + negative)."""
        import torch

        model, preprocess, tok = self._model
        with torch.no_grad():
            img = model.encode_image(preprocess(image.convert("RGB")).unsqueeze(0).to(self.device))
            txt = model.encode_text(tok(positive + negative).to(self.device))
            img = img / img.norm(dim=-1, keepdim=True)
            txt = txt / txt.norm(dim=-1, keepdim=True)
            p = (100 * img @ txt.T).softmax(dim=-1)[0].cpu().numpy()
        return float(p[: len(positive)].sum())

    def is_photo(self, image) -> float:
        return self.share(image, PHOTO, NOT_PHOTO)

    def bare_head(self, crop) -> float:
        return self.share(crop, BARE_HEAD, NOT_BARE_HEAD)

    def ordinary_clothes(self, crop) -> float:
        return self.share(crop, ORDINARY_CLOTHES, NOT_ORDINARY_CLOTHES)


class Detector:
    """The frozen E2 baseline (G3) — also proposes boxes for labels that changed."""

    def __init__(self, weights: Path = E2_WEIGHTS, conf: float = 0.25):
        self.weights, self.conf = weights, conf

    @cached_property
    def _model(self):
        from ultralytics import YOLO

        return YOLO(str(self.weights))

    def detect(self, image) -> list[tuple[str, tuple[float, float, float, float], float]]:
        r = self._model.predict(image, conf=self.conf, verbose=False)[0]
        return [(r.names[int(c)], tuple(b), float(s))
                for b, c, s in zip(r.boxes.xyxy.tolist(), r.boxes.cls.tolist(), r.boxes.conf.tolist())]

    @staticmethod
    def found(dets, cls: str, box, min_iou: float = 0.3) -> list:
        return [d for d in dets if d[0] == cls and iou(d[1], box) > min_iou]


def kid(real_feats: np.ndarray, synth_feats: np.ndarray, subsets: int = 50, size: int = 100, seed: int = 0) -> float:
    """Kernel Inception Distance on precomputed features (G2; unbiased MMD² with a cubic polynomial kernel)."""
    rng = np.random.default_rng(seed)
    d = real_feats.shape[1]
    m = min(size, len(real_feats), len(synth_feats))
    vals = []
    for _ in range(subsets):
        x = real_feats[rng.choice(len(real_feats), m, replace=False)]
        y = synth_feats[rng.choice(len(synth_feats), m, replace=False)]
        kxx, kyy, kxy = ((x @ x.T) / d + 1) ** 3, ((y @ y.T) / d + 1) ** 3, ((x @ y.T) / d + 1) ** 3
        vals.append((kxx.sum() - np.trace(kxx)) / (m * (m - 1)) + (kyy.sum() - np.trace(kyy)) / (m * (m - 1))
                    - 2 * kxy.mean())
    return float(np.mean(vals))
