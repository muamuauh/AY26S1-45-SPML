# Milestones: Planned vs Actual

> 中文版：[milestones.md](milestones.md)

The EE6008 report template needs planned vs actual dates in §4 Schedule and a record of scope changes in §3 Scope. Add a row here every time a milestone is reached or a fallback path is triggered — do not leave it to the end.

Weeks follow the placeholder mapping in docs/05 §5 (W1 = 2026-09-07); replace them once the semester calendar is confirmed.

## Milestones

| Milestone | Content | Planned | Actual | Notes |
|---|---|---|---|---|
| M0 | Project initiation and Risk Taxonomy | W1 | `<<date>>` | Done offline |
| M1 | Public data consolidation (TG1) | W3 | `<<date>>` | Data survey done offline; phase 1 recollected per configs/sources.yaml. Actual TG1 counts: TelecomSeed `<<n>>` / TelecomEval `<<n>>` |
| M2 | Baseline Demo (TGB) | W7 | In progress | 2026-09-29: baseline v1, rule judgement and Demo v1 done; YOLO11s kept after the 11s / 11m comparison. **2026-10-06: baseline v2 frozen** (tag `phase1-baseline-v2`): Work at Height added, 960 trial not adopted, validation mAP50 E1 0.596 / E2 0.737 ± 0.007 (3 seeds). TelecomEval evaluation and TGB meeting pending |
| M3 | Generative augmentation (TG2) | W10 | | |
| M4 | Retraining with the same configuration (TG3) | W12 | | |
| M5 | Fusion upgrade (TG4) | W14 | | |
| M6 | Full evaluation (TG5) | W15 | | |
| M7 | Delivery | W16 | | |

## Deferred

| Recorded | Item | Status | When to resume |
|---|---|---|---|
| 2026-09-28 | **TelecomEval annotation and freezing** | Resumed 2026-10-02: with more sources there were 1,930 candidates, scored by `telecomsafe.data.screen` and all reviewed by hand: **95 telecom and 72 near (power-line work) kept**. Pre-labelled with E2 and packed as an annotation package (`dist/packages/`). Single-person from 2026-10-05: **annotated by the project member**. The training set is already de-duplicated against these 167 images, so freezing needs no baseline retraining | Next: ① annotate the 167 images → `package intake-annotations` → check the spot-check sheet → `freeze_eval --create`; ② evaluate E1 and the 3 E2 seeds on TelecomEval, telecom and near reported separately; ③ if telecom stays under 100, apply D1 and say so in the report (Flickr / DVIDS or images from the supervisor may help) |

## Scope changes

| Date | Change | Reason | Impact |
|---|---|---|---|
| 2026-08-24 | Field collection cancelled; public data sources only | Safety risk and cost too high (confirmed by the supervisor) | Less real data; more reliance on generative augmentation |
| 2026-09-28 | Two phases: baseline demo first, generative augmentation second | Supervisor's advice | Generative augmentation moves to W8–W10; new decision gate TGB |
| 2026-09-28 | Phase 1 covers Workers + Machinery only (D8 applied by default) | Single-person project, scope control | Terrain / Materials may be added in phase 2 depending on progress |
| 2026-09-28 | harness (vgg2coco) dataset dropped | Checked after download: boxes labelled harness are actually hi-vis vests, and all images are staged video frames of one indoor scene | body_harness is the only harness source left (about 150 instances after de-duplication) |
| 2026-09-28 | 3 Construction Workers dataset dropped | The Roboflow project has no published version and cannot be exported | None |
| 2026-09-28 | APD and construction safety v2 added (provided by the user) | APD adds many real-site no-vest examples; v2 adds helmet and person diversity | APD is private data shared with us: internal training only, never redistributed |
| 2026-09-29 | Construction Site Safety switched from the Kaggle mirror (Roboflow v28) to Roboflow v30 | The Kaggle training split is entirely mosaic-augmented composites: E1 was no longer a "no augmentation" control, and the rules judged people and machines in different tiles as adjacent | The dataset shrinks from about 2,800 to 717 original images; teacher, E1 and E2 all retrained |
| 2026-10-05 | Work at Height Safety (Roboflow v1) added, images with a harness only, minus 862 mirror-padded images | Only 143 harness training instances from one source, and no harness detected on the telecom candidates | Training set 5,537 → 7,475 images; harness instances 143 → 2,619; teacher unchanged, E1 / E2 all retrained (baseline v2), v1 results archived in `reports/phase1/v1/` |
| 2026-10-06 | E2 with 3 random seeds; 640 kept after a 960 input-size trial; baseline v2 frozen | Lets phase 2's E3 vs E2 comparison rule out random variation; 960 barely helps small objects at twice the training time | E2 reported as mean ± std (mAP50 0.737 ± 0.007); TG3 judged on means |
