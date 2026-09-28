# EE6008 Project Charter

> Document version: **v3.0** ｜ Generated: 2026-08-22 ｜ Revised: 2026-09-28 (two-phase flow on the supervisor's advice)
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

`<<YYYY-MM-DD>>` — suggested: the date of charter signature

---

## Project Information

| Field | Content |
|-------|---------|
| **Project No. & Project Title** | `<<45>>` — TelecomSafe: A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects |
| **Project Supervisor** | `<<Supervisor name>>` |
| **Team Leader** | `<<To be elected>>` — nomination criteria and election process in document [06 §3](06-Teamwork-Allocation-EN.md) |
| **Names of Team Members** | `<<Member A>>`, `<<Member B>>`, `<<Member C>>`, `<<Member D>>`, `<<Member E>>` (5 in total) |

> **Note**: the Team Leader field must be completed once the leader has been elected. The process is defined in document 06 §3.3 (nomination → eligibility check → secret ballot).

---

## Project Purpose or Justification

> *Template requirement: Describe the reason or justification the project is being undertaken.*

Telecommunication construction sites present multiple categories of safety risk, including uneven terrain, improperly operated machinery, poorly stored materials, missing personal protective equipment and unsafe worker behaviour. Conventional manual inspection is time-consuming, subjective and difficult to sustain across a whole site.

Deep-learning-based computer vision offers an effective means of automated safety monitoring, but its application in the telecommunication sector is constrained by one decisive bottleneck: **labelled, sector-specific imagery is both scarce and insufficiently diverse**. This bottleneck has three causes:

1. **Distribution mismatch.** All existing public construction datasets (SODA, MOCS, ACID and others) originate from building and municipal sites. Telecommunication scenes — lattice towers, monopoles, base-station equipment rooms, cable trenches, rooftop antennas — differ systematically in object morphology, camera viewpoint and working height, so directly transferred general-purpose models degrade substantially.

2. **Long-tail risks cannot be collected.** Genuinely hazardous scenes (for example a worker leaning out from a tower without a fall-arrest harness) are extremely rare in real data; and even when they occur, they are difficult to photograph and publish for ethical, legal and labour-relations reasons. This constitutes a structural deadlock in data acquisition.

3. **No sector-specific resources exist.** A systematic search of Google Scholar, IEEE Xplore and the ACM Digital Library found **no public annotated dataset or dedicated framework for telecommunication construction safety**. The nearest existing work concerns asset inspection of telecommunication towers, at the commercial-product level, rather than safety during construction.

> **Data source constraint**: following discussion with the supervisor, this project performs **no field data collection** (the safety risk and cost are too high); all real data comes from public online datasets and openly licensed image repositories.
> This constraint in fact **corroborates causes 2 and 3 above**: the team, unable to bear the cost of collection, must rely on generative methods, thereby demonstrating first-hand the founding premise that telecommunication-specific data is hard to obtain.

This project exists to fill that gap. TelecomSafe introduces **generative artificial intelligence** to synthesise training data and break the data-scarcity constraint, and combines deep-learning image processing with information fusion to appraise construction risk across four dimensions — terrain, machinery, materials and workers. The project carries both **academic value** (the relevant literature is concentrated in 2024–2026, making the topic timely, and none of it targets the telecommunication sector) and **engineering value** (transferable to the safety management practice of telecommunication operators and contractors).

---

## Project Description

> *Template requirement: Provide a summary description of the project. This section may include information on project deliverables as well as the approach of the project.*

### Overview

TelecomSafe is a multi-dimensional intelligent safety risk identification framework for telecommunication construction scenes. Its core innovations are **resolving sector-specific data scarcity through generative data augmentation** and **converting point detections into an interpretable, site-level risk appraisal through hierarchical information fusion**.

On the supervisor's advice, the project proceeds in **two phases**. **Phase 1** uses only the curated public data to train a baseline perception model, judge risk levels with safety rules, and deliver a working Baseline Demo. **Phase 2** then introduces generative data augmentation and compares against the baseline on the same test set with the same training configuration, demonstrating the gain.

### Technical Approach

The system adopts a five-layer architecture:

| Layer | Name | Content |
|-------|------|---------|
| **L1** | Input | Still images (phase 1 scope); video, UAV aerial imagery and tower-mounted recorders (extensions) |
| **L2** | **Data ★ CORE INNOVATION ★** | Curation and annotation of public data (T1 academic sets / T2 community sets / T3 openly licensed imagery) + generative augmentation pipeline + four quality gates. **No field collection whatsoever** |
| **L3** | Perception | Phase 1: a single Workers (people and PPE) + Machinery detector; phase 2 adds terrain segmentation and material state judgement if time allows |
| **L4** | **Fusion & Decision ★ SECONDARY CORE ★** | Phase 1: regulation-derived rules judge the risk level directly; phase 2: entity graph → rule layer → learnable fusion → risk score |
| **L5** | Application | Demo (v1 in phase 1 / v2 in phase 2): detection visualisation, risk scorecard, triggered-rule list |

### Core Method: Generative Data Augmentation (Phase 2)

The pipeline uses SDXL with LoRA domain adaptation, **generating data targeted at the weak classes identified by the baseline's per-class error analysis**. Routes advance from lowest to highest risk:

- **Inpainting local editing** — remove PPE such as helmets from real images while the bounding-box annotation is inherited unchanged (smallest domain gap)
- **Background replacement** — produce rain, fog and night-time variants for robustness testing, with annotations unchanged
- **Text-to-image** — generate rare hazardous scenes entirely absent from the real world
- **ControlNet layout control** — the semantic layout map is both the generation condition and, directly, the segmentation annotation (zero annotation cost)

All synthetic data must pass four quality gates (G1 semantic consistency / G2 distributional consistency / G3 annotation reliability / G4 human spot-check), with an expected retention rate of 50–65%.

### Data Sources (public sources only, zero field collection; T1–T3 curated offline)

| Tier | Source | Content | Scale |
|------|--------|---------|-------|
| **T1** | Academic public datasets | SODA, MOCS, ACID, CHV, SHEL5K, SHWD, Pictor-v3 | 20,000+ images (transfer base) |
| **T2** | Community dataset platforms | Roboflow Universe (telecom tower set, safety harness sets), Kaggle construction safety set (includes NO-Hardhat negatives) | 2,000–5,000 images |
| **T3** | Openly licensed repositories | Wikimedia Commons, Openverse, Flickr CC — manually searched and screened, with source and attribution recorded per image | 200–500 images (source of sector specificity) |
| **T4** | Generative synthesis | TelecomSynth, the core output of this project | 3,000–10,000 images |

> 🔒 **Test set discipline**: TelecomEval (150–300 real images drawn from T2/T3) stays frozen throughout and never participates in LoRA fine-tuning or generation conditioning. Every experimental conclusion depends on this.
> ⚖️ **Licence compliance**: CC BY and CC BY-SA require attribution; `licence_manifest.csv` must accompany the report.

### Principal Deliverables

| Category | Deliverables |
|----------|-------------|
| **Data** | Risk Taxonomy for telecommunication construction, annotation guideline, **TelecomSeed** (real seed set from public sources, 200–500 images), 🔒 **TelecomEval** (isolated test set, 150–300 images), **TelecomSynth** (synthetic dataset, ≥ 3,000 images), `licence_manifest.csv` (open-licence attribution manifest) |
| **Models** | Baseline perception model, LoRA domain-adapted generative model, generation engines, augmented perception model, information fusion module |
| **System** | Baseline Demo v1 (phase 1) and the augmented Demo v2 (phase 2): upload image → detection boxes → risk scorecard → triggered rules |
| **Experiments** | Complete E1–E9 results, centred on E3 (validation of augmentation effectiveness) and E7 (robustness) |
| **Documentation** | EE6008 project report, defence presentation, code repository with reproduction scripts |

### Method of Working and Key Criteria

The project manages technical risk through a **two-phase, decision-gate mechanism**: phase 1 delivers a Baseline Demo first, and phase 2 then adds generative augmentation and compares against the baseline. At W3, W7, W10, W12, W14 and W15, objective metrics determine whether to continue, adjust or downgrade, with a fallback pre-defined for every gate (see document [05 §4](05-Technological-Roadmap-EN.md)).

Key gates:

| Gate | Timing | Criterion |
|------|--------|-----------|
| **TG1** Data foundation | End W3 | TelecomSeed ≥ 200; TelecomEval ≥ 150, frozen — ✅ curation completed offline |
| **TGB** Baseline | End W7 | Demo v1 runs end-to-end; E1/E2 results on TelecomEval recorded; baseline training configuration fixed |
| **TG2** Generation quality | End W10 | FID(synthetic, real) < 50; human realism rating ≥ 3.0/5 |
| **TG3** Augmentation effectiveness | End W12 | E3 improves mAP over E2 by ≥ 2.0 (overall or on weak classes) — **the project's decisive checkpoint** |

### Scope Note

Delivering all four risk dimensions to high quality within a single semester is not realistic. **It has been decided that phase 1 covers only the Workers and Machinery dimensions, with Terrain and Materials added in phase 2 if time allows**; this scope boundary will be stated honestly in the final report.

---

## Summary Milestones

> *Template requirement: List significant activities / events in the project. Target completion date of the milestone.*

| Summary Milestones | Target Date |
|-------------------|-------------|
| **M0 Setup and Risk Taxonomy** — Risk Taxonomy v1.0, literature survey, role assignment ✅ done | W1 ｜ `<<YYYY-MM-DD>>` |
| **M1 Public data curation** — curate T1/T2/T3 public data; deliver TelecomSeed, TelecomEval (frozen) and `licence_manifest.csv`; **Gate TG1** ✅ done | End W3 ｜ `<<YYYY-MM-DD>>` |
| **M2 Baseline Demo (phase 1)** — class mapping, baseline detector and experiments E1/E2, weak-class list, rule-based risk judgement, Demo v1; **Gate TGB** | End W7 ｜ `<<YYYY-MM-DD>>` |
| **M3 Generative augmentation (phase 2)** — LoRA model, generation engines, four quality gates, TelecomSynth-v1 (≥ 3,000 images); **Gate TG2** | End W10 ｜ `<<YYYY-MM-DD>>` |
| **M4 Retrain with the same configuration** — E3 compared against the baseline, Demo v2; **Gate TG3 (decisive)** | End W12 ｜ `<<YYYY-MM-DD>>` |
| **M5 Fusion upgrade** — safety rule base (≥ 15 rules), three-level fusion module, expert risk annotation set, experiment E8; **Gate TG4** | End W14 ｜ `<<YYYY-MM-DD>>` |
| **M6 Full evaluation** — experiments E4–E9, robustness test set, ablation tables, final Demo v2; **Gate TG5** | End W15 ｜ `<<YYYY-MM-DD>>` |
| **M7 Delivery** — project report, defence presentation, curated code repository | W16 ｜ `<<YYYY-MM-DD>>` |

> **To confirm**: whether the project runs 12 or 16 weeks. The table above assumes 16; for 12 weeks, compress M3 and M5–M6 and make video behaviour recognition and Terrain / Materials optional (see document [01 §4](01-Technical-Plan-and-Milestones-EN.md)).
> **Dates**: once the semester start week is confirmed, convert W1–W16 into calendar dates in the right-hand column.

---

## Team Member Activity

> *Template requirement: Activity in which a team member plays a key role.* ✅ marks a key role; **●** marks the accountable owner.

| Activity | Member 1<br>`<<A Data>>` | Member 2<br>`<<B Generation>>` | Member 3<br>`<<C Perc-Workers>>` | Member 4<br>`<<D Perc-Scene>>` | Member 5<br>`<<E Fusion/System>>` |
|---------|:---:|:---:|:---:|:---:|:---:|
| A1 Risk Taxonomy and annotation guideline | ● | ✅ | | | |
| A2 Public data curation, licence records and class mapping (TelecomSeed / TelecomEval) | ● | | ✅ | ✅ | |
| A3 Baseline detector training and experiments E1/E2 | | | ● | ✅ | |
| A4 Per-class error analysis and weak-class list | | | ✅ | ● | |
| A5 Rule-based risk judgement and Baseline Demo v1 | | | | ✅ | ● |
| A6 Risk scenario specification library | ✅ | ● | | | |
| A7 LoRA domain adaptation and generation engines | ✅ | ● | | | |
| A8 Quality gates and bulk synthetic generation (TelecomSynth) | | ● | | | ✅ |
| A9 **Core experiment E3 (augmentation effectiveness)** | | ✅ | ● | | ✅ |
| A10 Machinery / Materials / Terrain model extension | ✅ | | | ● | |
| A11 Behaviour recognition (skeleton action, optional) | | ✅ | ● | | |
| A12 Three-level fusion module and expert annotation | | | ✅ | ✅ | ● |
| A13 Demo v2, experiment tracking platform and reproduction scripts | | ✅ | ✅ | ✅ | ● |
| A14 Robustness and generalisation experiments (E7 / E9) | | ✅ | ● | ✅ | |
| A15 Project report writing and defence presentation | ✅ | ✅ | ✅ | ✅ | ✅ |

> **Notes**:
> - Members 1–5 correspond one-to-one with Members A–E in document [06 §2](06-Teamwork-Allocation-EN.md); names to be filled in
> - The team leader carries approximately 20–25% additional coordination load on top of their technical role (supervisor liaison, chairing weekly and gate meetings, progress tracking)
> - A15 is shared by all: **each member drafts the section covering their own module**, with the leader consolidating. This maps directly onto the "Individual Reports from Team Members" section required by the official report template

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
| **Work on live construction sites** | ❌ **Not involved at all.** Following discussion with the supervisor, the safety risk and cost of field collection were judged too high, and **all on-site data collection has been cancelled**. Every real image comes from public online datasets and openly licensed repositories; the team enters no construction site, climbs no tower, and approaches no operating machinery |
| **Equipment usage training** | `<<To confirm>>` — confirm whether training and account provisioning for the laboratory GPU cluster/workstations are complete |
| **General laboratory safety training** | `<<To confirm>>` — if required by the school, to be completed by `<<date>>` |

### General Project Risks

| ID | Risk | Probability | Impact | Mitigation | Gate |
|----|------|------------|--------|-----------|------|
| **R1** | Limited real telecommunication data (no dedicated public dataset, and no field collection) | High | High | Four-tier public-source strategy (T1 academic / T2 community / T3 openly licensed imagery, curated offline); weak classes exposed by the baseline are filled by targeted generative augmentation (T4) in phase 2 | TG1 ✅ |
| **R2** | Source datasets name labels inconsistently, so merged labels contradict each other | High | High | First job of phase 1: a class mapping table aligned to the Risk Taxonomy; spot-check 50 annotations per community dataset | TGB |
| **R3** | The baseline training configuration or test set changes mid-project, so phase 2 cannot be compared fairly with the baseline | Medium | **High** | Commit the baseline configuration file and a hash of the TelecomEval file list, read-only from then on; E3 changes only the training data | TG3 |
| **R4** | Generated image quality inadequate, causing negative transfer (synthetic data degrades performance) | Medium | **High** | ① Strict filtering by the four quality gates ② Conservative ratio (start at 25%) ③ Inpainting route first. If FID > 70, trigger **D2**: keep only the inpainting and background-replacement routes that edit real images | TG2 |
| **R5** | E3 fails to demonstrate augmentation effectiveness (the project's central claim does not hold) | Medium | **High** | ① Diagnose label noise and mixing ratio first ② Switch to class-adaptive ratios. If there is still no gain, trigger **D3**: narrow the conclusion to "improves weak / long-tail class performance" and state honestly that overall performance did not improve | TG3 |
| **R6** | Insufficient compute (diffusion training and inference are expensive) | Medium | Medium | ① LoRA rather than full fine-tuning ② SDXL-Turbo for >10× faster bulk generation ③ 8-bit quantisation and gradient checkpointing ④ Apply for cloud GPU if necessary. Triggers **D7** | — |
| **R7** | Scope too large (four dimensions cannot all be completed in one semester) | High | High | **Decided: phase 1 covers Workers + Machinery only**, with Terrain and Materials added in phase 2 if time allows (D8) | — |
| **R8** | No video data, so behaviour recognition cannot proceed | High | Low | Not in phase 1; in phase 2, replace temporal action recognition with single-frame pose estimation plus rules (**D6**) | — |
| **R9** | No ground truth for the fusion module (risk level has no objective standard) | Medium | Medium | ① Generate weak labels from the rule base ② Have 2–3 annotators assign risk levels to 200 images and compute agreement Kappa ③ Begin recruiting annotators in W10 | TG4 |
| **R10** | Teamwork risks: absence, uneven progress, unclear contribution | Medium | Medium | ① Weekly in-person meetings (a hard project requirement) ② Kanban plus a full trail in Git/PR/W&B ③ Document [06 §9](06-Teamwork-Allocation-EN.md) pre-defines handover plans for the loss of any member | — |
| **R11** | Data privacy and compliance (public images contain identifiable workers) | Low | Medium | ① Research use only; original images are not redistributed ② Follow each dataset's licence and attribution terms (`licence_manifest.csv`) ③ **Synthetic data depicts no real individual** — an additional advantage of the generative approach | — |
| **R12** | The in-person attendance requirement cannot be met (the brief prohibits remote work) | Low | **High** | Fix the weekly meeting time and place with written confirmation from all members; leader candidates must confirm they can meet this mandatory requirement first | — |

> **Full definitions of the downgrade paths (DB, D2–D8)** are given in document [05 §4](05-Technological-Roadmap-EN.md). Each path has been assessed for its effect on final outcomes, ensuring that no single risk trigger causes overall project failure.

---

## Appendix A: Supplementary Internal Management Material (Not in the Official Template)

> The following is outside the official charter template's fields but retains practical value for project management, and is kept for internal team reference.

### A.1 Explicit Non-Objectives (Out of Scope)

The following are explicitly **excluded** to prevent scope creep:

- ❌ Production-grade real-time video stream deployment and edge device (Jetson) optimisation
- ❌ Integration with operators' existing safety management systems
- ❌ Commercial product development, UI polish, multi-user permission management
- ❌ Work on live construction sites, field data collection, or long-term deployed monitoring
- ❌ Sensor modalities beyond vision (IoT sensors, wearables, BIM data)
- ❌ Quality inspection and asset auditing of telecommunication equipment itself (an inspection problem, not a construction safety problem)

### A.2 Key Assumptions

| # | Assumption | Response if it fails |
|---|-----------|---------------------|
| 1 | Enough real telecommunication images can be obtained from public sources | ✅ Met (curation completed) |
| 2 | The team has access to at least one 24 GB GPU | Trigger D7; reduce model scale |
| 3 | Phase 1 can deliver the Baseline Demo by W7 | Trigger DB: shrink to the Workers dimension with script output; phase 2 slips by at most one week |
| 4 | 2–3 annotators can be found for 200 risk-level annotations | Team members cross-annotate per the guideline; report agreement Kappa |
| 5 | All members can meet the weekly in-person meeting requirement | Escalate to the supervisor; reassess team composition |

### A.3 Change Control (Internal Convention)

Changes requiring the formal process: any change of scope, milestone slippage beyond one week, triggering of any downgrade path (DB, D2–D8), or major reassignment of member responsibilities.

Process: **written proposal (change, reason, impact) → discussion at the weekly or gate meeting → team vote → supervisor approval where scope or milestones are affected → recorded in the change log and reflected in the relevant documents**.

Changes not requiring the process: implementation details, hyperparameter and model configuration changes, documentation wording, and task reordering that does not affect delivery dates.

### A.4 Change Log

| Version | Date | Change | Author |
|---------|------|--------|--------|
| v1.0 | 2026-08-19 | Initial version (generic PMBOK structure, 15 sections) | — |
| v2.0 | 2026-08-22 | **Restructured to the official template `EE6008_Project_Charter_Template.docx`**; content outside the official template moved to Appendix A | — |
| v2.1 | 2026-08-24 | **Data strategy change**: following discussion with the supervisor, all field collection is cancelled in favour of public sources only (T1 academic / T2 community / T3 openly licensed / T4 generative synthesis). Project description, budget (collection costs zeroed) and risk assessment (R1 rewritten, site-work risk zeroed) updated accordingly | `<<Team leader>>` |
| v3.0 | 2026-09-28 | **Flow change**: on the supervisor's advice, two phases — phase 1 delivers a Baseline Demo from public data only; phase 2 adds generative augmentation and compares against the baseline. Project description, key criteria (TGB added), milestones, activity matrix and risk assessment updated; M0–M1 marked done | `<<Team leader>>` |
| `<<v3.1>>` | `<<date>>` | `<<Fill in names, team leader, Project No., supervisor and specific dates>>` | `<<Team leader>>` |

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
| [05 Technological Roadmap](05-Technological-Roadmap-EN.md) | The two-phase flow, and full definitions of the gates (TGB, TG1–TG5) and downgrade paths cited in Risk Assessment |
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
□ Two-phase flow and scope confirmed with the supervisor (phase 1: Workers + Machinery only)
□ Laboratory equipment and safety training status confirmed and recorded
□ Decided whether a cloud GPU budget application is needed
□ Content pasted into the Word template and formatting checked
```
