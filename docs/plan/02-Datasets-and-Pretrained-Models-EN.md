# Public Datasets and Pretrained Models — Survey

> Document version: **v2.1** ｜ Generated: 2026-08-18 ｜ Revised: 2026-09-28
> Chinese counterpart: [02-数据集与预训练模型调研-CN.md](02-数据集与预训练模型调研-CN.md)
> Purpose: selection basis for TelecomSafe phase 1 (baseline perception) and phase 2 (generative augmentation); public data curation (M1) has been completed offline

---

## 📌 Data Strategy: Public Sources Only, Zero Field Collection

Confirmed with the supervisor: the safety risk and cost of on-site collection are too high, so **this project performs no field data collection whatsoever**. All real data comes from publicly available datasets and openly licensed image repositories (T1–T3, **curated offline**), which phase 2 then expands with generative AI (T4).

The contribution statement is accordingly: "Under a strict **no-field-collection** constraint, we construct a usable data benchmark and recognition framework for telecommunication construction safety, by curating public sources and generative synthesis." It is highly reproducible (others need no site access to replicate it) and internally consistent with the very problem the project addresses.

---

## ⚠️ Headline Conclusion

**No public dataset dedicated to safety detection in telecommunication construction currently exists.**

This is both the project's central difficulty and its justification — precisely the `limited availability and diversity of labelled, sector-specific images` named in the project brief.

Under the **no-field-collection** constraint, the data strategy becomes four-tiered:

```
T1  Academic public datasets (transfer base, large volume, high annotation quality)
    SODA / MOCS / ACID / CHV / SHEL5K / SHWD / Pictor-v3
        ↓
T2  Community dataset platforms (telecom and work-at-height specifics)
    Roboflow Universe / Kaggle — small dedicated sets: telecom tower, safety harness, etc.
        ↓
T3  Openly licensed image repositories (★ the source of sector specificity ★)
    Wikimedia Commons / Openverse / Flickr CC — manual screening + team annotation
    → forms TelecomSeed (LoRA fine-tuning seeds) and TelecomEval (isolated test set)
        ↓
T4  Generatively synthesised data (this project's innovation, closing the long tail)
    → TelecomSynth
```

### Test Set Discipline (The One Non-Negotiable Rule)

**The TelecomEval test set must satisfy three conditions**:

1. 100% **real imagery** (no synthetic data whatsoever)
2. As close as possible to telecommunication construction scenes (from T2/T3)
3. **Never used in LoRA fine-tuning; never used to build generation conditions**

> ⚠️ This rule matters **more**, not less, now that field collection is cancelled. If T1's generic construction data serves as both training and test data, the "sector-specific" conclusion loses all support. The test set must be carved out of T2/T3 separately and frozen, targeting **150–300 images**.

---

## 1. Generic Construction Safety Datasets

### 1.1 Comprehensive Scene Detection

| Dataset | Scale | Classes | Characteristics | Value to this project |
|---------|-------|---------|----------------|---------------------|
| **SODA** (Site Object Detection dAtaset) | 19,846 images / 286,201 objects | 15 classes across worker / material / machine / layout groups | Multiple viewpoints (long shot 42.8%, close shot 34.7%, crane-hook monitor 15.5%, UAV 7.0%); YOLOv3/v4 baseline mAP 81.47% | ⭐⭐⭐⭐⭐ **Primary transfer base.** Its class grouping aligns closely with this project's four dimensions |
| **MOCS** (Moving Objects in Construction Sites) | 41,668 images | 13 classes, **pixel-level** annotation | Largest available; includes low-altitude UAV views; no top-down views | ⭐⭐⭐⭐ Suits the Machinery branch and instance-segmentation pretraining |
| **ACID** (Alberta Construction Image Dataset) | 10,000 images | 10 machinery classes | Ground-level viewpoints, machinery-focused | ⭐⭐⭐⭐ Dedicated to the Machinery branch |
| **AIDCON** | Aerial imagery | Construction machinery | **UAV-specific benchmark** | ⭐⭐⭐ Essential if UAV input is pursued |

> SODA paper: Duan, R., Deng, H., Tian, M., Deng, Y., Lin, J. (2022). *SODA: A large-scale open site object detection dataset for deep learning in construction*. Automation in Construction. arXiv:2202.09554

### 1.2 PPE / Safety Helmet

| Dataset | Scale | Classes | Characteristics | Value |
|---------|-------|---------|----------------|-------|
| **CHV** (Color Helmet and Vest) | 1,330 images | Multi-class PPE (helmet colour + hi-vis vest) | Real site backgrounds; varied gestures, angles and distances; publicly available | ⭐⭐⭐⭐⭐ Best starting point for the Workers branch |
| **SHEL5K** | 5,000 images, extended annotation | 6 classes (head / helmeted head / unhelmeted head / person / helmet / face) | Enhanced extension of the Safety Helmet Detection dataset; high annotation quality | ⭐⭐⭐⭐⭐ Most completely annotated PPE set |
| **SHWD** (Safety Helmet Wearing Dataset) | ~7,581 images | 2 classes (hat / person) | The most widely used benchmark in the Chinese-language community | ⭐⭐⭐⭐ Plentiful and easy to obtain; few classes |
| **Pictor-v3** | ~1,500 images | Worker / hat / vest combination states | Includes crowdsourced and web imagery | ⭐⭐⭐ Its combination-state annotation scheme is worth adopting |
| **Large-scale safety clothing datasets** | Tens of thousands | Safety clothing + helmets | Complex realistic scenes | ⭐⭐⭐ Supplementary diversity |

### 1.3 Unsafe Behaviour / Video Action

| Resource | Description | Value |
|----------|------------|-------|
| **Construction Action Recognition** (GitHub: S1mpleyang) | Unsafe-action video dataset and code accompanying an *Automation in Construction* paper | ⭐⭐⭐⭐⭐ The **only directly usable public resource** for the behaviour branch; acquire first |
| **CMAR / construction worker action datasets** | Construction action classification | ⭐⭐⭐ |
| **NTU RGB+D 60/120** | Generic human action skeleton dataset | ⭐⭐⭐⭐ ST-GCN pretraining base; transfers well |
| **Kinetics-400/700** | Generic video action | ⭐⭐⭐⭐ Source of pretrained weights for VideoMAE and similar models |

> Reference: Yang, M., Wu, C., Guo, Y., Jiang, R., Zhou, F., Zhang, J., Yang, Z. (2023). *Transformer-based deep learning model and video dataset for unsafe action identification in construction projects*. Automation in Construction, 146, 104703.

### 1.4 Terrain / Ground Condition

**⚠️ No directly usable public dataset exists.** This is the most data-starved of the four dimensions.

**Viable alternatives**:

| Route | Approach | Cost |
|-------|----------|------|
| A. Re-annotate SODA/MOCS | Add a 5-class ground-region segmentation layer to existing images | Medium (300–500 images suffice to train a lightweight segmentation head) |
| B. SAM 2 auto-segmentation + human class assignment | Use SAM 2 to propose ground regions; humans only assign classes | **Low (recommended)** — saves roughly 70% of annotation time |
| C. Transfer from generic scene segmentation | ADE20K / Cityscapes pretraining → fine-tune | Low, but class semantics do not match |
| D. Generative synthesis | ControlNet-Depth to generate potholed / trenched / waterlogged ground | Medium — and precisely the capability this project sets out to demonstrate |

> **Recommended: combine B and D.** B supplies the real test set; D supplies training data at scale. Together they form an elegant case study of generative augmentation's effectiveness.

### 1.5 Material Storage

**Also without a dedicated public dataset.** SODA's material group (rebar, timber, brick, etc.) is the closest starting point, but "improper storage" is a **state judgement** that must be defined and annotated in-house.

**Recommended: define quantifiable criteria** to avoid subjective annotation disputes:

- Stack height / base width ratio above a threshold → toppling risk
- Encroachment beyond a demarcated zone (requires site boundary annotation)
- Obstruction of passageways or escape routes
- Presence or absence of strapping/securing

---

### 1.6 T2 — Community Dataset Platforms

Beyond academic datasets, Roboflow Universe and Kaggle host many community-contributed sets. They are typically smaller with variable annotation quality, but **highly targeted by class** and exportable directly to YOLO/COCO format.

| Resource | Scale | Content | Value to this project |
|----------|-------|---------|---------------------|
| **Telecom Tower Object Detection** (Roboflow Universe) | ~128 images | Telecommunication tower detection | ⭐⭐⭐⭐ **One of the few directly telecom resources.** Small, but usable as a telecom appearance anchor for LoRA and as part of TelecomEval |
| **Construction Site Safety Image Dataset** (Kaggle / Roboflow, YOLOv8 format) | Thousands | 10 classes: Hardhat / **NO-Hardhat** / Safety Vest / **NO-Safety Vest** / Mask / NO-Mask / Person / Safety Cone / machinery / vehicle | ⭐⭐⭐⭐⭐ **Includes NO-* negative classes** — exactly the violation samples this project needs, saving the work of defining negatives |
| **Safety Harness datasets** (Roboflow Universe, several) | Hundreds to thousands | Safety harness / lanyard detection | ⭐⭐⭐⭐⭐ **The key PPE for work at height**, highly relevant to tower climbing; publicly available and previously overlooked |
| Roboflow Universe searches such as `class:safety` | Numerous | Assorted site safety objects | ⭐⭐⭐ Supplement scarce classes |

> **Cautions**:
> - Community annotation quality **must be spot-checked** (randomly verify 50 images per dataset); where it fails, take the images only and re-annotate
> - Confirm licence terms per dataset (Roboflow Universe is often CC BY 4.0, but not always)
> - Class naming is inconsistent and must be folded into the **class mapping table** owned by Member A

### 1.7 T3 — Curating Openly Licensed Image Repositories (★ Core Source of Sector Specificity ★)

With field collection cancelled, this is **the only route to real telecommunication construction imagery**, and the principal source for the TelecomEval test set.

| Source | Note | Entry point |
|--------|------|------------|
| **Wikimedia Commons** | Dedicated categories; all images freely licensed with complete metadata | `Category:Communications towers`, `Category:Construction workers`, `Category:Telecommunications infrastructure` |
| **Openverse** | Aggregates Flickr, Wikimedia and more; indexes 700M+ openly licensed images, **filterable by licence** | wordpress.org/openverse |
| **Flickr (CC filter)** | High photographic quality, rich in engineering and construction imagery | Advanced search → filter by CC licence |
| Operator / tower company press releases and annual reports | Often contain real construction photographs, but **usually all rights reserved** — usable only for observing visual style, never for inclusion in the dataset | — |

**Suggested search terms**:
```
cell tower technician / tower climber / antenna installation
telecommunication mast construction / fiber optic cable laying
base station installation / rooftop antenna work
```

**Curation workflow (completed as below)**:

```
1. Search Openverse / Wikimedia with the terms above, filtering by licence
   (CC0 / CC BY / CC BY-SA / Public Domain)
2. Screen manually: discard diagrams, renders, logos and empty scenes
3. Record source URL, licence type and author attribution per image
   → licence_manifest.csv (mandatory for compliance)
4. Pre-label with Grounding DINO → correct manually in CVAT
5. Split: TelecomEval (150–300 images, frozen) ｜ TelecomSeed (remainder, for LoRA)
```

> ⚠️ **Compliance requirement**: CC BY and CC BY-SA require **attribution**. Author and licence must be recorded per image, and `licence_manifest.csv` must accompany the report and any data release. This is a hard obligation of using openly licensed imagery and cannot be skipped.

> **Realistic expectation**: T3 will yield a limited number of telecommunication construction images (optimistically 200–500, weighted towards tower exteriors with few close-ups of workers). **That limitation is exactly what generative augmentation exists to address**, and should be stated plainly in the report.

---

## 2. Generative Model Selection

### 2.1 Base Text-to-Image Models

| Model | Parameters | VRAM (inference / LoRA training) | Image quality | Ecosystem maturity | Licence | Recommendation |
|-------|-----------|----------------------------------|--------------|-------------------|---------|---------------|
| **SDXL 1.0** | 2.6B | 8 GB / 12–16 GB | Good | **Very mature** (fullest ControlNet/LoRA ecosystem) | CreativeML Open RAIL++-M | ⭐⭐⭐⭐⭐ **First choice** |
| **Stable Diffusion 3.5 Medium** | 2.5B | 10 GB / 16 GB | Very good (strong text rendering) | Maturing | Stability Community License (free for research) | ⭐⭐⭐⭐ Alternative |
| **FLUX.1-dev** | 12B | 24 GB / 24 GB+ | **Best** | Maturing rapidly | Non-commercial (research permitted) | ⭐⭐⭐⭐ Use if VRAM allows |
| **SD 1.5** | 0.86B | 4 GB / 8 GB | Fair | Very mature | CreativeML Open RAIL-M | ⭐⭐⭐ Fallback under compute constraints |
| **SDXL-Turbo / LCM** | — | Same as SDXL | Slightly reduced | Mature | As above | ⭐⭐⭐⭐ **Use for bulk generation — 1–4 steps, >10× speedup** |

> **Recommended combination: SDXL 1.0 + LoRA + ControlNet.** Rationale: the fullest ecosystem (all ControlNet conditioning variants available), VRAM-friendly (trainable and servable on a single 4090), sufficient quality, and a clear licence. Switch to SDXL-Turbo for the bulk generation phase to save time.

### 2.2 Controllable Generation Components

| Component | Function | Use in this project |
|-----------|----------|-------------------|
| **ControlNet-Canny** | Edge conditioning | Preserve the structural outline of towers/machinery while changing scene and personnel |
| **ControlNet-Depth** | Depth conditioning | Control terrain undulation and trench depth |
| **ControlNet-OpenPose** | Pose conditioning | **Generate precise unsafe postures** (climbing, over-reaching, crouching) — the key to synthesising behaviour data |
| **ControlNet-Seg** | Segmentation-map conditioning | 🌟 **Layout is annotation**: draw a semantic layout → generate the image → the layout map *is* the segmentation ground truth, at zero annotation cost |
| **SD Inpainting** | Local repainting | 🌟 **PPE negative-sample synthesis**: erase helmet/harness while the bounding box stays fixed, so annotations are directly reusable |
| **IP-Adapter** | Image style reference | Use a few real telecommunication photos as style anchors to improve domain consistency |

> **`ControlNet-Seg` and `Inpainting` are the two highest-value routes for this project**, because they make synthetic data self-annotating and thereby remove the largest cost bottleneck in synthetic data creation.

### 2.3 Domain Adaptation Methods Compared

| Method | Data required | Training cost | Overfitting risk | Recommendation |
|--------|--------------|--------------|-----------------|---------------|
| **LoRA** (rank 16–32) | 200–500 images | 1–3 GPU-hours | Low | ⭐⭐⭐⭐⭐ **First choice** |
| DreamBooth | 20–50 images | 1–2 GPU-hours | High | ⭐⭐⭐ Suits a single specific subject (e.g. one tower model) |
| Textual Inversion | 5–20 images | 30 minutes | Medium | ⭐⭐⭐ Lightweight supplement; stackable with LoRA |
| Full fine-tuning | 5,000+ images | Tens of GPU-hours | Medium | ⭐ Neither data nor compute suffice; not recommended |

---

## 3. Perception Model Selection

### 3.1 Object Detection

| Model | mAP (COCO) | Speed | Ease of use | Recommended for |
|-------|-----------|-------|------------|----------------|
| **YOLOv11-m/l** | 51.5 / 53.4 | Very fast | ⭐⭐⭐⭐⭐ (Ultralytics one-line training) | ⭐⭐⭐⭐⭐ **Primary detector**; first choice for engineering delivery |
| **RT-DETRv2-L** | 53.4 | Fast | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ NMS-free; steadier on dense small targets |
| **Co-DETR / DINO** | 60+ | Slow | ⭐⭐⭐ | ⭐⭐⭐ If SOTA accuracy figures are the goal |
| **Grounding DINO** | 52.5 (zero-shot) | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ **Pre-labelling workhorse**; open-vocabulary zero-shot detection, essential for any re-annotation |

> **Recommended strategy**: use **YOLOv11** for the main line (fast iteration, easy reproduction); add a **RT-DETRv2** result set in the paper to show the method is backbone-agnostic, which strengthens the argument considerably.

### 3.2 Segmentation

| Model | Use | Recommendation |
|-------|-----|---------------|
| **SAM 2** | Interactive/automatic segmentation, pre-labelling | ⭐⭐⭐⭐⭐ Annotation accelerator |
| **SegFormer-B0/B2** | Semantic segmentation (terrain) | ⭐⭐⭐⭐⭐ Lightweight and efficient; ADE20K pretraining available |
| **Mask2Former** | Panoptic/instance segmentation | ⭐⭐⭐⭐ More accurate but heavier |
| **YOLOv11-seg** | Instance segmentation | ⭐⭐⭐⭐ Unified with detection; simpler engineering |

### 3.3 Pose and Behaviour

| Model | Use | Recommendation |
|-------|-----|---------------|
| **YOLOv11-pose** | 2D human keypoints | ⭐⭐⭐⭐⭐ Same framework as detection; 17 keypoints suffice |
| **RTMPose** | High-accuracy keypoints | ⭐⭐⭐⭐ Higher precision |
| **ST-GCN++ / CTR-GCN** | Skeleton action recognition | ⭐⭐⭐⭐⭐ **Resilient to low resolution and illumination change — first choice for site conditions** |
| **VideoMAE V2** | RGB video action recognition | ⭐⭐⭐⭐ Higher accuracy but needs more video data |
| **X3D / SlowFast** | Lightweight video action | ⭐⭐⭐ Reliable classical baseline |

> **Strong recommendation: run the behaviour branch on the skeleton stream (YOLOv11-pose → ST-GCN++).** Site cameras are low-resolution and poorly lit, and workers are often distant and small; skeleton representations are far more robust to these degradations than RGB. Moreover, skeleton data can be synthesised directly with ControlNet-OpenPose, dovetailing naturally with this project's generative main line.

### 3.4 Vision-Language Models (Optional Enhancement)

| Model | Use | Recommendation |
|-------|-----|---------------|
| **Qwen2.5-VL** | Hazard description generation, open-ended risk Q&A | ⭐⭐⭐⭐ Open-source, strong Chinese, locally deployable |
| **InternVL 2.5** | As above | ⭐⭐⭐⭐ |
| **GPT-4o / Claude** | Prompt engineering, semantic verification of generated data | ⭐⭐⭐⭐ Convenient API; suits the semantic review stage of the quality gates |
| **CLIP (ViT-L/14)** | Semantic consistency scoring of synthetic images | ⭐⭐⭐⭐⭐ **Mandatory component of the quality gates** |

---

## 4. Licensing and Compliance Notes

| Category | Considerations |
|----------|---------------|
| Datasets | SODA/MOCS/ACID are generally for academic use; **commercial use requires separate application**. Always state source and licence in the paper |
| SDXL | CreativeML Open RAIL++-M; permits research and most commercial use, but prohibits unlawful/infringing content |
| FLUX.1-dev | **Non-commercial licence**; usable for academic research. If commercialisation is anticipated, switch to FLUX.1-schnell (Apache 2.0) |
| Ultralytics YOLO | **AGPL-3.0**; a commercial licence is required if the work is not open-sourced. Usually not an issue for a campus research project, but state it in the report |
| **Openly licensed imagery (T3)** ★ | **CC BY / CC BY-SA require attribution.** Record source URL, licence type and author per image, and ship `licence_manifest.csv` with the report and any data release. CC BY-SA is **copyleft** (derivatives must carry the same licence), so prefer CC0 / CC BY / Public Domain if a public dataset release is planned |
| **Community datasets (T2)** ★ | Roboflow Universe is often CC BY 4.0 but not always — **confirm individually**; Kaggle licences vary more widely |
| Generated data | Synthetic persons involve no real individual's privacy. **An additional advantage of the generative approach, worth emphasising in the paper** — and more prominent still now that field collection is cancelled |

---

## 5. Phase 1 Preparation Checklist (W4)

Downloading, screening and splitting T1–T3 was completed offline. Before baseline training:

```
[Data wrap-up]
□ 1. Commit the actual counts (TelecomSeed / TelecomEval) and a hash of the TelecomEval file list
□ 2. Confirm licence_manifest.csv covers every T3 image; licence terms recorded for each T2 dataset
□ 3. Spot-check 50 random images per community (T2) dataset; where quality fails,
     take images only and re-annotate

[Class mapping and format]
□ 4. Build the class mapping table: merge synonyms (helmet / hardhat / Hardhat) and map
     negatives such as NO-Hardhat to the taxonomy's violation classes
□ 5. Convert to YOLO format (training) + COCO format (evaluation and rule layer); fix the train / val split

[Model weights]
□ 6. Phase 1: YOLOv11-s/m (COCO-pretrained); Grounding DINO (for re-annotation)
□ 7. Phase 2 (prepared by Member B during W4-W7): SDXL 1.0 + ControlNet + SD Inpainting,
     CLIP ViT-L/14, SAM 2

[Version control]
□ 8. Set up DVC; record provenance, licence and split membership for every subset
```

---

## 6. Data Scale Targets

| Data category | Tier | Target scale | Actual | Purpose | Phase |
|--------------|------|-------------|--------|---------|-------|
| Academic public data | T1 | 20,000+ images | `<<to record>>` | Backbone pretraining / transfer base | ✅ Curated |
| Community specialist data | T2 | 2,000–5,000 images | `<<to record>>` | Telecom towers / harnesses / PPE negatives | ✅ Curated |
| **Openly licensed telecom imagery** | **T3** | **200–500 images** | `<<to record>>` | Real training set + LoRA seeds | ✅ Curated |
| 🔒 **TelecomEval test set** | **T3 (+T2)** | **150–300 images (isolated, frozen)** | `<<to record>>` | **The sole yardstick, shared by both phases** | ✅ Split |
| Synthetic data | T4 | 3,000–10,000 images | — | Augmented training set, targeting weak classes | Phase 2 |
| Video clips (behaviour) | T1 | 200–500 clips | — | Action recognition training (optional) | Phase 2 (D6 if unavailable) |
| Expert risk-level annotation | Team | 200 images | — | Fusion module ground truth | Phase 2 |

> Record the "Actual" column in the repository — the final report's Scope and Schedule sections require planned vs actual.
