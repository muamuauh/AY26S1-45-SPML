# TelecomSafe — Technological Roadmap

> Document version: v1.0 ｜ Generated: 2026-08-19
> Chinese counterpart: [05-技术路线图-CN.md](05-技术路线图-CN.md)
> Companion documents: `01-Technical-Plan-and-Milestones-EN.md` (schedule), `06-Teamwork-Allocation-EN.md` (people)

---

## 0. How This Differs from the Milestone Document

| | `01-Technical-Plan-and-Milestones` | **This document (roadmap)** |
|---|---|---|
| Perspective | **Time**: what is done when | **Technology**: how capability evolves |
| Unit | Weeks, deliverables, checkpoints | Technology layers, maturity, decision gates |
| Answers | "What is due in week 7?" | "Where do we fall back if this technology fails?" |

Use both together: the milestone document governs schedule, the roadmap governs technology choices and fallbacks.

---

## 1. Roadmap Principles

### 1.1 Three Design Rules

| # | Rule | Meaning |
|---|------|---------|
| 1 | **Every layer has a minimum working version** | The first version of any technology layer must run end to end, however crude. Close the loop first, optimise accuracy second |
| 2 | **Every decision gate has a fallback** | A technology with no alternative is not allowed on the critical path. Every TG gate defines a downgrade path |
| 3 | **Concentrate the innovation, keep the engineering conservative** | The entire innovation budget goes to generative augmentation (L2) and information fusion (L4). Perception (L3) and system (L5) layers use mature, proven solutions only — no technical adventures |

### 1.2 Three Horizons

```
H1  MVP closed loop    W1–W9    "It runs"
    └─ Single dimension (Workers) + basic generation + detection output
       Goal: prove generative augmentation works (judged by experiment E3)

H2  Full framework     W10–W16  "It can be evaluated"
    └─ Four-dimension perception + three-level fusion + integration + full experiments
       Goal: deliver a defensible, complete TelecomSafe

H3  Extensions         Post-project  "It can be published / deployed"
    └─ Video behaviour, UAV viewpoint, edge deployment, dataset release, journal submission
       Goal: academic and engineering value beyond the course requirement
```

> ⚠️ **Do not enter H2 if H1 has not been met.** If experiment E3 at W9 shows that synthetic data delivers no improvement, adding four-dimension perception will only magnify the problem. Better to spend two more weeks in H1.

---

## 2. Layered Technology Evolution

The following swimlane chart shows how each of the five technology layers evolves. Each cell states the technology form for that phase.

```
        │ H1 MVP (W1–W9)          │ H2 Full (W10–W16)         │ H3 Extension (post)
────────┼─────────────────────────┼───────────────────────────┼──────────────────────
        │ Public dataset transfer │ + Real telecom data growth│ + Multi-site, seasons
L2 Data │ 300 annotated seeds     │ + Terrain/material subsets│ + Crowdsourced/partner
        │ Risk Taxonomy v1.0      │ Risk Taxonomy v2.0        │ Industry standard prop.
────────┼─────────────────────────┼───────────────────────────┼──────────────────────
L2 Gen  │ SDXL + LoRA             │ + Layered LoRA composition│ + SD3.5/FLUX upgrade
 ★CORE★ │ T2I + Inpainting        │ + ControlNet Seg/Pose/Dep.│ + Video gen (behaviour)
        │ Gates G1+G3             │ Full gates G1–G4          │ Adaptive gate thresholds
        │ 3,000 synthetic images  │ 8,000–10,000              │ Public dataset release
────────┼─────────────────────────┼───────────────────────────┼──────────────────────
        │ YOLOv11, one branch     │ Four branches in parallel │ + RT-DETR control
L3 Perc.│ Detection + PPE labels  │ + Segmentation (Terrain)  │ + Open-vocab (GDINO)
        │ Single-frame pose       │ + Skeleton act (ST-GCN++) │ + Two-stream fusion
────────┼─────────────────────────┼───────────────────────────┼──────────────────────
L4 Fuse │ Direct rules (if-then)  │ Three-level fusion        │ + D-S evidence control
 ★CORE★ │ 5 hard rules            │ 15+ rules + graph + GNN   │ + Temporal risk evolution
        │ Four risk levels        │ Continuous score + attrib.│ + Interpretability viz
────────┼─────────────────────────┼───────────────────────────┼──────────────────────
        │ CLI scripts             │ FastAPI + Gradio web demo │ + Edge deploy (Jetson)
L5 Sys. │ JSON result output      │ + Overlays + scorecard    │ + Real-time video stream
        │ Manual experiment runs  │ W&B tracking + repro scripts│ + VLM narrative reports
```

---

## 3. Technology Decision Gates

Decision gates are the core mechanism of this roadmap: **on reaching a given point in time, use objective metrics to decide whether to continue, adjust, or downgrade.** Every gate must be formally reviewed in a team meeting, with the conclusion recorded in the minutes.

### TG1 ｜ End of W3 — Data Foundation Gate

| Item | Content |
|------|---------|
| **Criteria** | ≥ 300 annotated real telecommunication seed images; Risk Taxonomy v1.0 finalised |
| ✅ Pass | Proceed to generation pipeline development as planned |
| ⚠️ Partial (150–300 images) | Reduce the Risk Taxonomy to 4 categories × 12 sub-classes; rely more on ControlNet than T2I during generation |
| ❌ Fail (< 150 images) | **Downgrade path D1**: abandon the "telecommunication-specific" positioning; reframe as "work-at-height and tower-type construction" and use public datasets plus a small set of telecommunication images for style transfer |

### TG2 ｜ End of W6 — Generation Quality Gate ★ Most Critical ★

| Item | Content |
|------|---------|
| **Criteria** | FID(synthetic, real) < 50; human realism rating ≥ 3.0/5; post-gate retention ≥ 40% |
| ✅ Pass | Bulk-generate 3,000 images and proceed to perception model training |
| ⚠️ Partial (FID 50–70) | Raise the inpainting route's share to 50% (smallest domain gap) and reduce pure T2I |
| ❌ Fail (FID > 70 or rating < 2.5) | **Downgrade path D2**: abandon T2I novel-scene generation; keep only inpainting and background replacement — the two routes that edit real images. Their domain gap is inherently minimal and they almost never fail |

### TG3 ｜ End of W9 — Augmentation Effectiveness Gate ★ Project Make-or-Break ★

| Item | Content |
|------|---------|
| **Criteria** | E3 (generative augmentation) improves mAP by ≥ 2.0 over E2 (conventional augmentation) |
| ✅ Pass | Enter H2; expand to four-dimension perception and fusion |
| ⚠️ Gain of 0–2.0 | Diagnose in order: ① check label noise (is the consistency check active?) ② reduce synthetic ratio to 25% ③ switch to class-adaptive ratios, supplying data only to long-tail classes |
| ❌ No gain or a decline | **Downgrade path D3**: narrow the research question from "synthetic data improves overall performance" to **"synthetic data improves long-tail class performance"** — report rare-class AP only. The narrower claim usually still holds and retains academic value. State honestly that overall performance did not improve |

> **On D3**: this is not failure but confining the conclusion to what is actually true. Kim & Yi (2024) achieved only ~64% mAP with purely synthetic data, which shows the domain gap is real. Reporting a limited but honest finding is far more credible than forcing a claim of across-the-board improvement.

### TG4 ｜ End of W11 — Fusion Feasibility Gate

| Item | Content |
|------|---------|
| **Criteria** | Risk-level classification accuracy ≥ 0.70 against 200 expert-annotated images |
| ✅ Pass | Retain the three-level fusion; proceed to system integration |
| ⚠️ 0.55–0.70 | Drop level 3 (learnable fusion) and keep only L1 entity graph + L2 rule layer (pure rules are usually steadier and fully interpretable) |
| ❌ < 0.55 | **Downgrade path D4**: check inter-annotator agreement (Kappa < 0.5 means the annotation itself is unreliable and the problem is not the model). If the annotation is reliable, simplify to the conservative rule "overall risk = highest single-source risk" |

### TG5 ｜ End of W13 — System Integration Gate

| Item | Content |
|------|---------|
| **Criteria** | End-to-end pipeline runs; single-image inference < 3 s; demo interface presentable |
| ✅ Pass | Proceed to full evaluation |
| ❌ Fail | **Downgrade path D5**: drop the web interface in favour of scripts, rendered output images and a screen recording. Slightly weaker for the defence, but the academic conclusions are unaffected |

---

## 4. Technology Dependencies and Critical Path

```
Risk Taxonomy ──┬──> Annot. guideline ──> Seed dataset ──┬──> LoRA ──> Gen engines ──┐
   [TG1]        │                                        │    [TG2]                  │
                │                                        │                           ▼
                └──> Spec library (Stage 0) ─────────────┘                  Synthetic dataset
                                                                                     │
                                                                                     ▼
Public datasets ──> Pretrain/transfer ──> Perception baseline (E1) ──> Mixed training (E3) [TG3]
                                                │                                 │
                                                ▼                                 ▼
                                      Four-branch output ──────────────> Entity graph
                                                                                     │
Safety regulations ──> Rule predicate base ─────────────────────────────> Rule layer [TG4]
                                                                                     │
Expert risk annotation ────────────────────────────────────────────> Learnable fusion
                                                                                     │
                                                                                     ▼
                                                                        System integration [TG5]
```

### Critical Path

**Risk Taxonomy → annotation guideline → seed data → LoRA → generation engines → synthetic data → experiment E3**

Any delay on this chain delays the whole project. Three notes:

1. **The Risk Taxonomy is the start of the critical path and the most underestimated item.** It is not "a list of categories" but a definition of **decidable criteria** for each risk (what counts as "poorly stored"? which height-to-width ratio?). Without this, annotation, generation and evaluation will each mean something different.
2. **Seed data collection is the only step that compute cannot accelerate.** Start it in parallel in W1; do not wait for the taxonomy to be finalised.
3. **Expert risk annotation (fusion ground truth) can be done early in parallel.** It is not on the critical path, but it is routinely deferred until the end, leaving TG4 unmeasurable. Start recruiting annotators in W8.

---

## 5. Technology Maturity Assessment

A TRL-like reading of how well-understood each technology is within this project, used to guide risk allocation.

| Technology | Maturity | Risk | Note |
|-----------|----------|------|------|
| YOLOv11 object detection | 🟢 Mature | Low | Industrial-grade, fully documented, essentially cannot fail |
| SDXL + LoRA fine-tuning | 🟢 Mature | Low | Abundant community recipes and tutorials |
| SD Inpainting editing | 🟢 Mature | Low | Annotations inherited; the steadiest generation route |
| SAM 2 segmentation | 🟢 Mature | Low | Works out of the box |
| Grounding DINO pre-labelling | 🟢 Mature | Low | Large efficiency gain, no technical risk |
| ControlNet-Seg layout control | 🟡 Medium | Medium | Requires programmatic layout-map generation; the engineering effort is widely underestimated |
| ST-GCN++ skeleton action | 🟡 Medium | Medium | **Depends on video data**; without it the whole line is infeasible (see D6) |
| Quality gate threshold calibration | 🟡 Medium | Medium | No off-the-shelf standard; must be determined experimentally, consuming much of W6 |
| Three-level information fusion | 🔴 Novel | High | Original to this project, no mature precedent; reserve debugging time |
| Rule predicate base construction | 🟡 Medium | Medium | Technically easy, but requires regulatory research and expert confirmation — time-consuming |
| Terrain semantic segmentation | 🔴 Novel | High | **No public data**; class definitions subjective; the most likely candidate for downgrade |
| Material storage state judgement | 🔴 Novel | High | As above; "improper" lacks an objective definition |

**Risk allocation conclusion**: put the strongest people on the 🔴 items (fusion, terrain, materials); the 🟢 items can go to less experienced members or use off-the-shelf solutions directly.

---

## 6. Consolidated Downgrade Paths

All fallbacks are collected here for quick reference during gate meetings.

| ID | Trigger | Downgrade action | Effect on outcomes |
|----|---------|-----------------|-------------------|
| **D1** | < 150 real telecommunication images | Reposition to "work-at-height / tower-type construction" | Weakens sector specificity (gap G1) but does not affect the core generative augmentation contribution |
| **D2** | Generation quality FID > 70 | Keep only inpainting and background replacement | Less synthetic diversity, but smaller domain gap — E3 may even improve |
| **D3** | E3 shows no gain | Narrow the claim to "improves long-tail class performance" | Narrower selling point but still valid; must be stated honestly |
| **D4** | Fusion accuracy < 0.55 | Remove the learnable layer; pure rule-based fusion | Loses the learning-based novelty of L4, but interpretability improves |
| **D5** | System integration fails | Scripts + screen recording instead of a web interface | Affects only the defence presentation, not the academic conclusions |
| **D6** | No video data | Replace action recognition with **single-frame pose + rules** (e.g. arm angle for climbing) | No temporal actions, but PPE + pose still covers most unsafe behaviours |
| **D7** | Insufficient compute (< 16 GB VRAM) | SD 1.5 instead of SDXL; YOLOv11-s instead of -m; 8-bit quantisation | Slight accuracy loss; the full pipeline still runs |
| **D8** | More than 2 weeks behind schedule | Drop the Terrain and Materials dimensions; deliver Workers + Machinery only | "Four-dimension" becomes "two-dimension"; scope must be redefined in the report |

> **D8 is the last line of insurance.** Document 01 §5 R7 already recommends focusing on two dimensions from the outset; if that recommendation is followed, D8 becomes unnecessary.

---

## 7. Technology Selection Alternatives Matrix

A/B/C options for the key technology decisions, to enable rapid switching.

| Decision point | Option A (preferred) | Option B (alternative) | Option C (last resort) |
|---------------|---------------------|----------------------|----------------------|
| Generative base | SDXL 1.0 | SD 3.5 Medium | SD 1.5 |
| Bulk generation speed | SDXL-Turbo | LCM-LoRA | Full SDXL (slow but workable) |
| Domain adaptation | LoRA rank 32 | LoRA rank 16 | Textual Inversion |
| Layout control | ControlNet-Seg | ControlNet-Canny | No control; pure T2I + auto-annotation |
| Detector | YOLOv11-m | RT-DETRv2 | YOLOv8-s |
| Segmentation | SegFormer-B2 | YOLOv11-seg | SAM 2 + classification head |
| Pose | YOLOv11-pose | RTMPose | No pose; boxes only |
| Action recognition | ST-GCN++ | VideoMAE V2 | Single-frame pose rules (D6) |
| Fusion | Three-level hierarchy | Rule layer + weighting | Highest single-source risk |
| Auto-annotation | Grounding DINO + SAM 2 | Grounding DINO only | Manual annotation |
| Experiment tracking | Weights & Biases | MLflow | CSV + Git |

---

## 8. Technology Risks and Mitigation

| Risk | Layer | Likelihood | Impact | Mitigation | Related gate |
|------|-------|-----------|--------|-----------|-------------|
| Structural hallucination in generated images (distorted towers) | L2 | High | Medium | Lock structure with ControlNet-Canny + negative prompts + G4 spot-checks | TG2 |
| Label noise in synthetic data causing negative transfer | L2 | Medium | **High** | Consistency checking + G3 gate + loss down-weighting | TG3 |
| Gates too strict, retention too low | L2 | Medium | Medium | Calibrate thresholds in stages, loose before tight; log rejection rate per gate | TG2 |
| Repeated redefinition of terrain/material classes | L3 | High | Medium | Fix quantitative criteria at the taxonomy stage; avoid subjective descriptions | TG1 |
| Resource contention across four training branches | L3 | Medium | Medium | Time-share training + shared backbone; prioritise Workers/Machinery | — |
| Inconsistent expert annotation (low Kappa) | L4 | Medium | High | Train annotators beforehand; align on a 20-image pilot | TG4 |
| Fusion module overfits a small sample | L4 | Medium | Medium | Rules primary, learning secondary; cross-validation | TG4 |
| End-to-end latency too high | L5 | Low | Low | ONNX export + branch parallelism + lower resolution | TG5 |

---

## 9. H3 Extension Directions (Post-Project)

Ordered by return on effort, for teams with capacity to spare:

| Priority | Direction | Note | Estimated effort |
|----------|-----------|------|-----------------|
| ⭐⭐⭐⭐⭐ | **Release the TelecomSynth dataset** | Synthetic data involves no real individual's privacy, so release is unobstructed; a dataset is itself a citable contribution | 1–2 weeks (curation + documentation) |
| ⭐⭐⭐⭐⭐ | **Submit to *Automation in Construction*** | The field's principal venue, already hosting comparable work by Kim & Yi and Lee et al.; strong topical match | 4–6 weeks |
| ⭐⭐⭐⭐ | Complete video behaviour recognition | Restores what was cut if D6 was taken during H2 | 3–4 weeks (incl. data collection) |
| ⭐⭐⭐⭐ | VLM natural-language risk reports | Integrate Qwen2.5-VL; strong demonstration value, low effort | 1 week |
| ⭐⭐⭐ | UAV viewpoint extension | Clear advantage for tower scenes, but needs extra data and equipment | 4 weeks |
| ⭐⭐⭐ | Edge deployment (Jetson) | High engineering value, limited academic contribution | 3 weeks |
| ⭐⭐ | Temporal risk evolution modelling | From per-frame risk to risk trend prediction; academically novel but difficult | 6+ weeks |

---

## 10. Roadmap Checklist

Before each gate meeting, the team should self-check against this list:

```
□ Have the gate criteria been measured (not estimated)?
□ Are the actions for all three outcomes (pass / partial / downgrade) agreed by the team?
□ If a downgrade is triggered, has the effort for the corresponding D path been assessed?
□ Is any task on the critical path delayed? By how long?
□ Are there new technical risks to add to §8?
□ Have the meeting conclusions been minuted and pushed to the repository?
```

---

## 11. One-Page Summary

```
Innovation bets:  L2 generative augmentation (core) + L4 information fusion (secondary)
Conservative:     L3 perception and L5 system layers use mature solutions only

Three must-pass gates:  TG1 data foundation (W3) → TG2 generation quality (W6)
                        → TG3 augmentation effectiveness (W9)
                        Any failure triggers its downgrade path; do not force ahead

Critical path:    Risk Taxonomy → annotation guideline → seed data → LoRA
                  → generation engines → E3

Largest risks:    ① Insufficient real telecom data   → D1
                  ② Negative transfer from synthetic → D2/D3
                  ③ Four-dimension scope too large   → D8 (better: do two from the start)

Safest bet:       The inpainting route (inherited annotation + minimal domain gap)
                  — it does not fail under any circumstances
```
