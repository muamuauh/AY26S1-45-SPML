# AY26S1-45-SPML — TelecomSafe

**A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects**

面向电信施工安全的生成式图像学习框架 · 项目规划与调研文档

---

## 项目简介 / Overview

电信施工现场的安全风险来自地形不平、机械操作不当、材料堆放不当、防护装备缺失与工人不安全行为。基于深度学习的计算机视觉可以高效识别这些风险，但受限于**行业专用标注图像的稀缺性与多样性不足**。

TelecomSafe 以**生成式 AI 合成训练数据**补齐数据缺口，并结合深度学习图像处理与信息融合，从**地形、机械、材料、人员**四个维度对施工风险进行综合评估。

*Safety risks at telecommunication construction sites arise from uneven terrain, improperly operated machinery, poorly stored materials, missing PPE and unsafe worker behaviour. TelecomSafe addresses the scarcity of labelled, sector-specific imagery through generative AI, and appraises risk across four dimensions — terrain, machinery, materials and workers — via deep learning and information fusion.*

---

## 文档 / Documentation

完整文档见 **[docs/](docs/)**，全部提供中英双版。
Full documentation lives in **[docs/](docs/)**, available in Chinese and English.

| # | 中文版 | English |
|---|--------|---------|
| 00 | [项目需求分析](docs/00-项目需求分析-CN.md) | [Requirements Analysis](docs/00-Requirements-Analysis-EN.md) |
| 01 | [技术方案与里程碑](docs/01-技术方案与里程碑-CN.md) | [Technical Plan & Milestones](docs/01-Technical-Plan-and-Milestones-EN.md) |
| 02 | [数据集与预训练模型调研](docs/02-数据集与预训练模型调研-CN.md) | [Datasets & Pretrained Models](docs/02-Datasets-and-Pretrained-Models-EN.md) |
| 03 | [生成式数据增广 Pipeline 设计](docs/03-生成式数据增广Pipeline设计-CN.md) | [Generative Augmentation Pipeline](docs/03-Generative-Augmentation-Pipeline-EN.md) |
| 04 | [文献综述](docs/04-文献综述-CN.md) | [Literature Survey](docs/04-Literature-Survey-EN.md) |
| 05 | [技术路线图](docs/05-技术路线图-CN.md) | [Technological Roadmap](docs/05-Technological-Roadmap-EN.md) |
| 06 | [团队分工](docs/06-团队分工-CN.md) | [Teamwork Allocation](docs/06-Teamwork-Allocation-EN.md) |
| 07 | [项目章程](docs/07-项目章程-CN.md) | [Project Charter](docs/07-Project-Charter-EN.md) |
| 08 | [阶段一训练复现指南](docs/08-阶段一训练复现指南-CN.md) | — |

→ 索引与阅读路径见 [docs/README.md](docs/README.md)

**学校官方模板 / Official templates** — [`template/`](template/)
`EE6008_Project_Charter_Template.docx`（项目章程）｜ `EE6008-Project ReportTemplate.docx`（项目报告）
文档 07 按 Charter 模板组织；文档 01 §7 与 04 §9 按 Report 模板校准。
*Document 07 follows the Charter template; documents 01 §7 and 04 §9 are calibrated to the Report template.*

---

## 阶段一代码 / Phase 1 Code

完整的复现步骤、每一步的预期输出与常见问题见 **[阶段一训练复现指南](docs/08-阶段一训练复现指南-CN.md)**。

```bash
conda env create -f environment.yml && conda activate telecomsafe
pytest                                               # 单元测试，不需要 GPU 与数据

cp .env.example .env                                 # 填 Kaggle / Roboflow API key（.env 不入库）
python -m telecomsafe.data.download --list           # 查看数据集下载状态
python -m telecomsafe.data.download                  # 下载可脚本化的数据集到 data/raw/
python -m telecomsafe.data.catalog                   # 生成数据集说明 data/README.md
python -m telecomsafe.data.collect_open              # 检索 TelecomEval 候选图（开放许可，自动记录署名）
python -m telecomsafe.data.labelstudio serve        # 启动标注工具（账号见 .env）；另开终端执行 push / pull
python -m telecomsafe.data.build --dry-run           # 映射 / 覆盖矩阵 / 去重统计
python -m telecomsafe.data.build                     # 生成 data/processed/yolo/
python -m telecomsafe.data.freeze_eval --create      # 冻结 TelecomEval（之后只读）
python -m telecomsafe.train --exp e1                 # E1：关闭内置增广
python -m telecomsafe.train --exp e2                 # E2：configs/baseline.yaml
python -m telecomsafe.evaluate                       # 报告与图表 → reports/phase1/
python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt
```

**Windows 一键启动 Demo**：双击项目根目录的 `start_demo.bat`，就绪后自动打开浏览器（http://127.0.0.1:7860）；关闭窗口即停止。

| 目录 | 内容 |
|---|---|
| [`configs/`](configs/) | 类别体系、数据来源登记、baseline 训练配置、规则库 |
| [`telecomsafe/`](telecomsafe/) | 数据（下载、构建、伪标签、冻结）、训练、评估、规则判断、Demo |
| [`data/README.md`](data/README.md) | 每个数据集的来源、链接、许可与规模（自动生成） |
| [`reports/phase1/`](reports/phase1/) | 阶段一成果总结与实验结果 |
| [`progress/`](progress/) | 里程碑计划 vs 实际、范围变更记录 |

### 获取数据与模型 / Data & Models

仓库只放代码、配置和报告；数据与权重按"能否重新获取、能否公开"分三处存放：

| 内容 | 存放位置 | 怎么获取 |
|---|---|---|
| **模型权重**（E1 / E2，各约 19 MB） | GitHub Release [`phase1-baseline-v1`](https://github.com/muamuauh/AY26S1-45-SPML/releases/tag/phase1-baseline-v1) | `python -m telecomsafe.weights`（自动校验 sha256）；`start_demo.bat` 在缺少权重时会自动下载 |
| **公开数据集**（Construction Site Safety v30、Construction-PPE、body_harness、construction safety v2） | 各自的原始发布页 | 在 `.env` 填好自己的 Kaggle / Roboflow key，运行 `python -m telecomsafe.data.download`；版本已固定在 `configs/sources.yaml` |
| **无法重新下载的数据**（APD、TelecomEval 候选图与许可清单、后续的标注结果） | 组内共享文件夹（学校 OneDrive / Teams，**仅限组员与导师**） | 按共享文件夹里的 `README.md` 解压到指定位置 |

> ⚠️ 本仓库是**公开**的：APD 等私有数据、`.env` 中的 key 绝不能提交或放进 Release。
> 数据集的来源、许可与实际张数见 [`data/README.md`](data/README.md)。

---

## 当前状态 / Status

🚧 **阶段一 · Baseline** — ① Risk Taxonomy 与 ② 公开数据整编已于线下完成，正在进入 ③ 训练 baseline 模型。

> 🔄 **2026-09-28 流程调整（v3.0）**：按导师建议改为**两阶段**：
> **阶段一** 只用已整编的公开数据，训练 baseline 感知模型 + 规则风险判断 + 小型 Demo（目标 W7）；
> **阶段二** 再引入生成式增广，在同一测试集、同一训练配置下与 baseline 对比。
> 详见 [docs/05](docs/05-技术路线图-CN.md)。
>
> *Flow change (2026-09-28): on the supervisor's advice, phase 1 builds a baseline demo from the curated public data only (target W7); phase 2 then adds generative augmentation and compares against the baseline on the same test set and training configuration.*

> 🔄 **2026-08-24 数据策略变更**：经与导师沟通，**取消一切现场数据采集**（安全风险与成本过高），改为纯公开来源的四层策略：
> **T1** 学术公开数据集 → **T2** 社区数据集平台（Roboflow Universe / Kaggle）→ **T3** 开放许可图像库整编（Wikimedia Commons / Openverse）→ **T4** 生成式合成。
> 详见 [docs/02](docs/02-数据集与预训练模型调研-CN.md)。
>
> *Data strategy change (2026-08-24): all field collection is cancelled; real data now comes from public sources only (T1 academic datasets, T2 community platforms, T3 openly licensed repositories), expanded by T4 generative synthesis.*

*Phase 1 · Baseline. The Risk Taxonomy and public data curation were completed offline; baseline model training is starting.*

### 待办 / Open items

**组建与行政**
- [ ] 召开阶段一启动会议：确认 A–E 角色、**选举队长**（若尚未完成），议程见 [docs/06 §10](docs/06-团队分工-CN.md)
- [ ] 核对 Project No.（推测 45）、学年学期、导师姓名，填入 [docs/07](docs/07-项目章程-CN.md) 并誊入 Word 模板（附提交前检查清单）
- [ ] 确认项目周期（12 / 16 周）、学期 W1 的真实日期与可用算力
- [ ] 向导师确认是否需要提交 team project video（报告模板附录提及）

**阶段一（W4–W7）**
- [x] 确定风险分类体系 Risk Taxonomy（线下完成）—— 草案已转录到 `configs/taxonomy.yaml`，待与线下定稿核对
- [x] 数据集清单与类别映射表 —— `configs/sources.yaml`，说明文档 `data/README.md`
- [ ] ⏸ **TelecomEval 标注与冻结（暂缓，Demo v1 完成后恢复）** —— 31 张候选已预标注并导入 Label Studio，恢复步骤见 [progress/milestones.md](progress/milestones.md#暂缓事项)
- [x] 训练 baseline（E1 / E2）—— 验证集 mAP50 0.611 / 0.756，见 [reports/phase1/](reports/phase1/README.md)；`configs/baseline.yaml` 在 TGB 后冻结
- [x] 规则风险判断 + Gradio Demo v1 —— `python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt`
- [ ] TGB 会议（W7 末）：准备幻灯片与 Demo 录屏

**贯穿全程**
- [x] 建立 `progress/` 目录记录里程碑**实际**完成日期与范围变更 —— 每完成一个里程碑就补一行（见 [docs/01 §7.4](docs/01-技术方案与里程碑-CN.md)）
- [ ] 核实文献引用（见 [docs/04 §8](docs/04-文献综述-CN.md) 核实状态表）

---

## ⚠️ 说明 / Note

`docs/04` 中的参考文献书目信息部分来自网络检索元数据，**正式引用前需按文末核实状态表逐条核对**。

*Some bibliographic details in `docs/04` were gathered from search metadata. Verify each entry against the status table before formal citation.*
