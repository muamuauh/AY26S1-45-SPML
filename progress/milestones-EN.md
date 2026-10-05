# Milestones: Planned vs Actual

> 中文版：[milestones.md](milestones.md)

The EE6008 report template needs planned vs actual dates in §4 Schedule and a record of scope changes in §3 Scope. Add a row here every time a milestone is reached or a fallback path is triggered — do not leave it to the end.

Weeks follow the placeholder mapping in docs/05 §5 (W1 = 2026-09-07); replace them once the semester calendar is confirmed.

## Milestones

| Milestone | Content | Planned | Actual | Notes |
|---|---|---|---|---|
| M0 | Project initiation and Risk Taxonomy | W1 | `<<date>>` | Done offline |
| M1 | Public data consolidation (TG1) | W3 | `<<date>>` | Data survey done offline; phase 1 recollected per configs/sources.yaml. Actual TG1 counts: TelecomSeed `<<n>>` / TelecomEval `<<n>>` |
| M2 | Baseline Demo (TGB) | W7 | In progress | 2026-09-29: baseline (E1/E2), rule judgement and Demo v1 done; validation mAP50 E1 0.611 / E2 0.756; 11s / 11m comparison done, YOLO11s kept; TelecomEval evaluation and TGB meeting pending |
| M3 | Generative augmentation (TG2) | W10 | | |
| M4 | Retraining with the same configuration (TG3) | W12 | | |
| M5 | Fusion upgrade (TG4) | W14 | | |
| M6 | Full evaluation (TG5) | W15 | | |
| M7 | Delivery | W16 | | |

## Deferred

| Recorded | Item | Status | When to resume |
|---|---|---|---|
| 2026-09-28 | **TelecomEval annotation and freezing** | Resumed 2026-10-02: with more sources (Openverse, Wikimedia work subcategories, multilingual queries, frames from Creative Commons YouTube videos) there were 1,930 candidates, scored by `telecomsafe.data.screen` and all reviewed by hand: **95 telecom and 72 near (power-line work) kept**, 1,763 rejected. Pre-labelled with E2 (confidence 0.3) and imported into Label Studio project 2 (167 images; the old, unannotated project 1 was deleted). Telecom is still below 100. Flickr / DVIDS need keys; a draft email asks the supervisor for site photos ([email_supervisor_telecom_eval.md](email_supervisor_telecom_eval.md)) | Next: ① packages built 2026-10-05 (`telecomsafe.data.package`): an annotation package (167 images, for a teammate; returned work goes in with `package intake-annotations`) and collection packages (telecom target 80, near target 30; `package intake-collection`) → `freeze_eval --create`; ② review newly collected images and build a follow-up annotation package; ③ if still under 100 at freezing time, apply D1 and say so in the report; ④ re-evaluate E1/E2 on TelecomEval, reporting telecom and near separately |

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
