# TelecomSafe 项目文档集 / Project Documentation

> 项目 / Project：A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects
> 生成日期 / Generated：2026-08-18 ｜ 修订 / Revised：2026-09-28（全部文档已同步 v3.0 两阶段流程）
> 全部文档提供中英双版，章节编号与表格结构一一对应，可逐段对照使用。
> All documents exist in Chinese and English versions with matching section numbering and table structure, usable side by side.

---

## 当前流程 / Current Flow

```
①定标准 ✅ → ②备料 ✅
  → 阶段一 Baseline（W4–W7）：③训练 baseline → ④规则判断 → ⑤Demo v1
  → 阶段二 增广（W8–W16）：  ⑥生成式增广 → ⑦同配置再训练对比 → ⑧升级与交付
```

*Phase 1 builds a baseline demo from the curated public data only; phase 2 adds generative augmentation and compares against the baseline on the same test set and training configuration.* 详见 / See [05](05-技术路线图-CN.md)。

---

## 文档索引 / Document Index

| # | 中文版 | English | 内容 / Content |
|---|--------|---------|---------------|
| 00 | [项目需求分析](00-项目需求分析-CN.md) | [Requirements Analysis](00-Requirements-Analysis-EN.md) | 项目本质拆解、四个风险维度、三大技术支柱、创新点定位、交付物要求、非技术约束、三大难点 |
| 01 | [技术方案与里程碑](01-技术方案与里程碑-CN.md) | [Technical Plan & Milestones](01-Technical-Plan-and-Milestones-EN.md) | 五层架构、分层技术选型、E1–E9 实验矩阵、**两阶段里程碑 M0–M7**、风险登记表、算力配置、EE6008 报告写作指引 |
| 02 | [数据集与预训练模型调研](02-数据集与预训练模型调研-CN.md) | [Datasets & Pretrained Models](02-Datasets-and-Pretrained-Models-EN.md) | T1–T4 纯公开来源策略、学术与社区数据集、开放许可图像库、生成与感知模型选型、许可证合规、**阶段一准备清单** |
| 03 | [生成式数据增广 Pipeline 设计](03-生成式数据增广Pipeline设计-CN.md) | [Generative Augmentation Pipeline](03-Generative-Augmentation-Pipeline-EN.md) | 阶段二的施工图：规格库（按弱类别排优先级）、生成路线实施顺序、四道质量闸门、混合训练策略、失败模式对策 |
| 04 | [文献综述](04-文献综述-CN.md) | [Literature Survey](04-Literature-Survey-EN.md) | 四条文献主线、50 条参考文献、5 个研究空白（G1–G5）、定位陈述、引文核实状态表 |
| 05 | [技术路线图](05-技术路线图-CN.md) | [Technological Roadmap](05-Technological-Roadmap-EN.md) | ⭐ **v3.0 Baseline 优先**：为什么先做 baseline、主流程图、八步详解、两阶段衔接的三条硬约束、决策门（TGB、TG1–TG5）与降级路径、甘特时间线、关键路径 |
| 06 | [团队分工](06-团队分工-CN.md) | [Teamwork Allocation](06-Teamwork-Allocation-EN.md) | 5 人角色与两阶段交付物、队长选举、RACI 矩阵、工作量分布、接口约定、协作机制、应急预案、**阶段一启动会议议程** |
| 07 | [项目章程](07-项目章程-CN.md) | [Project Charter](07-Project-Charter-EN.md) | 按学校官方模板组织：立项依据、项目描述、里程碑摘要、成员活动矩阵、预算、风险评估；模板外内容在附录 A |

> 📄 **学校官方模板**存放于 [`template/`](../template/)：`EE6008_Project_Charter_Template.docx`（项目章程）与 `EE6008-Project ReportTemplate.docx`（项目报告）。文档 07 按 Charter 模板组织；文档 01 §7 与 04 §9 按 Report 模板校准。
> *Official school templates live in [`template/`](../template/). Document 07 follows the Charter template; documents 01 §7 and 04 §9 are calibrated to the Report template.*

> 中文版 04 的参考文献额外附了中文标题译名，方便撰写中文报告时引用。
> *The Chinese version of document 04 additionally provides Chinese translations of reference titles.*

---

## 快速上手路径 / Reading Paths

**全员（阶段一开工前）/ Everyone (before phase 1)**
```
05 §0–§2（为什么先做 baseline、每一步做什么） → 06 §2（自己的角色与交付物） → 06 §10（启动会议议程）
05 §0–§2 (why baseline first, what each step does) → 06 §2 (your role and deliverables) → 06 §10 (kick-off agenda)
```

**Baseline 与实验 / Baseline & experiments**
```
05 §2.2 ③④⑤ → 02 §5（阶段一准备清单） → 01 §3（实验矩阵 E1–E9）
05 §2.2 ③④⑤ → 02 §5 (phase 1 preparation checklist) → 01 §3 (experiment matrix E1–E9)
```

**生成（阶段二）/ Generation (phase 2)**
```
05 §2.2 ⑥⑦ → 03（全文，这是你的施工图） → 02 §2（生成模型选型）
05 §2.2 ⑥⑦ → 03 (in full — your blueprint) → 02 §2 (generative model selection)
```

**队长 / 项目管理 · Team leader & project management**
```
07（章程） → 01 §4（里程碑）→ 01 §5（风险表） → 05 §4（决策门与降级路径） → 06 §4（RACI）
07 (charter) → 01 §4 (milestones) → 01 §5 (risk register) → 05 §4 (gates and downgrade paths) → 06 §4 (RACI)
```

**报告写作 / Report writing**
```
01 §7（EE6008 报告章节对照） → 04（立项依据与参考文献） → 04 §9（综述内容在报告中的去向）
01 §7 (EE6008 report chapter mapping) → 04 (justification and references) → 04 §9 (where survey content goes in the report)
```

---

## 最关键的提醒 / Critical Reminders

1. **TelecomEval 测试集只用真实图像，冻结后两个阶段共用**
   不得参与训练、LoRA 微调与生成条件构建，不得混入合成数据。若测试集变了，阶段二的 E3 与 baseline 就不可比。
   *TelecomEval contains only real imagery and, once frozen, is shared by both phases — never used in training, LoRA fine-tuning or generation conditioning. Change it and E3 is no longer comparable with the baseline.*

2. **baseline 配置一旦提交就不再改**
   `configs/baseline.yaml` 在 W7 提交后只读；阶段二的 E3 只改训练数据。否则提升可能来自调参而不是增广。
   *`configs/baseline.yaml` is read-only once committed in W7; phase 2's E3 changes only the training data. Otherwise any gain may come from tuning rather than augmentation.*

3. **Baseline Demo 不是终点**
   生成式增广是立项理由。TGB 会议上就要定下弱类别清单与阶段二的开工日期。
   *The Baseline Demo is not the finish line. Generative augmentation is why the project exists; settle the weak-class list and the phase 2 start date at the TGB meeting.*

4. **报告要「计划 vs 实际」对照，必须全程记录**
   学校报告模板的 Schedule 与 Cost 都有 Planned / Actual 两列，Scope 要说明范围变更（取消现场采集、改为两阶段）。建 `progress/` 目录，每周例会后更新。详见 [01 §7.4](01-技术方案与里程碑-CN.md)。
   *The report template requires planned-vs-actual columns and a record of scope changes (field collection cancelled, two-phase flow). Keep a `progress/` directory updated weekly.*

---

## 待办事项 / Open Items

见项目主页 [README.md](../README.md#待办--open-items)。
*See the open items on the project [README](../README.md#待办--open-items).*
