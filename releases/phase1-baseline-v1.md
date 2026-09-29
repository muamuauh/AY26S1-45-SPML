# TelecomSafe Phase 1 Baseline v1

Baseline detectors for the TelecomSafe Demo v1: a YOLO11s model detecting workers, PPE and machinery on construction sites, plus a rule layer that turns detections into a low / medium / high risk level.

## Assets

| File | Model | sha256 |
|---|---|---|
| `e2_best.pt` | **E2** — Ultralytics default augmentation (used by the demo) | `4d64ab6f1b1e142a24091d117a2749aa38d162c603b6ad4eeb2e1ac0bc66e0e1` |
| `e1_best.pt` | E1 — all built-in augmentation off (experimental control) | `3184e3d198197a20338ab039bb1fdc6fc5d71e6f83c893782e355d1a9f8932f6` |

Classes: `person, helmet, no_helmet, vest, no_vest, harness, machinery, vehicle` (see `configs/taxonomy.yaml`).

## Use

```bash
conda env create -f environment.yml && conda activate telecomsafe
python -m telecomsafe.weights          # downloads both files and checks sha256
start_demo.bat                          # Windows; or: python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt --open
```

## Results (validation split, 553 images)

| Model | mAP50 | mAP50-95 | Precision | Recall |
|---|---|---|---|---|
| E1 | 0.611 | 0.350 | 0.690 | 0.630 |
| E2 | 0.756 | 0.499 | 0.825 | 0.711 |

The validation split comes from the same sources as the training data, so these numbers are optimistic. The telecom-specific test set (TelecomEval) is not built yet. Known weaknesses: vehicle, no_helmet and machinery; harness is scored 0.98 on validation but is barely detected on real telecom images. Details: `reports/phase1/README.md`.

## Training

- YOLO11s, 640 px, seed 0, `configs/baseline.yaml`; E1 early-stopped at epoch 42, E2 ran 100 epochs.
- 5,537 images after perceptual-hash de-duplication from Construction Site Safety (Roboflow v30), Ultralytics Construction-PPE, body_harness, construction safety v2 and APD; missing classes filled with teacher pseudo-labels (18% of boxes). Sources and licences: `data/README.md`.

## Licences

- Weights are trained with Ultralytics YOLO and are released under **AGPL-3.0**.
- The training data is **not** included. Public datasets can be re-downloaded with `python -m telecomsafe.data.download`; APD is private data shared with the team and is not redistributed.
