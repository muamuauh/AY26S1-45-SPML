# Generative Data Augmentation Pipeline — Design

> Document version: v1.0 ｜ Generated: 2026-08-18
> Chinese counterpart: [03-生成式数据增广Pipeline设计-CN.md](03-生成式数据增广Pipeline设计-CN.md)
> This is TelecomSafe's **core innovation module**, corresponding to `generative AI is introduced to address the scarcity of training data` in the project brief.

---

## 1. Design Principles

Before writing any code, establish four principles. They determine whether this pipeline constitutes an academic contribution or merely "calling an API to produce a pile of images."

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Annotation must come for free** | If synthetic images still require manual annotation, the point of addressing data scarcity is lost. Every generation route must be designed so that generation *is* annotation |
| 2 | **Quality must be filterable** | Generative models hallucinate (six-fingered workers, floating helmets, structurally impossible towers). **Automatic gates are mandatory**; discarding 50% is preferable to polluting the training set |
| 3 | **Prioritise the long tail** | The value of synthetic data lies in **scenes that cannot be photographed in reality** (a worker leaning out from a tower without a harness), not in duplicating common samples. This is also where gains are largest |
| 4 | **The real test set must stay uncontaminated** | The test set uses real imagery only, and those images must never participate in generative fine-tuning, or the experimental conclusions become invalid |

---

## 2. Pipeline Overview

```
                        ┌─────────────────────────┐
                        │  Stage 0: Risk Scenario  │
                        │  Specification Library   │
                        │  (risk × scene × cond.)  │
                        └───────────┬─────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
    │ Stage 1        │  │ Stage 1'       │  │ Stage 1''      │
    │ Domain adapt.  │  │ Condition maps │  │ Prompt synth.  │
    │ LoRA fine-tune │  │ Seg/Pose/Depth │  │ Prompt Builder │
    └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
            └───────────────────┼───────────────────┘
                                ▼
              ┌──────────────────────────────────────┐
              │  Stage 2: Four generation engines     │
              │  ① T2I new scenes  ② ControlNet layout│
              │  ③ Inpainting edit ④ Background swap  │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │  Stage 3: Automatic annotation        │
              │  Layout→GT / mask inheritance /       │
              │  GDINO+SAM fallback                   │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │  Stage 4: Four quality gates ★KEY★    │
              │  G1 semantic → G2 distribution →      │
              │  G3 annotation → G4 human spot-check  │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │  Stage 5: Ratio & curriculum mixing   │
              │  Real:Synth scheduling + loss weights │
              └──────────────────────────────────────┘
```

---

## 3. Stage 0 — Risk Scenario Specification Library

The stage most often skipped, and the most important. Do not "generate whatever comes to mind." Build a **structured specification table** first, so that generation becomes enumerable, coverable and countable.

### Specification Dimensions

```yaml
risk_scenario:
  id: TS-W-003
  dimension: workers            # terrain | machinery | materials | workers
  risk_type: missing_fall_arrest
  description: "Worker at height on a lattice tower without a fall-arrest harness"
  severity: critical

  scene_context:                # scene context (determines background)
    - cell_tower_lattice
    - monopole_tower
    - rooftop_antenna
    - cable_trench
    - equipment_room

  environment:                  # environment variables (determine robustness coverage)
    weather:  [sunny, overcast, rain, fog, snow]
    lighting: [daylight, dusk, night_floodlight, backlight]
    season:   [summer, winter]

  viewpoint:
    - ground_upward
    - drone_level
    - drone_top_down
    - tower_mounted_camera
    - handheld_close

  target_count: 120             # number of images to generate for this scenario
```

### Coverage Matrix

| Dimension | Suggested sub-classes | Notes |
|-----------|----------------------|-------|
| Terrain | 5–6 | Level / potholed / waterlogged / open trench / sloped / loose backfill |
| Machinery | 6–8 | Excavator / crane / drilling rig / cable winch / generator / aerial work platform + violation states |
| Materials | 5–6 | Cable drums / steel / tower sections / concrete units / toolboxes + improper storage states |
| Workers | 8–10 | No helmet / no hi-vis / no harness / no gloves / unsafe climbing / over-reaching / lone work at height / unsafe positioning |

> **Target: 25–30 risk scenarios × environment combinations.** Generate 100–150 images per scenario — a figure with empirical support: Lee et al. (2025) found the optimal augmentation size to lie in the 100–150 images-per-category range.

---

## 4. Stage 1 — Domain Adaptation (LoRA Fine-tuning)

### Objective

Teach the base model to "recognise" the visual features of telecommunication construction — lattice towers, antenna mounting poles, feeder cables, cable drums, equipment cabinets, climbing ladders — all of which generic models typically render very poorly.

### Suggested Configuration

```python
# Key LoRA fine-tuning hyperparameters
base_model      = "stabilityai/stable-diffusion-xl-base-1.0"
lora_rank       = 32              # 16–32; use the lower end with less data
lora_alpha      = 32
learning_rate   = 1e-4
train_steps     = 1500-3000       # ~2000 steps for 500 images
resolution      = 1024
batch_size      = 1
grad_accum      = 4
mixed_precision = "fp16"
# Objective: inject domain appearance without overfitting to specific training images
```

### Data Preparation Notes

| Point | Approach |
|-------|----------|
| Data source | **Only real telecommunication images outside the test set** (200–500 images) |
| Caption generation | Auto-caption with BLIP-2 or Qwen2-VL, then correct key terminology by hand |
| Trigger word | Set a rare trigger token (e.g. `tlcmsite`) and include it at inference to activate the domain style |
| Overfitting monitoring | Generate a sample batch every 500 steps and check visually whether the model has begun reproducing training images |

### Layered LoRA Strategy (Advanced)

Training 2–3 independent LoRAs and composing them at inference gives finer control than one large LoRA:

- `lora_scene`: overall telecommunication site style (towers, equipment rooms, trenches)
- `lora_ppe`: PPE appearance detail (helmets, hi-vis vests, harnesses)
- `lora_machinery`: construction machinery

Weight them per scenario at inference: `scene(0.8) + ppe(0.6)`.

---

## 5. Stage 2 — Four Generation Engines

### Route ① Text-to-Image (New Scenes)

**Purpose**: generate rare hazardous scenes entirely absent from the real world
**Annotation cost**: requires the Stage 3 fallback annotator
**Suggested share of output**: 20%

**Structured prompt template** (more stable than free-form writing, and enables ablation studies):

```
[TRIGGER] [VIEWPOINT], [SUBJECT + STATE], [CONTEXT], [ENVIRONMENT], [STYLE], [QUALITY]

Example:
tlcmsite, ground-level upward view, a construction worker climbing a lattice
telecommunication tower without a fall-arrest harness, wearing an orange
high-visibility vest but no safety helmet, steel lattice structure with antennas,
overcast sky, light rain, photorealistic documentary photograph,
sharp focus, natural lighting, 35mm lens

Negative: cartoon, illustration, 3d render, deformed hands, extra limbs,
floating objects, distorted metal structure, watermark, text, blurry
```

**Three prompting strategies** (worth running as a comparison — a ready-made ablation):

| Strategy | Description | Expected effect |
|----------|------------|----------------|
| Zero-shot | A single natural-language sentence | Baseline; high diversity, poor controllability |
| Structured | The template above | Markedly better consistency |
| **Image-guided structured** | Structured template + IP-Adapter referencing real images | **Best** (supported by existing findings) |

### Route ② ControlNet Layout Control 🌟 Strongly Recommended

**Purpose**: precise control of object position and structure
**Annotation cost**: **zero** (the layout map *is* the annotation)
**Suggested share of output**: 40%

```
Workflow:
  1. Extract condition maps from real images (Canny / Depth / Seg / OpenPose),
     or generate a semantic layout map programmatically (random box placement → fill colours)
  2. Semantic layout map → ControlNet-Seg → photorealistic image
  3. Each colour region in the layout map = one instance mask = annotation ground truth
  4. Derive bounding boxes from masks → COCO-format annotation
```

**Key techniques**:

- **Pose control for unsafe behaviour**: specify keypoints for "climbing", "over-reaching", "crouching" via an OpenPose skeleton map and generate the corresponding image. The skeleton is itself the pose annotation and can be fed directly to ST-GCN training
- **Depth control for terrain**: feed a programmatically generated depth map (with potholes and trench undulation) to ControlNet-Depth to obtain images with terrain segmentation ground truth
- **Composed control**: run several ControlNets in parallel — Seg (layout) + Depth (terrain) + Pose (people). Stronger conditioning yields more accurate annotation

### Route ③ Inpainting Local Editing 🌟 Best Value

**Purpose**: produce new samples through **minimal edits** to real images
**Annotation cost**: **near zero** (annotations are inherited)
**Suggested share of output**: 30%

**Four high-value editing operations**:

| Operation | Approach | Resulting sample |
|-----------|----------|-----------------|
| **PPE removal** | Segment the helmet region with SAM → inpaint as a bare head | Positive sample for "no helmet"; person box unchanged |
| **PPE addition / recolouring** | Inpaint a differently-coloured helmet in the head region | Increases PPE colour diversity |
| **Object injection** | Inpaint an excavator at a specified location | New machinery instance; box given by the mask |
| **State transformation** | Inpaint a neatly stacked material pile into a leaning, disordered one | Improper material storage sample |

```python
# PPE removal logic
mask = SAM.segment(image, point_prompt=helmet_center)   # helmet mask
mask = dilate(mask, kernel=5)                            # slight dilation to avoid edge residue
new_image = sd_inpaint(
    image, mask,
    prompt="a construction worker's bare head with short dark hair, "
           "no helmet, natural skin, photorealistic",
    strength=0.95
)
# Annotation change: person box unchanged; helmet instance deleted; label: no_helmet
```

> **Why this route deserves the most investment**: it preserves the real image's background, illumination and noise distribution, minimising the domain gap, while precisely producing the hardest-to-obtain **violation samples**. Photographs of workers in violation are both rare and legally difficult to capture — the generative approach solves the data problem and the ethical problem at once, which is a powerful argument in the paper.

### Route ④ Background Replacement / Environment Transfer

**Purpose**: robustness data (rain, fog, night and backlit variants of the same scene)
**Suggested share of output**: 10%

- Separate the foreground (people/machinery) with SAM → inpaint a replacement background
- Or apply low-strength img2img (strength 0.3–0.5) with environment prompts for global style transfer
- Annotations are entirely unchanged. **This is the most economical way to build the E7 robustness test set**

---

## 6. Stage 3 — Automatic Annotation

| Generation route | Annotation source | Reliability |
|-----------------|------------------|------------|
| ② ControlNet-Seg | Direct conversion of the input layout map | ⭐⭐⭐⭐⭐ Exact |
| ② ControlNet-Pose | The input skeleton is the keypoint GT | ⭐⭐⭐⭐⭐ Exact |
| ③ Inpainting | Inherited from the source annotation + mask correction | ⭐⭐⭐⭐⭐ Very good |
| ④ Background replacement | Source annotation unchanged | ⭐⭐⭐⭐⭐ Exact |
| ① Text-to-image | **Requires an automatic annotator** | ⭐⭐⭐ Needs filtering |

**Automatic annotation scheme for the T2I route**:

```
Grounding DINO (text prompt = the class list from that scenario's specification)
        ↓  bounding boxes + confidences
     Confidence threshold filtering (> 0.35)
        ↓
     SAM 2 (box prompt) → fine masks
        ↓
     Consistency check against the generation prompt:
       prompt says "no helmet" but a helmet is detected → discard the image
        ↓
     Emit COCO annotations
```

> **The consistency check is the critical step.** Generative models frequently disobey — ask for no helmet and one appears anyway. Omitting this check introduces substantial label noise and will cause the E3 experiment to fail outright.

---

## 7. Stage 4 — Four Quality Gates ★ The Project Succeeds or Fails Here ★

```
Generated image
   │
   ├─ G1 Semantic consistency gate ─────────────────────────
   │    CLIP-Score(image, prompt) > 0.28
   │    VLM semantic review: ask Qwen2.5-VL "is the worker wearing a helmet?"
   │    → discard if inconsistent with the specification label
   │    Expected rejection rate: 15–25%
   │
   ├─ G2 Distributional consistency gate ───────────────────
   │    Per image: nearest-neighbour feature distance to the real set < threshold
   │    Per batch: FID(synth_set, real_set) < 50 ; KID < 0.05
   │    → if exceeded, roll back and adjust prompts / LoRA strength
   │    Expected rejection rate: 10–15%
   │
   ├─ G3 Annotation reliability gate ───────────────────────
   │    Run a real-data-trained baseline detector on the synthetic image
   │    · > 70% of detections match the auto-annotation at IoU > 0.5 → pass
   │    · Nothing detected at all → image is degenerate, discard
   │    · Many detections absent from the annotation → annotation is incomplete, discard
   │    Expected rejection rate: 10–20%
   │
   ├─ G4 Human spot-check gate ─────────────────────────────
   │    Randomly sample 5% for human rating (realism 1–5, annotation correct Y/N)
   │    Mean realism < 3.0 → reject the whole batch
   │    Annotation correctness < 90% → reject the whole batch
   │    ≥3 raters; report inter-rater Kappa
   │
   ▼
Final synthetic dataset (expected overall retention 50–65%)
```

**Important caveat**: G3 carries a subtle circularity risk — filtering data with a baseline detector and then training a detector on the filtered data may retain only samples the model already handles, weakening the augmentation effect. **Mitigation**: use G3 only to remove **extreme failures** (nothing detected / large numbers of hallucinated objects), with loose thresholds; do not use it for fine-grained selection. This discussion is itself worth including in the paper's Limitations.

---

## 8. Stage 5 — Mixed Training Strategy

### 8.1 Ratio Scheduling

| Strategy | Description | Recommendation |
|----------|------------|---------------|
| Fixed ratio | Real : Synth = 1 : 0.5 / 1 : 1 / 1 : 2 | ⭐⭐⭐⭐ Simple; use for the E5 sweep |
| **Curriculum** | High synthetic proportion early (feature learning) → decreasing to pure real late (distribution alignment) | ⭐⭐⭐⭐⭐ **Recommended**; usually optimal |
| Class-adaptive | Higher synthetic proportion for long-tail classes, lower for common ones | ⭐⭐⭐⭐⭐ **Consistent with Principle 3; strongly recommended** |
| Two-stage | Stage 1: pretrain on synthetic; Stage 2: fine-tune on real | ⭐⭐⭐⭐ Robust and easy to implement |

**Recommended combination: class-adaptive ratios + two-stage training**

```python
# Class-adaptive synthetic ratio
for cls in classes:
    n_real = count_real(cls)
    # Supply more to long-tail classes, but cap it so synthetic data does not dominate
    n_synth = min(max(0, TARGET_PER_CLASS - n_real), 3 * n_real + 100)
```

### 8.2 Loss Weighting

Give synthetic samples a slightly lower loss weight to reduce the impact of label noise:

```python
loss = loss_real + lambda_synth * loss_synth     # lambda_synth ≈ 0.7–0.9
```

**Confidence weighting** is also possible: samples with higher Stage 4 CLIP-Scores receive greater weight.

### 8.3 Validation Discipline (Strictly Enforced)

```
train:  real data + synthetic data
val:    real data only          ← used for early stopping and hyperparameter selection
test:   real data only, strictly isolated ← used exactly once, at final evaluation
```

⚠️ **Synthetic data must never enter val or test.** This is the easiest and the most fatal experimental error to make.

---

## 9. Pipeline Ablation Design (A Major Part of the Paper)

| Ablation | Comparison | Question answered |
|----------|-----------|------------------|
| A1 | Without LoRA vs with LoRA | Is domain adaptation necessary? |
| A2 | Zero-shot vs structured vs image-guided prompting | Effect of prompting strategy |
| A3 | Single route vs four-route mixture | Value of generation-route diversity |
| A4 | No gates vs G1 vs G1+G2 vs all gates | **Contribution of the quality gates (important)** |
| A5 | Fixed ratio vs class-adaptive | Effect of ratio strategy |
| A6 | Base models (SDXL / SD3.5 / FLUX) | Effect of generative model choice |
| A7 | Synthetic data volume (500 / 1k / 3k / 5k / 10k) | Marginal-return curve; locate the inflection point |

> A4 usually produces the most striking result: **unfiltered synthetic data often degrades performance**, which reverses to improvement once the gates are applied. That reversal is the strongest available evidence for the necessity of quality control.

---

## 10. Engineering Notes

### Directory Structure

```
telecomsafe/
├── data/
│   ├── real/              # real data (DVC-managed)
│   │   ├── seed/          # for LoRA fine-tuning
│   │   ├── train/
│   │   ├── val/
│   │   └── test/          # 🔒 strictly isolated
│   └── synth/
│       ├── raw/           # raw generation output
│       ├── filtered/      # passed the gates
│       └── rejected/      # rejected samples (retain for analysis and paper figures)
├── specs/
│   └── risk_scenarios.yaml    # Stage 0 specification library
├── gen/
│   ├── lora_train.py
│   ├── prompt_builder.py
│   ├── engines/           # t2i / controlnet / inpaint / bg_replace
│   ├── auto_label.py
│   └── gates/             # g1_semantic / g2_distribution / g3_detector / g4_human
├── perception/
├── fusion/
├── eval/
└── configs/
```

### Generation Throughput Estimates

| Configuration | Per image | For 3,000 images |
|--------------|----------|-----------------|
| SDXL 30 steps @1024 (RTX 4090) | ~6–8 s | ~6 hours |
| SDXL-Turbo 4 steps @1024 | ~1 s | ~1 hour |
| + ControlNet | ×1.3–1.5 | Proportionally more |
| + gate filtering (CLIP/FID/detector) | ~0.3 s per image | ~15 minutes |

> Conclusion: **use SDXL-Turbo for bulk generation and full SDXL for final output**. Three thousand synthetic images can be produced overnight on a single 4090 — compute is not the bottleneck. **The bottlenecks are specification-library design and gate calibration.**

### Reproducibility Checklist

- Fix random seeds and record `(seed, prompt, control_image_hash, lora_weights)` for every image
- Store per-image metadata as a sidecar JSON for traceability and the paper appendix
- Keep generation configurations in Git and the data in DVC

---

## 11. Common Failure Modes and Remedies

| Failure mode | Symptom | Remedy |
|-------------|---------|--------|
| Structural hallucination | Disordered tower structure; broken, floating steelwork | Lock structure with ControlNet-Canny; add `distorted metal structure` to the negative prompt |
| Human deformity | Extra fingers, extra limbs | Negative prompts; constrain with OpenPose; focus G4 spot-checks here |
| Prompt disobedience | "No helmet" requested but a helmet is generated | Raise CFG scale (7–9); switch to the inpainting route to force removal; intercept at the G1 semantic check |
| Mode collapse | Generated images highly similar; insufficient diversity | Increase prompt randomisation; lower LoRA weight; vary seeds and environment conditions |
| Excessive domain gap | E4 (synthetic-only training) collapses | Strengthen IP-Adapter referencing; increase the inpainting route's share; incorporate real backgrounds |
| Label noise | E3 falls rather than rises | Check G3 and the consistency check; lower `lambda_synth`; reduce the synthetic proportion |
| Overfitting to LoRA data | Synthetic images closely resemble the seed images | Reduce training steps; lower rank; check nearest-neighbour distances |

---

## 12. Milestone Mapping

This document corresponds to **M2 (W4–W6)** in `01-Technical-Plan-and-Milestones-EN.md`, with a suggested internal breakdown:

| Week | Task |
|------|------|
| W4 first half | Finalise the Stage 0 specification library (25–30 scenarios) + base model selection trials |
| W4 second half | Stage 1 LoRA fine-tuning + visual validation |
| W5 first half | Implement the Stage 2 engines (prioritise ② ControlNet and ③ Inpainting) |
| W5 second half | Stage 3 automatic annotation + consistency checking |
| W6 first half | Implement the Stage 4 gates and calibrate thresholds |
| W6 second half | Bulk-generate 3,000+ images + quality report + **decide whether to proceed to M3** |
