# TelecomSafe — Teamwork Allocation

> Document version: v1.0 ｜ Generated: 2026-08-19
> Chinese counterpart: [06-团队分工-CN.md](06-团队分工-CN.md)
> Team size: 5 (this document uses the placeholders **Member A–E**; replace with real names once the team is formed)

---

## 0. How to Use This Document

- **Member A–E** are placeholders. After the first team meeting, fill names and contact details into the role table in §2.
- The **Team Leader is deliberately not pre-assigned**. They are elected at the first meeting using the nomination criteria and process in §3.
- The allocation is based on the five-layer architecture and M0–M7 milestones in `01-Technical-Plan-and-Milestones-EN.md`; the two documents must be kept in sync.

---

## 1. Allocation Design Principles

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Divide by technology layer, not by week** | Each person owns one complete technology layer end to end. This avoids the "you annotate this week, he annotates next week" fragmentation that destroys accountability |
| 2 | **Two people on the innovation module** | The L2 generation layer is the project's core innovation; single-point-of-failure risk is unacceptable, so it needs a lead and a deputy |
| 3 | **Everyone owns one 🔴 high-risk task** | Following the maturity assessment in roadmap §5, high-risk tasks are distributed across members rather than concentrated on one person |
| 4 | **Interfaces before implementation** | Data formats and interface contracts between members must be agreed in writing before coding (see §6), or integration will inevitably require rework |
| 5 | **The leader does not take the heaviest technical task** | The leader needs 20–25% of their time for coordination, supervisor liaison and schedule management. Carrying the hardest technical module as well means doing both badly |

---

## 2. Role Definitions and Responsibilities

### 2.1 Role Overview

| ID | Role | Primary layer | Core deliverables | High-risk task |
|----|------|--------------|------------------|---------------|
| **Member A** | Data Lead | L2 Data | Risk Taxonomy, annotation guideline, TelecomSeed dataset | 🔴 Defining quantitative criteria in the Risk Taxonomy |
| **Member B** | Generation Lead | L2 Generation (lead) ★ | LoRA models, four generation engines, TelecomSynth dataset | 🔴 Meeting generation quality targets (TG2) |
| **Member C** | Perception Lead – Workers | L3 Workers + Behaviour | Workers multi-head model, action recognition, experiments E1–E3 | 🔴 Validating augmentation effectiveness (TG3) |
| **Member D** | Perception Lead – Scene | L3 Machinery + Materials + Terrain | Three branch models, terrain segmentation, material state judgement | 🔴 No public data for terrain/materials |
| **Member E** | Fusion & System Lead | L4 Fusion + L5 System | Rule base, three-level fusion, web demo, experiment tracking | 🔴 No mature precedent for three-level fusion (TG4) |

> ★ **Member A also serves as deputy for L2 generation.** Generation is the core innovation and requires close collaboration: A supplies the seed data and specification library, B handles generation and the quality gates. Both are jointly accountable for TG2.

### 2.2 Detailed Responsibilities

#### Member A ｜ Data Lead

**Responsibilities**
- Define the **Risk Taxonomy** (4 categories × 20–30 sub-classes), specifying **decidable, quantitative criteria** for every risk
- Write the annotation guideline, including edge-case adjudication rules
- Organise public dataset download, format normalisation and class mapping
- Collect and screen real telecommunication scene imagery (target ≥ 500 images)
- Pre-label with Grounding DINO, correct manually, and produce TelecomSeed-v1
- Maintain DVC data version control, recording provenance and licence of every subset
- **Deputy role**: the Stage 0 risk scenario specification library (with B)

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Risk Taxonomy v1.0 | End W1 | TG1 |
| Annotation guideline | Mid W2 | — |
| TelecomSeed-v1 (≥ 300 annotated) | End W3 | **TG1** |
| Data split and isolation scheme | End W3 | — |
| Risk Taxonomy v2.0 (terrain/material refinement) | W10 | — |

**Why this role starts first**: the Risk Taxonomy is the head of the critical path. Annotation, generation and evaluation all depend on it. If A's W1 delivery is weak, everyone else reworks later.

---

#### Member B ｜ Generation Lead ★ CORE INNOVATION ★

**Responsibilities**
- Comparative selection of the base generative model (SDXL / SD3.5 / FLUX)
- LoRA fine-tuning to inject telecommunication construction visual characteristics
- Implement the four generation engines: T2I / ControlNet layout control / inpainting / background replacement
- Implement automatic annotation (layout-map conversion / mask inheritance / Grounding DINO + SAM fallback)
- Implement and calibrate the four quality gates (G1 semantic / G2 distribution / G3 annotation / G4 human)
- Bulk-generate the TelecomSynth dataset and produce the quality assessment report
- Own pipeline ablation experiments A1–A7

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Base model selection report | Mid W4 | — |
| LoRA fine-tuned model | End W4 | — |
| Four generation engines | End W5 | — |
| Four quality gates + threshold calibration | Mid W6 | — |
| TelecomSynth-v1 (≥ 3,000 images) + quality report | End W6 | **TG2** |
| Pipeline ablations A1–A7 | W14 | — |

**Risk note**: this is the most technically demanding role and the one most likely to slip. B should run a minimal end-to-end chain in W4 (T2I → 10 images → visual inspection) rather than waiting until all four engines are built before validating anything.

---

#### Member C ｜ Perception Lead — Workers

**Responsibilities**
- Workers branch: shared backbone with multiple heads (detection + pose + multi-label PPE)
- Behaviour branch: skeleton action recognition (YOLOv11-pose → ST-GCN++)
- **Execute the core comparison experiments E1 / E2 / E3** — the make-or-break experiments for the project
- Implement the synthetic/real mixed training strategy (ratio scheduling, loss weighting)
- Long-tail class experiment E6
- Model-side execution of robustness experiment E7

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Workers detection + PPE baseline (E1) | End W7 | — |
| E2 conventional augmentation control | Mid W8 | — |
| **E3 generative augmentation results** | End W9 | **TG3** |
| Complete multi-head implementation | W10 | — |
| Behaviour model (or D6 fallback) | W11 | — |
| E6 long-tail experiment | W14 | — |

**Risk note**: C's E3 experiment is the project's decision point. C should get the E1 baseline running and **frozen** by W7, so that every subsequent comparison uses the same baseline — a moving baseline makes the conclusions incomparable.

---

#### Member D ｜ Perception Lead — Scene

**Responsibilities**
- Machinery branch: detection + operating state + person–machine distance computation
- Materials branch: detection + stacking geometry rules (height/width ratio, boundary breach, passage obstruction)
- Terrain branch: semantic segmentation (level / potholed / waterlogged / trench / slope)
- Build the terrain segmentation subset using SAM 2 region proposals plus manual class assignment
- Work with A to define quantitative criteria for "poorly stored" materials and "uneven" terrain
- Cross-site generalisation experiment E9

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Machinery detection model | End W8 | — |
| Terrain segmentation subset (SAM 2 assisted) | End W9 | — |
| Materials state rules + model | End W10 | — |
| Terrain segmentation model | End W11 | — |
| E9 cross-site generalisation | W14 | — |

**Risk note**: of D's three dimensions, Terrain and Materials are both 🔴 — no public data and subjective class definitions. **If the project falls behind, downgrade path D8 cuts these two first.** D should confirm priorities with the leader by W7: Machinery is protected, Terrain/Materials are downgradable.

---

#### Member E ｜ Fusion & System Lead

**Responsibilities**
- Encode the safety rule base (≥ 15 decidable predicates, each citing OSHA / GB 26859 or similar)
- Implement entity graph construction (spatial relations among people, machines, materials, terrain)
- Implement three-level hierarchical fusion (entity graph → rule layer → learnable fusion)
- Organise expert risk-level annotation (200 images, 2–3 annotators, compute agreement Kappa)
- System integration: end-to-end pipeline, FastAPI backend, Gradio/React frontend
- Model export and acceleration (ONNX / TensorRT)
- Set up and maintain the experiment tracking platform (W&B / MLflow)

**Key deliverables**

| Deliverable | Due | Gate |
|------------|-----|------|
| Experiment tracking platform | End W2 | — |
| Safety rule base v1.0 (≥ 15 rules) | Mid W10 | — |
| Expert risk annotation set (200 images) | End W10 | — |
| Three-level fusion module + E8 | End W11 | **TG4** |
| Web demo system | End W13 | **TG5** |
| End-to-end performance optimisation | W14 | — |

**Risk note**: both of E's workstreams fall in the second half, so the early weeks look quiet. **E should stand up the experiment tracking platform in W2** (the whole team benefits) and start recruiting expert annotators by W8 — this is the task most often deferred until it is too late, leaving TG4 unmeasurable.

---

## 3. Team Leader

### 3.1 Leader Responsibilities

The leader is **not** the chief engineer but the project coordinator:

| Category | Responsibility |
|----------|---------------|
| **External** | Sole point of contact with the supervisor; convenes and chairs the weekly in-person meeting; prepares reporting material |
| **Schedule** | Maintains the kanban; checks milestones weekly; identifies and flags slippage early |
| **Decisions** | Chairs gate meetings TG1–TG5; organises assessment and voting on downgrade paths |
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

To be completed at the **first team meeting (M0, W1)**:

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
| Public dataset curation | I | **A/R** | I | C | C | I |
| Real telecom data collection | C | **A/R** | I | I | I | I |
| Seed data annotation | I | **A/R** | I | R | R | I |
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
| Core experiments E1/E2/E3 | C | I | C | **A/R** | I | C |
| Safety rule base encoding | C | C | I | C | C | **A/R** |
| Entity graph + three-level fusion | I | I | I | C | C | **A/R** |
| Expert risk annotation | C | C | I | I | I | **A/R** |
| System integration + web demo | I | I | I | C | C | **A/R** |
| Experiment tracking platform | I | C | C | C | C | **A/R** |
| Robustness experiment E7 | C | I | R | **A/R** | R | I |
| Chairing gates TG1–TG5 | **A/R** | C | C | C | C | C |
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
| M0 Setup | W1 | 8 | **12** | 6 | 6 | 6 | 8 |
| M1 Data | W2–W3 | 8 | **16** | 10 | 8 | 10 | 10 |
| M2 Generation | W4–W6 | 8 | 12 | **18** | 8 | 10 | 8 |
| M3 Perception | W7–W9 | 8 | 8 | 12 | **18** | **16** | 8 |
| M4 Fusion | W10–W11 | 8 | 8 | 8 | 12 | **14** | **18** |
| M5 Integration | W12–W13 | 8 | 6 | 6 | 10 | 10 | **18** |
| M6 Evaluation | W14–W15 | 10 | 8 | 12 | **14** | 12 | 12 |
| M7 Delivery | W16 | **14** | 10 | 10 | 10 | 10 | 10 |

\* The leader's hours are **coordination work**, added on top of their own technical role. Bold marks the phase's principal contributor.

**Peak-load notes**:
- **B peaks in W4–W6** — the entire generation pipeline compressed into three weeks; the tightest period of the project
- **C and D peak together in W7–W9**, just after B delivers the synthetic data, making a "data problem → rollback → perception waits" chain delay likely
- **E peaks in W10–W13** and is relatively light early on, so E should actively take on support tasks in the early phase

### 5.2 Early-phase Rebalancing

During W1–W3, A carries the heaviest load (taxonomy + guideline + collection) while C/D/E are relatively idle. Recommended:

- **C and D support annotation in W2–W3** (50–100 images each) while familiarising themselves with the data distribution — directly useful for later training and tuning
- **E stands up the experiment tracking platform in W2**, preparing the ground for everyone's experiments
- **Data collection is parallelisable manual work**: everyone should contribute photographs and collection, with A responsible for screening and standards

---

## 6. Inter-member Interface Contracts

Almost all integration rework traces back to interfaces agreed too late. The following must be **confirmed in writing by end of W2**; any change must be notified to all downstream members.

| ID | Upstream | Downstream | Contract | Due |
|----|----------|-----------|----------|-----|
| I1 | A | B, C, D | **Data format**: COCO JSON; class-ID mapping table; image naming convention | End W2 |
| I2 | A | All | **Risk Taxonomy**: class hierarchy, quantitative criterion per class, severity values | End W1 |
| I3 | A | B | **Spec library schema**: field definitions for `risk_scenarios.yaml` (see document 03, Stage 0) | End W3 |
| I4 | B | C, D | **Synthetic data delivery format**: identical to I1 + metadata JSON (seed/prompt/route/gate scores) | End W5 |
| I5 | C, D | E | **Perception output schema**: unified detection/segmentation/attribute JSON structure with confidence fields | End W6 |
| I6 | E | All | **Experiment logging convention**: W&B project name, run naming rules, mandatory metric list | End W2 |
| I7 | A | E | **Expert annotation format**: risk level values, annotator ID, timestamp | End W8 |

> **I5 is the interface most likely to cause problems.** The four perception branches emit different forms (boxes / masks / multi-labels / action classes), and E needs the unified schema by W6 to design the fusion module. C, D and E should hold a dedicated interface alignment meeting in W6.

---

## 7. Collaboration Mechanisms

### 7.1 Meeting Cadence

| Meeting | Frequency | Duration | Format | Chair | Output |
|---------|-----------|----------|--------|-------|--------|
| **Weekly stand-up** | Weekly | 60 min | ⚠️ **In person (hard project requirement)** | Leader | Minutes committed to the repo |
| Technical alignment | As needed | 30–60 min | In person preferred | Initiator | Decision record |
| **Gate meeting** | 5 (TG1–TG5) | 90 min | ⚠️ **In person + supervisor present** | Leader | Decision record + downgrade trigger status |
| Daily sync | Daily | Asynchronous | Chat / Issues | — | Blockers surfaced same day |

**Fixed weekly agenda**:
```
1. Review of last week against plan (10 min) — 2 minutes per person
2. This week's plan and declared dependencies (15 min) — state "I need X from Y by Z"
3. Blockers and requests for help (15 min)
4. Milestone and critical-path check (10 min) — chaired by the leader
5. Decisions and action items (10 min) — each action gets an owner and a due date
```

> ⚠️ **On the in-person requirement**: the brief states explicitly that `regular in-person meetings and discussions on campus are required` and that `absence and remote working on the project are unacceptable`. Fix the weekly meeting time and place at the first meeting, have everyone confirm they can attend, and record this in the minutes as a commitment.

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
| A (Data) | Taxonomy → Leader + E; annotation → split between C and D; collection → everyone | Reduced data scale; may trigger D1 |
| B (Generation) | Generation → A (already deputy); gates → E | **D2** (inpainting route only) |
| C (Perception-Workers) | Workers → D; behaviour recognition → dropped | **D6** (single-frame pose substitute) |
| D (Perception-Scene) | Machinery → C; Terrain/Materials → dropped | **D8** (reduce to two dimensions) |
| E (Fusion/System) | Fusion → Leader + C; system → simplified to scripts | **D4 + D5** |

> The purpose of this table is not to anticipate departures but to make clear **how irreplaceable each role is**. Losing B or E is the most costly, so those two modules most need a second person who can read the code — deliberately assign their PR reviews to one other member.

---

## 10. First Team Meeting Agenda (M0, W1)

Follow directly; approximately 90 minutes.

```
1. Read the project brief together (10 min)
   · Confirm: four risk dimensions, three technical pillars, mandatory in-person attendance

2. Read the documents together (20 min)
   · 00 Requirements §2 (four dimensions), §7 (three difficulties)
   · 01 Technical plan §1 (five-layer architecture), §5 (risk register)
   · 05 Roadmap §11 (one-page summary)

3. Role claiming (20 min)
   · Read out the five roles in §2
   · Each member states their preference and background
   · Negotiate assignment of A–E; resolve conflicts by draw or vote

4. Leader election (20 min)
   · Run Steps 1–5 of §3.3

5. Key decisions (15 min)
   □ Project duration: 12 weeks or 16?
   □ Scope: all four dimensions, or focus on Workers + Machinery? (the latter is strongly recommended)
   □ Available compute: GPU model and count?
   □ Telecommunication sub-scenarios: towers / optical cable / equipment rooms — which are in scope?

6. Administrative items (5 min)
   · Fix the weekly meeting time and place (in person)
   · Set up the chat group and kanban
   · Confirm GitHub repository access

【Within 24 hours after the meeting】
   · Leader publishes the minutes
   · Update §2.1 of this document with real names and the elected leader
   · Commit to the repository
```
