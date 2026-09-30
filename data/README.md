# 数据集说明 / Dataset Catalogue

> English version: [README-EN.md](README-EN.md)
> 本文件由 `python -m telecomsafe.data.catalog` 根据 `configs/sources.yaml` 自动生成，**请勿手动编辑**。
> 数据本身不入库（见 `.gitignore`），按下文的获取方式下载到 `data/raw/<名称>/`。

## 总览

| 数据集 | 用途 | 参与构建 | 计划规模 | 本地原始张数 | 构建后张数 | 许可 | 链接 |
|---|---|---|---|---|---|---|---|
| `construction_site_safety` Construction Site Safety (Roboflow Universe, version 30) | 训练 · A 核心 | 是 | 717 张（train 521 / valid 114 / test 82） | 717 | 683 | CC BY 4.0 | [主页](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety) |
| `construction_ppe` Ultralytics Construction-PPE | 训练 · A 核心 | 是 | 1,416 张（train 1,132 / val 143 / test 141） | 1,416 | 1319 | AGPL-3.0 | [主页](https://docs.ultralytics.com/datasets/detect/construction-ppe) |
| `body_harness` body_harness (Construction Images, Roboflow Universe) | 训练 · A 核心 | 是 | 796 张 | 796 | 154 | CC BY 4.0 | [主页](https://universe.roboflow.com/construction-images/body_harness) |
| `construction_workers_fyp` 3 Construction Workers (FYP, Roboflow Universe) | 训练 · B 补充 | 否 | 600 张 | 未下载 | — | CC BY 4.0 | [主页](https://universe.roboflow.com/fyp-h6hxz/3-construction-workers) |
| `apd` APD — 施工人员安全帽与反光衣检测（Roboflow 私有项目） | 训练 · B 补充 | 是 | 2,300 张（train 1,610 / valid 460 / test 230） | 2,300 | 2259 | 私有（Roboflow 工作区 fathorazi-nur-fajri/apd-8wyrt，他人分享）——仅限本项目内部训练，不再分发 | — |
| `construction_safety_v2` construction safety v2 (yun-pl2q1, Roboflow Universe) | 训练 · B 补充 | 是 | 1,206 张（train 997 / valid 119 / test 90） | 1,206 | 1122 | CC BY 4.0 | [主页](https://universe.roboflow.com/yun-pl2q1/construction-safety-ejqd8) |
| `shel5k` SHEL5K — Safety Helmet detection with Extended Labels | 训练 · B 补充 | 是 | 5,000 张 | 未下载 | — | CC BY 4.0 | [主页](https://data.mendeley.com/datasets/9rcv8mm682/4) |
| `chv` CHV — Color Helmet and Vest | 训练 · B 补充 | 是 | 1,330 张 | 未下载 | — | 未注明（按作者要求引用论文） | [主页](https://github.com/ZijianWang-ZW/PPE_detection) |
| `acid` ACID — Alberta Construction Image Dataset | 训练 · B 补充 | 否 | 10,000 张 | 未下载 | — | CC BY-NC 4.0（仅限非商业用途） | [主页](https://profsckang.wixsite.com/uofa-rlab/copy-of-r-lab-design) |
| `telecom_tower` Telecom Tower Object Detection (Roboflow Universe) | 训练 · 可选 | 否 | 128 张 | 未下载 | — | 以数据集页面为准 | [主页](https://universe.roboflow.com/object-detection-yolo-c8gsd/telecom-tower-object-detection) |
| `telecom_eval` TelecomEval — 电信施工场景真实测试集（自建） | 测试（TelecomEval） | 是 | ≥150 张（理想 200 张） | 未下载 | — | 逐图记录（CC0 / Public Domain / CC BY / CC BY-SA），见 licence_manifest.csv | — |

## 目标类别（阶段一）

| id | 类别 | 维度 | 含义 | 判定标准 |
|---|---|---|---|---|
| 0 | `person` | workers | 施工现场人员（完整人体框） | 人体可见部分超过一半即标注；被遮挡时按可见范围画框 |
| 1 | `helmet` | workers | 安全帽 | 只标佩戴在头上的安全帽；放在地上、拿在手里的不标 |
| 2 | `no_helmet` | workers | 未戴安全帽的头部 | 框住头部；戴普通帽子、头巾也算未戴安全帽 |
| 3 | `vest` | workers | 反光背心 / 高可视性工作服 | 框住穿着的反光衣上身部分 |
| 4 | `no_vest` | workers | 未穿反光衣的人员上身 | 框住未穿反光衣的躯干 |
| 5 | `harness` | workers | 全身式安全带（含胸带、腿带） | 框住穿在身上的安全带主体；仅挂在结构上的安全绳不标 |
| 6 | `machinery` | machinery | 工程机械（挖掘机、吊车、装载机、压路机、推土机、搅拌车、自卸车等） | 框住机械整体，包括伸出的臂架与铲斗 |
| 7 | `vehicle` | machinery | 普通车辆（轿车、皮卡、面包车、普通货车） | 非施工专用的车辆 |

## 各数据集详情

### `construction_site_safety` — Construction Site Safety (Roboflow Universe, version 30)

- **来源**：https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety
- **简介**：Roboflow 官方整理的工地安全数据集（version 30，未经增广的原始图像），包含安全帽 / 反光衣的正负类 （NO-Hardhat、NO-Safety Vest），以及人员、细分的工程机械与车辆。与本项目阶段一的目标类别重合度最高， 也是工程机械与车辆的唯一来源。
- **规模**：计划 717 张（train 521 / valid 114 / test 82） ｜ 本地原始 717 ｜ 构建后 683
- **格式 / 本地路径**：yolo ｜ `data/raw/construction_site_safety`
- **类别映射**：Hardhat→helmet, NO-Hardhat→no_helmet, Safety Vest→vest, NO-Safety Vest→no_vest, Person→person, Excavator→machinery, wheel loader→machinery, dump truck→machinery, machinery→machinery, SUV→vehicle, bus→vehicle, mini-van→vehicle, sedan→vehicle, semi→vehicle, trailer→vehicle, truck→vehicle, truck and trailer→vehicle, van→vehicle, vehicle→vehicle, Gloves→丢弃, Ladder→丢弃, Mask→丢弃, NO-Mask→丢弃, Safety Cone→丢弃, fire hydrant→丢弃
- **完整标注的目标类别**：person, helmet, no_helmet, vest, no_vest, machinery, vehicle（其余类别由 teacher 补伪标签）
- **许可**：CC BY 4.0
- **引用**：Construction Site Safety dataset (version 30), Roboflow Universe Projects, https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety
- **获取方式**：Roboflow API：workspace `roboflow-universe-projects` / project `construction-site-safety`（`python -m telecomsafe.data.download --only construction_site_safety`）
- **用途**：训练 · A 核心
- **备注**：核对（2026-09-29）：最初用的 Kaggle 镜像实为 Roboflow version 28，其训练集是 521 张原图各生成 5 个 增广版本（马赛克、cutout、裁剪、旋转等）得到的 2,605 张拼图——既让 E1 不再是"无增广"对照，也让 规则把不同子图里的人和机械误判为相邻。已换成未增广的 version 30（717 张）。

### `construction_ppe` — Ultralytics Construction-PPE

- **来源**：https://docs.ultralytics.com/datasets/detect/construction-ppe
- **简介**：Ultralytics 官方整理的施工 PPE 数据集，采集自真实工地，包含合规与不合规样本， 标注了安全帽、反光衣、手套、靴子、护目镜及其缺失状态。
- **规模**：计划 1,416 张（train 1,132 / val 143 / test 141） ｜ 本地原始 1,416 ｜ 构建后 1319
- **格式 / 本地路径**：yolo ｜ `data/raw/construction_ppe`
- **类别映射**：helmet→helmet, vest→vest, Person→person, no_helmet→no_helmet, gloves→丢弃, boots→丢弃, goggles→丢弃, none→丢弃, no_goggle→丢弃, no_gloves→丢弃, no_boots→丢弃
- **完整标注的目标类别**：person, helmet, no_helmet, vest（其余类别由 teacher 补伪标签）
- **许可**：AGPL-3.0
- **引用**：Ultralytics Construction-PPE dataset, https://docs.ultralytics.com/datasets/detect/construction-ppe
- **获取方式**：随 Ultralytics 的 `construction-ppe.yaml` 自动下载（`python -m telecomsafe.data.download --only construction_ppe`）
- **用途**：训练 · A 核心
- **备注**：没有 no_vest 与机械类别，由 teacher 补伪标签。下载后核对（2026-09-28）：1,416 张，类别顺序与 Ultralytics 官方 construction-ppe.yaml 一致；含同一视频的相邻帧（跨 train / test），构建时去重。

### `body_harness` — body_harness (Construction Images, Roboflow Universe)

- **来源**：https://universe.roboflow.com/construction-images/body_harness
- **简介**：796 张的施工人员安全带数据集，类别包含 safety harness 与 worker。
- **规模**：计划 796 张 ｜ 本地原始 796 ｜ 构建后 154
- **格式 / 本地路径**：yolo ｜ `data/raw/body_harness`
- **类别映射**：safety harness→harness, worker→person
- **完整标注的目标类别**：harness, person（其余类别由 teacher 补伪标签）
- **许可**：CC BY 4.0
- **引用**：body_harness dataset by Construction Images, Roboflow Universe, https://universe.roboflow.com/construction-images/body_harness
- **获取方式**：Roboflow API：workspace `construction-images` / project `body_harness`（`python -m telecomsafe.data.download --only body_harness`）
- **用途**：训练 · A 核心
- **备注**：下载后核对（2026-09-28）：version 5，796 张，标的是真实工地上穿戴的全身式安全带。 大量图片是同一视频的相邻帧，构建时去重；少数图中的人员漏标，由 teacher 补伪标签。

### `construction_workers_fyp` — 3 Construction Workers (FYP, Roboflow Universe)

- **来源**：https://universe.roboflow.com/fyp-h6hxz/3-construction-workers
- **简介**：600 张的施工人员数据集，包含安全带与未戴安全帽等类别。
- **规模**：计划 600 张 ｜ 本地原始 未下载 ｜ 构建后 —
- **格式 / 本地路径**：yolo ｜ `data/raw/construction_workers_fyp`
- **类别映射**：待填写（下载后按数据集自带的类别表补全）
- **完整标注的目标类别**：harness, no_helmet（其余类别由 teacher 补伪标签）
- **许可**：CC BY 4.0
- **引用**：3 Construction Workers dataset by FYP, Roboflow Universe, https://universe.roboflow.com/fyp-h6hxz/3-construction-workers
- **获取方式**：Roboflow API：workspace `fyp-h6hxz` / project `3-construction-workers`（`python -m telecomsafe.data.download --only construction_workers_fyp`）
- **用途**：训练 · B 补充（当前未参与构建）
- **备注**：类别表来自搜索结果，下载后核对。
- ⚠️ 类别表与规模尚未按下载后的实际文件核对

### `apd` — APD — 施工人员安全帽与反光衣检测（Roboflow 私有项目）

- **来源**：无公开页面（见获取方式）
- **简介**：2,300 张真实国内工地照片（多为新闻图片，带网站水印），标注安全帽、未戴安全帽、反光衣、 未穿反光衣；No_Vest 框住未穿反光衣的躯干，与判定标准一致。未穿反光衣样本（4,245 个）是 全部数据中最多的，是 no_vest 类的主要来源。没有人员类，由 teacher 补伪标签。
- **规模**：计划 2,300 张（train 1,610 / valid 460 / test 230） ｜ 本地原始 2,300 ｜ 构建后 2259
- **格式 / 本地路径**：yolo ｜ `data/raw/apd`
- **类别映射**：Helmet→helmet, No_Helmet→no_helmet, No_Vest→no_vest, Vest→vest
- **完整标注的目标类别**：helmet, no_helmet, vest, no_vest（其余类别由 teacher 补伪标签）
- **许可**：私有（Roboflow 工作区 fathorazi-nur-fajri/apd-8wyrt，他人分享）——仅限本项目内部训练，不再分发
- **引用**：APD dataset v1 (Roboflow private project fathorazi-nur-fajri/apd-8wyrt), shared with the project team; used for internal training only.
- **获取方式**：手动：从组内共享文件夹（OneDrive / Teams，仅限组员）获取 APD.v1i.yolov8.zip，解压到 data/raw/apd/。
- **用途**：训练 · B 补充
- **备注**：核对（2026-09-28）：标注质量好；与已有数据集近似重复仅 6 张，内部重复 30 张。 图片来自新闻网站（带水印），版权不属于数据集作者：报告中注明来源，不公开发布这些图片。

### `construction_safety_v2` — construction safety v2 (yun-pl2q1, Roboflow Universe)

- **来源**：https://universe.roboflow.com/yun-pl2q1/construction-safety-ejqd8
- **简介**：1,206 张安全帽检测图像，标注安全帽、未戴安全帽和人员。含较多图库 / 棚拍照片，真实工地比例较低； 主要补充安全帽与人员的多样性。图中可见的反光衣未标注，由 teacher 补伪标签。
- **规模**：计划 1,206 张（train 997 / valid 119 / test 90） ｜ 本地原始 1,206 ｜ 构建后 1122
- **格式 / 本地路径**：yolo ｜ `data/raw/construction_safety_v2`
- **类别映射**：helmet→helmet, no-helmet→no_helmet, person→person
- **完整标注的目标类别**：person, helmet, no_helmet（其余类别由 teacher 补伪标签）
- **许可**：CC BY 4.0
- **引用**：construction safety dataset v2 by yun-pl2q1, Roboflow Universe, https://universe.roboflow.com/yun-pl2q1/construction-safety-ejqd8
- **获取方式**：Roboflow API：workspace `yun-pl2q1` / project `construction-safety-ejqd8`（`python -m telecomsafe.data.download --only construction_safety_v2`）
- **用途**：训练 · B 补充
- **备注**：核对（2026-09-28）：由用户提供导出包（data/other_data/），与已有数据集近似重复 24 张，内部重复 15 张。

### `shel5k` — SHEL5K — Safety Helmet detection with Extended Labels

- **来源**：https://data.mendeley.com/datasets/9rcv8mm682/4
- **论文**：https://www.mdpi.com/1424-8220/22/6/2315
- **简介**：在 Safety Helmet Detection 数据集基础上扩展标注的 5,000 张安全帽数据集， 标注了安全帽、头部、戴 / 未戴安全帽的人和人脸。没有反光衣标注。
- **规模**：计划 5,000 张 ｜ 本地原始 未下载 ｜ 构建后 —
- **格式 / 本地路径**：voc ｜ `data/raw/shel5k`
- **类别映射**：helmet→helmet, head→no_helmet, person_with_helmet→person, person_no_helmet→person, head_with_helmet→丢弃, face→丢弃
- **完整标注的目标类别**：person, helmet, no_helmet（其余类别由 teacher 补伪标签）
- **许可**：CC BY 4.0
- **引用**：Otgonbold, M.-E. et al. SHEL5K: An Extended Dataset and Benchmarking for Safety Helmet Detection. Sensors 2022, 22(6), 2315.
- **获取方式**：手动：打开 Mendeley 页面下载全部文件，解压到 data/raw/shel5k/（保留 Annotations/ 与图片目录）。
- **用途**：训练 · B 补充
- **备注**：XML 中的类别名以实际文件为准，构建报错时按提示补全 class_map。
- ⚠️ 类别表与规模尚未按下载后的实际文件核对

### `chv` — CHV — Color Helmet and Vest

- **来源**：https://github.com/ZijianWang-ZW/PPE_detection
- **论文**：https://www.mdpi.com/1424-8220/21/10/3478
- **简介**：从约 1 万张网络与公开数据中精选的 1,330 张工地图像，标注了人员、反光衣和四种颜色的安全帽。
- **规模**：计划 1,330 张 ｜ 本地原始 未下载 ｜ 构建后 —
- **格式 / 本地路径**：yolo ｜ `data/raw/chv`
- **类别映射**：person→person, vest→vest, blue→helmet, red→helmet, white→helmet, yellow→helmet
- **完整标注的目标类别**：person, vest, helmet（其余类别由 teacher 补伪标签）
- **许可**：未注明（按作者要求引用论文）
- **引用**：Wang, Z.; Wu, Y.; Yang, L.; Thirunavukarasu, A.; Evison, C.; Zhao, Y. Fast Personal Protective Equipment Detection for Real Construction Sites Using Deep Learning Approaches. Sensors 2021, 21, 3478.
- **获取方式**：手动：从 GitHub README 中的 Google Drive 链接下载，解压到 data/raw/chv/（images/ 与 labels/ 同级）。
- **用途**：训练 · B 补充
- **备注**：没有 no_helmet 类，由 teacher 补伪标签。
- ⚠️ 类别表与规模尚未按下载后的实际文件核对

### `acid` — ACID — Alberta Construction Image Dataset

- **来源**：https://profsckang.wixsite.com/uofa-rlab/copy-of-r-lab-design
- **论文**：https://ascelibrary.org/doi/abs/10.1061/(ASCE)CP.1943-5487.0000945
- **简介**：10,000 张地面视角的工程机械图像，共 10 类机械。只取不含人员的图补充机械多样性。
- **规模**：计划 10,000 张 ｜ 本地原始 未下载 ｜ 构建后 —
- **格式 / 本地路径**：voc ｜ `data/raw/acid`
- **类别映射**：excavator→machinery, compactor→machinery, dozer→machinery, grader→machinery, dump_truck→machinery, concrete_mixer_truck→machinery, backhoe_loader→machinery, wheel_loader→machinery, tower_crane→machinery, mobile_crane→machinery
- **完整标注的目标类别**：machinery（其余类别由 teacher 补伪标签）
- **许可**：CC BY-NC 4.0（仅限非商业用途）
- **引用**：Xiao, B.; Kang, S.-C. Development of an Image Data Set of Construction Machines for Deep Learning Object Detection. Journal of Computing in Civil Engineering 2021, 35(2).
- **获取方式**：手动：按 R-Lab 页面指引从阿尔伯塔大学图书馆申请下载，解压到 data/raw/acid/。
- **用途**：训练 · B 补充（当前未参与构建）
- **过滤**：no_person
- ⚠️ 类别表与规模尚未按下载后的实际文件核对

### `telecom_tower` — Telecom Tower Object Detection (Roboflow Universe)

- **来源**：https://universe.roboflow.com/object-detection-yolo-c8gsd/telecom-tower-object-detection
- **简介**：128 张通信塔检测图像，是少数直接面向电信设施的公开数据。
- **规模**：计划 128 张 ｜ 本地原始 未下载 ｜ 构建后 —
- **格式 / 本地路径**：yolo ｜ `data/raw/telecom_tower`
- **类别映射**：待填写（下载后按数据集自带的类别表补全）
- **完整标注的目标类别**：tower（其余类别由 teacher 补伪标签）
- **许可**：以数据集页面为准
- **引用**：Telecom Tower Object Detection dataset, Roboflow Universe, https://universe.roboflow.com/object-detection-yolo-c8gsd/telecom-tower-object-detection
- **获取方式**：Roboflow API：workspace `object-detection-yolo-c8gsd` / project `telecom-tower-object-detection`（`python -m telecomsafe.data.download --only telecom_tower`）
- **用途**：训练 · 可选（当前未参与构建）
- ⚠️ 类别表与规模尚未按下载后的实际文件核对

### `telecom_eval` — TelecomEval — 电信施工场景真实测试集（自建）

- **来源**：自建
- **简介**：从 Openverse 与 Wikimedia Commons 检索的开放许可电信施工图像，人工筛选（画面中有人在电信场景作业） 并标注。两个阶段共用的唯一评估标尺，冻结后只读，绝不参与训练、LoRA 微调或生成条件构建。
- **规模**：计划 ≥150 张（理想 200 张） ｜ 本地原始 未下载 ｜ 构建后 —
- **格式 / 本地路径**：yolo ｜ `data/raw/telecom_eval`
- **类别映射**：直接按目标类别标注
- **完整标注的目标类别**：person, helmet, no_helmet, vest, no_vest, harness, machinery, vehicle
- **许可**：逐图记录（CC0 / Public Domain / CC BY / CC BY-SA），见 licence_manifest.csv
- **引用**：逐图署名见 licence_manifest.csv
- **获取方式**：手动：collect_open 检索候选图 → 人工筛选 → pseudo_label 预标注 → labelstudio serve / push 标注 → labelstudio pull 导出到 data/raw/telecom_eval/ → freeze_eval --create（详见 data/README.md）
- **用途**：测试（TelecomEval）
- ⚠️ 类别表与规模尚未按下载后的实际文件核对
- **冻结状态**：尚未冻结（标注完成后运行 `python -m telecomsafe.data.freeze_eval --create`）
- **候选图**：保留 31 张，剔除 388 张（逐图许可见 `data/licence_manifest.csv`）

## 调研过但阶段一未使用

| 数据集 | 规模 | 许可 | 未使用原因 |
|---|---|---|---|
| [harness (vgg2coco, Roboflow Universe)](https://universe.roboflow.com/vgg2coco/harness-dyxml) | 约 1,000 张（实际 2,582 张） | CC BY 4.0 | 下载后核对（2026-09-28）：标成 harness 的其实是反光背心而非安全带；helmat 框包含手持的安全帽； 全部是同一室内场景、同一人的摆拍视频帧。标注语义与判定标准冲突，领域也不符，停用。 |
| [SHWD — Safety Helmet Wearing Dataset](https://github.com/njvisionpower/Safety-Helmet-Wearing-Dataset) | 7,581 张 | MIT | 负样本多来自教室场景的人头数据集 SCUT-HEAD，与施工领域不符；只有头部级标注。 |
| [SODA — Site Object Detection dAtaset](https://arxiv.org/abs/2202.09554) | 19,846 张 | 仅限研究用途 | 没有 no_helmet 类，机械类别少；数据量大但与阶段一目标类别重合度低。 |
| [MOCS — Moving Objects in Construction Sites](https://www.sciencedirect.com/science/article/abs/pii/S0926580520310621) | 41,668 张 | 未注明（研究用途） | 只标注了工人、未标注 PPE，混入会让安全帽 / 反光衣被当作背景；下载页不稳定。 |
| [Construction Site Safety Image Dataset (Kaggle mirror = Roboflow version 28)](https://www.kaggle.com/datasets/snehilsanyal/construction-site-safety-image-dataset-roboflow) | 2,801 张 | CC BY 4.0 | 训练集是 521 张原图各生成 5 个增广版本（马赛克、cutout 等）得到的拼图，会污染 E1 的"无增广"对照 并让规则误判跨子图的人机距离；改用同一项目未增广的 version 30。本地副本在 data/raw/css_kaggle_v28/。 |
| [SH17 — Human safety and PPE detection](https://github.com/ahmadmughees/SH17dataset) | 8,099 张 | CC BY-NC-SA 4.0 | 制造业场景，没有 no_helmet 类。 |

## TelecomEval 建立流程

1. `python -m telecomsafe.data.collect_open` —— 从 Openverse 与 Wikimedia Commons 检索开放许可（CC0 / PD / CC BY / CC BY-SA）候选图，自动记录署名
2. 人工筛选：只保留**有人在电信场景作业**的照片，其余直接删除；然后 `python -m telecomsafe.data.collect_open --sync`
3. `python -m telecomsafe.data.pseudo_label --weights <teacher> --images data/raw/t3_candidates/images` —— 生成预标注（teacher 标人员与 PPE，COCO 模型补车辆）
4. `python -m telecomsafe.data.labelstudio serve` 启动 Label Studio（账号见 `.env`），另开终端 `python -m telecomsafe.data.labelstudio push` 导入图片与预标注
5. 在 http://localhost:8080 逐张按上方「判定标准」修正：检查每个预标注框，补画漏标（安全带、机械没有预标注，必须手画）；不可用的图点 Skip
6. `python -m telecomsafe.data.labelstudio pull` —— 导出为 YOLO 格式到 `data/raw/telecom_eval/`
7. `python -m telecomsafe.data.freeze_eval --create` —— 冻结；此后只读，两个阶段共用
