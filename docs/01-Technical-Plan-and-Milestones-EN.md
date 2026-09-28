# TelecomSafe — Technical Plan and Milestones

> Document version: v2.0 ｜ Generated: 2026-08-18 ｜ Revised: 2026-09-28 (milestones re-planned for the v3.0 two-phase flow)
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

> **Scope**: phase 1 handles **still images only** (all public data is imagery); video streams, UAV and tower-mounted recorders are extensions, to avoid over-extending the project.

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
- **Stack**: phase 1 uses a single-page **Gradio** demo (a few dozen lines); phase 2 adds a FastAPI backend only if needed. Deployment acceleration (ONNX / TensorRT) earns no marks and is out of scope
- **Risk report**: optionally integrate a VLM (e.g. Qwen2.5-VL) to produce natural-language hazard descriptions and remediation advice — low cost, high demonstration value

---

## 3. Evaluation Plan

### 3.1 Core Experiment Matrix (Mandatory)

| ID | Experiment | Purpose | Key metrics |
|----|-----------|---------|-------------|
| E1 | Real-data baseline (YOLO built-in augmentation **off**) · phase 1 | Establish the baseline | mAP@50, mAP@50-95, per-class AP |
| E2 | + conventional augmentation (YOLO default Mosaic/flip/HSV, etc.) · phase 1 | Rule out "any extra data helps"; **what phase 2 must beat** | Δ mAP vs E1 |
| E3 | **+ generative augmentation (this method) · phase 2, same config as E1/E2** | **Core contribution validation** | Δ mAP vs E2 (overall + weak classes) |
| E4 | Synthetic-only training → real testing | Quantify the sim-to-real gap | mAP retention |
| E5 | Synthetic/real ratio sweep (0/25/50/100/200%) | Find the optimal ratio; plot the curve | mAP–ratio curve |
| E6 | Long-tail class study | Show larger gains on rare risk classes | Rare-class AP improvement |
| E7 | Robustness testing | Addresses the brief's robustness requirement | mAP degradation under low light / rain-fog / blur / small targets |
| E8 | Fusion module ablation | Validate the L4 design | Risk-level accuracy / macro-F1 / Kappa |
| E9 | Cross-site generalisation | Train on site A → test on site B | Cross-domain mAP drop |

> **E3 and E6 are the two strongest cards**: generative augmentation yields its most pronounced gains on **rare hazard classes** — scenes that essentially cannot be photographed in reality. This is the most persuasive evidence available. In v3.0, phase 2 already generates data targeted at the baseline's weak-class list, so E6 follows directly from it.

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

Based on a **16-week** semester and organised around the v3.0 **two-phase** flow (flow and technical detail in [05 Technological Roadmap](05-Technological-Roadmap-EN.md)). For a 12-week variant, compress M3 and M5–M6, and make video behaviour recognition and Terrain / Materials optional.

### Phase Overview

| Stage | Milestone | Weeks | Name | Key deliverables | Gate | Status |
|-------|-----------|-------|------|-----------------|------|--------|
| Preparation | M0 | W1 | Setup and Risk Taxonomy | Risk Taxonomy v1.0, roles | — | ✅ Done offline |
| Preparation | M1 | W2–W3 | Public data curation | TelecomSeed + 🔒 TelecomEval + `licence_manifest.csv` | TG1 | ✅ Done offline |
| **Phase 1** | **M2** | **W4–W7** | **Baseline Demo** | Baseline weights + E1/E2 + rule judgement + Demo v1 | **TGB** | 🚧 In progress |
| Phase 2 | M3 | W8–W10 | Generative augmentation | TelecomSynth + generation quality report | TG2 | |
| Phase 2 | M4 | W11–W12 | Retrain with the same config | E3 comparison table + Demo v2 | TG3 | |
| Phase 2 | M5 | W13–W14 | Fusion upgrade | Level-3 fusion + E8 | TG4 | |
| Phase 2 | M6 | W13–W15 | Full evaluation | E4–E9 + final Demo v2 | TG5 | |
| Delivery | M7 | W16 | Delivery | Project report + defence + code repository | — | |

### Detailed Milestones

#### M0 ｜ W1 — Setup and Risk Taxonomy ✅
- [x] Risk Taxonomy v1.0 (done offline)
- [x] First draft of the literature survey (see `04-Literature-Survey-EN.md`)
- [ ] Commit the taxonomy to the repository (suggested `data/taxonomy.yaml`, with every class name and its decision criterion)

#### M1 ｜ W2–W3 — Public Data Curation ✅
- [x] T1 academic datasets, T2 community datasets and T3 openly licensed imagery curated (done offline; see document 02)
- [x] TelecomSeed and 🔒 TelecomEval carved out
- [ ] Record the actual counts in the repository (TG1 criteria: TelecomSeed ≥ 200, TelecomEval ≥ 150), plus a hash of the TelecomEval file list
- [ ] Confirm `licence_manifest.csv` covers every T3 image

#### M2 ｜ W4–W7 — Baseline Demo (Phase 1)
- [ ] **Class mapping table**: align every dataset's labels to the taxonomy classes (first job of W4)
- [ ] Convert all data to a single YOLO / COCO format and fix the train / val split
- [ ] Train a single YOLOv11 detector covering Workers + Machinery
- [ ] Run E1 (built-in augmentation off) and E2 (YOLO default conventional augmentation)
- [ ] Report per-class AP and the confusion matrix on TelecomEval, and list the 3–5 weakest classes
- [ ] Commit `configs/baseline.yaml` (read-only from then on; reused in phase 2)
- [ ] Encode 5–10 hard rules (each citing its regulatory source) that output a low / medium / high risk level
- [ ] Gradio Demo v1: upload → detection boxes → risk-level card → triggered rules
- [ ] **Deliverable**: baseline weights + E1/E2 results + weak-class list + Demo v1
- [ ] ⚠️ **TGB (end W7)**: demo runs end-to-end, E1/E2 recorded, configuration committed; otherwise take DB

#### M3 ｜ W8–W10 — Generative Augmentation ★ CORE ★
- [ ] Stage 0 specification library: cover the M2 weak-class list first
- [ ] LoRA fine-tuning (environment and trial runs prepared by Member B during W4–W7)
- [ ] Advance generation routes from lowest to highest risk: inpainting → background swap → T2I / ControlNet
- [ ] Four quality gates (G3 reuses the M2 baseline detector directly)
- [ ] Generate **≥3,000** synthetic images; record the post-gate retention rate
- [ ] **Deliverable**: TelecomSynth-v1 + generation quality report
- [ ] ⚠️ **TG2 (end W10)**: FID < 50, human realism ≥ 3.0; otherwise take D2 — do not enter M4 with a defective dataset

#### M4 ｜ W11–W12 — Retrain with the Same Configuration ★ Decisive checkpoint ★
- [ ] Run E3 with the same `configs/baseline.yaml`, changing only the training data
- [ ] Compare E1 / E2 / E3 on the same TelecomEval, focusing on the weak classes
- [ ] Swap the new weights into the demo to obtain Demo v2
- [ ] **Deliverable**: E1–E3 comparison table + Demo v2
- [ ] ⚠️ **TG3 (end W12)**: E3 improves on E2 by ≥ 2.0 mAP (overall or on weak classes); otherwise diagnose the cause (generation quality? ratio? class selection?) and take D3 rather than pressing ahead

#### M5 ｜ W13–W14 — Fusion Upgrade
- [ ] Extend the rule base to ≥ 15 decidable rules
- [ ] Entity-graph construction + level-3 learnable fusion (optional)
- [ ] Expert risk annotation of 200 images (recruit from W10, finish by W12) as fusion ground truth
- [ ] Run experiment E8
- [ ] ⚠️ **TG4 (end W14)**: risk-level accuracy ≥ 0.70; otherwise keep the phase 1 pure-rule judgement (D4)

#### M6 ｜ W13–W15 — Full Evaluation
- [ ] Run experiments E4–E9 in full
- [ ] Build the robustness test set (synthetic degradation: low light, rain/fog, motion blur, occlusion, small targets)
- [ ] Finalise all ablation tables and figures
- [ ] ⚠️ **TG5 (end W15)**: Demo v2 runs end-to-end, single image < 3 s; otherwise reuse Demo v1 plus a screen recording (D5)

#### M7 ｜ W16 — Delivery
- [ ] Finalise the project report (following the official template structure in §7)
- [ ] Defence slides + live demo rehearsal
- [ ] Tidy the code repository (README, environment, reproduction scripts, data documentation)

---

## 5. Risk Register

| ID | Risk | Likelihood | Impact | Mitigation | Trigger threshold |
|----|------|-----------|--------|-----------|------------------|
| R1 | Source datasets name labels inconsistently, so merged labels contradict each other | High | High | Write the class mapping table first thing in M2; spot-check 50 annotations per community dataset | Mapping table not done by end of W4 |
| R2 | Baseline configuration or TelecomEval changes mid-project, so phase 2 cannot be compared fairly | Medium | High | Commit `configs/baseline.yaml` and a TelecomEval hash; treat both as read-only | Any change to either |
| R3 | Limited telecom-specific real data leaves the baseline weak on telecom classes | High | Medium | This is exactly phase 2's rationale: the weak-class list drives targeted generation | Weak-class AP well below overall at TGB |
| R4 | Generated image quality inadequate; negative transfer | Medium | High | Strict quality gates; conservative ratio (start at 25%); inpainting route first | FID > 60, or E3 below E2 |
| R5 | The team slows down after Demo v1 and phase 2 starts late | Medium | High | Settle the weak-class list and M3 start date at the TGB meeting; Member B prepares the generation environment during phase 1 | Generation not started by end of W8 |
| R6 | Insufficient compute (diffusion training is expensive) | Medium | Medium | Use LoRA rather than full fine-tuning; SDXL-Turbo for speed; rent cloud GPUs; generate in batches | Single GPU < 16 GB |
| R7 | No ground truth for the fusion module | Medium | Medium | Weak labels from the rule base, calibrated with a small expert-annotated set; recruit from W10 | Still no annotation by W12 |
| R8 | No video data for behaviour recognition | High | Low | Not in phase 1; in phase 2 use single-frame pose plus rules instead (D6) | — |
| R9 | Team coordination / schedule imbalance | Medium | Medium | Weekly in-person meetings (a hard project requirement) + kanban + code review | Any milestone slips > 1 week |
| R10 | Scope creep (all four dimensions is too much) | High | High | Phase 1 covers Workers + Machinery only (D8 applied by default); add Terrain / Materials in phase 2 if time allows | — |

> **R1 and R2 matter most**: R1 decides whether the baseline can be trained at all, and R2 decides whether phase 2's conclusions will hold up. Both must be settled in the first week of M2.

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

The EE6008 project report follows the official school template `template/EE6008-Project ReportTemplate.docx`. It is a **project management report**, not an academic paper, and three points need particular attention:

1. **There is no Related Work chapter.** The literature survey in document 04 cannot be transplanted wholesale. Compress it into §1 Purpose/Objectives as the project justification, and list the sources under §8 References.
2. **Planned vs actual comparison is required.** Both §4 Schedule and §5 Cost have "Planned" and "Actual" columns. **Actual completion dates must be recorded throughout the project**, not reconstructed at the end.
3. **Every member must write an individual report and reflection.** §7 is written individually (engineering knowledge learned, problem analysis, design/development of solutions, anything to share). It cannot be ghost-written and bears directly on individual grades.

### 7.1 EE6008 Report Chapter Mapping

Organised by the official template's eight sections plus appendix, with the source of each:

| Official section | Template requirement | Source material | Suggested length |
|-----------------|---------------------|----------------|-----------------|
| **1. Purpose / Project Objectives** | Overview and objectives | Document 07 Project Purpose; document 00 §1/§4; the research gaps G1–G5 from document 04 (compressed to 1–2 paragraphs) | 1–2 pages |
| **2. Project Summary** | Work done / problems solved / achievements | **The technical core of the report**: document 01 §1 five-layer architecture, document 05 two-phase flow (baseline → augmentation), document 03 generation pipeline, document 01 §3 results E1–E9 | 8–15 pages |
| **3. Scope** | Final total scope, deliverables, activity summary, **changes** | Document 07 deliverables; **the cancellation of field collection (v2.1), the switch to the two-phase flow (v3.0) and any downgrade path triggered must all be documented here** | 2–3 pages |
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
2.2 Architecture and two-phase flow    ← five-layer architecture (doc 01 §1) + two-phase flow (doc 05)
2.3 Telecom construction risk taxonomy ← 🌟 Contribution 1
2.4 Baseline system                    ← public data curation, baseline detector, rule judgement, Demo v1 (phase 1)
2.5 Generative data augmentation       ← 🌟 Contribution 2, the report's most important section (doc 03)
    · Risk scenario library driven by the baseline's weak classes
    · Generation routes and four quality gates
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
| Design/development of solutions | The design you chose and the trade-off. E.g. "I chose the inpainting route over T2I because annotations are inherited and the domain gap is smaller" | Technology selection rationale (doc [02](02-Datasets-and-Pretrained-Models-EN.md)) and downgrade paths (doc [05 §4](05-Technological-Roadmap-EN.md)) |
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
| 2 | `<<Name>>` | Generation Lead; LoRA fine-tuning, four generation engines, quality gates, TelecomSynth dataset | Chapter 2.5; Pages xx–xx |
| 3 | `<<Name>>` | Perception Lead (Workers); Workers model, behaviour recognition, core experiments E1–E3 | Chapters 2.4, 2.7; Pages xx–xx |
| 4 | `<<Name>>` | Perception Lead (Scene); Machinery/Materials/Terrain models, experiment E9 | Chapter 2.4; Pages xx–xx |
| 5 | `<<Name>>` | Fusion & System Lead; rule base, three-level fusion, demo, experiment tracking | Chapters 2.4, 2.6, 6; Pages xx–xx |

> The template's own example mentions a "team project video". **Confirm with the supervisor whether a project video must be submitted.** If so, reserve recording time during W14–W15.
