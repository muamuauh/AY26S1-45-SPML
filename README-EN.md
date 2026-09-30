# AY26S1-45-SPML — TelecomSafe

**A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects**

> 中文版：[README.md](README.md)

---

## Overview

Safety risks at telecommunication construction sites come from uneven terrain, improperly operated machinery, poorly stored materials, missing PPE and unsafe worker behaviour. Deep-learning computer vision can recognise these risks efficiently, but is held back by the **scarcity and limited diversity of labelled, sector-specific images**.

TelecomSafe fills the data gap with **training data synthesised by generative AI**, and combines deep-learning image processing with information fusion to appraise construction risk across four dimensions: **terrain, machinery, materials and workers**.

---

## Documentation

Full documentation lives in **[docs/](docs/)**, available in Chinese and English.

| # | English | 中文版 |
|---|---------|--------|
| 00 | [Requirements Analysis](docs/00-Requirements-Analysis-EN.md) | [项目需求分析](docs/00-项目需求分析-CN.md) |
| 01 | [Technical Plan & Milestones](docs/01-Technical-Plan-and-Milestones-EN.md) | [技术方案与里程碑](docs/01-技术方案与里程碑-CN.md) |
| 02 | [Datasets & Pretrained Models](docs/02-Datasets-and-Pretrained-Models-EN.md) | [数据集与预训练模型调研](docs/02-数据集与预训练模型调研-CN.md) |
| 03 | [Generative Augmentation Pipeline](docs/03-Generative-Augmentation-Pipeline-EN.md) | [生成式数据增广 Pipeline 设计](docs/03-生成式数据增广Pipeline设计-CN.md) |
| 04 | [Literature Survey](docs/04-Literature-Survey-EN.md) | [文献综述](docs/04-文献综述-CN.md) |
| 05 | [Technological Roadmap](docs/05-Technological-Roadmap-EN.md) | [技术路线图](docs/05-技术路线图-CN.md) |
| 06 | [Teamwork Allocation](docs/06-Teamwork-Allocation-EN.md) | [团队分工](docs/06-团队分工-CN.md) |
| 07 | [Project Charter](docs/07-Project-Charter-EN.md) | [项目章程](docs/07-项目章程-CN.md) |
| 08 | [Phase 1 Training Guide](docs/08-Phase1-Training-Guide-EN.md) | [阶段一训练复现指南](docs/08-阶段一训练复现指南-CN.md) |

→ Index and reading paths: [docs/README.md](docs/README.md)

**Official templates** — [`template/`](template/)
`EE6008_Project_Charter_Template.docx` (project charter) ｜ `EE6008-Project ReportTemplate.docx` (project report)
Document 07 follows the Charter template; documents 01 §7 and 04 §9 are calibrated to the Report template.

---

## Phase 1 Code

Full reproduction steps, the expected output of each step and troubleshooting are in the **[Phase 1 Training Guide](docs/08-Phase1-Training-Guide-EN.md)**.

```bash
conda env create -f environment.yml && conda activate telecomsafe
pytest                                               # unit tests; no GPU or data needed

cp .env.example .env                                 # fill in Kaggle / Roboflow API keys (.env is not committed)
python -m telecomsafe.data.download --list           # dataset download status
python -m telecomsafe.data.download                  # download the scriptable datasets into data/raw/
python -m telecomsafe.data.catalog                   # generate the dataset catalogue data/README(-EN).md
python -m telecomsafe.data.collect_open              # search TelecomEval candidates (open licences, attribution recorded)
python -m telecomsafe.data.labelstudio serve         # start the annotation tool (account in .env); push / pull in another terminal
python -m telecomsafe.data.build --dry-run           # mapping / coverage matrix / de-duplication statistics
python -m telecomsafe.data.build                     # write data/processed/yolo/
python -m telecomsafe.data.freeze_eval --create      # freeze TelecomEval (read-only afterwards)
python -m telecomsafe.train --exp e1                 # E1: built-in augmentation off
python -m telecomsafe.train --exp e2                 # E2: configs/baseline.yaml
python -m telecomsafe.evaluate                       # reports and charts → reports/phase1/
python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt
```

**One-click Demo on Windows**: double-click `start_demo.bat` in the repository root; the browser opens when it is ready (http://127.0.0.1:7860). Close the window to stop it.

| Directory | Contents |
|---|---|
| [`configs/`](configs/) | Class taxonomy, dataset registry, baseline training configuration, rule library |
| [`telecomsafe/`](telecomsafe/) | Data (download, build, pseudo-labels, freezing), training, evaluation, rule judgement, Demo |
| [`data/README-EN.md`](data/README-EN.md) | Source, link, licence and size of every dataset (generated) |
| [`reports/phase1/`](reports/phase1/README-EN.md) | Phase 1 results and experiments |
| [`progress/`](progress/milestones-EN.md) | Milestones planned vs actual, scope changes |

### Data & Models

The repository holds only code, configuration and reports; data and weights live in three places depending on whether they can be re-downloaded and whether they may be public:

| Content | Where | How to get it |
|---|---|---|
| **Model weights** (E1 / E2, ~19 MB each) | GitHub Release [`phase1-baseline-v1`](https://github.com/muamuauh/AY26S1-45-SPML/releases/tag/phase1-baseline-v1) | `python -m telecomsafe.weights` (verifies sha256); `start_demo.bat` downloads them automatically if missing |
| **Public datasets** (Construction Site Safety v30, Construction-PPE, body_harness, construction safety v2) | Their original release pages | Put your own Kaggle / Roboflow keys in `.env` and run `python -m telecomsafe.data.download`; versions are pinned in `configs/sources.yaml` |
| **Data that cannot be re-downloaded** (APD, TelecomEval candidates and licence manifest, later annotations) | Team shared folder (university OneDrive / Teams, **team members and supervisor only**) | Extract as described in the shared folder's `README-EN.md` |

> ⚠️ This repository is **public**: never commit private data such as APD, or the keys in `.env`, and never put them in a Release.
> Dataset sources, licences and actual counts: [`data/README-EN.md`](data/README-EN.md).

---

## Status

🚧 **Phase 1 · Baseline** — ① Risk Taxonomy and ② public data curation were completed offline; ③ baseline training is under way.

> 🔄 **Flow change (2026-09-28, v3.0)**: on the supervisor's advice the project now has **two phases**:
> **Phase 1** uses only the curated public data to build a baseline perception model + rule-based risk judgement + a small Demo (target W7);
> **Phase 2** then adds generative augmentation and compares against the baseline on the same test set and training configuration.
> See [docs/05](docs/05-Technological-Roadmap-EN.md).

> 🔄 **Data strategy change (2026-08-24)**: after discussion with the supervisor, **all field data collection is cancelled** (safety risk and cost too high) in favour of a four-tier public-source strategy:
> **T1** academic datasets → **T2** community dataset platforms (Roboflow Universe / Kaggle) → **T3** curation from openly licensed image repositories (Wikimedia Commons / Openverse) → **T4** generative synthesis.
> See [docs/02](docs/02-Datasets-and-Pretrained-Models-EN.md).

### Open items

**Team and administration**
- [ ] Hold the phase 1 kick-off meeting: confirm roles A–E and **elect a team lead** (if not done yet); agenda in [docs/06 §10](docs/06-Teamwork-Allocation-EN.md)
- [ ] Check the Project No. (presumably 45), academic year / semester and supervisor's name, fill them into [docs/07](docs/07-Project-Charter-EN.md) and copy into the Word template (pre-submission checklist attached)
- [ ] Confirm the project length (12 / 16 weeks), the real date of semester W1 and available compute
- [ ] Ask the supervisor whether a team project video is required (mentioned in the report template's appendix)

**Phase 1 (W4–W7)**
- [x] Risk Taxonomy (done offline) — draft transcribed into `configs/taxonomy.yaml`, to be checked against the final offline version
- [x] Dataset list and class mapping — `configs/sources.yaml`, catalogue in `data/README-EN.md`
- [ ] ⏸ **TelecomEval annotation and freezing (deferred until Demo v1 is done)** — 31 candidates pre-labelled and imported into Label Studio; how to resume: [progress/milestones-EN.md](progress/milestones-EN.md#deferred)
- [x] Baseline training (E1 / E2) — validation mAP50 0.611 / 0.756, see [reports/phase1/](reports/phase1/README-EN.md); `configs/baseline.yaml` is frozen after TGB
- [x] Rule-based risk judgement + Gradio Demo v1 — `python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt`
- [ ] TGB meeting (end of W7): prepare slides and a Demo recording

**Throughout**
- [x] `progress/` directory records **actual** milestone dates and scope changes — add a row for every milestone reached (see [docs/01 §7.4](docs/01-Technical-Plan-and-Milestones-EN.md))
- [ ] Verify literature citations (see the verification table in [docs/04 §8](docs/04-Literature-Survey-EN.md))

---

## ⚠️ Note

Some bibliographic details in `docs/04` were gathered from search metadata. **Verify each entry against the status table at the end before formal citation.**
