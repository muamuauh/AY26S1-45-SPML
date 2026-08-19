# TelecomSafe — Technical Plan and Milestones

> Document version: v1.0 ｜ Generated: 2026-08-18
> Chinese counterpart: [01-技术方案与里程碑-CN.md](01-技术方案与里程碑-CN.md)
> Companion documents: `00-Requirements-Analysis-EN.md`, `02-Datasets-and-Pretrained-Models-EN.md`, `03-Generative-Augmentation-Pipeline-EN.md`

---

## 1. Overall System Architecture

TelecomSafe adopts a **five-layer architecture** in which each layer has a single responsibility and can be independently evaluated and independently assigned.

```
┌──────────────────────────────────────────────────────────────┐
│  L5  Application                                              │
│      Risk report generation / Web dashboard / Alerts / Search │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L4  Fusion & Decision                                        │
│      Evidence alignment → rule constraints → risk scoring     │
│      → level assignment → interpretable output                │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L3  Perception  (four parallel branches)                     │
│   ┌──────────┬──────────┬──────────┬─────────────────────┐  │
│   │ Terrain  │ Machinery│ Materials│ Workers             │  │
│   │ Segment  │ Detect + │ Detect + │ Detect + PPE attrs  │  │
│   │          │ state    │ stacking │ + action            │  │
│   └──────────┴──────────┴──────────┴─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L2  Data   ★ CORE INNOVATION ★                               │
│      Real data capture/annotation ── Generative augmentation  │
│      pipeline ── Quality gates                                │
└──────────────────────────────────────────────────────────────┘
                              ▲
┌──────────────────────────────────────────────────────────────┐
│  L1  Input                                                    │
│      Fixed cameras / handheld photos / UAV / tower-mounted cam│
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Selection by Layer

### L1 Input Layer

| Source | Scenario | Note |
|--------|----------|------|
| Handheld photos | Inspection photography, hazard reporting | **Support first**; easiest to obtain; the MVP should start here |
| Fixed cameras | Base-station perimeter, equipment-room entrances | Supports video streams; required for behaviour recognition |
| UAV aerial | Whole-tower views, site terrain | Unusual viewpoint; requires dedicated data (see the AIDCON dataset) |
| Tower-mounted recorder | Work-at-height PPE / harness | The **most distinctive** input source for the telecommunication sector; a differentiation highlight |

> **Recommendation**: restrict the MVP to handheld photos plus fixed cameras. Treat UAV and tower-mounted recorders as extensions, to avoid over-extending the project.

### L2 Data Layer (see `03-Generative-Augmentation-Pipeline-EN.md`)

| Component | Selection | Alternatives |
|-----------|-----------|-------------|
| Base generative model | **SDXL / Stable Diffusion 3.5** | FLUX.1-dev (better quality, higher VRAM demand) |
| Domain adaptation | **LoRA fine-tuning** (200–500 seed images) | DreamBooth (needs less data but overfits easily) |
| Layout control | **ControlNet** (Canny / Depth / OpenPose / Seg) | GLIGEN, T2I-Adapter |
| Local editing | **SD Inpainting + SAM masks** | Paint-by-Example |
| Automatic annotation | **Grounding DINO + SAM 2** | ControlNet-Seg route knows the layout at generation time — zero annotation cost |
| Quality gates | CLIP-Score + FID + detector confidence + human spot-check | Joint structure/appearance metrics |

### L3 Perception Layer

| Branch | Task | Recommended model | Output |
|--------|------|------------------|--------|
| **Terrain** | Semantic segmentation | SegFormer-B2 / SAM 2 + lightweight classification head | Ground-class mask (level / potholed / waterlogged / trenched / sloped) |
| **Machinery** | Detection + state | YOLOv11 / RT-DETRv2 | Machine box + class + operating state + distance to persons |
| **Materials** | Detection + relations | YOLOv11 + stacking geometry rules | Material box + stack height ratio + boundary violation flag |
| **Workers** | Detection + attributes | YOLOv11-pose + multi-label PPE head | Person box + keypoints + PPE state vector |
| **Behaviour** | Action recognition | **ST-GCN++** (skeleton stream, resilient to low resolution) + VideoMAE-v2 (RGB stream) | Action class + confidence |

> **Key design decision**: the Workers branch uses a **shared backbone with multiple heads** (detection head + pose head + multi-label PPE head), avoiding the inference overhead and inconsistency of three independent models.

### L4 Fusion & Decision Layer ★ Second locus of academic contribution ★

**Do not use a simple weighted sum.** A **three-level hierarchical fusion** is recommended:

```
Level 1 ｜ Entity-level fusion
  · Spatial alignment: associate people–machines–materials–terrain in one image frame
  · Output an entity graph G = (V, E), V = detected entities, E = spatial/interaction relations
      e.g.  worker_1 --[distance 1.2 m]--> excavator_1
            worker_2 --[standing on]-----> terrain_uneven_3

Level 2 ｜ Rule layer
  · Encode safety regulations as decidable predicates (OSHA 1926 / GB 26859 / operator work procedures)
      R1: work at height (h > 2 m) ∧ ¬harness      → critical violation (w = 1.0)
      R2: person–machine distance < safe radius     → high risk       (w = 0.8)
      R3: stack height > 1.8 m ∧ unsecured          → medium risk     (w = 0.5)
      R4: person within 1 m of trench edge ∧ no rail → high risk      (w = 0.8)
  · Advantages: interpretable, auditable, alignable to regulation — the decisive factor for reviewers

Level 3 ｜ Learnable fusion
  · A GNN over the entity graph G, or an attention network, learns rule weights and interaction terms
  · Handles composite risks not covered by the rules
  · Output: scene risk score s ∈ [0,1] + per-source contribution (interpretability)
```

**Risk level mapping**: `s < 0.3` low ｜ `0.3 ≤ s < 0.6` medium ｜ `0.6 ≤ s < 0.85` high ｜ `s ≥ 0.85` critical

### L5 Application Layer

- **Web demonstration dashboard**: upload image/video → overlaid four-dimension detection visualisation → risk scorecard → list of triggered rules
- **Suggested stack**: FastAPI (backend) + Gradio or React (frontend); model serving via ONNX Runtime / TensorRT
- **Risk report**: optionally integrate a VLM (e.g. Qwen2.5-VL) to produce natural-language hazard descriptions and remediation advice — low cost, high demonstration value

---

## 3. Evaluation Plan

### 3.1 Core Experiment Matrix (Mandatory)

| ID | Experiment | Purpose | Key metrics |
|----|-----------|---------|-------------|
| E1 | Real-data baseline | Establish the baseline | mAP@50, mAP@50-95 |
| E2 | + conventional augmentation (flip/crop/Mosaic/HSV) | Rule out "any extra data helps" | Δ mAP vs E1 |
| E3 | **+ generative augmentation (this method)** | **Core contribution validation** | Δ mAP vs E2 |
| E4 | Synthetic-only training → real testing | Quantify the sim-to-real gap | mAP retention |
| E5 | Synthetic/real ratio sweep (0/25/50/100/200%) | Find the optimal ratio; plot the curve | mAP–ratio curve |
| E6 | Long-tail class study | Show larger gains on rare risk classes | Rare-class AP improvement |
| E7 | Robustness testing | Addresses the brief's robustness requirement | mAP degradation under low light / rain-fog / blur / small targets |
| E8 | Fusion module ablation | Validate the L4 design | Risk-level accuracy / macro-F1 / Kappa |
| E9 | Cross-site generalisation | Train on site A → test on site B | Cross-domain mAP drop |

> **E3 and E6 are the two strongest cards**: generative augmentation yields its most pronounced gains on **rare hazard classes** — scenes that essentially cannot be photographed in reality. This is the most persuasive evidence available.

### 3.2 Metric Definitions

| Level | Metrics |
|-------|---------|
| Detection | mAP@50, mAP@50-95, Precision, Recall, FPS |
| Segmentation | mIoU, Pixel Accuracy |
| Attributes / behaviour | Multi-label F1, Top-1 Accuracy, confusion matrix |
| Generation quality | FID, KID, CLIP-Score, human realism rating (5-point scale, ≥3 raters, report inter-rater Kappa) |
| Fusion decision | Risk-level Accuracy, Macro-F1, Cohen's Kappa (against safety-expert annotation) |
| System | End-to-end latency, VRAM footprint, model size |

### 3.3 Comparison Baselines

- General detectors: YOLOv8/v11, RT-DETR (no domain adaptation)
- Published PPE detection results on CHV / SHEL5K
- Published metrics from commercial products where obtainable
- Prior generative augmentation work: reported figures from Kim & Yi (2024) and Lee et al. (2025) — see the literature survey

---

## 4. Milestone Plan

Based on a **16-week** semester. For a 12-week variant, compress M2/M5 and downgrade UAV input and video behaviour recognition to optional.

### Phase Overview

| Phase | Weeks | Name | Key deliverables |
|-------|-------|------|-----------------|
| M0 | W1 | Project setup and survey | Requirements document, literature survey, role assignment |
| M1 | W2–W3 | Data infrastructure | Seed dataset + annotation guideline + risk taxonomy |
| M2 | W4–W6 | Generation pipeline | Fine-tuned generative model + synthetic data v1 + quality report |
| M3 | W7–W9 | Perception models | Four branches + E1/E2/E3 results |
| M4 | W10–W11 | Fusion and decision | Rule base + fusion module + E8 results |
| M5 | W12–W13 | System integration | Runnable demo system |
| M6 | W14–W15 | Full evaluation | E4–E9 complete + ablation tables |
| M7 | W16 | Delivery | Paper/report + defence slides + code repository |

### Detailed Milestones

#### M0 ｜ W1 — Project Setup and Survey
- [ ] Define the telecommunication construction **Risk Taxonomy** — the single most important first step; all subsequent annotation, generation and evaluation depend on it
- [ ] Complete the first draft of the literature survey (see `04-Literature-Survey-EN.md`)
- [ ] Fix roles and collaboration conventions (Git + DVC, experiment tracking via Weights & Biases or MLflow)
- [ ] **Deliverable**: Risk Taxonomy v1.0 (suggested: 4 major categories × 20–30 sub-classes)

#### M1 ｜ W2–W3 — Data Infrastructure
- [ ] Download and normalise public datasets (SODA / MOCS / CHV / SHEL5K — see document 02)
- [ ] Collect and manually screen **≥500** telecommunication scene images (base stations, towers, trenching, equipment rooms)
- [ ] Write an **annotation guideline** including edge-case adjudication rules, to prevent inconsistency across annotators
- [ ] Annotate **≥300** seed images (Label Studio / CVAT; pre-label with Grounding DINO then correct manually — saves roughly 60% of the effort)
- [ ] Split train/val/test; **the test set must consist entirely of real images and be strictly isolated**
- [ ] **Deliverable**: TelecomSeed-v1 dataset + annotation guideline

#### M2 ｜ W4–W6 — Generation Pipeline ★ CORE ★
- [ ] Comparative selection of the base model (SDXL vs SD3.5 vs FLUX, small-scale trials)
- [ ] LoRA fine-tuning to inject telecommunication construction domain characteristics
- [ ] Implement four generation routes: text-to-image / ControlNet layout control / inpainting / background replacement
- [ ] Implement the quality gates (CLIP + FID + detector filtering)
- [ ] Generate **≥3,000** synthetic images; record the post-gate retention rate
- [ ] **Deliverable**: TelecomSynth-v1 + generation quality report
- [ ] ⚠️ **Risk checkpoint**: if FID > 60 or the human realism rating < 3.0, roll back and adjust immediately — do not enter M3 with a defective dataset

#### M3 ｜ W7–W9 — Perception Models
- [ ] Train the four branches (the two highest-value branches, Workers and Machinery, may be done first)
- [ ] Run experiments E1 / E2 / E3 — **the decisive checkpoint for the project**
- [ ] Implement and tune the Workers multi-head structure
- [ ] **Deliverable**: model weights + E1–E3 comparison table
- [ ] ⚠️ **Decision point**: if E3 improves on E2 by less than 2 mAP, diagnose the cause (generation quality? ratio? class selection?) and adjust rather than pressing ahead

#### M4 ｜ W10–W11 — Fusion and Decision
- [ ] Encode the safety rule base (≥15 decidable rules, each citing its regulatory source)
- [ ] Implement entity-graph construction and three-level fusion
- [ ] Have 2–3 safety experts (or trained annotators following the regulations) assign risk levels to 200 test images as fusion ground truth
- [ ] Run experiment E8
- [ ] **Deliverable**: fusion module + risk rule base documentation

#### M5 ｜ W12–W13 — System Integration
- [ ] Complete the end-to-end inference pipeline
- [ ] Build the web demo interface (upload → visualisation → scorecard → rule list)
- [ ] Export and accelerate models (ONNX / TensorRT)
- [ ] **Deliverable**: runnable TelecomSafe demo

#### M6 ｜ W14–W15 — Full Evaluation
- [ ] Run experiments E4–E9 in full
- [ ] Build the robustness test set (synthetic degradation: low light, rain/fog, motion blur, occlusion, small targets)
- [ ] Finalise all ablation tables and figures
- [ ] **Deliverable**: complete experimental report

#### M7 ｜ W16 — Delivery
- [ ] Finalise the paper / technical report
- [ ] Defence slides + live demo rehearsal
- [ ] Tidy the code repository (README, environment, reproduction scripts, data documentation)
- [ ] **Deliverable**: all final outputs

---

## 5. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Trigger threshold |
|----|------|-----------|--------|-----------|------------------|
| R1 | Insufficient real telecommunication data | High | High | Transfer from public datasets + web collection + on-site capture; if necessary downgrade to "telecommunication-styled" scenes | < 300 seed images by end of W3 |
| R2 | Generated image quality inadequate; negative transfer | Medium | High | Strict quality gates; conservative ratio (start at 25%); retain the pure-real baseline | FID > 60, or E3 below E2 |
| R3 | Insufficient compute (diffusion training is expensive) | Medium | Medium | Use LoRA rather than full fine-tuning; SDXL-Turbo for speed; rent cloud GPUs; generate in batches | Single GPU < 16 GB |
| R4 | No video data for behaviour recognition | High | Medium | **Fallback**: replace video action recognition with single-frame pose plus rule-based judgement | No usable video by end of W9 |
| R5 | No ground truth for the fusion module | Medium | Medium | Generate weak labels from the rule base, calibrated with a small expert-annotated set | W10 |
| R6 | Team coordination / schedule imbalance | Medium | Medium | Weekly in-person meetings (a hard project requirement) + kanban + code review | Any milestone slips > 1 week |
| R7 | Scope creep (all four dimensions is too much) | High | High | MVP prioritises Workers + Machinery; simplified Terrain and Materials | W7 |

> **The most important entry is R7.** Delivering all four dimensions to high quality within a single semester is close to impossible. **Decide at M0 to focus on Workers + Machinery, with Terrain and Materials merely functional**, and state the scope boundary honestly in the report.

---

## 6. Compute and Environment

| Item | Recommended | Minimum |
|------|------------|---------|
| GPU | RTX 4090 24GB × 1–2, or A100 40GB | RTX 3090 24GB / cloud on demand |
| Generative fine-tuning | LoRA rank 16–32, batch 1–2, ~8–14 GB VRAM | 8-bit + gradient checkpointing compresses to ~10 GB |
| Detector training | YOLOv11-m, batch 16, ~12 GB | YOLOv11-s, batch 8 |
| Storage | ≥ 500 GB (raw + synthetic + weights + artefacts) | 250 GB |
| Frameworks | PyTorch 2.x, Ultralytics, diffusers, transformers, mmsegmentation | — |
| Experiment tracking | Weights & Biases / MLflow + DVC | Git + CSV tables |

---

## 7. Writing and Presentation Guidance

Recommended paper/report structure, mapped one-to-one onto the project's contributions:

1. **Introduction** — industry pain points in telecommunication construction safety + the data scarcity problem
2. **Related Work** — see `04-Literature-Survey-EN.md` (three strands: CV for construction safety / generative data augmentation / information fusion for risk assessment)
3. **Risk Taxonomy for Telecom Construction** — 🌟 Contribution 1: a sector-specific risk system
4. **Generative Data Augmentation Pipeline** — 🌟 Contribution 2: the core innovation
5. **Multi-dimensional Perception** — implementation of the four branches
6. **Hierarchical Information Fusion** — 🌟 Contribution 3: interpretable risk appraisal
7. **Experiments** — E1–E9
8. **Discussion & Limitations** — state honestly the domain gap, class coverage, and compliance boundaries
9. **Conclusion**

> **Bonus**: release the TelecomSynth synthetic dataset and the Risk Taxonomy publicly. A dataset is itself a citable academic contribution, and synthetic data avoids the privacy problems of real imagery.
