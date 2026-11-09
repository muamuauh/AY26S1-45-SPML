# TelecomSafe Phase 2: E3 (generative augmentation)

Phase 2 models (2026-11-07): the phase 1 baseline E2 retrained on its real training images plus **TelecomSynth**, 1,724 generated images for the five classes the baseline detects worst on telecom sites. Everything except the training data is identical to E2: the same `configs/baseline.yaml` (YOLO11s, 640 px, up to 100 epochs, patience 20, batch 16) and the same three seeds.

## Assets

| File | Model | sha256 |
|---|---|---|
| `e3_best.pt` | **E3**, seed 0 | `c76630f011d60f2ea2de1bf329a3ddf5d91487a07ceb12e9855e25fbf2421a49` |
| `e3_s1_best.pt` | E3, seed 1 | `3ad4dccb0fbcd8e0d8abac1cdb5e052e832cc07bce04749b534fb6eb312512e2` |
| `e3_s2_best.pt` | E3, seed 2 | `6c72d239156c2eace0b0d68d9a1acde1a43fd21e0b817bdd0e588ed0d79729d9` |

Classes: `person, helmet, no_helmet, vest, no_vest, harness, machinery, vehicle` (see `configs/taxonomy.yaml`). The baseline weights E1 and E2 are in the [`phase1-baseline-v2`](https://github.com/muamuauh/AY26S1-45-SPML/releases/tag/phase1-baseline-v2) release.

## Use

```bash
conda env create -f environment.yml && conda activate telecomsafe
python -m telecomsafe.weights e3 e3_s1 e3_s2     # downloads the three files and checks sha256
python -m telecomsafe.demo.app --weights runs/phase1/e3/weights/best.pt --open
```

## Results on TelecomEval v2 (mAP50, %)

TelecomEval is a frozen test set of 222 telecom and power-line work images. Real telecom photos are the headline subset; generated test images are reported for reference only. E2 and E3 are the mean ± standard deviation of three seeds.

| Subset | Images | E2 | E3 | E3 − E2 |
|---|---|---|---|---|
| **Real photos, telecom work** | 77 | 44.2 ± 4.0 | **50.1 ± 0.9** | **+5.9** |
| Real photos, power-line work | 47 | 29.0 ± 1.0 | 40.2 ± 0.2 | +11.2 |
| Real photos, all | 124 | 37.0 ± 2.7 | 45.4 ± 0.6 | +8.4 |
| Generated images | 98 | 54.2 ± 1.0 | 73.5 ± 1.1 | +19.3 |

Every E3 seed scores above every E2 seed on real telecom photos. On real photos, the five weak classes improve: `no_helmet` +13.2, `vehicle` +12.1, `no_vest` +11.1, `machinery` +6.8 and `harness` +5.6 points. On the validation split (same sources as training), E3 reaches 74.6 ± 0.1% against E2's 73.7 ± 0.7%. Details: `docs/results/phase2/README-EN.md`.

## Training data

- **Real:** the 6,728 training images of the phase 1 baseline (six public datasets; see `docs/datasets/README-EN.md`).
- **TelecomSynth (1,724 generated images):** `harness` 380, `machinery` 350, `no_vest` 394, `no_helmet` 300 and `vehicle` 300, each labelled with all eight classes. Images were generated with commercial image models and labelled either by hand or by a hybrid pipeline (detector boxes, vision-language model classes, human screening); every set was checked on intake. See `docs/guides/Phase2-Synth-Task-EN.md`.
- The E3 runs stopped at epochs 98, 88 and 88.

## Licences

- Weights are trained with Ultralytics YOLO and are released under **AGPL-3.0**.
- The training data is **not** included. Public datasets can be re-downloaded with `python -m telecomsafe.data.download`; APD (private, internal training only) and TelecomSynth are not redistributed.
