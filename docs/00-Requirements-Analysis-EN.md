# TelecomSafe — Project Requirements Analysis

> Full title: **A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects (TelecomSafe)**
> Document version: v1.0 ｜ Generated: 2026-08-18 ｜ Source: `project.txt`
> Chinese counterpart: [00-项目需求分析-CN.md](00-项目需求分析-CN.md)

---

## 1. What This Project Actually Is

This is a research project that applies **generative AI plus computer vision to a few-shot industrial safety detection problem**. The central tension is stated explicitly in the project brief:

> Deep-learning-based computer vision can identify construction risks efficiently, but performance is constrained by the **limited availability and diversity of labelled, sector-specific images** for the telecommunication industry.

TelecomSafe's answer: use generative AI to **synthesise training data** and close the data gap, then apply deep learning together with image processing and information fusion to perform **multi-dimensional risk appraisal**.

**One-sentence positioning**: an intelligent, multi-dimensional construction safety risk identification framework for the telecommunication sector, whose core innovation is generative data augmentation.

---

## 2. The Risks to Identify: Four Dimensions

The risk sources listed in the brief map precisely onto four detection targets, which also form the natural module decomposition of the system:

| # | Dimension | Risk described in the brief | Vision task form | Difficulty |
|---|-----------|----------------------------|-----------------|------------|
| 1 | **Terrain** | uneven terrain | Semantic segmentation / scene-state classification | Medium-high (subjective annotation, almost no public data) |
| 2 | **Machinery** | improperly operated machinery | Object detection + state/interaction reasoning | Medium (transferable public datasets exist) |
| 3 | **Materials** | poorly stored materials | Object detection + spatial relation / stacking stability | Medium-high ("improper" lacks an objective definition) |
| 4 | **Workers** | missing PPE + unsafe behaviour | Person detection + PPE attribute recognition + action recognition | Medium (PPE easy, behaviour hard) |

> ⚠️ **Note**: dimension 4 is in fact a **dual task** —
> - PPE detection is **static attribute recognition** (is a helmet / harness / hi-vis vest being worn); a single frame suffices.
> - Unsafe behaviour is **temporal action recognition** (climbing, over-reaching, unsafe posture); video input is required.
>
> The two have entirely different technical routes and data forms and **must be treated separately in the plan**. Failing to do so will become the project's largest hidden risk.

---

## 3. Three Technical Pillars (All Mandatory)

### 3.1 Generative AI — the project's principal innovation

- **Stated purpose in the brief**: `generative AI is introduced to address the scarcity of training data`
- **Not an embellishment but the reason the project exists**: reviewers will weight this most heavily, so a quantifiable demonstration of its contribution is required
- **Candidate technical routes**:
  - Text-to-image: Stable Diffusion / SDXL / FLUX for generating rare hazardous scenes
  - Controllable generation: ControlNet (edge / depth / pose maps constraining layout)
  - Local editing: inpainting (e.g. "erasing" a worker's helmet to synthesise negative samples, with bounding boxes reusable as-is)
  - Domain adaptation: LoRA / DreamBooth fine-tuning on a small set of real telecommunication construction images to inject sector-specific visual characteristics

### 3.2 Deep-learning-based Image Processing

- Detection / segmentation / classification backbones: YOLO family, RT-DETR, DINO, SAM, etc.
- Provides the **base perception** for all four dimensions

### 3.3 Information Fusion — the pillar most likely to be done superficially

- **Requirement in the brief**: `provide multiple dimensions to accurately appraise the potential risks`
- The goal is to fuse the heterogeneous outputs of four dimensions into **a single overall risk appraisal** (risk level / risk score / risk report)
- ❗ **A simple weighted sum will not do** — that does not constitute an academic contribution. A defensible fusion mechanism is required (see the technical plan document)

---

## 4. Where the Novelty Comes From

The brief states `Different from existing frameworks and software products`. Differentiation has two sources:

1. **Vertical-domain specificity**
   - Not generic site safety, but **specifically the telecommunication construction context**: base stations, tower climbing, optical-cable trenching, antenna installation, equipment-room cabling
   - Generic building-site datasets (SODA / MOCS / ACID) **cannot be transplanted directly**. This is both the difficulty and the project's foothold

2. **Novelty of the technical combination**
   - Generative AI for data completion **plus** multi-dimensional information fusion for appraisal; the combination is what constitutes a "novel framework"

**Performance requirement**: `high effectiveness and robustness`
- Effectiveness → quantified experiments are mandatory (mAP / F1 / Recall)
- Robustness → stability under varying illumination, weather, viewpoint and occlusion must be verified (a point many student projects omit)

---

## 5. Deliverables

The verb pair `develop and evaluate` implies two categories of deliverable:

| Category | Content | Note |
|----------|---------|------|
| **Develop** | A runnable **framework / system** | The word "framework" implies a complete pipeline, not merely model weights; an interactive demonstration interface is recommended |
| **Evaluate** | Rigorous evaluation experiments | **The core experiment**: an ablation with and without generated data, proving that generated data genuinely improves performance |

**Recommended mandatory experiment list**:

1. Baseline: trained on real data only
2. + conventional augmentation (flip / crop / Mosaic)
3. + generative augmentation (this project's method)
4. Trained on synthetic data only → tested on real data (measures the domain gap)
5. Curve over varying synthetic-to-real ratios
6. Robustness testing: low light, rain and fog, motion blur, small targets
7. Fusion module ablation: single dimension vs. multi-dimensional fusion

---

## 6. Non-technical Requirements (Firmly Worded — Take Seriously)

The second paragraph of the brief is unusually explicit:

- ⚠️ **On-campus attendance is mandatory**: `regular in-person meetings and discussions on campus are required`; the brief states plainly that `absence and remote working on the project are unacceptable`
- 👥 **Team collaboration**: `This project is of a complex nature and requires close collaboration among team members`
  - This indicates a **multi-person project**; a suggested division of labour follows
- ⏰ **High time commitment**: `substantial time commitment`, requiring students who are `very self-motivated` and `willing to learn new things`

**Suggested division of labour (3–4 people)**:

| Role | Responsibilities |
|------|-----------------|
| A ｜ Data & Generation | Public dataset curation and annotation, openly licensed image screening, generative model fine-tuning, synthetic data pipeline, quality filtering |
| B ｜ Perception Models | Detection / segmentation / PPE model training and tuning, robustness experiments |
| C ｜ Behaviour & Fusion | Action recognition, safety rule base, information fusion and risk scoring module |
| D ｜ System & Evaluation | System integration, visualisation interface, experiment management, report and paper writing |

---

## 7. Risk Identification: The Three Hardest Problems

### 🔴 Difficulty 1: Acquiring real telecommunication construction data

Even obtaining real benchmark data is hard, and the generative model itself needs seed material for fine-tuning.

- **Mitigation (revised in v2.0)**: ❌ **Field collection has been ruled out** (safety risk and cost too high; confirmed with the supervisor). Replaced by a four-tier public-source strategy:
  T1 academic public datasets (SODA/CHV/SHEL5K etc., transfer base) → T2 community dataset platforms (Roboflow Universe telecom tower and safety harness sets) → T3 curation of openly licensed repositories (Wikimedia Commons / Openverse, forming TelecomSeed and the isolated TelecomEval test set) → T4 generative synthesis
- **Read it the other way**: the fact that the team cannot bear the cost of collection **demonstrates the project's founding premise first-hand** — telecommunication-specific data really is hard to obtain. Generative AI is thereby elevated from a convenience to the only viable route, which is a strong argument for the report

### 🔴 Difficulty 2: Quality and trustworthiness of generated data

If generated images deviate substantially from the real distribution, they will **degrade** model performance (negative transfer).

- **Mitigation**: build automatic filtering gates (CLIP semantic consistency + FID distributional distance + detector-confidence filtering + human spot-check)

### 🔴 Difficulty 3: Depth of the information fusion design

The four dimensions produce heterogeneous outputs (segmentation maps / bounding boxes / attribute labels / action classes). How should these be fused into a convincing risk appraisal?

- **Mitigation**: adopt a layered "rule constraints + learnable weights" fusion, aligned to real safety regulations (OSHA, GB 26859, etc.), so that the score is both interpretable and grounded in compliance

---

## 8. Companion Documents

| Document | Content |
|----------|---------|
| `01-Technical-Plan-and-Milestones-EN.md` | System architecture, technology selection, 12/16-week milestones and delivery checkpoints |
| `02-Datasets-and-Pretrained-Models-EN.md` | Public dataset inventory, pretrained model comparison, licensing notes |
| `03-Generative-Augmentation-Pipeline-EN.md` | End-to-end generation pipeline design, prompting strategy, quality gates, experiment design |
| `04-Literature-Survey-EN.md` | Literature survey and references |
