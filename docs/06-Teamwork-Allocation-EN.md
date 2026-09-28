# TelecomSafe — Teamwork Allocation

> Document version: v2.0 ｜ Generated: 2026-08-19 ｜ Revised: 2026-09-28 (duties and schedule adjusted for the v3.0 two-phase flow)
> Chinese counterpart: [06-团队分工-CN.md](06-团队分工-CN.md)
> Team size: 5 (this document uses the placeholders **Member A–E**; replace with real names once the team is formed)

---

## 0. How to Use This Document

- **Member A–E** are placeholders. After the first team meeting, fill names and contact details into the role table in §2.
- The **Team Leader is deliberately not pre-assigned**. If not yet elected, they are elected at the phase 1 kick-off meeting (§10) using the nomination criteria and process in §3.
- The allocation is based on the five-layer architecture and M0–M7 milestones (v3.0 two-phase version) in `01-Technical-Plan-and-Milestones-EN.md`; the two documents must be kept in sync.

---

## 1. Allocation Design Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Divide by technology layer, not by week** | Each person owns one complete technology layer end to end. This avoids the "you annotate this week, he annotates next week" fragmentation that destroys accountability |
| 2 | **Two people on the innovation module** | The L2 generation layer is the project's core innovation; single-point-of-failure risk is unacceptable, so it needs a lead and a deputy |
| 3 | **Everyone owns one 🔴 high-risk task** | Following the maturity assessment in roadmap §6, high-risk tasks are distributed across members rather than concentrated on one person |
| 4 | **Interfaces before implementation** | Data formats and interface contracts between members must be agreed in writing before coding (see §6), or integration will inevitably require rework |
| 5 | **The leader does not take the heaviest technical task** | The leader needs 20–25% of their time for coordination, supervisor liaison and schedule management. Carrying the hardest technical module as well means doing both badly |

---

## 2. Role Definitions and Responsibilities

### 2.1 Role Overview

| ID | Role | Primary layer | Core deliverables | High-risk task |
|----|------|--------------|------------------|---------------|
| **Member A** | Data Lead | L2 Data | Risk Taxonomy ✅, TelecomSeed / TelecomEval ✅, class mapping table | 🔴 Class mapping and dataset merging |
| **Member B** | Generation Lead | L2 Generation (lead) ★ | LoRA models, generation engines, TelecomSynth dataset | 🔴 Meeting generation quality targets (TG2) |
| **Member C** | Perception Lead – Workers | L3 Workers + Behaviour | Baseline detector, experiments E1 / E2 / E3 | 🔴 Validating augmentation effectiveness (TG3) |
| **Member D** | Perception Lead – Scene | L3 Machinery (phase 1) + Materials / Terrain (phase 2, optional) | Machinery classes, per-class error analysis, E9 | 🔴 No public data for terrain/materials |
| **Member E** | Fusion & System Lead | L4 Fusion + L5 System | Rule judgement, Demo v1 / v2, three-level fusion, experiment tracking | 🔴 Demo v1 running on time (TGB); three-level fusion (TG4) |

> ★ **Member A also serves as deputy for L2 generation.** Generation is the core innovation and requires close collaboration: A supplies the seed data and specification library, B handles generation and the quality gates. Both are jointly accountable for TG2.

### 2.2 Detailed Responsibilities

#### Member A ｜ Data Lead

**Responsibilities**
- ✅ **Done offline**: Risk Taxonomy, T1/T2/T3 public data curation, TelecomSeed and 🔒 TelecomEval split, `licence_manifest.csv`
- Commit the taxonomy file, actual image counts and a hash of the TelecomEval file list to the repository
- **Class mapping table**: align every dataset's labels to the taxonomy classes (first job of phase 1, with C and D)
- Maintain the annotation guideline and adjudicate edge cases that still conflict after mapping
- Maintain DVC data version control, recording provenance and licence of every subset
- **Deputy role**: the phase 2 Stage 0 risk scenario specification library (with B, prioritised by the baseline weak-class list)

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Risk Taxonomy v1.0 | End W1 | ✅ Done |
| TelecomSeed-v1 + 🔒 TelecomEval-v1 + licence_manifest.csv | End W3 | ✅ TG1 passed |
| Repository records: taxonomy file, actual counts, TelecomEval hash | Mid W4 | — |
| Class mapping table | End W4 | TGB |
| Risk scenario specification library (with B) | End W8 | TG2 |
| Risk Taxonomy v2.0 (terrain/material refinement) | W12 | — |

**Phase 1 focus**: the class mapping table is the precondition for training any baseline (document 01 §5 R1). Without clean mapping, the model learns contradictory labels.

---

#### Member B ｜ Generation Lead ★ CORE INNOVATION ★

**Responsibilities**
- **Phase 1 preparation (W4–W7)**: set up the generation environment, trial SDXL + LoRA + inpainting, and run a minimal end-to-end chain (10 images → visual inspection)
- Comparative selection of the base generative model (SDXL / SD3.5 / FLUX)
- LoRA fine-tuning to inject telecommunication construction visual characteristics
- Implement the generation routes from lowest to highest risk: inpainting → background swap → T2I / ControlNet
- Implement automatic annotation (mask inheritance / layout-map conversion / Grounding DINO + SAM fallback)
- Implement and calibrate the four quality gates (G3 reuses the phase 1 baseline detector)
- Bulk-generate TelecomSynth targeted at the baseline weak-class list, and produce the quality assessment report
- Own pipeline ablation experiments A1–A7

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Generation environment + minimal chain trial | End W7 | — |
| LoRA fine-tuned model + base model selection | End W8 | — |
| Inpainting + background swap routes | Mid W9 | — |
| Four quality gates + threshold calibration | End W9 | — |
| TelecomSynth-v1 (≥ 3,000 images) + quality report | End W10 | **TG2** |
| Pipeline ablations A1–A7 | W15 | — |

**Risk note**: this is the most technically demanding role and the one most likely to slip. v3.0 moves the generation start to W8, but **the four weeks of phase 1 are not idle time** — entering phase 2 without a working environment leaves the three-week generation window very tight.

---

#### Member C ｜ Perception Lead — Workers

**Responsibilities**
- **Phase 1**: train the baseline detector (YOLOv11, Workers + Machinery classes), run E1 / E2, and report per-class AP and the confusion matrix
- Write and commit `configs/baseline.yaml`, read-only from then on
- **Phase 2**: run E3 with the same configuration — the make-or-break experiment for the project
- Implement the synthetic/real mixed training strategy (ratio scheduling, loss weighting)
- Long-tail / weak-class experiment E6; model-side execution of robustness experiment E7
- Optional: Workers multi-head structure (pose + multi-label PPE), skeleton action recognition (or the D6 single-frame substitute)

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Baseline detector + E1 / E2 results | End W6 | — |
| `configs/baseline.yaml` committed + per-class AP (weak-class list with D) | End W7 | **TGB** |
| **E3 generative augmentation results** | End W12 | **TG3** |
| Behaviour model (or D6 fallback; optional) | W14 | — |
| E6 long-tail and E7 robustness experiments | W15 | — |

**Risk note**: C's E3 experiment is the project's decision point. **Once the baseline is frozen in W7 it must not change** — alter the configuration, data split or random seed and E3 is no longer comparable with E1/E2.

---

#### Member D ｜ Perception Lead — Scene

**Responsibilities**
- **Phase 1**: prepare and quality-check the Machinery classes (completing the class mapping with A)
- **Phase 1**: own the baseline's **per-class error analysis**, producing the weak-class list together with C
- Machinery: person–machine distance computation (handed to E's rule layer)
- **Phase 2 (if time allows, optional)**: Materials stacking geometry rules, Terrain semantic segmentation (SAM 2 assisted annotation)
- Work with A to define quantitative criteria for "poorly stored" materials and "uneven" terrain
- Cross-site generalisation experiment E9

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Machinery class data check | End W5 | — |
| Person–machine distance module (handed to E) | End W6 | — |
| Per-class error analysis + weak-class list (with C) | End W7 | **TGB** |
| Materials / Terrain models (optional) | W14 | — |
| E9 cross-site generalisation | W15 | — |

**Risk note**: Terrain and Materials are both 🔴 — no public data and subjective class definitions — so **from v3.0 they are out of phase 1 by default (D8)**. They start in phase 2 only if TG3 passes and the schedule is on track.

---

#### Member E ｜ Fusion & System Lead

**Responsibilities**
- **Phase 1**: encode 5–10 hard rules (each citing OSHA / GB 26859 or similar) that turn detection boxes into a low / medium / high risk level
- **Phase 1**: Gradio Demo v1 (decoupled into `detect` → `judge` → `render`)
- Define the perception output schema (interface I5) so the rule layer can be developed against mock detections
- Set up and maintain the experiment tracking platform (W&B / MLflow)
- **Phase 2**: extend the rule base to ≥ 15 rules; entity graph + level-3 learnable fusion (optional)
- Organise expert risk-level annotation (200 images, 2–3 annotators, compute agreement Kappa)
- Demo v2 (with the augmented weights swapped in)

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Experiment tracking platform + perception output schema (I5) | End W4 | — |
| Rule judgement module (5–10 rules) | End W6 | — |
| Demo v1 | End W7 | **TGB** |
| Expert risk annotation set (200 images) | End W12 | — |
| Three-level fusion module + E8 | End W14 | **TG4** |
| Demo v2 | End W15 | **TG5** |

**Risk note**: v3.0 pulls E's work forward sharply — Demo v1 is the phase 1 deliverable, so E is on the critical path from W4. Start recruiting expert annotators in W10; this is the task most often deferred until it is too late, leaving TG4 unmeasurable.

---

## 3. Team Leader

### 3.1 Leader Responsibilities

The leader is **not** the chief engineer but the project coordinator:

| Category | Responsibility |
|----------|---------------|
| **External** | Sole point of contact with the supervisor; convenes and chairs the weekly in-person meeting; prepares reporting material |
| **Schedule** | Maintains the kanban; checks milestones weekly; identifies and flags slippage early |
| **Decisions** | Chairs the gate meetings (TGB, TG2–TG5); organises assessment and voting on downgrade paths |
| **Coordination** | Resolves interface disputes between members; reallocates temporary support to lagging modules |
| **Documentation** | Ensures minutes, decision records and contribution logs reach the repository promptly |
| **Arbitration** | Calls a vote when technical disagreement cannot be resolved; makes the final call on allocation conflicts |

**Time allocation**: roughly 20–25% goes to coordination, so the leader's technical module should be one of the lighter of the five roles.

### 3.2 Nomination Criteria

Candidates should meet the following. **Bold items are mandatory**; the rest are advantageous.

| # | Criterion | Note | Weight |
|---|-----------|------|--------|
| 1 | **Can guarantee on-campus attendance** | The brief requires `regular in-person meetings on campus` and states `absence and remote working are unacceptable`. Anyone unable to attend reliably is not eligible | **Mandatory** |
| 2 | **Can guarantee time commitment** | The project requires `substantial time commitment`; the leader carries an extra 20–25% coordination load | **Mandatory** |
| 3 | **Willingness to communicate and coordinate** | Willing to chase progress and handle disagreement, not only to write code | **Mandatory** |
| 4 | Project management experience | Prior experience leading or organising a team is an advantage | High |
| 5 | System-level technical understanding | Understands the interdependence of all five layers, not only their own | High |
| 6 | Written communication | Must write reporting material, minutes and written communication with the supervisor | Medium |
| 7 | Conflict handling | Can stay neutral in disagreement and drive to a decision | Medium |

> **Important**: criterion 1 (on-campus attendance) is an explicit requirement of the project brief, worded as `absence and remote working on the project are unacceptable`. All candidates should confirm they can meet it before the election.

### 3.3 Election Process

If the leader has not yet been elected, complete this at the **phase 1 kick-off meeting** (§10):

```
Step 1  Read out responsibilities and criteria (5 min)
        All members read §3.1 and §3.2 and confirm understanding

Step 2  Self-nomination / nomination by others (10 min)
        · Self-nomination: state which criteria you meet
        · Nomination by others: the nominee must accept or decline on the spot
        · Each candidate speaks for 2 minutes: why me, and how I intend to manage progress

Step 3  Eligibility confirmation (5 min)
        Check each candidate against the three mandatory criteria (1/2/3)
        Anyone failing any of them withdraws

Step 4  Secret ballot (5 min)
        · One vote each; self-voting permitted
        · Highest number of votes wins
        · Tie: a second round among the tied candidates only
        · Still tied: the supervisor decides

Step 5  Confirmation and recording (5 min)
        · The elected member confirms acceptance on the spot
        · Record in the minutes; update the role table in §2.1
        · Inform the supervisor
```

### 3.4 Term and Replacement

| Item | Rule |
|------|------|
| Term | The full project cycle (W1–W16) |
| Mid-term review | **An anonymous satisfaction review at W8** (project midpoint), 5-point scale; below 3.0 triggers discussion |
| Replacement conditions | Any of: ① the leader resigns; ② more than half the members request replacement in writing; ③ core duties unperformed for two consecutive weeks (no meeting convened, kanban not maintained) |
| Replacement process | Re-run Steps 2–5 of §3.3 |
| Deputy leader | Recommended: elect a deputy at the same time (runner-up by votes) to act in the leader's absence |

---

## 4. RACI Responsibility Matrix

**R** = Responsible ｜ **A** = Accountable (exactly one per row) ｜ **C** = Consulted ｜ **I** = Informed

| Work item | Leader | A Data | B Gen | C Perc-W | D Perc-S | E Fusion/Sys |
|-----------|--------|--------|-------|----------|----------|-------------|
| Risk Taxonomy definition | C | **A/R** | C | C | C | C |
| Annotation guideline | I | **A/R** | C | C | C | I |
| T1/T2/T3 public data curation and licence records ✅ | C | **A/R** | I | I | I | I |
| Seed data annotation ✅ | I | **A/R** | I | R | R | I |
| Class mapping table | I | **A/R** | I | R | R | C |
| Baseline training and E1/E2 | C | I | I | **A/R** | R | C |
| Per-class error analysis and weak-class list | C | C | C | R | **A/R** | I |
| Rule judgement and Demo v1 | C | I | I | C | C | **A/R** |
| Risk scenario spec library | I | R | **A/R** | C | C | C |
| LoRA fine-tuning | I | C | **A/R** | I | I | I |
| Four generation engines | I | C | **A/R** | I | I | I |
| Automatic annotation | I | C | **A/R** | C | C | I |
| Quality gates + calibration | I | C | **A/R** | C | I | I |
| Bulk synthetic generation | I | C | **A/R** | I | I | I |
| Workers perception model | I | I | I | **A/R** | I | C |
| Behaviour recognition model | I | I | C | **A/R** | I | C |
| Machinery perception model | I | I | I | C | **A/R** | C |
| Materials state judgement | I | C | I | I | **A/R** | C |
| Terrain segmentation model | I | C | C | I | **A/R** | C |
| Core experiment E3 (retrain, same config) | C | I | C | **A/R** | I | C |
| Safety rule base encoding | C | C | I | C | C | **A/R** |
| Entity graph + three-level fusion | I | I | I | C | C | **A/R** |
| Expert risk annotation | C | C | I | I | I | **A/R** |
| Demo v2 + system integration | I | I | I | C | C | **A/R** |
| Experiment tracking platform | I | C | C | C | C | **A/R** |
| Robustness experiment E7 | C | I | R | **A/R** | R | I |
| Chairing gates (TGB, TG2–TG5) | **A/R** | C | C | C | C | C |
| Progress tracking and alerts | **A/R** | I | I | I | I | I |
| Supervisor communication | **A/R** | I | I | I | I | I |
| Paper/report consolidation | **A/R** | R | R | R | R | R |
| Defence presentation | **A/R** | R | R | R | R | R |

> **On writing**: the leader consolidates, but **every member drafts the section covering their own module**. This is what makes contribution traceable — style can be harmonised at the end, but the content must be written by whoever did the work.

---

## 5. Workload Distribution

### 5.1 Estimated Hours per Person per Week

| Phase | Weeks | Leader* | A Data | B Gen | C Perc-W | D Perc-S | E Fusion/Sys |
|-------|-------|---------|--------|-------|----------|----------|-------------|
| M0–M1 Preparation | W1–W3 | ✅ Done | | | | | |
| M2 Baseline | W4–W7 | 8 | **12** | 8 | **16** | **14** | **16** |
| M3 Generation | W8–W10 | 8 | 12 | **18** | 8 | 8 | 10 |
| M4 Retrain | W11–W12 | 8 | 6 | 10 | **16** | 10 | 10 |
| M5–M6 Fusion & evaluation | W13–W15 | 10 | 8 | 12 | **14** | 12 | **16** |
| M7 Delivery | W16 | **14** | 10 | 10 | 10 | 10 | 10 |

\* The leader's hours are **coordination work**, added on top of their own technical role. Bold marks the phase's principal contributors.

**Peak-load notes**:
- **In phase 1, C, D and E are all principal contributors**: baseline training, error analysis, rules and the demo run in parallel, so interface I5 must be settled by end of W4
- **B peaks in W8–W10**; the phase 1 preparation decides whether three weeks is enough
- **M4's E3 experiment is on the critical path**; if TG2 slips, M4 is squeezed directly

### 5.2 Phase 1 Staffing

- **A**: after the class mapping table in W4, help C and D check data quality
- **B**: prepare the generation environment in W4–W7 (off the phase 1 critical path, but it decides whether phase 2 starts on time)
- **E**: deliver interface I5 (perception output schema) by end of W4, so the rule layer is developed against mock detections in parallel with baseline training
- **During M3 (W8–W10), C and D are lightly loaded**: support B with G4 human spot-checks and prepare the E7 robustness test set early

---

## 6. Inter-member Interface Contracts

Almost all integration rework traces back to interfaces agreed too late. The following must be **confirmed in writing by their due dates**; any change must be notified to all downstream members.

| ID | Upstream | Downstream | Contract | Due |
|----|----------|-----------|----------|-----|
| I1 | A | B, C, D | **Data format**: YOLO / COCO; class mapping table; image naming convention | End W4 |
| I2 | A | All | **Risk Taxonomy**: class hierarchy, quantitative criterion per class, severity values | ✅ Done (to be committed) |
| I3 | A | B | **Spec library schema**: field definitions for `risk_scenarios.yaml` (see document 03, Stage 0) | Mid W8 |
| I4 | B | C, D | **Synthetic data delivery format**: identical to I1 + metadata JSON (seed/prompt/route/gate scores) | End W9 |
| I5 | C, D | E | **Perception output schema**: detection JSON (class, box, confidence) | **End W4** |
| I6 | E | All | **Experiment logging convention**: W&B project name, run naming rules, mandatory metric list | End W4 |
| I7 | A | E | **Expert annotation format**: risk level values, annotator ID, timestamp | End W10 |

> **v3.0 moves I5 forward to W4**: the phase 1 rule layer is developed against mock data in this format. The baseline emits boxes only, so the schema can be simple; phase 2 adds fields for segmentation / attribute outputs without changing existing ones.

---

## 7. Collaboration Mechanisms

### 7.1 Meeting Cadence

| Meeting | Frequency | Duration | Format | Chair | Output |
|---------|-----------|----------|--------|-------|--------|
| **Weekly stand-up** | Weekly | 60 min | ⚠️ **In person (hard project requirement)** | Leader | Minutes committed to the repo |
| Technical alignment | As needed | 30–60 min | In person preferred | Initiator | Decision record |
| **Gate meeting** | 5 (TGB, TG2–TG5) | 90 min | ⚠️ **In person + supervisor present** | Leader | Decision record + downgrade trigger status |
| Daily sync | Daily | Asynchronous | Chat / Issues | — | Blockers surfaced same day |

**Fixed weekly agenda**:
```
1. Review of last week against plan (10 min) — 2 minutes per person
2. This week's plan and declared dependencies (15 min) — state "I need X from Y by Z"
3. Blockers and requests for help (15 min)
4. Milestone and critical-path check (10 min) — chaired by the leader
5. Decisions and action items (10 min) — each action gets an owner and a due date
```

> ⚠️ **On the in-person requirement**: the brief states explicitly that `regular in-person meetings and discussions on campus are required` and that `absence and remote working on the project are unacceptable`. Fix the weekly meeting time and place, have everyone confirm they can attend, and record this in the minutes as a commitment.

### 7.2 Code Collaboration Conventions

| Item | Convention |
|------|-----------|
| Repository | https://github.com/muamuauh/AY26S1-45-SPML |
| Branching | `main` protected; each member develops on `feat/<module>`; merged via PR |
| PR rules | At least one reviewer; linked to its Issue; CI passing (once configured) |
| Commit format | `<type>: <description>`, type ∈ {feat, fix, docs, exp, refactor, chore} |
| Large files | Data and model weights **never** in Git; managed with DVC (`.gitignore` already configured) |
| Experiment records | Every experiment logged in W&B; run names include branch and key hyperparameters |

### 7.3 Escalation

```
Problem arises
   │
   ├─ Technical issue, no progress within 4 hours
   │     → ask for help in the group chat, tagging the relevant member
   │
   ├─ Cross-module dependency blocked for more than 1 day
   │     → report to the leader, who arbitrates priority
   │
   ├─ Milestone expected to slip by more than 3 days
   │     → leader raises it at the weekly meeting; the team assesses whether to trigger a downgrade path
   │
   └─ Gate failed / prolonged member absence / irreconcilable disagreement
         → leader escalates to the supervisor
```

---

## 8. Contribution Tracking and Fairness

The most common source of conflict in group projects is that contribution cannot be established afterwards. Build a traceable record from week one rather than arguing at the end.

| Record | Content | Maintained by |
|--------|---------|--------------|
| Git commit history | Code contribution; inherently traceable | Automatic |
| PR and review records | Who wrote it, who reviewed it | Automatic |
| Action items in minutes | Owner and completion status of every task | Leader |
| Experiment logs (W&B) | Who ran which experiments | Automatic |
| Document section authorship | Author of each report/paper section | Leader consolidates |
| **Periodic contribution statements** | A 200-word summary from each member at W4 / W8 / W12 / W16 | Each member |

> **Recommendation**: include a **Contribution Statement** table in the final report listing each person's modules and main outputs. This is standard academic practice (see the CRediT taxonomy) and effectively prevents grading disputes.

---

## 9. Contingency Plans

| Situation | Response |
|-----------|----------|
| **A member is absent for more than 2 weeks** | ① Leader speaks with them privately to understand why ② If unresolved, escalate to the supervisor ③ Reallocate duties per the table below |
| **A member falls seriously behind** | Assess openly at the weekly meeting; leader assigns temporary support; reduce their module scope if necessary |
| **The leader cannot perform the role** | Deputy takes over; re-elect per §3.4 |
| **A key member (B) leaves** | A takes over generation (already the deputy); simultaneously trigger downgrade path D2 to simplify the generation routes |
| **Two or more members absent simultaneously** | Escalate to the supervisor immediately and re-scope the project (D8 is the likely outcome) |

### Duty Reallocation on Member Loss

| Member lost | Handover plan | Downgrade triggered |
|------------|--------------|-------------------|
| A (Data) | Taxonomy and class mapping → Leader + D; data maintenance → split between C and D | — (curation already done) |
| B (Generation) | Generation → A (already deputy); gates → E | **D2** (inpainting route only) |
| C (Perception-Workers) | Workers → D; behaviour recognition → dropped | **D6** (single-frame pose substitute) |
| D (Perception-Scene) | Machinery → C; Terrain/Materials → dropped | **D8** (reduce to two dimensions) |
| E (Fusion/System) | Rules and demo → C; fusion → Leader + C; system → simplified to scripts | **DB / D4 + D5** |

> The purpose of this table is not to anticipate departures but to make clear **how irreplaceable each role is**. Losing B or E is the most costly, so those two modules most need a second person who can read the code — deliberately assign their PR reviews to one other member.

---

## 10. Phase 1 Kick-off Meeting Agenda (W4)

The first all-hands meeting after the v3.0 flow change; approximately 90 minutes.

```
1. The flow change (10 min)
   · Read 05 §0–§2 together: why baseline first, and how the two phases connect

2. Outstanding team set-up (20 min)
   □ Have roles A–E been claimed? If not, agree them per §2
   □ Has a leader been elected? If not, run §3.3
   □ Fill real names into §2.1 of this document and into document 07

3. Phase 1 hard constraints (20 min)
   □ Is TelecomEval frozen? Are the actual counts and file-list hash committed?
   □ Who completes the class mapping table by end of W4?
   □ configs/baseline.yaml is committed by C before W7 and read-only afterwards — everyone aware
   □ Interface I5 (perception output schema) finalised by end of W4

4. Key decisions (20 min)
   □ Project duration: 12 weeks or 16? Real calendar date of W1?
   □ Available compute: GPU model and count? (decides YOLOv11-s vs -m, and whether D7 applies)
   □ Telecommunication sub-scenarios: towers / optical cable / equipment rooms — which are in scope?

5. TGB arrangements (10 min)
   · Set the end-of-W7 TGB meeting time and invite the supervisor

6. Administrative items (10 min)
   · Fix the weekly meeting time and place (in person)
   · Create the progress/ directory for actual milestone completion dates

【Within 24 hours after the meeting】
   · Leader publishes the minutes and commits them to the repository
   · Update names in §2.1 of this document and in document 07
```
