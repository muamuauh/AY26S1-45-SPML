# EE6008 Project Charter

> Document version: v2.0 ｜ Generated: 2026-08-22
> Chinese counterpart: [07-项目章程-CN.md](07-项目章程-CN.md)
> **This document follows the fields and tables of the official school template `template/EE6008_Project_Charter_Template.docx` exactly, and can be copied section by section into the Word template.**

---

## 📌 How to Use

| Item | Content |
|------|---------|
| Template source | `template/EE6008_Project_Charter_Template.docx` |
| Official sections | Cover → Date Prepared → Project information table → Project Purpose or Justification → Project Description → Summary Milestones → Team Member Activity matrix → Summary Budget → Risk Assessment |
| Approach here | Section headings match the official template **exactly**; content is pre-filled for TelecomSafe |
| `<<...>>` | Placeholder requiring confirmation by the team or supervisor |
| Detailed rationale | The official template is deliberately brief; full argumentation lives in companion documents 00–06 (see Appendix B) |

> ⚠️ **Change from v1.0 to v2.0**: v1.0 followed a generic PMBOK structure (15 sections including scope, stakeholders, assumptions, constraints, change control and a signature page), which does not match the school template. v2.0 has been restructured into the official template's 8 fields. Content dropped by the official template (out-of-scope statements, stakeholder analysis, assumptions and constraints, change control) has been moved to **Appendix A** and retained for internal management use.

---

## Cover Page

```
EE6008 Collaborative Research and Development Project

                        Project Charter

        <<Project No. 45>> & TelecomSafe: A Novel Generative
        Image-based Learning Framework for Enhancing the
        Construction Safety of Telecommunication Projects

        Students' Names:   <<Member A>>, <<Member B>>, <<Member C>>,
                           <<Member D>>, <<Member E>>
        Supervisor's Name: <<XXX>>

        School of Electrical and Electronic Engineering
        Academic Year 2026/27
        Semester 1
```

> **To confirm**:
> - Project No.: inferred as **45** from the repository name `AY26S1-45-SPML`; verify with the supervisor
> - Academic Year / Semester: inferred as **2026/27 Semester 1** from `AY26S1`; verify
> - Supervisor's Name: to be filled

---

## Date Prepared

`<<YYYY-MM-DD>>` — suggested: the date of the first team meeting or of charter signature

---

## Project Information

| Field | Content |
|-------|---------|
| **Project No. & Project Title** | `<<45>>` — TelecomSafe: A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects |
| **Project Supervisor** | `<<Supervisor name>>` |
| **Team Leader** | `<<To be elected>>` — nomination criteria and election process in document [06 §3](06-Teamwork-Allocation-EN.md) |
| **Names of Team Members** | `<<Member A>>`, `<<Member B>>`, `<<Member C>>`, `<<Member D>>`, `<<Member E>>` (5 in total) |

> **Note**: the Team Leader field must be completed after the election at the first team meeting. The process is defined in document 06 §3.3 (nomination → eligibility check → secret ballot).

---

## Project Purpose or Justification

> *Template requirement: Describe the reason or justification the project is being undertaken.*

Telecommunication construction sites present multiple categories of safety risk, including uneven terrain, improperly operated machinery, poorly stored materials, missing personal protective equipment and unsafe worker behaviour. Conventional manual inspection is time-consuming, subjective and difficult to sustain across a whole site.

Deep-learning-based computer vision offers an effective means of automated safety monitoring, but its application in the telecommunication sector is constrained by one decisive bottleneck: **labelled, sector-specific imagery is both scarce and insufficiently diverse**. This bottleneck has three causes:

1. **Distribution mismatch.** All existing public construction datasets (SODA, MOCS, ACID and others) originate from building and municipal sites. Telecommunication scenes — lattice towers, monopoles, base-station equipment rooms, cable trenches, rooftop antennas — differ systematically in object morphology, camera viewpoint and working height, so directly transferred general-purpose models degrade substantially.

2. **Long-tail risks cannot be collected.** Genuinely hazardous scenes (for example a worker leaning out from a tower without a fall-arrest harness) are extremely rare in real data; and even when they occur, they are difficult to photograph and publish for ethical, legal and labour-relations reasons. This constitutes a structural deadlock in data acquisition.

3. **No sector-specific resources exist.** A systematic search of Google Scholar, IEEE Xplore and the ACM Digital Library found **no public annotated dataset or dedicated framework for telecommunication construction safety**. The nearest existing work concerns asset inspection of telecommunication towers, at the commercial-product level, rather than safety during construction.

This project exists to fill that gap. TelecomSafe introduces **generative artificial intelligence** to synthesise training data and break the data-scarcity constraint, and combines deep-learning image processing with information fusion to appraise construction risk across four dimensions — terrain, machinery, materials and workers. The project carries both **academic value** (the relevant literature is concentrated in 2024–2026, making the topic timely, and none of it targets the telecommunication sector) and **engineering value** (transferable to the safety management practice of telecommunication operators and contractors).

---

## Project Description

> *Template requirement: Provide a summary description of the project. This section may include information on project deliverables as well as the approach of the project.*

### Overview

TelecomSafe is a multi-dimensional intelligent safety risk identification framework for telecommunication construction scenes. Its core innovations are **resolving sector-specific data scarcity through generative data augmentation** and **converting point detections into an interpretable, site-level risk appraisal through hierarchical information fusion**.

### Technical Approach

The system adopts a five-layer architecture:

| Layer | Name | Content |
|-------|------|---------|
| **L1** | Input | Handheld photographs and fixed cameras (MVP scope); UAV aerial imagery and tower-mounted recorders (extensions) |
| **L2** | **Data ★ CORE INNOVATION ★** | Real data collection and annotation + generative augmentation pipeline + four quality gates |
| **L3** | Perception | Four parallel branches: terrain segmentation, machinery detection, material state judgement, worker detection with PPE attributes |
| **L4** | **Fusion & Decision ★ SECONDARY CORE ★** | Three-level fusion: entity graph → regulation-derived rule predicates → learnable fusion → risk score |
| **L5** | Application | Web visualisation dashboard, risk scorecard, hazard report generation |

### Core Method: Generative Data Augmentation

The pipeline uses SDXL with LoRA domain adaptation across four generation routes:

- **ControlNet layout control** — the semantic layout map is both the generation condition and, directly, the segmentation annotation (zero annotation cost)
- **Inpainting local editing** — remove PPE such as helmets from real images while the bounding-box annotation is inherited unchanged (smallest domain gap)
- **Text-to-image** — generate rare hazardous scenes entirely absent from the real world
- **Background replacement** — produce rain, fog and night-time variants for robustness testing

All synthetic data must pass four quality gates (G1 semantic consistency / G2 distributional consistency / G3 annotation reliability / G4 human spot-check), with an expected retention rate of 50–65%.

### Principal Deliverables

| Category | Deliverables |
|----------|-------------|
| **Data** | Risk Taxonomy for telecommunication construction, annotation guideline, TelecomSeed (real seed dataset, ≥ 500 images), TelecomSynth (synthetic dataset, ≥ 3,000 images) |
| **Models** | LoRA domain-adapted generative model, four generation engines, four-branch perception models, three-level information fusion module |
| **System** | A runnable end-to-end TelecomSafe demo (web interface + risk scorecard) |
| **Experiments** | Complete E1–E9 results, centred on E3 (validation of augmentation effectiveness) and E7 (robustness) |
| **Documentation** | EE6008 project report, defence presentation, code repository with reproduction scripts |

### Method of Working and Key Criteria

The project manages technical risk through a **decision-gate mechanism**: at W3, W6, W9, W11 and W13, objective metrics determine whether to continue, adjust or downgrade, with a fallback pre-defined for every gate (see document [05 §3](05-Technological-Roadmap-EN.md)).

The three must-pass gates:

| Gate | Timing | Criterion |
|------|--------|-----------|
| **TG1** Data foundation | End W3 | ≥ 300 annotated real telecommunication seed images |
| **TG2** Generation quality | End W6 | FID(synthetic, real) < 50; human realism rating ≥ 3.0/5 |
| **TG3** Augmentation effectiveness | End W9 | E3 improves mAP over E2 by ≥ 2.0 — **the project's decisive checkpoint** |

### Scope Note ⚠️

Delivering all four risk dimensions to high quality within a single semester is not realistic. **It is recommended that the first team meeting explicitly resolves to focus on the Workers and Machinery dimensions, keeping Terrain and Materials merely functional**, and to state this scope boundary honestly in the final report. This decision should be confirmed and recorded at project start.

---

## Summary Milestones

> *Template requirement: List significant activities / events in the project. Target completion date of the milestone.*

| Summary Milestones | Target Date |
|-------------------|-------------|
| **M0 Project setup and survey** — Risk Taxonomy v1.0, literature survey, role assignment and leader election, charter signature | W1 ｜ `<<YYYY-MM-DD>>` |
| **M1 Data infrastructure** — annotation guideline and TelecomSeed-v1 (≥ 300 annotated); **Gate TG1** | End W3 ｜ `<<YYYY-MM-DD>>` |
| **M2 Generation pipeline** — LoRA model, four generation engines, four quality gates, TelecomSynth-v1 (≥ 3,000 images); **Gate TG2** | End W6 ｜ `<<YYYY-MM-DD>>` |
| **M3 Perception models** — four-branch perception models and core comparison experiments E1/E2/E3; **Gate TG3 (decisive)** | End W9 ｜ `<<YYYY-MM-DD>>` |
| **M4 Fusion and decision** — safety rule base (≥ 15 rules), three-level fusion module, expert risk annotation set, experiment E8; **Gate TG4** | End W11 ｜ `<<YYYY-MM-DD>>` |
| **M5 System integration** — runnable TelecomSafe web demo; **Gate TG5** | End W13 ｜ `<<YYYY-MM-DD>>` |
| **M6 Full evaluation** — experiments E4–E9, robustness test set, all ablation tables | End W15 ｜ `<<YYYY-MM-DD>>` |
| **M7 Delivery** — project report, defence presentation, curated code repository | W16 ｜ `<<YYYY-MM-DD>>` |

> **To confirm**: whether the project runs 12 or 16 weeks. The table above assumes 16; for 12 weeks, compress M2 and M5 and downgrade UAV input and video behaviour recognition to optional (see document [01 §4](01-Technical-Plan-and-Milestones-EN.md)).
> **Dates**: once the semester start week is confirmed, convert W1–W16 into calendar dates in the right-hand column.

---

## Team Member Activity

> *Template requirement: Activity in which a team member plays a key role.* ✅ marks a key role; **●** marks the accountable owner.

| Activity | Member 1<br>`<<A Data>>` | Member 2<br>`<<B Generation>>` | Member 3<br>`<<C Perc-Workers>>` | Member 4<br>`<<D Perc-Scene>>` | Member 5<br>`<<E Fusion/System>>` |
|---------|:---:|:---:|:---:|:---:|:---:|
| A1 Risk Taxonomy and annotation guideline | ● | ✅ | | | |
| A2 Real data collection, screening and annotation (TelecomSeed) | ● | | ✅ | ✅ | |
| A3 Risk scenario specification library | ✅ | ● | | | |
| A4 LoRA domain adaptation of the generative model | | ● | | | |
| A5 Four generation engines and automatic annotation | ✅ | ● | | | |
| A6 Four quality gates and threshold calibration | | ● | | | ✅ |
| A7 Bulk synthetic dataset generation (TelecomSynth) | ✅ | ● | | | |
| A8 Workers perception model and PPE attribute recognition | | | ● | | |
| A9 Behaviour recognition (skeleton action) | | ✅ | ● | | |
| A10 Machinery / Materials / Terrain perception models | ✅ | | | ● | |
| A11 **Core experiments E1/E2/E3 (augmentation effectiveness)** | | ✅ | ● | | ✅ |
| A12 Safety rule base encoding and entity graph construction | | | | ✅ | ● |
| A13 Three-level fusion module and expert annotation | | | ✅ | ✅ | ● |
| A14 System integration and web demo development | | | | | ● |
| A15 Experiment tracking platform and reproduction scripts | | ✅ | ✅ | ✅ | ● |
| A16 Robustness and generalisation experiments (E7 / E9) | | ✅ | ● | ✅ | |
| A17 Project report writing and defence presentation | ✅ | ✅ | ✅ | ✅ | ✅ |

> **Notes**:
> - Members 1–5 correspond one-to-one with Members A–E in document [06 §2](06-Teamwork-Allocation-EN.md); names to be filled after the first meeting
> - The team leader carries approximately 20–25% additional coordination load on top of their technical role (supervisor liaison, chairing weekly and gate meetings, progress tracking)
> - A17 is shared by all: **each member drafts the section covering their own module**, with the leader consolidating. This maps directly onto the "Individual Reports from Team Members" section required by the official report template

---

## Summary Budget

> *Template requirement: List the initial range of budget for the project.*

**Expected cash expenditure: S$0 — this is a purely computational project requiring no hardware purchase or consumables.**

| Item | Note | Budget |
|------|------|--------|
| Compute | Prefer the school laboratory GPU workstations or cluster (RTX 4090 24GB or A100 40GB recommended) | S$0 (campus resource) |
| Cloud GPU (contingency) | Only if campus resources are unavailable; estimated 100 GPU-hours × approx. S$1.5–3/hour | S$150–300 (**TBD, requires application**) |
| Software and frameworks | PyTorch, Ultralytics, diffusers, SDXL, ControlNet, SAM 2 — all open source | S$0 |
| Experiment tracking | Weights & Biases academic tier / self-hosted MLflow | S$0 |
| Datasets | SODA, MOCS, ACID, CHV, SHEL5K and others; free for academic use | S$0 |
| Data collection | Travel costs for on-site photography of telecommunication scenes, if required | `<<To be estimated>>` |
| Storage | ≥ 500 GB (raw + synthetic data + model weights + experiment artefacts) | S$0 (campus storage) |

**Licensing notes** (no cost implication, but relevant to compliance):
- Ultralytics YOLO is **AGPL-3.0**; a commercial licence is required if the work is not open-sourced — normally unproblematic for a campus research project, but it should be stated in the report
- FLUX.1-dev carries a **non-commercial licence**; usable for academic research. If commercialisation is anticipated, switch to FLUX.1-schnell (Apache 2.0)
- Most public datasets are for academic use; commercial use requires separate application

---

## Risk Assessment

> *Template requirement: List the general risks... assess the probability and potential impacts. Provide solutions and mitigation plans. State whether the training of equipment usage and safety training have been completed.*

### Laboratory Equipment Use and Safety Training Status

| Item | Status |
|------|--------|
| **Laboratory equipment used** | Yes — GPU workstations / compute cluster only. **No mechanical, electrical, chemical or high-voltage hazardous equipment is involved** |
| **Work on live construction sites** | ❌ **Not involved.** The project does not carry out work on real construction sites. If on-site photography of telecommunication scenes is required, it will be conducted **only from outside the safety perimeter** — no tower climbing, no entry to work faces, no approach to operating machinery |
| **Equipment usage training** | `<<To confirm>>` — confirm whether training and account provisioning for the laboratory GPU cluster/workstations are complete |
| **General laboratory safety training** | `<<To confirm>>` — if required by the school, to be completed by `<<date>>` |
| **Field data collection safety** | If on-site photography is confirmed, notify the supervisor of route and timing in advance and comply with the site's safety rules |

### General Project Risks

| ID | Risk | Probability | Impact | Mitigation | Gate |
|----|------|------------|--------|-----------|------|
| **R1** | Insufficient real telecommunication data (no public dataset; must be self-collected) | High | High | ① Use public construction datasets as a transfer base ② Web collection with manual screening ③ On-site capture at campus or partner facilities. If < 150 images by end of W3, trigger downgrade path **D1**: reposition to generalised "work-at-height / tower-type construction" | TG1 |
| **R2** | Generated image quality inadequate, causing negative transfer (synthetic data degrades performance) | Medium | **High** | ① Strict filtering by the four quality gates ② Conservative ratio (start at 25%) ③ Always retain a pure-real baseline for comparison. If FID > 70, trigger **D2**: keep only the inpainting and background-replacement routes that edit real images | TG2 |
| **R3** | E3 fails to demonstrate augmentation effectiveness (the project's central claim does not hold) | Medium | **High** | ① Diagnose label noise and mixing ratio first ② Switch to class-adaptive ratios. If there is still no gain, trigger **D3**: narrow the conclusion to "improves long-tail rare-class performance" and state honestly that overall performance did not improve | TG3 |
| **R4** | Insufficient compute (diffusion training and inference are expensive) | Medium | Medium | ① LoRA rather than full fine-tuning ② SDXL-Turbo for >10× faster bulk generation ③ 8-bit quantisation and gradient checkpointing ④ Apply for cloud GPU if necessary. Triggers **D7** | — |
| **R5** | No video data, so behaviour recognition cannot proceed | High | Medium | Trigger downgrade path **D6**: replace temporal action recognition with single-frame pose estimation plus rules (e.g. arm angle to detect climbing) | — |
| **R6** | Scope too large (four dimensions cannot all be completed in one semester) | High | High | **Resolve at project start to focus on Workers + Machinery**, keeping Terrain and Materials merely functional. If more than 2 weeks behind, trigger **D8** | — |
| **R7** | No ground truth for the fusion module (risk level has no objective standard) | Medium | Medium | ① Generate weak labels from the rule base ② Have 2–3 annotators assign risk levels to 200 images and compute agreement Kappa ③ Begin recruiting annotators in W8 rather than deferring to the end | TG4 |
| **R8** | Teamwork risks: absence, uneven progress, unclear contribution | Medium | Medium | ① Weekly in-person meetings (a hard project requirement) ② Kanban plus a full trail in Git/PR/W&B ③ Document [06 §9](06-Teamwork-Allocation-EN.md) pre-defines handover plans for the loss of any member | — |
| **R9** | Data privacy and compliance (self-collected data captures worker likeness) | Medium | Medium | ① Face blurring or informed consent ② Internal use only, not published ③ **Synthetic data depicts no real individual and avoids the problem at its root** — an additional advantage of the generative approach | — |
| **R10** | The in-person attendance requirement cannot be met (the brief prohibits remote work) | Low | **High** | Fix the weekly meeting time and place at the first meeting with written confirmation from all members; leader candidates must confirm they can meet this mandatory requirement first | — |

> **Full definitions of downgrade paths D1–D8** are given in document [05 §6](05-Technological-Roadmap-EN.md). Each path has been assessed for its effect on final outcomes, ensuring that no single risk trigger causes overall project failure.

---

## Appendix A: Supplementary Internal Management Material (Not in the Official Template)

> The following is outside the official charter template's fields but retains practical value for project management, and is kept for internal team reference.

### A.1 Explicit Non-Objectives (Out of Scope)

The following are explicitly **excluded** to prevent scope creep:

- ❌ Production-grade real-time video stream deployment and edge device (Jetson) optimisation
- ❌ Integration with operators' existing safety management systems
- ❌ Commercial product development, UI polish, multi-user permission management
- ❌ Work on live construction sites or long-term deployed monitoring
- ❌ Sensor modalities beyond vision (IoT sensors, wearables, BIM data)
- ❌ Quality inspection and asset auditing of telecommunication equipment itself (an inspection problem, not a construction safety problem)

### A.2 Key Assumptions

| # | Assumption | Response if it fails |
|---|-----------|---------------------|
| 1 | At least 300 usable real telecommunication images can be obtained | Trigger D1; reposition to generalised work-at-height scenes |
| 2 | The team has access to at least one 24 GB GPU | Trigger D7; reduce model scale |
| 3 | Public datasets (SODA/MOCS/CHV etc.) can be requested and downloaded normally | Increase the self-collected share; extend M1 |
| 4 | 2–3 annotators can be found for 200 risk-level annotations | Team members cross-annotate per the guideline; report agreement Kappa |
| 5 | All members can meet the weekly in-person meeting requirement | Escalate to the supervisor; reassess team composition |

### A.3 Principal Stakeholders

| Stakeholder | Role | Interest | Communication frequency |
|------------|------|----------|------------------------|
| Project supervisor | Decision and acceptance | Academic contribution, progress, methodological rigour | Weekly (in person, via the leader) |
| Team members (5) | Execution | Fair allocation, traceable contribution | Daily asynchronous + weekly meeting |
| EE6008 assessors | Grading | Completeness of deliverables, report and defence quality | At milestones |
| Potential adopters (operators / contractors) | Indirect beneficiaries | Practicality, transferability | After project completion |

### A.4 Change Control (Internal Convention)

Changes requiring the formal process: any change of scope, milestone slippage beyond one week, triggering of any downgrade path D1–D8, or major reassignment of member responsibilities.

Process: **written proposal (change, reason, impact) → discussion at the weekly or gate meeting → team vote → supervisor approval where scope or milestones are affected → recorded in the change log and reflected in the relevant documents**.

Changes not requiring the process: implementation details, hyperparameter and model configuration changes, documentation wording, and task reordering that does not affect delivery dates.

### A.5 Change Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2026-08-19 | Initial version (generic PMBOK structure, 15 sections) | — |
| v2.0 | 2026-08-22 | **Restructured to the official template `EE6008_Project_Charter_Template.docx`**; content outside the official template moved to Appendix A | — |
| `<<v2.1>>` | `<<date>>` | `<<Fill in names, team leader, Project No., supervisor and specific dates>>` | `<<Team leader>>` |

---

## Appendix B: Companion Document Index

The official charter template is deliberately brief; the following documents provide full argumentation:

| Document | Which part of this charter it supports |
|----------|--------------------------------------|
| [00 Requirements Analysis](00-Requirements-Analysis-EN.md) | Detailed argumentation for Project Purpose or Justification |
| [01 Technical Plan & Milestones](01-Technical-Plan-and-Milestones-EN.md) | Full technical approach behind Project Description; detailed task breakdown behind Summary Milestones |
| [02 Datasets & Pretrained Models](02-Datasets-and-Pretrained-Models-EN.md) | Technology selection rationale; licensing notes for Summary Budget |
| [03 Generative Augmentation Pipeline](03-Generative-Augmentation-Pipeline-EN.md) | Complete design of the core method |
| [04 Literature Survey](04-Literature-Survey-EN.md) | Academic grounding for the justification (50 references, five research gaps) |
| [05 Technological Roadmap](05-Technological-Roadmap-EN.md) | Full definitions of gates TG1–TG5 and downgrade paths D1–D8 cited in Risk Assessment |
| [06 Teamwork Allocation](06-Teamwork-Allocation-EN.md) | Detailed responsibilities behind the Team Member Activity matrix; leader election; contingency plans |

---

## ✅ Pre-Submission Checklist

```
□ Project No. verified with the supervisor (inferred as 45)
□ Academic Year / Semester verified (inferred as 2026/27 Semester 1)
□ Supervisor name filled in
□ Real names of all five members entered in the information table and activity matrix
□ Team Leader elected and recorded
□ Date Prepared filled in
□ W1–W16 in Summary Milestones converted to calendar dates
□ Project duration (12 or 16 weeks) confirmed
□ Scope confirmed (whether to focus on Workers + Machinery)
□ Laboratory equipment and safety training status confirmed and recorded
□ Decided whether a cloud GPU budget application is needed
□ Content pasted into the Word template and formatting checked
```
