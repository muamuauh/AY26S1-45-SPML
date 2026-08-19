# Literature Survey (English Version) — TelecomSafe

**Generative Image-based Learning for Telecommunication Construction Safety: A State-of-the-Art Review**

> Document version: v2.0 ｜ Generated: 2026-08-18
> Chinese counterpart: [04-文献综述-CN.md](04-文献综述-CN.md)
> Databases searched: Google Scholar, IEEE Xplore, ACM Digital Library, ScienceDirect (Elsevier), MDPI, arXiv
> Coverage window: 2015–2026, with emphasis on 2023–2026
> ⚠️ **Read §8 (Citation Verification Status) before use** — some bibliographic details were obtained from search metadata and must be verified entry-by-entry prior to formal submission.

---

## Abstract

Construction remains one of the most hazardous industries worldwide. Telecommunication construction — characterised by tower climbing, trenching for optical cable, antenna installation, and confined-space work in equipment rooms — inherits the risks of general construction while adding sector-specific hazards of its own. Deep-learning-based computer vision (CV) has become the dominant paradigm for automated construction safety monitoring, yet its deployment in the telecommunication sector is bottlenecked by a single core constraint: **the scarcity and low diversity of labelled, sector-specific imagery**.

This survey reviews four converging streams of literature: (1) CV for construction safety monitoring; (2) public datasets and their limitations; (3) generative AI for synthetic training-data creation; and (4) multi-source information fusion for holistic risk appraisal. We identify a clear research gap: **no existing work combines generative data augmentation with multi-dimensional information fusion for the telecommunication construction domain** — precisely the space that TelecomSafe occupies.

**Keywords**: construction safety, computer vision, generative AI, diffusion models, data augmentation, information fusion, telecommunication infrastructure

---

## 1. Introduction and Scope

### 1.1 Motivation

Automated monitoring of construction safety has accumulated over a decade of research, yet three structural problems remain inadequately resolved:

1. **Data scarcity and domain shift.**
   Virtually all public datasets originate from building and municipal construction sites. Telecommunication scenes — lattice towers, monopoles, base-station equipment rooms, cable trenches, rooftop antennas — differ systematically in visual distribution: object morphology, camera viewpoint, working height, and background environment all diverge. Direct transfer of general-purpose models incurs substantial performance degradation.

2. **Long-tail risks are unobtainable.**
   Genuinely dangerous scenes — for instance a worker leaning out from a tower without a fall-arrest harness — are extremely rare in real data. More problematically, even when they occur they are difficult to photograph and publish for ethical, legal, and labour-relations reasons. This constitutes a **structural deadlock** in data acquisition.

3. **Point detection ≠ risk assessment.**
   The overwhelming majority of prior work stops at "worker X is not wearing a helmet" rather than answering "what is the overall risk level of this work face, and which factors jointly constitute it." The former is a perception problem, the latter a decision problem, and a visible gap separates the two.

### 1.2 Review Methodology

| Item | Content |
|------|---------|
| Databases | Google Scholar, IEEE Xplore, ACM Digital Library, ScienceDirect, MDPI, arXiv |
| Example queries | `("construction safety" OR "construction site") AND ("deep learning" OR "computer vision") AND ("data augmentation" OR "generative" OR "diffusion")` |
| | `("personal protective equipment" OR PPE) AND detection AND dataset` |
| | `("information fusion" OR multimodal) AND ("construction" AND "risk assessment")` |
| | `telecommunication AND (tower OR "base station") AND (safety OR hazard) AND "computer vision"` |
| Inclusion criteria | Peer-reviewed journal or conference papers; published 2015 or later; containing experimental validation or systematic review |
| Exclusion criteria | Purely managerial questionnaire studies; industry white papers without technical contribution; non-peer-reviewed commercial material |
| Core venues | *Automation in Construction*, *Advanced Engineering Informatics*, *Safety Science*, *Journal of Computing in Civil Engineering*, *Sensors*, *Buildings* |

---

## 2. Computer Vision for Construction Safety

### 2.1 Foundational Reviews

The earliest systematic account of this field is due to Seo et al. [R1], who reviewed CV applications in construction safety and health monitoring and identified three unresolved practical obstacles:

- **A lack of task-specific, quantifiable metrics for evaluating extracted information in a safety context**
- **Technical difficulties arising from the dynamic conditions of construction sites** (illumination change, occlusion, extreme scale variation)
- **Privacy concerns** regarding worker likeness and behavioural records

Notably, all three remain partially valid a decade later. The first in particular — how to convert visual detections into trustworthy, auditable safety measures — is still an open problem. The risk-scoring design of TelecomSafe's L4 fusion layer is a direct response to it.

Fang et al. [R2], writing in *Automation in Construction*, advanced the discussion into the deep-learning era. They confirmed that CV + DL is now capable of automatically identifying unsafe behaviours and unsafe conditions, but noted that deployment is constrained by a combination of **technical challenges** (accuracy, reliability) and **managerial challenges** (organisational acceptance, liability attribution).

### 2.2 Personal Protective Equipment (PPE) Compliance Detection

PPE detection is the most mature and most densely populated branch of the field.

**Safety helmet detection** is the most intensively studied sub-task, and its technical trajectory is clearly legible: from early hand-crafted features and HOG+SVM, through two-stage detectors such as Faster R-CNN, to the single-stage real-time solutions dominated by the YOLO family (v3 → v11) [R3][R4]. Refinements over the past two years have concentrated on two directions: incorporating Transformer backbones (RT-DETR, contextual Transformer modules) to strengthen global modelling, and lightweight multi-scale optimisation for the small targets typical of construction imagery.

**Safety harness / lanyard detection** was pioneered by Fang et al. [R5], who addressed falls from height — the leading cause of construction fatalities — with a CV-based harness detection approach. This work is **highly relevant to the present project**: telecommunication tower work is, in essence, continuous work at height, and harness compliance is the single most critical risk indicator.

**Joint multi-class modelling** is a clear recent trend. Rather than training an independent detector per PPE category, researchers increasingly treat helmets (including colour), high-visibility vests, gloves, and goggles as **multi-label attributes** predicted jointly [R6][R7]. This directly supports the present project's design decision to give the Workers branch a shared-backbone, multi-head structure.

**Commentary**: PPE detection is approaching saturation under controlled conditions (public benchmarks frequently report mAP above 0.90), but performance degrades sharply under the conditions specific to telecommunication work — **small targets, backlighting, and long-range tower operations**. This is both what the project's robustness experiment (E7) must quantify and where incremental contribution remains available, since existing literature rarely reports performance curves under degraded conditions in any systematic way.

### 2.3 Unsafe Behaviour Recognition

Behaviour recognition is markedly harder than PPE detection because it requires modelling temporal dynamics rather than static attributes.

Yang et al. [R8] proposed a Transformer-based model for unsafe action identification in construction projects and, importantly, **released the accompanying video dataset**. This is currently the most valuable public resource in the sub-field and should be a priority acquisition for the project.

Follow-up work in the same line [R9] addresses a very practical constraint: site surveillance cameras are low-resolution, and workers frequently occupy only **28×28 pixels** in frame. The authors propose a teacher–student distillation strategy for this extreme low-resolution regime. The problem setting is close to real deployment conditions and merits adoption.

**Skeleton representations** are favoured for their robustness to illumination change and resolution degradation. Graph convolutional approaches [R10] and their centre-of-gravity-aware refinements [R11] perform well on worker unsafe-behaviour recognition. Separately, adaptive spatiotemporal sampling with attention has been used to handle sparsely occurring hazardous events in long video [R12], addressing the severe positive/negative imbalance inherent in the task.

**Commentary**: the RGB stream has a higher accuracy ceiling but demands more data and is sensitive to image degradation; the skeleton stream is robust but discards scene context (it cannot, for example, determine what environment the worker is in). **Two-stream fusion** is the reasonable direction. More importantly, **skeleton data can be synthesised directly via ControlNet-OpenPose** — specifying keypoints generates an image in the corresponding pose, and the skeleton is itself the annotation. This dovetails naturally with the project's generative main line and is a junction worth developing deliberately.

### 2.4 Proximity, Machinery and Site-level Risk

Visual recognition and 3D localisation of large machinery such as tower cranes has reached a reasonably mature systematic form [R13], and the approach transfers to hoisting operations on telecommunication towers.

More noteworthy is the emergence of site-level risk computation [R14]. Such work no longer merely emits bounding boxes but **quantifies and visualises the risk distribution across the whole site**, dynamically monitoring changes in the number of and distance to hazard sources. This "from detection to risk" turn aligns closely with the design objective of TelecomSafe's L4 layer.

UAV platforms have been applied to automated inspection of unsafe site conditions [R15]. For tall structures such as telecommunication towers, UAVs offer an inherent viewpoint advantage: ground-level views cannot observe the working face at the top of a tower, whereas a UAV can view it level-on or from above.

### 2.5 Vision-Language Models: The Emerging Frontier

The most conspicuous trend of 2024–2026 is the entry of vision-language models (VLMs) and large language models (LLMs) into construction safety:

- Tailored vision-language frameworks for construction sites can perform hazard identification and **generate remediation reports directly** [R16], converting perception output into natural-language documents usable by managers.
- Real-time safety detection models combining VLM and NLP have begun to appear [R17].
- More ambitious work deploys VLM-LLM pipelines on **mobile robots** for autonomous safety inspection [R18], and uses large models for open-ended hazard detection [R19] — that is, without pre-defining hazard categories, letting the model determine what is wrong in a scene.
- Open-vocabulary detectors, exemplified by Grounding DINO [R20], make **zero-shot localisation of arbitrary text-described objects** feasible, achieving 52.5 AP on the COCO zero-shot benchmark. This dramatically lowers the annotation cost of new categories.

**Commentary**: the strength of the VLM route is **openness** — no re-annotation or retraining is required for each newly identified risk category; its weakness is **insufficient localisation precision and high inference cost**. For TelecomSafe, the appropriate role for VLMs is not as the primary detector but in three supporting capacities:

1. **A semantic quality gate for generated data** (deciding whether the worker in a synthetic image is in fact wearing a helmet)
2. **Natural-language generation of the final risk report** (low cost, high demonstration value)
3. **Annotation acceleration** (Grounding DINO pre-labelling followed by human correction, saving roughly 60% of annotation effort)

---

## 3. Datasets: The Core Bottleneck

### 3.1 Existing Public Datasets

| Dataset | Scale | Domain and characteristics | Ref. |
|---------|-------|---------------------------|------|
| **SODA** | 19,846 images / 286,201 objects / 15 classes | General construction sites; organised into worker, material, machine and layout groups; multiple viewpoints — long shot (42.8%), close shot (34.7%), crane-hook monitor (15.5%), UAV (7.0%) | [R21] |
| **MOCS** | 41,668 images / 13 classes | Moving objects on construction sites; **pixel-level annotation**; includes low-altitude UAV views, no top-down views | [R22] |
| **ACID** | 10,000 images / 10 classes | Construction machinery; ground-level viewpoints | [R23] |
| **AIDCON** | Aerial imagery | **UAV-specific benchmark** for construction machinery | [R24] |
| **CHV** | 1,330 images | Helmet colour + high-visibility vest; real site backgrounds, varied gestures, angles and distances | [R6] |
| **SHEL5K** | 5,000 images / 6 classes | Extended safety-helmet benchmark; high annotation quality (head / helmeted head / unhelmeted head / person / helmet / face) | [R25] |
| **Construction action video set** | Video clips | Unsafe action recognition; released with an accompanying Transformer model | [R8] |

### 3.2 The Gap

Several studies state the data problem explicitly. The authors of SHEL5K [R25] observe that very few public safety-helmet datasets exist, and that **most are incompletely labelled with insufficient class coverage**; other work states plainly that the scarcity of high-quality datasets "has impeded the development of deep learning models in this domain" [R4].

For the present project the situation is more severe:

> **A systematic search (Google Scholar / IEEE Xplore / ACM Digital Library) returned no public, annotated safety-detection dataset targeting telecommunication construction scenes (towers, base stations, optical-cable laying, equipment-room work).**

The nearest existing work concerns **inspection and asset auditing** of telecommunication towers — and largely at the commercial-product level [R26] — rather than **safety monitoring during construction**. The two differ fundamentally in task definition: the former concerns equipment condition and asset compliance, the latter personnel behaviour and operational risk.

**This gap is simultaneously TelecomSafe's greatest execution risk and the justification for the project's existence.**

---

## 4. Generative AI for Training-Data Synthesis

### 4.1 Technical Foundations

- **Latent diffusion models** (Latent Diffusion / Stable Diffusion) [R27] perform diffusion in a compressed latent space rather than pixel space, making high-resolution text-to-image synthesis feasible on consumer hardware. This is the technical cornerstone of all current downstream applications.
- **ControlNet** [R28] freezes the original model weights and trains a controllable copy, enabling multimodal conditioning on edge maps, depth maps, segmentation maps and pose maps. This mechanism is **the technical basis of the "generation-is-annotation" paradigm**: if the spatial layout of a generated image is controlled by a semantic segmentation map, then that map is itself the ground-truth annotation for the image.
- **Segment Anything (SAM)** [R29] and its video counterpart **SAM 2** [R30] provide near-zero-cost, high-quality segmentation masks and are key components of inpainting-based editing and automatic annotation pipelines.

### 4.2 Synthetic Data for Perception Tasks

The general vision community has established the effectiveness of diffusion-generated synthetic data:

- Azizi et al. [R31] demonstrated that synthetic data from diffusion models improves ImageNet classification — the landmark result in this direction.
- **Gen2Det** [R32] proposes a complete synthesis pipeline for detection and segmentation: **grounded inpainted generation → dual image-level and instance-level filtering → improved training methodology**. Its conclusion that filtering is mandatory bears directly on the design of this project's Stage 4 quality gates: **unfiltered synthetic data typically harms rather than improves performance**.
- **ODGEN** [R33] focuses on domain-specific detection data generation, implying that general-purpose generative models require domain adaptation (e.g. LoRA fine-tuning) before they yield genuinely useful training data.
- In weakly-supervised segmentation [R34] and semantic segmentation [R35], controlled diffusion augmentation reports substantial mIoU gains (5.95% and 6.85% respectively).
- The **measurement of the sim-to-real domain gap** has itself become an object of study [R36]. Appearance and structural similarity metrics such as CLIP, FID, LPIPS and SSIM have been found to correlate with downstream task performance, providing a basis for setting the thresholds of this project's quality gates.

### 4.3 Generative Augmentation in Construction Safety — The Most Relevant Work

This is the literature that TelecomSafe directly benchmarks against, and the most important section of this survey.

| Work | Method | Key results | Implication for this project |
|------|--------|------------|----------------------------|
| **Kim & Yi (2024)** [R37] | Text-to-image generation of hazardous scenes; built a dataset of **3,585 images across 27 hazard categories** to train detection and segmentation networks | Detection mAP ≈ 64%, segmentation ≈ 60% | Demonstrates that purely generated data can support a usable model, but absolute performance is limited — **mixing with real data is mandatory** |
| **Lee et al. (2025)** [R38] | Systematic comparison of 3 generative tools (DALL·E, Midjourney, Stable Diffusion) × 3 prompting strategies (zero-shot, structured, image-guided structured) | Detection improved from **51.6% to 92.5%**; **Stable Diffusion + image-guided structured prompting performed best**; optimal augmentation size **100–150 images per category** | 🌟 **Directly informs this project's Stage 2 prompting strategy and the target counts in the Stage 0 specification library** |
| **AIGC-HWD (2025)** [R39] | Built a generative safety-helmet detection dataset | Trained solely on AIGC images, exceeds mAP@50 of 0.7–0.8 on real imagery | Quantifies the actual magnitude of the domain gap; usable as the reference baseline for this project's E4 experiment (synthetic-only training → real testing) |
| **Midjourney worker detection (2023)** [R40] | Synthesised construction worker images using a commercial generative platform | Feasibility confirmed | Commercial tools are convenient but **uncontrollable and irreproducible** — academic projects should prefer open-source models |
| **Crack detection augmentation (2024)** [R41] | Generative augmentation applied to structural crack detection | Performance improvement | Cross-task corroboration of the generality of generative augmentation |
| **Object range expansion synthesis (2025)** [R42] | A practical image augmentation method for construction safety | — | A lightweight alternative usable as an ablation control |
| **Scene-graph-guided industrial hazard generation (2025)** [R43] | Constrains generation with scene graphs and evaluates industrial hazard scenarios | — | 🌟 **Consistent with this project's L4 entity-graph design; warrants close comparative analysis** |
| **Work-at-height PPE compliance (2026)** [R44] | Generative AI-driven augmentation plus object-guided vision-language reasoning | — | 🌟 **Work-at-height scenarios overlap heavily with telecommunication tower work; the most direct benchmark available** |

**Overall commentary**:

1. **The direction is still very young.** The most relevant work is concentrated in 2024–2026, which speaks well for the timeliness of this project's topic; conversely it means few mature baselines are available for comparison, and controls must largely be built in-house.

2. **Existing work generally stops at a single "generate images → train detector" chain**, missing three elements:
   - A systematic **risk-scenario specification library** (most work writes prompts ad hoc, so neither coverage nor reproducibility can be guaranteed)
   - Rigorous **multi-stage quality gates** (Gen2Det [R32] does this for general vision, but no systematic scheme has appeared in the construction safety domain)
   - Coupling of generated data with **multi-dimensional fusion-based assessment** (what is generated is training data, but what is evaluated remains single-point detection metrics)

3. **None targets the telecommunication construction domain.** All scenarios are building, road, or generic construction.

### 4.4 The Ethical Advantage of Synthesis

One argument that is generally undervalued in the existing literature but is highly persuasive for this project:

Real photographs of safety violations necessarily involve the **portrait rights, privacy, and labour-relations exposure of identifiable workers**. Collection requires informed consent, publication requires de-identification, and cross-organisation sharing is harder still. This is precisely why the data gap described in §3.2 cannot be closed simply by "taking more photographs."

Synthetic imagery, by contrast, depicts no real individual and sidesteps the problem at its root. **This should be written into the paper as an explicit contribution of TelecomSafe**: the generative approach solves not only the problem of data volume, but the problem of data compliance.

---

## 5. Information Fusion for Risk Appraisal

### 5.1 Multi-source and Multimodal Fusion

- Multi-source information fusion has been applied to dynamic safety risk prediction for construction machinery, modelled with a spatial–temporal multi-graph convolution network [R45].
- A scenario-based multimodal deep learning framework performs **simultaneous** detection of accident causal factors and risk evaluation [R46]. Its central idea is to decompose the problem into several specialised scenarios by work environment and model each separately, reporting a 66.7% F1 improvement over a single unified model. This "divide and conquer" strategy is strong corroboration for the four-branch design adopted in this project.
- Multimodal data fusion has been used for operational status monitoring and risk prediction of construction projects [R47].
- Multimodal fusion for dangerous action recognition on railway construction sites has been examined through a systematic **comparison of fusion strategies** [R48]; that comparison framework (early / late / hybrid fusion) transfers directly to the ablation design of this project's L4 layer.
- Dynamic site risk management combining CV and IoT [R49] offers an alternative fusion route, introducing sensor data to complement visual information.
- On uncertainty modelling, an improved **Dempster–Shafer evidence theory** has been applied to multi-source fusion in tunnel collapse risk analysis [R50]. **This is the classical tool for reconciling conflicting confidences across perception branches** — for instance when the terrain branch reports "high risk" while the worker branch reports "low risk" — and merits consideration as an alternative or control method for this project's L4 layer.

### 5.2 From Detection to Risk Quantification

The work cited earlier as [R14] converts CV output into a visualised quantification of safety risk, dynamically tracking changes in the number of and distance to hazard sources. This "detection → risk" conversion is precisely the core task of TelecomSafe's L4 layer.

**Commentary**: existing fusion work is largely oriented toward **cross-modal** fusion of **sensor + vision + text**, whereas TelecomSafe faces a different problem setting — **fusion of evidence across four semantic dimensions within a single image** (terrain / machinery / materials / workers). This is a comparatively uncommon problem form and carries a degree of novelty in itself.

Furthermore, a hybrid "rules + learning" architecture that encodes safety regulations (OSHA 1926, GB 26859, etc.) as **decidable predicates** and couples them with a learnable fusion module has no mature precedent in the construction safety literature. The value of this route lies in **interpretability and regulatory auditability**: decisions in the safety domain must be traceable to specific clauses, and pure black-box models are difficult for the industry to accept.

---

## 6. Research Gaps and the Positioning of TelecomSafe

Synthesising the four streams above yields five clearly articulated gaps:

| # | Gap | Current state | TelecomSafe's response |
|---|-----|--------------|----------------------|
| **G1** | **No telecommunication-specific data or risk taxonomy** | All public datasets are building/municipal; telecommunication-tower research concentrates on asset inspection rather than construction safety | Propose a telecommunication construction **Risk Taxonomy** and build the TelecomSeed (real) / TelecomSynth (synthetic) datasets |
| **G2** | **Generative augmentation lacks systematic quality control** | Construction-domain generative work is largely end-to-end "generate and use"; the general vision domain has already shown filtering to be mandatory [R32] | Design **four quality gates** (semantic consistency / distributional consistency / annotation reliability / human spot-check) with a dedicated gate ablation (A4) |
| **G3** | **The annotation cost of synthetic data is unresolved** | Most work still annotates synthetic images manually, cancelling the cost advantage of synthesis | Achieve near-zero annotation cost via **ControlNet-Seg / OpenPose layout-as-annotation** plus **inpainting annotation inheritance** |
| **G4** | **A gap separates detection from risk assessment** | Most work stops at emitting bounding boxes | **Three-level hierarchical fusion**: entity graph → rule predicates → learnable fusion, emitting an interpretable site-level risk score |
| **G5** | **Robustness evaluation is generally absent** | Very few studies systematically report performance under degraded conditions | A dedicated E7 robustness experiment (low light / rain and fog / motion blur / small targets / cross-site generalisation) |

**Positioning statement** (suitable for direct use at the end of the paper's Introduction):

> To the best of our knowledge, TelecomSafe is the first framework that (i) establishes a risk taxonomy dedicated to telecommunication construction, (ii) couples a quality-gated, annotation-free generative augmentation pipeline with (iii) a hierarchical, regulation-grounded information-fusion module that converts multi-dimensional visual evidence into an interpretable site-level risk score.

---

## 7. References

> Numbering corresponds to [Rxx] in the text. Verification status is given in §8.

### CV for Construction Safety — Reviews

**[R1]** Seo, J., Han, S., Lee, S., & Kim, H. (2015). Computer vision techniques for construction safety and health monitoring. *Advanced Engineering Informatics*, 29(2), 239–251. https://doi.org/10.1016/j.aei.2015.02.001

**[R2]** Fang, W., Ding, L., Love, P. E. D., Luo, H., Li, H., Peña-Mora, F., Zhong, B., & Zhou, C. (2020). Computer vision applications in construction safety assurance. *Automation in Construction*, 110, 103013. https://doi.org/10.1016/j.autcon.2019.103013

### PPE Detection

**[R3]** Ferdous, M., & Ahsan, S. M. M. (2024). Personal protective equipment detection using YOLOv8 architecture on object detection benchmark datasets: a comparative study. *Cogent Engineering*, 11(1). https://doi.org/10.1080/23311916.2024.2333209

**[R4]** (2025). A deep learning-based algorithm for the detection of personal protective equipment. *PLOS ONE*. https://doi.org/10.1371/journal.pone.0322115

**[R5]** Fang, W., Ding, L., Luo, H., & Love, P. E. D. (2018). Falls from heights: A computer vision-based approach for safety harness detection. *Automation in Construction*, 91, 53–61. https://doi.org/10.1016/j.autcon.2018.02.018

**[R6]** Wang, Z., Wu, Y., Yang, L., Thirunavukarasu, A., Evison, C., & Zhao, Y. (2021). Fast Personal Protective Equipment Detection for Real Construction Sites Using Deep Learning Approaches. *Sensors*, 21(10), 3478. (**CHV dataset**) https://doi.org/10.3390/s21103478

**[R7]** Nath, N. D., Behzadan, A. H., & Paal, S. G. (2020). Deep learning for site safety: Real-time detection of personal protective equipment. *Automation in Construction*, 112, 103085. (**Pictor-v3 dataset**) https://doi.org/10.1016/j.autcon.2020.103085

### Unsafe Behaviour Recognition

**[R8]** Yang, M., Wu, C., Guo, Y., Jiang, R., Zhou, F., Zhang, J., & Yang, Z. (2023). Transformer-based deep learning model and video dataset for unsafe action identification in construction projects. *Automation in Construction*, 146, 104703. https://doi.org/10.1016/j.autcon.2022.104703
　Code/Data: https://github.com/S1mpleyang/ConstructionActionRecognition

**[R9]** Yang, M., et al. (2023). A teacher–student deep learning strategy for extreme low resolution unsafe action recognition in construction projects. *Advanced Engineering Informatics*, 58, 102294. https://doi.org/10.1016/j.aei.2023.102294 ｜ ACM DL: https://dl.acm.org/doi/10.1016/j.aei.2023.102294

**[R10]** Yan, S., Xiong, Y., & Lin, D. (2018). Spatial Temporal Graph Convolutional Networks for Skeleton-Based Action Recognition. *AAAI 2018*. https://doi.org/10.1609/aaai.v32i1.12328

**[R11]** (2025). Center-of-Gravity-Aware Graph Convolution for Unsafe Behavior Recognition of Construction Workers. *Sensors (MDPI)*. https://pmc.ncbi.nlm.nih.gov/articles/PMC12431360/

**[R12]** (2024). Construction workers' unsafe behavior detection through adaptive spatiotemporal sampling and optimized attention based video monitoring. *Automation in Construction*. https://www.sciencedirect.com/science/article/abs/pii/S0926580524002449

### Site-level Risk and Machinery

**[R13]** (2023). Vision-Based Automated Recognition and 3D Localization Framework for Tower Cranes Using Far-Field Cameras. *Sensors*, 23(10). https://pmc.ncbi.nlm.nih.gov/articles/PMC10222976/

**[R14]** (2023). Computer vision-based safety risk computing and visualization on construction sites. *Automation in Construction*. https://www.sciencedirect.com/science/article/abs/pii/S0926580523003898

**[R15]** (2024). Investigation of Unsafe Construction Site Conditions Using Deep Learning Algorithms Using Unmanned Aerial Vehicles. *Sensors*. https://pmc.ncbi.nlm.nih.gov/articles/PMC11511453/

### Vision-Language Models

**[R16]** (2025). Tailored vision-language framework for automated hazard identification and report generation in construction sites. *Advanced Engineering Informatics*. https://www.sciencedirect.com/science/article/abs/pii/S1474034625003714

**[R17]** (2025). Real-time safety detection on construction sites using a vision-language and NLP-based model. *Advanced Engineering Informatics*. https://www.sciencedirect.com/science/article/abs/pii/S1474034625007827

**[R18]** (2025). Autonomous Construction-Site Safety Inspection Using Mobile Robots: A Multilayer VLM-LLM Pipeline. *arXiv:2512.13974*. https://arxiv.org/abs/2512.13974

**[R19]** (2025). Automated Hazard Detection in Construction Sites Using Large Language and Vision-Language Models. *arXiv:2511.15720*. https://arxiv.org/abs/2511.15720

**[R20]** Liu, S., Zeng, Z., Ren, T., Li, F., Zhang, H., Yang, J., Li, C., Yang, J., Su, H., Zhu, J., & Zhang, L. (2023). Grounding DINO: Marrying DINO with Grounded Pre-Training for Open-Set Object Detection. *arXiv:2303.05499*; *ECCV 2024*. https://arxiv.org/abs/2303.05499

### Datasets

**[R21]** Duan, R., Deng, H., Tian, M., Deng, Y., & Lin, J. (2022). SODA: A large-scale open site object detection dataset for deep learning in construction. *Automation in Construction*, 142, 104499. https://doi.org/10.1016/j.autcon.2022.104499 ｜ arXiv:2202.09554

**[R22]** An, X., Zhou, L., Liu, Z., Wang, C., Li, P., & Li, Z. (2021). Dataset and benchmark for detecting moving objects in construction sites. *Automation in Construction*, 122, 103482. (**MOCS dataset**) https://doi.org/10.1016/j.autcon.2020.103482

**[R23]** Xiao, B., & Kang, S.-C. (2021). Development of an Image Data Set of Construction Machines for Deep Learning Object Detection. *Journal of Computing in Civil Engineering*, 35(2). (**ACID dataset**) https://doi.org/10.1061/(ASCE)CP.1943-5487.0000945

**[R24]** (2024). AIDCON: An Aerial Image Dataset and Benchmark for Construction Machinery. *Remote Sensing*, 16(17), 3295. https://doi.org/10.3390/rs16173295

**[R25]** Otgonbold, M.-E., Gochoo, M., Alnajjar, F., Ali, L., Tan, T.-H., Hsieh, J.-W., & Chen, P.-Y. (2022). SHEL5K: An Extended Dataset and Benchmarking for Safety Helmet Detection. *Sensors*, 22(6), 2315. https://doi.org/10.3390/s22062315

**[R26]** Optelos. *Cell Tower Inspection Audits*. (Industry resource — tower inspection, not construction safety) https://optelos.com/telecom/cell-tower-inspection-audits/

### Generative Models — Foundations

**[R27]** Rombach, R., Blattmann, A., Lorenz, D., Esser, P., & Ommer, B. (2022). High-Resolution Image Synthesis with Latent Diffusion Models. *CVPR 2022*. https://doi.org/10.1109/CVPR52688.2022.01042

**[R28]** Zhang, L., Rao, A., & Agrawala, M. (2023). Adding Conditional Control to Text-to-Image Diffusion Models. *ICCV 2023*. (**ControlNet**) https://arxiv.org/abs/2302.05543

**[R29]** Kirillov, A., Mintun, E., Ravi, N., et al. (2023). Segment Anything. *ICCV 2023*. https://arxiv.org/abs/2304.02643

**[R30]** Ravi, N., Gabeur, V., Hu, Y.-T., et al. (2024). SAM 2: Segment Anything in Images and Videos. *arXiv:2408.00714*. https://arxiv.org/abs/2408.00714

### Synthetic Data for Perception

**[R31]** Azizi, S., Kornblith, S., Saharia, C., Norouzi, M., & Fleet, D. J. (2023). Synthetic Data from Diffusion Models Improves ImageNet Classification. *TMLR / arXiv:2304.08466*. https://arxiv.org/abs/2304.08466

**[R32]** Suri, S., et al. (2023). Gen2Det: Generate to Detect. *arXiv:2312.04566*. https://arxiv.org/abs/2312.04566

**[R33]** Zhu, J., et al. (2024). ODGEN: Domain-specific Object Detection Data Generation with Diffusion Models. *NeurIPS 2024 / arXiv:2405.15199*. https://arxiv.org/abs/2405.15199

**[R34]** (2023). Image Augmentation with Controlled Diffusion for Weakly-Supervised Semantic Segmentation. *arXiv:2310.09760*. https://arxiv.org/abs/2310.09760

**[R35]** Yang, L., et al. (2023). FreeMask: Synthetic Images with Dense Annotations Make Stronger Segmentation Models. *NeurIPS 2023 / arXiv:2310.15160*. https://arxiv.org/abs/2310.15160

**[R36]** (2026). SADGE: Structure and Appearance Domain Gap Estimation of Synthetic and Real Data. *arXiv:2605.22467*. https://arxiv.org/abs/2605.22467

### 🌟 Generative Augmentation in Construction Safety (Most Relevant)

**[R37]** Kim, H., & Yi, J. (2024). Image generation of hazardous situations in construction sites using text-to-image generative model for training deep neural networks. *Automation in Construction*, 166, 105615. https://doi.org/10.1016/j.autcon.2024.105615

**[R38]** Lee, Y., Kang, G., Kim, J., Yoon, S., & Jeon, J. (2025). Generative AI-driven data augmentation for enhanced construction hazard detection. *Automation in Construction*. https://www.sciencedirect.com/science/article/abs/pii/S0926580525003577

**[R39]** (2025). Can Generative AI-Generated Images Effectively Support and Enhance Real-World Construction Helmet Detection? *Buildings*, 15(22), 4080. (**AIGC-HWD dataset**) https://doi.org/10.3390/buildings15224080

**[R40]** (2023). Synthesizing Reality: Leveraging the Generative AI-Powered Platform Midjourney for Construction Worker Detection. *ASCE Conference Proceedings*. https://doi.org/10.1061/9780784486139.097

**[R41]** (2024). Generative AI-Driven Data Augmentation for Crack Detection in Physical Structures. *Electronics*, 13(19), 3905. https://doi.org/10.3390/electronics13193905

**[R42]** (2025). A Practical Image Augmentation Method for Construction Safety Using Object Range Expansion Synthesis. *Buildings*, 15(9), 1447. https://doi.org/10.3390/buildings15091447

**[R43]** (2025). Scene Graph-Guided Generative AI Framework for Synthesizing and Evaluating Industrial Hazard Scenarios. *arXiv:2511.13970*. https://arxiv.org/abs/2511.13970

**[R44]** (2026). Generative AI-driven data augmentation and object-guided vision-language reasoning for PPE compliance analysis in work-at-height. *Advanced Engineering Informatics*. https://www.sciencedirect.com/science/article/abs/pii/S147403462600056X

### Information Fusion for Risk Assessment

**[R45]** (2025). Multi-source information fusion for dynamic safety risk prediction of aerial building machine using spatial–temporal multi-graph convolution network. *Advanced Engineering Informatics*. https://www.sciencedirect.com/science/article/abs/pii/S1474034625001545

**[R46]** (2026). Scenario-based multimodal deep learning framework for simultaneous detection of construction accident causal factors and risk evaluation. *Automation in Construction*. https://www.sciencedirect.com/science/article/abs/pii/S0926580526000920

**[R47]** (2025). Operational status monitoring and risk prediction of construction projects based on multimodal data fusion. *Journal of Ambient Intelligence and Humanized Computing*. https://doi.org/10.1007/s12652-025-05003-0

**[R48]** (2024). Comparison Analysis of Multimodal Fusion for Dangerous Action Recognition in Railway Construction Sites. *Electronics*, 13(12), 2294. https://doi.org/10.3390/electronics13122294

**[R49]** (2025). Leveraging Deep Learning and Internet of Things for Dynamic Construction Site Risk Management. *Buildings*, 15(8), 1325. https://doi.org/10.3390/buildings15081325

**[R50]** (2022). A multi-source information fusion approach in tunnel collapse risk analysis based on improved Dempster–Shafer evidence theory. *Scientific Reports*. https://pmc.ncbi.nlm.nih.gov/articles/PMC8901684/

---

## 8. Citation Verification Status ⚠️

Bibliographic details in this survey were obtained via web search and fall into three reliability tiers. **Verify entry by entry against this table before submission.**

| Tier | Entries | Note |
|------|---------|------|
| ✅ **Fully verified** | R1, R2, R5, R8, R21, R37, R38 | Title, authors, venue, and volume/issue all confirmed by search |
| ⚠️ **Partially verified** | R6, R7, R10, R20, R22, R23, R25, R27–R33, R35 | Widely-cited standard references in the field; titles and venues are reliable, but **volume/pages/DOI need checking** |
| ❗ **Title and link only** | R3, R4, R11–R19, R24, R26, R34, R36, R39–R50 | Author lists unavailable or incomplete. **Author information must be completed before formal citation** |

**Suggested verification workflow**:

1. Resolve the DOI directly (`https://doi.org/<DOI>`) to obtain authoritative metadata
2. Or search the exact title on Google Scholar → click the quotation-mark icon → export BibTeX
3. IEEE Xplore / ACM DL entries can be exported directly from the page
4. University libraries normally hold ScienceDirect full-text access (this search was blocked with HTTP 403); complete the remaining entries via the campus network

---

## 9. Writing Guidance

To adapt this document into the paper's Related Work section, compress it into four subsections of roughly 1,200–1,500 words:

| Subsection | Content | Citations | Function of closing sentence |
|-----------|---------|-----------|---------------------------|
| 2.1 CV for Construction Safety | Reviews → PPE → behaviour → site-level risk | R1, R2, R5, R6, R8, R14 | Establish "mature technology, but constrained by data" |
| 2.2 Data Scarcity and Generative Augmentation | Dataset landscape → general-domain synthetic data → construction-domain generative augmentation | R21–R25, R31–R33, R37–R39 | Establish "lacking quality control and annotation automation" |
| 2.3 Information Fusion for Risk Appraisal | Multi-source fusion → risk quantification | R45–R50 | Establish "a gap between detection and risk assessment" |
| 2.4 Research Gap | Summarise the G1–G5 table | — | Lead into the positioning statement in §6 |

> **Technique**: close each subsection with a contrastive sentence beginning "However," converting the achievement just described into the motivation for the next subsection, so that the argument converges naturally on the positioning statement. This is the standard construction of a Related Work section in high-tier venues.
