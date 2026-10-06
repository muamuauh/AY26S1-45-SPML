# TelecomSafe Phase 1 Training Reproduction Guide

> Document version: v2.0 ｜ Written: 2026-09-29 ｜ Revised: 2026-10-06 (baseline v2: Work at Height added, E2 run with 3 seeds)
> Chinese counterpart: [08-阶段一训练复现指南-CN.md](08-阶段一训练复现指南-CN.md)
> Audience: team members reproducing the phase 1 results from scratch, or anyone retraining later
> Goal: obtain the E1 / E2 weights and every report and chart under `reports/phase1/`, and start the Demo
> Results are discussed in [reports/phase1/README-EN.md](../reports/phase1/README-EN.md). If you only want the released models and no training, go straight to [Section 9](#9-using-the-released-models-only).

---

## 0. Overview

**Pipeline**: train a teacher on the two datasets with the widest class coverage, let it pseudo-label the classes the other datasets lack, merge everything into the full training set, then train and evaluate E1 / E2.

```
Download → build teacher set → train teacher → pseudo-label → build full set → train E1 → train E2 × 3 seeds → evaluate → Demo
(~25 min)      (<1 min)          (~12 min)      (~5 min)        (~2 min)       (~35 min)  (~3.7 h)           (~3 min)
```

Timings are for an RTX 4070 SUPER (12 GB); the GPU steps take about 4.5 hours in total, or about 2 hours with a single E2 seed.

**Reference results** (baseline v2, 747 validation images; use them to check that your run reproduced correctly):

| Experiment | mAP50 | mAP50-95 | Epochs |
|---|---|---|---|
| E1 (augmentation off, seed 0) | 0.596 | 0.326 | early stop at epoch 41 |
| E2 (default augmentation, seeds 0 / 1 / 2) | 0.737 ± 0.007 | 0.451 ± 0.002 | ended at epochs 89 / 79 / 100 |

On the same machine with the same software versions a given seed should reproduce exactly; a different GPU, driver or library version may differ by about ±0.01. The v1 results (2026-09-29, without Work at Height) are in `reports/phase1/v1/`.

**⚠️ Three hard constraints** (breaking any of them makes results incomparable with ours):
1. **Do not change `configs/baseline.yaml`.** Phase 2's E3 must use the same configuration and change only the training data.
2. **Construction Site Safety must be Roboflow version 30**, not the Kaggle mirror. The Kaggle training split consists entirely of mosaic-augmented composites; see the scope-change log in [progress/milestones-EN.md](../progress/milestones-EN.md).
3. **Do not modify TelecomEval once frozen.** After it is built, every formal evaluation uses it.

---

## 1. Environment

**Hardware**: an NVIDIA GPU with ≥ 8 GB of memory (12 GB runs the default batch of 16) and a driver supporting CUDA 13. Leave at least 3 GB of disk for data and training output.

**Create the environment** (in Anaconda Prompt or PowerShell, from the repository root):

```powershell
conda env create -f environment.yml
conda activate telecomsafe
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
pytest            # unit tests, ~2 s; no GPU or data needed
```

The third line should print `True` and your GPU's name. Every command in this guide assumes you are **in the repository root with the `telecomsafe` environment active**.

Versions used for the phase 1 results: Python 3.12, PyTorch 2.14.0+cu130, Ultralytics 8.4.164.

> In Git Bash `conda` is not on the PATH: use Anaconda Prompt instead, or call the environment's Python directly, e.g. `~/.conda/envs/telecomsafe/python.exe -m telecomsafe.train ...`.

---

## 2. API keys

```powershell
copy .env.example .env      # then open .env in an editor and fill it in
```

| Variable | Where to get it | Used for |
|---|---|---|
| `KAGGLE_API_TOKEN` | kaggle.com → Settings → API → Generate New Token | Phase 1 does not actually use Kaggle (see Section 3); may be left empty |
| `ROBOFLOW_API_KEY` | app.roboflow.com → Settings → API Keys | **Required**: downloads the 4 Roboflow datasets |
| `LABEL_STUDIO_*` | choose your own | Only for annotating TelecomEval |

`.env` is in `.gitignore`; **never commit it**.

---

## 3. Data

### 3.1 Automatic download

```powershell
python -m telecomsafe.data.download --list     # show which datasets are present locally
python -m telecomsafe.data.download            # download every enabled, scriptable dataset
```

### 3.2 Placing APD by hand

APD is private data shared with us and cannot be downloaded publicly. Get `APD.v1i.yolov8.zip` from the **team-only shared folder** and extract it to `data/raw/apd/`; the directory should then contain `train/`, `valid/`, `test/` and `data.yaml` directly.

### 3.3 Check

Run `python -m telecomsafe.data.download --list`; all six below should show ✓:

| Dataset | Local directory | Raw images | Source |
|---|---|---|---|
| Construction Site Safety v30 | `data/raw/construction_site_safety/` | 717 | Roboflow (automatic) |
| Ultralytics Construction-PPE | `data/raw/construction_ppe/` | 1,416 | Ultralytics (automatic) |
| body_harness v5 | `data/raw/body_harness/` | 796 | Roboflow (automatic) |
| construction safety v2 | `data/raw/construction_safety_v2/` | 1,206 | Roboflow (automatic) |
| Work at Height Safety v1 | `data/raw/work_at_height/` | 12,712 (~760 MB) | Roboflow (automatic) |
| APD | `data/raw/apd/` | 2,300 | team share (manual) |

Only Work at Height images that contain a harness are used (`filter: has:harness` in `sources.yaml`), minus 862 mirror-padded images listed in [`configs/exclude/work_at_height.txt`](../configs/exclude/work_at_height.txt); the build applies both automatically.

Then run `python -m telecomsafe.data.catalog` to regenerate [data/README-EN.md](../data/README-EN.md); its "Local raw images" column should match the table above. Each dataset's source, licence and class mapping are recorded in `configs/sources.yaml`.

---

## 4. Build the teacher set

The teacher is trained only on the two datasets that fully annotate people. Once it knows every class, it fills in the classes the other datasets did not annotate.

```powershell
python -m telecomsafe.data.build --sources construction_site_safety construction_ppe --no-eval --no-pseudo --out data/processed/teacher
```

**Expected output**: `train: 1802 images`, `val: 200 images`, `Removed: {'duplicate': 131, ...}`

---

## 5. Train the teacher

```powershell
python -m telecomsafe.train --exp teacher --data data/processed/teacher/dataset.yaml --epochs 50
```

- About 12 minutes; validation mAP50 ≈ **0.733** at the end
- Weights are saved to `runs/phase1/teacher/weights/best.pt`

---

## 6. Pseudo-labels

```powershell
python -m telecomsafe.data.pseudo_label --weights runs/phase1/teacher/weights/best.pt
```

For each dataset, only the classes it **did not annotate** are filled in, only at confidence ≥ 0.5, and real annotations are never overwritten. Output goes to `data/interim/pseudo/<dataset>.json`.

**Expected pseudo-label counts**:

| Dataset | Boxes added | Main classes added |
|---|---|---|
| apd | 3,892 | person |
| body_harness | 1,743 | helmet, vest |
| construction_safety_v2 | 1,565 | vest |
| work_at_height | 11,297 | vest, no_vest, no_helmet, vehicle (all 12,712 images are labelled; the build uses only those with a harness) |
| construction_ppe | 0 | the teacher saw these images in training and adds none of the missing classes — a known limitation |
| construction_site_safety | 0 | only harness is missing, and the teacher does not know that class |

---

## 7. Build the full training set

```powershell
python -m telecomsafe.data.build --dry-run    # statistics only, no files written
python -m telecomsafe.data.build              # writes data/processed/yolo/
```

This step maps classes, merges pseudo-labels, applies filters and exclusion lists, removes duplicates by perceptual hash (including against the chosen TelecomEval images), and splits train / validation per source (90 / 10, fixed seed).

**Expected output**: `train: 6728 images`, `val: 747 images`, `Removed: {'eval_leak': 0, 'duplicate': 1059}`; it also writes `reports/phase1/dataset_stats.csv` and `coverage.csv`.

Until TelecomEval is built, the command warns "no test split"; that is expected.

Optional: `python -m telecomsafe.data.audit` draws the boxes on 50 random images per dataset into `runs/audit/`, for checking by eye that the mapping is right.

---

## 8. Train E1 / E2 and evaluate

### 8.1 Smoke test (recommended first, ~1 minute)

```powershell
python -m telecomsafe.train --exp e1 --name smoke --epochs 1 --fraction 0.05
```

If it finishes and creates `runs/phase1/smoke/`, the environment and data are fine. Delete `runs/phase1/smoke/` afterwards.

### 8.2 E1: all built-in augmentation off

```powershell
python -m telecomsafe.train --exp e1
```

- About 35 minutes; our run stopped early at epoch 41 (`patience 20`)
- Check: `mosaic`, `fliplr`, `hsv_h` and the other augmentation parameters in `runs/phase1/e1/args.yaml` should all be `0.0`

### 8.3 E2: Ultralytics default augmentation

```powershell
python -m telecomsafe.train --exp e2                          # seed 0
python -m telecomsafe.train --exp e2 --seed 1 --name e2_s1
python -m telecomsafe.train --exp e2 --seed 2 --name e2_s2
```

- About 1.1–1.4 hours per seed; our runs ended at epochs 89, 79 and 100
- Both experiments take their configuration from `configs/baseline.yaml` (YOLO11s, 640 px, batch 16); the only difference is that E1 turns augmentation off. `--seed` changes only the random seed, to estimate run-to-run variation (reported as mean ± std)

### 8.4 Optional: YOLOv8s comparison (done on v1 data)

```powershell
python -m telecomsafe.train --exp e2 --model yolov8s.pt --name e2_yolov8s
```

Same data and configuration as E2 with only the architecture changed, to justify the model choice. It was run on the v1 data, kept as `runs/phase1/v1_e2_yolov8s`, and not repeated for baseline v2.

### 8.5 Optional: YOLO11m comparison and input-size trial

```powershell
python -m telecomsafe.train --exp e2 --model yolo11m.pt --name e2_yolo11m
```

Again only the model changes, to justify the model size (v1 data, `runs/phase1/v1_e2_yolo11m`). Before freezing v2 an input-size trial was also run:

```powershell
python -m telecomsafe.train --exp e2 --imgsz 960 --name e2_960
```

About 2.3 hours and ~9.7 GB of GPU memory (batch 16). Results and conclusions for both are in the results summary; neither was adopted.

### 8.6 Evaluation

```powershell
# Before TelecomEval exists: evaluate on the validation split (development reference only)
python -m telecomsafe.evaluate --split val --skip-check      # e1, e2, e2_s1, e2_s2 by default
python -m telecomsafe.evaluate --exps e2 e2_960 --split val --skip-check --out <folder>   # trials go elsewhere

# After TelecomEval is frozen: formal evaluation (first checks that TelecomEval is unchanged)
python -m telecomsafe.evaluate
```

**Outputs** (all in `reports/phase1/`):

| File | Contents |
|---|---|
| `<run>_metrics.csv` | mAP50, mAP50-95, precision, recall of each run |
| `summary.csv` | per-experiment summary; runs named `<exp>_s<k>` count as further seeds of that experiment, giving mean and standard deviation |
| `per_class_ap.csv` / `per_class_ap.png` | per-class AP table and comparison bar chart (means over seeds, with standard-deviation error bars) |
| `<exp>_confusion_matrix.png` | normalised confusion matrix |
| `class_distribution.png` | training-set instances per class |
| `weak_classes.md` | weak-class list. **Not overwritten if it exists**, because the "likely reasons" column is written by hand; add `--rewrite-weak-classes` to regenerate it |

The mAP on the last line of the training log (in v1, 0.605 for E1) differs slightly from the evaluation script (0.611) because the two validate with different batching. Reports always use the evaluation script's numbers.

### 8.7 Start the Demo

Double-click `start_demo.bat` in the repository root, or:

```powershell
python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt --open
```

The browser opens http://127.0.0.1:7860. The page includes 5 examples (`reports/phase1/demo_examples/`) with expected risk levels Low / Medium / High / Low / Low (the last one is a deliberately kept failure case).

---

## 9. Using the released models only

No data and no training needed:

```powershell
python -m telecomsafe.weights     # downloads the E1 / E2 weights from the GitHub Release and verifies sha256
start_demo.bat
```

---

## 10. Everything in one go

Once the data is in place (Section 3), these commands in order reproduce everything in about 4.5 hours (about 2 hours with seed 0 only):

```powershell
python -m telecomsafe.data.build --sources construction_site_safety construction_ppe --no-eval --no-pseudo --out data/processed/teacher
python -m telecomsafe.train --exp teacher --data data/processed/teacher/dataset.yaml --epochs 50
python -m telecomsafe.data.pseudo_label --weights runs/phase1/teacher/weights/best.pt
python -m telecomsafe.data.build
python -m telecomsafe.train --exp e1
python -m telecomsafe.train --exp e2
python -m telecomsafe.train --exp e2 --seed 1 --name e2_s1
python -m telecomsafe.train --exp e2 --seed 2 --name e2_s2
python -m telecomsafe.evaluate --split val --skip-check
```

Before rerunning, delete the old results in `runs/phase1/{teacher,e1,e2,e2_s1,e2_s2}`. The training script overwrites logs in a directory of the same name, but leftover weight files are easy to confuse.

---

## 11. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `CUDA out of memory` | Not enough GPU memory: add `--batch 8` when training. This changes the training conditions, so note it with the results |
| `torch.cuda.is_available()` is `False` | The CPU build of PyTorch is installed: `pip install --force-reinstall --no-deps torch torchvision --index-url https://download.pytorch.org/whl/cu130` |
| Build fails with `ConfigError: class_map ... does not declare` | The dataset has a class not registered in `configs/sources.yaml`: map it to a target class as the message says, or to `null` (drop) |
| `FileNotFoundError: [WinError 3]` | Windows path too long: the build already shortens output names; if it still happens, move the project to a shorter path |
| Encoding errors on symbols such as ✓ ≈ | `set PYTHONIOENCODING=utf-8` (PowerShell: `$env:PYTHONIOENCODING="utf-8"`) |
| Kaggle authentication fails | Check `KAGGLE_API_TOKEN` in `.env`; phase 1 does not depend on Kaggle, so this can be ignored |
| Roboflow download fails | Check `ROBOFLOW_API_KEY`; `configs/sources.yaml` pins the version numbers — do not change them to `null`, or you will get the latest version |
| Demo says port 7860 is in use | A Demo is already running: close the old window, or add `--port 7861` |
| Data loading hangs or keeps spawning processes | Windows multiprocessing: the training entry point handles it; in your own scripts that call training, put the code under `if __name__ == "__main__":` |

---

## 12. After TelecomEval is built

TelecomEval is being annotated; see [progress/milestones-EN.md](../progress/milestones-EN.md#deferred) for progress. Once it is annotated and frozen:

1. `python -m telecomsafe.data.build`: TelecomEval becomes the test split in `dataset.yaml`.
2. `python -m telecomsafe.evaluate`: formal evaluation of E1 and the 3 E2 seeds on TelecomEval.
3. Update `reports/phase1/README.md` and `weak_classes.md`.

The training set does **not** change: the build already de-duplicates against the chosen TelecomEval images (the telecom / near images kept in review in the licence manifest), so baseline v2 needs no retraining. `configs/baseline.yaml` was frozen on 2026-10-06 (tag `phase1-baseline-v2`).
