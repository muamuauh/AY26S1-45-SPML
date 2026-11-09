# TelecomSafe

**A framework for telecommunication construction safety enhancement**
EE6008 Collaborative Research and Development Project · AY26S1-45-SPML · Nanyang Technological University

TelecomSafe detects workers, personal protective equipment (PPE) and machinery on telecom construction sites, and turns the detections into a site-level risk level. Because no public labelled dataset exists for telecom construction safety, the project trains on public building-site data and then adds **generated images aimed at the classes the detector gets wrong** on real telecom photos.

## Results at a glance

The detector is YOLO11s with eight classes: `person`, `helmet`, `no_helmet`, `vest`, `no_vest`, `harness`, `machinery` and `vehicle`. All models are evaluated on **TelecomEval**, a frozen test set of 222 telecom and power-line work images. The headline metric is mAP50 on its 77 real telecom photos.

| Experiment | Training data | mAP50, real telecom photos | mAP50, all real photos |
|---|---|---|---|
| E1 | Public data, no augmentation | 32.9% | 30.2% |
| E2 (baseline) | Public data, default augmentation | 44.2 ± 4.0% | 37.0 ± 2.7% |
| **E3** | **E2 + 1,724 generated images (TelecomSynth)** | **50.1 ± 0.9%** | **45.4 ± 0.6%** |

E2 and E3 use the same frozen configuration and three random seeds each (mean ± standard deviation). Every E3 seed beats every E2 seed, and all five weak classes improve on real photos. Full results: [docs/results/phase2/README-EN.md](docs/results/phase2/README-EN.md).

## How it works

1. **Phase 1, baseline.** Six public datasets are mapped to the eight classes, cleaned, de-duplicated and completed with teacher pseudo-labels. YOLO11s is trained without augmentation (E1) and with default augmentation (E2), and the configuration is frozen. A rule engine turns detections into a risk level (no helmet, no hi-vis vest, person near operating machinery), and a Gradio demo shows the result.
2. **TelecomEval.** Team members contributed labelled telecom photos and generated images. The set is frozen by a SHA-256 manifest, and real and generated images are reported separately.
3. **Phase 2, TelecomSynth.** The baseline's five weakest classes on TelecomEval (`no_helmet`, `vehicle`, `machinery`, `harness`, `no_vest`) each got 300–400 generated images. Images are labelled with a hybrid pipeline: detectors draw the boxes and a vision-language model decides the classes. Every submission is checked on intake.
4. **E3.** The detector is retrained on real + generated images with the baseline's configuration unchanged, and compared with E2 on TelecomEval.

## Repository layout

| Path | Contents |
|---|---|
| [`telecomsafe/data/`](telecomsafe/data/) | Dataset download and build, pseudo-labels, TelecomEval collection, screening, contribution checks and freezing, TelecomSynth generation, automatic labelling and intake |
| [`telecomsafe/gen/`](telecomsafe/gen/) | Phase 2 pre-study: SDXL inpainting routes, scene transfer, quality gates, human rating page |
| [`telecomsafe/judge/`](telecomsafe/judge/) | Rule-based risk judgement |
| [`telecomsafe/demo/`](telecomsafe/demo/) | Gradio demo |
| [`telecomsafe/train.py`](telecomsafe/train.py), [`evaluate.py`](telecomsafe/evaluate.py) | Training (E1, E2, E3 with seeds) and evaluation by TelecomEval subset |
| [`configs/`](configs/) | Class taxonomy, dataset registry, frozen baseline configuration, rules, released weights |
| [`splits/`](splits/) | TelecomEval frozen manifest (SHA-256 of every image and label) |
| [`tests/`](tests/) | Unit tests (no GPU or data needed) |
| [`docs/`](docs/) | Plans, guides, dataset catalogue, results and release notes ([index](docs/README.md)) |

## Getting started

```bash
conda env create -f environment.yml && conda activate telecomsafe
pytest                                   # unit tests, no GPU or data needed
```

**Demo.** On Windows, double-click `start_demo.bat`; it downloads the released weights (SHA-256 checked) and opens http://127.0.0.1:7860. On any system:

```bash
python -m telecomsafe.weights            # download the released baseline weights
python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt
```

## Reproducing the experiments

Step-by-step instructions, expected outputs and troubleshooting are in the [Phase 1 Training Guide](docs/guides/08-Phase1-Training-Guide-EN.md).

```bash
cp .env.example .env                                     # add your own Kaggle / Roboflow keys (never committed)
python -m telecomsafe.data.download                      # public datasets into data/raw/
python -m telecomsafe.data.build                         # merged YOLO dataset in data/processed/yolo/
python -m telecomsafe.train --exp e1                     # E1: no augmentation
python -m telecomsafe.train --exp e2 --seed 0 --name e2  # E2: configs/baseline.yaml (seeds 0, 1, 2)

python -m telecomsafe.data.freeze_eval --check           # TelecomEval unchanged?
python -m telecomsafe.data.synth check <folder> --target harness   # check a TelecomSynth submission
python -m telecomsafe.data.synth dataset                 # E3 training list: real + TelecomSynth
python -m telecomsafe.train --exp e3 --seed 0 --name e3  # E3 (seeds 0, 1, 2)
python -m telecomsafe.evaluate --exps e2 e2_s1 e2_s2 e3 e3_s1 e3_s2 --out docs/results/phase2/telecom_eval
```

Generating TelecomSynth images needs an image API and a vision-language model API (see `.env.example`):

```bash
python -m telecomsafe.data.generate_synth harness --dry-run    # prompt bank and cost estimate
python -m telecomsafe.data.generate_synth harness --n 450 --workers 4
python -m telecomsafe.data.autolabel <folder>                   # detector boxes + VLM classes
```

## Data and models

The repository holds code, configuration and reports only.

| Content | Where |
|---|---|
| Baseline weights (E1, E2 and two more E2 seeds) | GitHub release [`phase1-baseline-v2`](https://github.com/muamuauh/AY26S1-45-SPML/releases/tag/phase1-baseline-v2); `python -m telecomsafe.weights` |
| Phase 2 weights (E3, three seeds) | GitHub release [`phase2-e3`](https://github.com/muamuauh/AY26S1-45-SPML/releases/tag/phase2-e3); `python -m telecomsafe.weights e3 e3_s1 e3_s2` |
| Public datasets | Their original pages; versions pinned in `configs/sources.yaml`, catalogue in [docs/datasets/README-EN.md](docs/datasets/README-EN.md) |
| TelecomEval, TelecomSynth and a private dataset (APD) | Team shared folder only. APD is private data shared with the team for internal training; it must not be committed or redistributed |

## Documentation

- [Phase 1 results](docs/results/phase1/README-EN.md) and [phase 2 results](docs/results/phase2/README-EN.md)
- [Phase 1 Training Guide](docs/guides/08-Phase1-Training-Guide-EN.md), [TelecomEval contribution guide](docs/guides/TelecomEval-Contribution-EN.md), [phase 2 TelecomSynth task guide](docs/guides/Phase2-Synth-Task-EN.md)
- Planning documents: [requirements](docs/plan/00-Requirements-Analysis-EN.md), [technical plan](docs/plan/01-Technical-Plan-and-Milestones-EN.md), [datasets and models](docs/plan/02-Datasets-and-Pretrained-Models-EN.md), [generative augmentation design](docs/plan/03-Generative-Augmentation-Pipeline-EN.md), [literature survey](docs/plan/04-Literature-Survey-EN.md), [roadmap](docs/plan/05-Technological-Roadmap-EN.md), [teamwork](docs/plan/06-Teamwork-Allocation-EN.md), [charter](docs/plan/07-Project-Charter-EN.md)
- [Milestones and scope changes](docs/status/milestones-EN.md)

## Team

Supervisor: Shuping Dang. Students: Pandey Sneha, Guo Jiaqi, Lin Yuxuan, Lu Hancheng, Meng Xiangyu.

## Licences

Code dependencies include Ultralytics YOLO (AGPL-3.0). Each dataset keeps its own licence, recorded in [docs/datasets/README-EN.md](docs/datasets/README-EN.md); TelecomEval records the source and licence of every image.
