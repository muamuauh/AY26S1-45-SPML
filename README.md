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

→ 索引与阅读路径见 [docs/README.md](docs/README.md)

**学校官方模板 / Official templates** — [`template/`](template/)
`EE6008_Project_Charter_Template.docx`（项目章程）｜ `EE6008-Project ReportTemplate.docx`（项目报告）
文档 07 按 Charter 模板组织；文档 01 §7 与 04 §9 按 Report 模板校准。
*Document 07 follows the Charter template; documents 01 §7 and 04 §9 are calibrated to the Report template.*

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
- [x] 确定风险分类体系 Risk Taxonomy（线下完成）—— 待提交到仓库（建议 `data/taxonomy.yaml`）
- [x] 整编公开数据（线下完成）—— 待补记 TelecomSeed / TelecomEval 实际张数与 TelecomEval 文件列表哈希
- [ ] 确认 `licence_manifest.csv` 覆盖全部 T3 开放许可图像（CC BY / CC BY-SA 的署名义务）
- [ ] 写类别映射表：把各公开数据集的标签名对齐到 Taxonomy 类别（阶段一第一件事，见 [docs/02 §5](docs/02-数据集与预训练模型调研-CN.md)）
- [ ] 训练 baseline（E1 / E2），提交 `configs/baseline.yaml` —— 阶段二的 E3 必须沿用同一份
- [ ] 规则风险判断 + Gradio Demo v1，W7 末 TGB 会议验收

**贯穿全程**
- [ ] 建立 `progress/` 目录记录里程碑**实际**完成日期与范围变更 —— 报告模板要求 Planned vs Actual 对照（见 [docs/01 §7.4](docs/01-技术方案与里程碑-CN.md)）
- [ ] 核实文献引用（见 [docs/04 §8](docs/04-文献综述-CN.md) 核实状态表）

---

## ⚠️ 说明 / Note

`docs/04` 中的参考文献书目信息部分来自网络检索元数据，**正式引用前需按文末核实状态表逐条核对**。

*Some bibliographic details in `docs/04` were gathered from search metadata. Verify each entry against the status table before formal citation.*
