# TelecomSafe — Project Charter

> Document version: v1.0 (draft, pending signature) ｜ Generated: 2026-08-19
> Chinese counterpart: [07-项目章程-CN.md](07-项目章程-CN.md)
> Status: ⬜ Draft　⬜ Reviewed　⬜ Approved
>
> **The project charter is the project's formal authorisation document.** Once signed by the supervisor and all members, it becomes the baseline for scope, objectives and governance; any scope change must follow the change control process in §13.

---

## 1. Project Identification

| Item | Content |
|------|---------|
| **Project name** | TelecomSafe |
| **Full title** | A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects |
| **Project code** | AY26S1-45-SPML |
| **Repository** | https://github.com/muamuauh/AY26S1-45-SPML |
| **Project type** | Academic research project |
| **Duration** | W1 – W16 (16 weeks, one semester) ｜ Start date: TBC |
| **Team size** | 5 |
| **Charter version** | v1.0 (draft) |

---

## 2. Business Case

### 2.1 Problem Statement

Safety risks at telecommunication construction sites arise from five sources: **uneven terrain, improperly operated machinery, poorly stored materials, missing personal protective equipment, and unsafe worker behaviour**.

Deep-learning-based computer vision offers an efficient means of identifying these risks, but its performance is constrained by one core bottleneck:

> **The limited availability and diversity of labelled, sector-specific images** for the telecommunication industry.

A systematic literature search (Google Scholar / IEEE Xplore / ACM DL) established that **no public, annotated safety-detection dataset exists for telecommunication construction scenes** (see `04-Literature-Survey-EN.md` §3.2). The nearest existing work addresses asset inspection of telecommunication towers, not safety during construction.

### 2.2 Why Now

1. **The technology window is open**: diffusion models and controllable generation (ControlNet, inpainting) reached practical maturity in 2023–2024, making the "generation-is-annotation" paradigm viable
2. **The research gap is well defined**: generative augmentation work in construction safety is concentrated in 2024–2026, and no one has addressed the telecommunication vertical
3. **A structural data acquisition deadlock**: real photographs of safety violations involve worker portrait rights and labour-relations exposure, making lawful collection and publication difficult — synthetic data removes the problem at its root

### 2.3 Expected Value

| Type | Value |
|------|-------|
| Academic | Addresses five research gaps (G1–G5); credible target for submission to *Automation in Construction* |
| Data | Produces a releasable TelecomSynth synthetic dataset and Risk Taxonomy, each a citable contribution in its own right |
| Engineering | Delivers a working prototype for telecommunication construction safety appraisal |
| Compliance | The synthetic-data approach avoids real worker privacy issues, making practical adoption feasible |

---

## 3. Objectives and Success Criteria

### 3.1 Overall Objective

Develop and evaluate a generative image-based learning framework for telecommunication construction safety, achieving high effectiveness and robustness in identifying potential risks across four dimensions: **terrain, machinery, materials and workers**.

### 3.2 Specific Objectives and Success Criteria (SMART)

| # | Objective | Measurable success criterion | Verification | Priority |
|---|-----------|----------------------------|-------------|----------|
| **O1** | Establish a telecommunication construction risk taxonomy | Risk Taxonomy with 4 categories × ≥20 sub-classes, each with decidable quantitative criteria | Supervisor review | **Must** |
| **O2** | Build the generative augmentation pipeline | ≥3,000 synthetic images passing the quality gates; FID < 50; human realism ≥ 3.0/5 | Gate TG2 | **Must** |
| **O3** | Prove generative augmentation is effective | E3 improves mAP by ≥ 2.0 over E2 (conventional augmentation) | Gate TG3 | **Must** |
| **O4** | Implement multi-dimensional perception | ≥2 dimensions reach usable accuracy (mAP@50 ≥ 0.70); target is 4 dimensions | Experimental report | **Must (2)** |
| **O5** | Implement fusion-based risk appraisal | Risk-level classification accuracy ≥ 0.70 against expert annotation | Gate TG4 | Desired |
| **O6** | Deliver a runnable system | End-to-end demo presentable; single-image inference < 3 s | Gate TG5 | Desired |
| **O7** | Verify robustness | Complete performance degradation curves under low light / rain-fog / blur / small targets | Experimental report | Desired |
| **O8** | Complete academic output | Paper/technical report finalised; defence passed | Supervisor and examiners | **Must** |

> **On priority**: failure of a "Must" objective means the project has not met its target. Failure of a "Desired" objective can be handled through a downgrade path (see `05-Technological-Roadmap-EN.md` §6) and must be explained in the report.

### 3.3 Explicit Non-Objectives

The following are **not** success criteria, stated here to prevent scope inflation:

- ❌ Production-grade deployment on real-time video streams
- ❌ Integration with existing construction management systems (BIM / ERP)
- ❌ Commercial product development and market validation
- ❌ Procurement and deployment of hardware (cameras, UAVs)
- ❌ Coverage of every telecommunication construction trade and every risk type

---

## 4. Project Scope

### 4.1 In Scope

| Category | Content |
|----------|---------|
| **Risk dimensions** | Terrain, Machinery, Materials, Workers (including PPE and unsafe behaviour) |
| **Scenes** | Base stations, lattice and monopole towers, optical cable trenching, rooftop antennas, equipment-room work |
| **Input forms** | Handheld photographs, fixed camera imagery (video is a desired item) |
| **Technologies** | Generative AI data augmentation, deep-learning detection/segmentation, information fusion for risk appraisal |
| **Deliverables** | Datasets, models, pipeline code, demo system, experimental report, paper/technical report |

### 4.2 Out of Scope

| Category | Note |
|----------|------|
| UAV aerial input | Listed as an H3 extension, not delivered this cycle |
| Tower-mounted recorders | As above; requires additional equipment |
| Production deployment and operations | Prototype only |
| Multi-region regulatory adaptation | The rule base covers selected standards only (OSHA 1926, GB 26859) |
| Sensor / IoT data fusion | Fusion is within-image and multi-dimensional only |
| Edge device optimisation | Listed as H3 |

### 4.3 Key Scoping Decision ⚠️

> **Delivering all four risk dimensions to high quality within one semester is close to impossible.**
>
> **Recommendation**: decide at M0 to "focus on Workers + Machinery (satisfying O4), keeping Terrain and Materials merely functional", and state the scoping rationale honestly in the final report.
>
> This decision must be confirmed at the first team meeting and recorded in the minutes. If all four dimensions are pursued, raise the severity of risk R7 in §12 accordingly.

---

## 5. Deliverables

| ID | Deliverable | Form | Milestone | Acceptance criterion |
|----|------------|------|-----------|---------------------|
| **D1** | Risk Taxonomy | Document + YAML | M0 (W1) | 4 categories × ≥20 sub-classes, each with quantitative criteria; supervisor approved |
| **D2** | Annotation guideline | Document | M1 (W2) | Includes edge-case rules; two-annotator pilot agreement Kappa ≥ 0.7 |
| **D3** | TelecomSeed-v1 real dataset | Images + COCO annotation | M1 (W3) | ≥300 annotated; strict train/val/test split |
| **D4** | Generation pipeline code | Repository | M2 (W6) | Four engines + four gates runnable; documented |
| **D5** | TelecomSynth-v1 synthetic dataset | Images + annotation + metadata | M2 (W6) | ≥3,000 images; FID < 50; per-image seed/prompt metadata |
| **D6** | Generation quality report | Document | M2 (W6) | FID/CLIP/human ratings and per-gate rejection rates |
| **D7** | Perception models and weights | Model files + code | M3 (W9) | ≥2 dimensions at mAP@50 ≥ 0.70 |
| **D8** | E1–E3 core experiment results | Report + W&B logs | M3 (W9) | Complete comparison table; reproducible scripts |
| **D9** | Safety rule base | Code + document | M4 (W10) | ≥15 decidable rules citing regulatory sources |
| **D10** | Information fusion module | Code | M4 (W11) | Three-level fusion runnable; E8 complete |
| **D11** | TelecomSafe demo system | Running system | M5 (W13) | End-to-end presentable; < 3 s per image |
| **D12** | Full experimental report | Document | M6 (W15) | E1–E9 plus ablations A1–A7 |
| **D13** | Paper / technical report | Document | M7 (W16) | Structurally complete; citations verified |
| **D14** | Defence materials | Slides + demo | M7 (W16) | Rehearsed |
| **D15** | Archived repository | Git repository | M7 (W16) | README, environment, reproduction scripts complete |

---

## 6. Milestone Summary

| Milestone | Weeks | Name | Key deliverables | Gate |
|-----------|-------|------|-----------------|------|
| M0 | W1 | Setup and survey | D1 | — |
| M1 | W2–W3 | Data infrastructure | D2, D3 | **TG1** Data foundation |
| M2 | W4–W6 | Generation pipeline | D4, D5, D6 | **TG2** Generation quality |
| M3 | W7–W9 | Perception models | D7, D8 | **TG3** Augmentation effectiveness |
| M4 | W10–W11 | Fusion and decision | D9, D10 | **TG4** Fusion feasibility |
| M5 | W12–W13 | System integration | D11 | **TG5** System integration |
| M6 | W14–W15 | Full evaluation | D12 | — |
| M7 | W16 | Delivery | D13, D14, D15 | — |

> Detailed schedule: `01-Technical-Plan-and-Milestones-EN.md` §4. Gate criteria and downgrade paths: `05-Technological-Roadmap-EN.md` §3 and §6.

---

## 7. Stakeholders

| Stakeholder | Role | Interests | Engagement | Frequency |
|------------|------|-----------|-----------|-----------|
| **Supervisor** | Project sponsor, final acceptor | Academic quality, progress, member commitment | Weekly meeting + gate meetings | Weekly (in person) |
| **Team leader** | Project coordinator | Progress, collaboration, external communication | Throughout | Daily |
| **Members A–E** | Executors | Technical delivery, visibility of individual contribution | Throughout | Daily |
| **Course / degree examiners** | Assessors | Completeness of delivery, academic rigour | Defence | Once |
| **Safety domain experts** (external) | Risk annotation providers | Annotation workload, professional accuracy | 200-image annotation during M4 | As needed |
| **Potential data providers** (external, if any) | Source of real data | Data compliance, privacy | Data collection phase | As needed |

> **Key note**: the supervisor is the sole sponsor and acceptor, and the project explicitly requires `regular in-person meetings and discussions on campus`. As sole point of contact, the leader must ensure weekly in-person communication is never interrupted.

---

## 8. Team and Governance

### 8.1 Team Composition

| ID | Role | Name | Primary layer |
|----|------|------|--------------|
| Member A | Data Lead | ______________ | L2 Data |
| Member B | Generation Lead ★ | ______________ | L2 Generation |
| Member C | Perception Lead – Workers | ______________ | L3 Workers + Behaviour |
| Member D | Perception Lead – Scene | ______________ | L3 Machinery/Materials/Terrain |
| Member E | Fusion & System Lead | ______________ | L4 Fusion + L5 System |
| **Team Leader** | Project coordinator | ______________ | (elected from A–E) |
| Deputy Leader | Acts in the leader's absence | ______________ | (runner-up by votes) |

> Names to be filled in after the first team meeting. Role responsibilities: `06-Teamwork-Allocation-EN.md` §2.

### 8.2 How the Leader Is Determined

The leader is **not pre-assigned**. They are elected at the first team meeting following the process in `06-Teamwork-Allocation-EN.md` §3.3:

```
Nomination criteria (mandatory):
  ① Can guarantee on-campus attendance — a hard project requirement
  ② Can guarantee time commitment — an extra 20–25% coordination load
  ③ Willing to communicate and coordinate

Process: read responsibilities → nominations → eligibility check → secret ballot → record
Ties: second round; if still tied, the supervisor decides
```

### 8.3 Decision-Making

| Decision type | Method | Record |
|--------------|--------|--------|
| Technical approach | Decided by the responsible lead; leader informed | Technical alignment minutes |
| Cross-module interfaces | Agreed by the affected members | Interface contract document (`06` §6) |
| Gate pass / downgrade | Chaired by the leader, assessed by the team, confirmed by the supervisor | Gate decision record |
| Scope change | See §13 Change Control | Change request form |
| Deadlock | Team vote (majority); if still unresolved, the supervisor decides | Meeting minutes |

---

## 9. Resources and Budget

### 9.1 Compute

| Item | Recommended | Minimum | Status |
|------|------------|---------|--------|
| GPU | RTX 4090 24GB × 1–2, or A100 40GB | RTX 3090 24GB / cloud on demand | ⬜ TBC |
| Storage | ≥ 500 GB | 250 GB | ⬜ TBC |
| Cloud budget (if needed) | To be estimated | — | ⬜ TBC |

> ⚠️ **Compute is a precondition that must be confirmed at M0.** If single-GPU VRAM is below 16 GB, trigger downgrade path D7 immediately (SD 1.5 instead of SDXL).

### 9.2 Human Resources

5 members × ~10 hours/week × 16 weeks ≈ **800 person-hours**

### 9.3 External Resources

| Resource | Purpose | How obtained | Status |
|----------|---------|-------------|--------|
| Public datasets (SODA/MOCS/ACID/CHV/SHEL5K) | Transfer base | Academic request / download | ⬜ Pending |
| Pretrained model weights | SDXL / YOLOv11 / SAM 2 etc. | Open-source download | ⬜ Pending |
| Access to telecommunication sites | Real data collection | Requires supervisor coordination | ⬜ TBC |
| Safety domain experts (2–3) | Risk-level annotation | Requires supervisor introduction | ⬜ TBC |
| ScienceDirect full-text access | Citation verification | Campus network | ⬜ TBC |

### 9.4 Software and Tools

| Category | Tools | Licence |
|----------|-------|---------|
| Deep learning | PyTorch 2.x, Ultralytics, diffusers, transformers | Open source (Ultralytics is AGPL-3.0) |
| Annotation | CVAT / Label Studio | Open source |
| Experiment tracking | Weights & Biases / MLflow | Free academic tier |
| Data versioning | DVC | Open source |
| Collaboration | GitHub | In place |

---

## 10. Assumptions

This charter rests on the following assumptions. **If any fails, project scope must be reassessed.**

| # | Assumption | Consequence if false | Verified at |
|---|-----------|---------------------|------------|
| A1 | ≥300 real telecommunication images can be collected before W3 | Triggers D1; repositions the project to generic work-at-height scenarios | TG1 (W3) |
| A2 | The team has access to a GPU with ≥24 GB VRAM | Triggers D7; generation quality declines | M0 (W1) |
| A3 | All 5 members participate throughout at ≥10 hours/week each | Duties reallocated per `06` §9; may trigger D8 | Weekly |
| A4 | 2–3 safety experts can annotate 200 images | O5 becomes unverifiable; fusion downgrades to pure rules (D4) | W8 |
| A5 | All members can meet in person weekly | Violates a hard project requirement; escalate to the supervisor immediately | Weekly |
| A6 | Public datasets can be obtained without obstruction | Transfer base missing; requires more real or more synthetic data | M1 (W2) |
| A7 | LoRA fine-tuning yields usable telecommunication imagery | Triggers D2; only the inpainting route survives | TG2 (W6) |

---

## 11. Constraints

| # | Constraint | Type | Note |
|---|-----------|------|------|
| C1 | **In person required**: `absence and remote working on the project are unacceptable` | Mandatory rule | Explicit in the project brief; affects meeting arrangements and member selection |
| C2 | Fixed 16-week cycle | Time | Semester-bound; cannot be extended |
| C3 | Fixed team size of 5 | Human resources | No additional members |
| C4 | No budget for dedicated capture equipment | Resource | Collection limited to phones and existing cameras |
| C5 | Real worker imagery involves portrait rights | Legal / ethical | Requires de-identification or informed consent; limits public release |
| C6 | Ultralytics YOLO is AGPL-3.0 | Licence | Commercial licence required if not open-sourced; must be stated in the report |
| C7 | FLUX.1-dev is non-commercial | Licence | Fine for academic research; switch to the schnell variant if commercialisation is anticipated |
| C8 | The test set must be entirely real and strictly isolated | Methodological | Violation invalidates every experimental conclusion |

---

## 12. High-Level Risks

The full risk register is in `01-Technical-Plan-and-Milestones-EN.md` §5; technical risks are in `05-Technological-Roadmap-EN.md` §8. Listed here are the risks requiring **charter-level attention**.

| ID | Risk | Likelihood | Impact | Response | Owner |
|----|------|-----------|--------|----------|-------|
| R1 | Insufficient real telecommunication data | High | High | Public dataset transfer + whole-team collection; downgrade D1 | Member A |
| R2 | Negative transfer from synthetic data; E3 fails | Medium | **Very high** | Four quality gates + conservative ratio; downgrade D3 narrows the claim | Members B, C |
| R3 | Scope creep (attempting all four dimensions) | High | High | **Decide at M0 to focus on two dimensions**; downgrade D8 | Leader |
| R4 | Insufficient member commitment or absence | Medium | High | Traceable contribution records + W8 mid-term review; reallocate per `06` §9 | Leader |
| R5 | Breach of the in-person attendance requirement | Medium | **Very high** | Fix time and place at the first meeting with commitment from all; escalate any breach to the supervisor | Leader |
| R6 | Insufficient compute | Medium | Medium | LoRA rather than full fine-tuning; downgrade D7 | Member B |
| R7 | Expert annotation cannot be arranged | Medium | Medium | Start recruiting at W8; downgrade D4 to pure rule fusion | Member E |
| R8 | Unverified citations causing academic irregularity | Medium | Medium | Complete every entry per the verification status table in `04` §8 | Leader |

> **R2 and R5 are the two "very high impact" risks**: the first undermines the project's core academic claim, the second breaches an explicit project rule. Both should be confirmed as a standing item at every weekly meeting.

---

## 13. Change Control

### 13.1 Changes Requiring the Formal Process

- Addition, removal or adjustment of objectives (§3) or their success criteria
- Material change to scope (§4), including triggering any downgrade path D1–D8
- Milestone dates (§6) slipping by more than one week
- Reduction of deliverables (§5)
- Change of team roles or the team leader

### 13.2 Change Process

```
1. Raise      Any member submits a change request (background / change / impact / alternatives)
2. Assess     Leader organises assessment of impact on schedule, deliverables and other modules
3. Vote       Team vote at the weekly meeting (majority)
4. Approve    Changes to scope or objectives require written supervisor confirmation
5. Record     Increment this charter's version; log the change in §15
6. Notify     Leader informs all members and the supervisor
```

### 13.3 Changes Not Requiring the Process

- Adjustments to technical implementation detail (e.g. switching detector)
- Reordering tasks within a week
- Internal interface changes that do not affect deliverables (but downstream members must be notified)

---

## 14. Approval and Signature

This charter takes effect upon signature by the parties below. Signing indicates acceptance of the project's objectives, scope, role allocation and governance rules.

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Supervisor** | ______________ | ______________ | ______ |
| **Team Leader** | ______________ | ______________ | ______ |
| Member A (Data Lead) | ______________ | ______________ | ______ |
| Member B (Generation Lead) | ______________ | ______________ | ______ |
| Member C (Perception – Workers) | ______________ | ______________ | ______ |
| Member D (Perception – Scene) | ______________ | ______________ | ______ |
| Member E (Fusion & System) | ______________ | ______________ | ______ |

**Confirmations required before signature**:

```
□ Project duration confirmed (12 or 16 weeks)
□ Scope confirmed (all four dimensions / focus on two)
□ Available compute confirmed
□ Telecommunication sub-scenarios confirmed (towers / cable / equipment rooms)
□ Team leader and deputy elected
□ All members have confirmed they can meet the in-person requirement (constraint C1)
□ Weekly meeting time and place fixed
```

---

## 15. Change Log

| Version | Date | Change | Raised by | Approved by |
|---------|------|--------|-----------|------------|
| v1.0 | 2026-08-19 | Initial charter draft created | — | — |
| | | | | |
| | | | | |

---

## Appendix: Companion Document Index

| Document | Content | Relation to this charter |
|----------|---------|------------------------|
| `00-Requirements-Analysis-EN.md` | Requirements breakdown, four dimensions, three pillars | Source of §2 business case |
| `01-Technical-Plan-and-Milestones-EN.md` | Five-layer architecture, experiment matrix, 16-week schedule | Detailed version of §6 |
| `02-Datasets-and-Pretrained-Models-EN.md` | Dataset inventory, model selection, licensing | Basis for §9 resources |
| `03-Generative-Augmentation-Pipeline-EN.md` | Full generation pipeline | Technical specification for D4/D5 |
| `04-Literature-Survey-EN.md` | 50 references, 5 research gaps | Basis for §2.1 problem statement |
| `05-Technological-Roadmap-EN.md` | Three horizons, decision gates, downgrade paths | Basis for §12 risk responses |
| `06-Teamwork-Allocation-EN.md` | Five roles, RACI, leader election | Detailed version of §8 governance |
