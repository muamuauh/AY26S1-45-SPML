# Public Datasets and Pretrained Models — Survey

> Document version: v1.0 ｜ Generated: 2026-08-18
> Chinese counterpart: [02-数据集与预训练模型调研-CN.md](02-数据集与预训练模型调研-CN.md)
> Purpose: selection basis for TelecomSafe M1 (data infrastructure) and M3 (perception models)

---

## ⚠️ Headline Conclusion

**No public dataset dedicated to safety detection in telecommunication construction currently exists.**

This is both the project's central difficulty and its justification — precisely the `limited availability and diversity of labelled, sector-specific images` named in the project brief.

The data strategy must therefore be three-staged:

```
Public generic construction datasets (transfer base, large volume)
        ↓
Real telecommunication seed data (self-collected, small but critical → LoRA fine-tuning + test set)
        ↓
Generatively synthesised data (this project's innovation, closing the long tail at scale)
```

**The test set must consist 100% of real telecommunication imagery**, or every experimental conclusion becomes untrustworthy. Fix this at M1.

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
| **Grounding DINO** | 52.5 (zero-shot) | Medium | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ **Pre-labelling workhorse**; open-vocabulary zero-shot detection, essential at M1 |

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
| Self-collected data | Involves **worker likeness**; handle privacy via face blurring, informed consent, or internal-only use |
| Generated data | Synthetic persons involve no real individual's privacy. **This is an additional advantage of the generative approach and worth emphasising in the paper** |

---

## 5. Action Checklist (Directly Executable at M1)

```
□ 1. Request/download SODA, MOCS, ACID, CHV, SHEL5K, SHWD
□ 2. Clone the ConstructionActionRecognition repository; assess video data usability
□ 3. Convert everything to COCO format; build a class mapping table (merge synonyms, e.g. helmet/hardhat)
□ 4. Collect ≥500 telecommunication scene images; screen manually for quality
□ 5. Pre-label with Grounding DINO → correct in CVAT → produce TelecomSeed-v1
□ 6. Generate ground-region proposals with SAM 2 → assign classes manually → produce the terrain segmentation subset
□ 7. Split data strictly: the test set contains only real telecommunication imagery and never participates in generative fine-tuning
□ 8. Download SDXL 1.0 + the full ControlNet suite + CLIP ViT-L/14 weights
□ 9. Download YOLOv11-m/pose, SegFormer-B2, SAM 2, Grounding DINO weights
□ 10. Set up DVC data version control; record the provenance and licence of every subset
```

---

## 6. Data Scale Targets

| Data category | Target scale | Purpose |
|--------------|-------------|---------|
| Public generic data (transfer) | 20,000+ images | Backbone pretraining / transfer base |
| Real telecommunication seed data | 500–1,000 images | LoRA fine-tuning + real training set |
| **Real telecommunication test set** | **200–300 images (strictly isolated)** | **The sole yardstick for all evaluation** |
| Synthetic data | 3,000–10,000 images | Augmented training set; long-tail completion |
| Video clips (behaviour) | 200–500 clips | Action recognition training |
| Expert risk-level annotation | 200 images | Fusion module ground truth |
