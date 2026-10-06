# TelecomSafe Phase 1 Baseline v2

Frozen phase 1 baseline (2026-10-06): a YOLO11s model detecting workers, PPE and machinery on construction sites, plus a rule layer that turns detections into a low / medium / high risk level. Phase 2's generative-augmentation experiment (E3) is compared against these models with the same `configs/baseline.yaml`.

## What changed since v1

- **Work at Height Safety** (Roboflow v1, CC BY 4.0) added: images with a harness only, minus 862 mirror-padded images. Harness training instances 143 → 2,619; training set 5,537 → 7,475 images.
- **E2 trained with 3 seeds** (0 / 1 / 2) and reported as mean ± standard deviation.
- Input size stays at 640 (a 960 trial did not help small objects); model stays YOLO11s.

## Assets

| File | Model | sha256 |
|---|---|---|
| `e2_best.pt` | **E2**, seed 0 — Ultralytics default augmentation (used by the demo) | `46b23c12aadf53303abd218926730eece36222fb77a1d3f97f12ed04909686d5` |
| `e1_best.pt` | E1 — all built-in augmentation off (experimental control) | `cb63156ed0a77a265a2c701360377c1c33229e765c17441f894b6c6ef73bf82d` |
| `e2_s1_best.pt` | E2, seed 1 | `b8f2e34d0000fcd34d14cbd5c0744c6d36f68897c36a564c9f759c06cabea8c4` |
| `e2_s2_best.pt` | E2, seed 2 | `3156f1e1d3daabc263b580315032c6c5704087353cb1b200abfdfd5abdf030fc` |

Classes: `person, helmet, no_helmet, vest, no_vest, harness, machinery, vehicle` (see `configs/taxonomy.yaml`).

## Use

```bash
conda env create -f environment.yml && conda activate telecomsafe
python -m telecomsafe.weights          # downloads all four files and checks sha256 (or: python -m telecomsafe.weights e2)
start_demo.bat                          # Windows; or: python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt --open
```

## Results (validation split, 747 images)

| Model | Seeds | mAP50 | mAP50-95 | Precision | Recall |
|---|---|---|---|---|---|
| E1 | 1 | 0.596 | 0.326 | 0.718 | 0.560 |
| E2 | 3 | 0.737 ± 0.007 | 0.451 ± 0.002 | 0.787 ± 0.013 | 0.685 ± 0.014 |

The validation split comes from the same sources as the training data, so these numbers are optimistic; they are not comparable with v1, whose validation split was composed differently. The telecom-specific test set (TelecomEval) is being annotated. Weakest classes: vehicle (0.40) and no_helmet (0.42); harness reaches 0.81 on validation but is still detected with low confidence in telecom tower and pole scenes. Details: `reports/phase1/README-EN.md`.

## Training

- YOLO11s, 640 px, `configs/baseline.yaml`; up to 100 epochs with patience 20. E1 stopped early at epoch 41; the E2 seeds ended at epochs 89, 79 and 100.
- 7,475 images after perceptual-hash de-duplication from Construction Site Safety (Roboflow v30), Ultralytics Construction-PPE, body_harness, construction safety v2, Work at Height Safety (v1, harness subset) and APD; missing classes filled with teacher pseudo-labels (18.7% of boxes). Sources and licences: `data/README-EN.md`.

## Licences

- Weights are trained with Ultralytics YOLO and are released under **AGPL-3.0**.
- The training data is **not** included. Public datasets can be re-downloaded with `python -m telecomsafe.data.download`; APD is private data shared with the team and is not redistributed.
