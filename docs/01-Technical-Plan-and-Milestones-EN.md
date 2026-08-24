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
│      Public data curation/annotation ── Generative augment.   │
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
- [ ] **T2 community datasets**: download the Roboflow Universe telecom tower set, the safety harness sets, and the Kaggle construction safety set (includes NO-Hardhat negatives)
- [ ] **T3 open-licence curation**: search Openverse / Wikimedia Commons and manually screen **200–500** telecommunication scene images, building `licence_manifest.csv` with source and attribution as you go
- [ ] ❌ ~~Field collection~~ — cancelled in v2.0; this project performs no on-site capture
- [ ] Write an **annotation guideline** including edge-case adjudication rules, to prevent inconsistency across annotators
- [ ] Annotate **≥200** seed images (Label Studio / CVAT; pre-label with Grounding DINO then correct manually — saves roughly 60% of the effort)
- [ ] 🔒 Carve out and **freeze the TelecomEval test set (150–300 real images)** — never used in LoRA fine-tuning or generation conditioning
- [ ] **Deliverable**: TelecomSeed-v1 + TelecomEval-v1 + annotation guideline + `licence_manifest.csv`

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
| R1 | Insufficient real telecommunication data (**field collection cancelled**; entirely dependent on public sources) | High | High | T1 academic dataset transfer + T2 community specialist sets + T3 open-licence curation; volume is inherently limited, hence greater reliance on T4 synthesis. Downgrade to generalised "work-at-height / tower-type" scenes if needed (D1) | TelecomSeed < 150 images by end of W3 |
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

### ⚠️ Important Correction: The School Report Template Is Not an Academic Paper Structure

Version 1.0 of this section recommended an academic paper structure (Introduction / Related Work / Method / Experiments / Conclusion). **On checking the official school template `template/EE6008-Project ReportTemplate.docx`, the EE6008 project report turns out to be a project management report, not an academic paper.**

The two differ substantially, and the official template governs:

| Academic paper (original suggestion) | EE6008 official report template |
|-------------------------------------|--------------------------------|
| Introduction | 1. Purpose / Project Objectives |
| **Related Work (standalone chapter)** | ❌ **No standalone literature review chapter** |
| Method (several technical chapters) | 2. Project Summary (merged into one chapter) |
| Experiments | Folded into 2. Project Summary and 6. Outcomes / Benefits |
| — | 3. Scope (deliverables, activities, **changes to scope**) |
| — | 4. Schedule (planned vs **actual** milestone dates) |
| — | 5. Cost (planned vs actual) |
| Discussion & Limitations | Folded into 6. Outcomes / Benefits |
| — | 7. **Individual Reports from Team Members** (written individually + reflection) |
| References | 8. References |
| — | Appendix — Project Members Information (contribution table) |

**The three most consequential differences**:

1. **There is no Related Work chapter.** The literature survey in document 04 cannot be transplanted wholesale. Compress it into §1 Purpose/Objectives as the project justification, and list the sources under §8 References.
2. **Planned vs actual comparison is required.** Both §4 Schedule and §5 Cost have "Planned" and "Actual" columns. **This means actual completion dates must be recorded throughout the project**, not reconstructed at the end. Record each milestone's actual completion date on the kanban from M0 onwards.
3. **Every member must write an individual report and reflection.** §7 is written individually and covers "engineering knowledge learned, problem analysis, design/development of solutions, anything to share." This cannot be ghost-written and bears directly on individual grades.

---

### 7.1 EE6008 Report Chapter Mapping

Organised by the official template's eight sections plus appendix, with the source of each:

| Official section | Template requirement | Source material | Suggested length |
|-----------------|---------------------|----------------|-----------------|
| **1. Purpose / Project Objectives** | Overview and objectives | Document 07 Project Purpose; document 00 §1/§4; the research gaps G1–G5 from document 04 (compressed to 1–2 paragraphs) | 1–2 pages |
| **2. Project Summary** | Work done / problems solved / achievements | **The technical core of the report**: document 01 §1 five-layer architecture, document 03 generation pipeline, document 01 §3 results E1–E9 | 8–15 pages |
| **3. Scope** | Final total scope, deliverables, activity summary, **changes** | Document 07 deliverables; **if any downgrade path D1–D8 was triggered, the change must be documented here** | 2–3 pages |
| **4. Schedule** | Milestones: planned vs actual dates | Document 07 Summary Milestones plus actual completion dates recorded throughout | 1 page (table) |
| **5. Cost** | Cost items: planned vs actual | Document 07 Summary Budget (expected S$0 for this project; report it as such) | 0.5 page |
| **6. Outcomes / Benefits** | Outcomes and benefits | Experimental conclusions, system demo, dataset outputs; **limitations and honest caveats also belong here** | 2–4 pages |
| **7. Individual Reports** | Per member: name, contributions, reflection | **Written by each member individually**; the leader does not ghost-write | 1–2 pages each |
| **8. References** | References | The 50 references in document 04 §7, filtered to those actually cited | 1–2 pages |
| **Appendix** | Member table: name / project contributions / report contributions | The RACI matrix in document 06 plus the activity matrix in document 07 | 0.5 page |

### 7.2 Suggested Internal Structure for §2 Project Summary

This is the most technically substantial chapter. The template does not prescribe an internal structure; the following retains the logic of the academic layout while compressing it into a single chapter:

```
2.1 Problem and technical challenges   ← three causes of data scarcity (doc 07 Purpose)
2.2 System architecture overview       ← five-layer architecture (doc 01 §1)
2.3 Telecom construction risk taxonomy ← 🌟 Contribution 1
2.4 Generative data augmentation       ← 🌟 Contribution 2, the report's most important section (doc 03)
    · Risk scenario specification library
    · Four generation engines
    · Four quality gates
2.5 Multi-dimensional perception       ← four branches (doc 01 §2 L3)
2.6 Hierarchical information fusion    ← 🌟 Contribution 3 (doc 01 §2 L4)
2.7 Experimental setup and results     ← E1–E9, centred on E3 and E7 (doc 01 §3)
2.8 Ablation studies                   ← A1–A7 (doc 03 §9)
```

### 7.3 Guidance for §7 Individual Reports

The template requires each member to cover four points. This section **must be written by the member personally** and is direct evidence for individual grading:

| Template requirement | How to write it | Material to draw on |
|---------------------|----------------|-------------------|
| Engineering knowledge learned | Be specific to a technique; avoid generalities. E.g. "LoRA fine-tuning taught me how low-rank adaptation avoids overfitting on only 500 samples" | Your own module |
| Problem Analysis | Describe a problem you actually encountered and analysed. E.g. "I found prompt disobedience in generated images and used CLIP-Score to isolate the 15% that were semantically inconsistent" | Failure mode table (doc 03 §11) |
| Design/development of solutions | The design you chose and the trade-off. E.g. "I chose the inpainting route over T2I because annotations are inherited and the domain gap is smaller" | Alternatives matrix (doc 05 §7) |
| Anything to share | Collaboration experience, time management, reflections on the project | Periodic contribution statements (doc 06 §8) |

> **Recommendation**: each member writes a 200-word summary at W4 / W8 / W12 / W16 (already recommended in doc 06 §8). At M7 these four notes assemble into the individual report, avoiding reliance on recall.

### 7.4 What Must Be Recorded Throughout (Otherwise It Cannot Be Reconstructed)

The official template requires planned-versus-actual comparisons and individual contribution statements. These **must be captured as the project runs**:

```
□ Actual completion date of every milestone   → §4 Schedule, Actual column
□ Date and reason for every downgrade trigger → §3 Scope, Changes
□ Costs actually incurred (e.g. cloud GPU)    → §5 Cost, Actual column
□ Each member's modules and main outputs      → §7 + Appendix
□ Report sections and page ranges per member  → Appendix, Report Contribution column
□ Weekly minutes and decision records         → evidence base for §3 Changes
```

**Recommendation**: create a `progress/` directory in the repository with `milestones.md` for actual dates and `changes.md` for scope changes, updated by the leader after each weekly meeting.

### 7.5 Example Appendix Member Table

Following the template's own examples (`e.g., Team Leader`, `e.g. Pages 3-6, 24-25, Chapter 2, Appendix A`):

| # | Name | Project contributions | Report Contribution |
|---|------|----------------------|-------------------|
| 1 | `<<Name>>` | Team Leader; Data Lead; Risk Taxonomy, annotation guideline, TelecomSeed dataset | Chapters 1, 3, 4; Pages xx–xx |
| 2 | `<<Name>>` | Generation Lead; LoRA fine-tuning, four generation engines, quality gates, TelecomSynth dataset | Chapter 2.4; Pages xx–xx |
| 3 | `<<Name>>` | Perception Lead (Workers); Workers model, behaviour recognition, core experiments E1–E3 | Chapters 2.5, 2.7; Pages xx–xx |
| 4 | `<<Name>>` | Perception Lead (Scene); Machinery/Materials/Terrain models, experiment E9 | Chapter 2.5; Pages xx–xx |
| 5 | `<<Name>>` | Fusion & System Lead; rule base, three-level fusion, web demo, experiment tracking | Chapters 2.6, 6; Pages xx–xx |

> The template's own example mentions a "team project video". **Confirm with the supervisor whether a project video must be submitted.** If so, reserve recording time during M5–M6.

---

### 7.6 If Submitting to a Journal Later (Optional, Post-Project)

The EE6008 report and an academic paper serve different purposes. To pursue submission to *Automation in Construction* as described in roadmap horizon H3, rewrite separately along academic lines:

```
1. Introduction         ← industry pain points + data scarcity
2. Related Work         ← document 04 (three strands)
3. Risk Taxonomy        ← 🌟 Contribution 1
4. Generative Pipeline  ← 🌟 Contribution 2
5. Multi-dim Perception ← four branches
6. Hierarchical Fusion  ← 🌟 Contribution 3
7. Experiments          ← E1–E9
8. Discussion & Limitations
9. Conclusion
```

> **Bonus**: release the TelecomSynth synthetic dataset and the Risk Taxonomy publicly. A dataset is itself a citable academic contribution, and synthetic data avoids the privacy problems of real imagery.
