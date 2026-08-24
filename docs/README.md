# TelecomSafe 项目文档集 / Project Documentation

> 项目 / Project：A Novel Generative Image-based Learning Framework for Enhancing the Construction Safety of Telecommunication Projects
> 生成日期 / Generated：2026-08-18
> 全部文档提供中英双版，章节编号与表格结构一一对应，可逐段对照使用。
> All documents exist in Chinese and English versions with matching section numbering and table structure, usable side by side.

---

## 文档索引 / Document Index

| # | 中文版 | English | 内容 / Content |
|---|--------|---------|---------------|
| 00 | [项目需求分析](00-项目需求分析-CN.md) | [Requirements Analysis](00-Requirements-Analysis-EN.md) | 项目本质拆解、四个风险维度、三大技术支柱、创新点定位、交付物要求、非技术约束、三大难点 |
| 01 | [技术方案与里程碑](01-技术方案与里程碑-CN.md) | [Technical Plan & Milestones](01-Technical-Plan-and-Milestones-EN.md) | 五层架构、分层技术选型、三级信息融合设计、E1–E9 实验矩阵、16 周里程碑、风险登记表、算力配置 |
| 02 | [数据集与预训练模型调研](02-数据集与预训练模型调研-CN.md) | [Datasets & Pretrained Models](02-Datasets-and-Pretrained-Models-EN.md) | ⭐ **v2.0：取消现场采集**。T1–T4 四层纯公开来源策略、社区数据集平台、开放许可图像库整编、生成与感知模型选型、许可证合规、M1 行动清单 |
| 03 | [生成式数据增广 Pipeline 设计](03-生成式数据增广Pipeline设计-CN.md) | [Generative Augmentation Pipeline](03-Generative-Augmentation-Pipeline-EN.md) | 六阶段 pipeline、风险场景规格库、四路生成引擎、四道质量闸门、混合训练策略、失败模式对策 |
| 04 | [文献综述](04-文献综述-CN.md) | [Literature Survey](04-Literature-Survey-EN.md) | 四条文献主线、50 条参考文献、5 个研究空白（G1–G5）、定位陈述、引文核实状态表 |
| 05 | [技术路线图](05-技术路线图-CN.md) | [Technological Roadmap](05-Technological-Roadmap-EN.md) | 三视野 H1–H3、五层技术演进泳道、TG1–TG5 决策门、关键路径、技术成熟度、D1–D8 降级路径、备选矩阵 |
| 06 | [团队分工](06-团队分工-CN.md) | [Teamwork Allocation](06-Teamwork-Allocation-EN.md) | 5 人角色定义、队长提名标准与选举流程、RACI 矩阵、工作量分布、接口约定、协作机制、应急预案 |
| 07 | [项目章程](07-项目章程-CN.md) | [Project Charter](07-Project-Charter-EN.md) | ⭐ **已按学校官方模板重构**：立项依据、项目描述、里程碑摘要、成员活动矩阵、预算、风险评估（含实验室安全培训）；模板外内容移至附录 A |

> 📄 **学校官方模板**存放于 [`template/`](../template/)：`EE6008_Project_Charter_Template.docx`（项目章程）与 `EE6008-Project ReportTemplate.docx`（项目报告）。
> 文档 07 已严格按 Charter 模板重构；文档 01 §7 与 04 §9 已按 Report 模板校准。
> *Official school templates live in [`template/`](../template/). Document 07 now follows the Charter template exactly; documents 01 §7 and 04 §9 are calibrated to the Report template.*

> 中文版 04 的参考文献额外附了中文标题译名，方便撰写中文报告时引用。
> The Chinese version of document 04 additionally provides Chinese translations of reference titles.

---

## 快速上手路径 / Reading Paths

**项目负责人 / Project lead**
```
00（理解要求） → 01 §四（里程碑，定分工与排期） → 01 §五（风险表，提前布防）
00 (understand the brief) → 01 §4 (milestones, roles and schedule) → 01 §5 (risk register)
```

**数据与生成 / Data & generation**
```
02（选数据集与模型） → 03（全文，这是你的施工图）
02 (choose datasets and models) → 03 (in full — this is your blueprint)
```

**模型与实验 / Models & experiments**
```
01 §二（技术选型） → 01 §三（实验矩阵 E1–E9） → 02 §三（感知模型选型）
01 §2 (technology selection) → 01 §3 (experiment matrix E1–E9) → 02 §3 (perception models)
```

**论文写作 / Paper writing**
```
04（文献综述 + 参考文献） → 01 §七（论文结构建议） → 04 §9（Related Work 写作技巧）
04 (survey + references) → 01 §7 (paper structure) → 04 §9 (Related Work writing technique)
```

**队长 / 项目管理 · Team leader & project management**
```
07（章程：官方模板 8 个字段） → 06 §3（队长职责与选举） → 06 §4（RACI）
→ 05 §3（TG1–TG5 决策门） → 05 §6（D1–D8 降级路径）
07 (charter) → 06 §3 (leader role and election) → 06 §4 (RACI)
→ 05 §3 (decision gates) → 05 §6 (downgrade paths)
```

**第一次团队会议 · First team meeting**
```
直接照 06 §10 的议程执行（90 分钟：角色认领 → 队长选举 → 关键决策确认）
Follow the agenda in 06 §10 directly (90 min: role claiming → leader election → key decisions)
```

---

## 三条最关键的提醒 / Three Critical Reminders

1. **先定风险分类体系（Risk Taxonomy），再做别的**
   后续所有标注、生成、评估都依赖它。M0 第一周必须产出。
   *Define the Risk Taxonomy first. All subsequent annotation, generation and evaluation depend on it; deliver it in week 1 of M0.*

2. **TelecomEval 测试集只用真实图像，划出后立即冻结**
   不得参与 LoRA 微调，不得参与生成条件构建，不得混入合成数据。取消现场采集后真实数据更少，这条**反而更关键**——若破坏，「电信专用」的结论完全失去支撑。
   *TelecomEval must contain only real imagery and be frozen once carved out — never used in LoRA fine-tuning, generation conditioning, or mixed with synthetic data. With less real data after cancelling field collection, this matters more, not less.*

3. **报告要「计划 vs 实际」对照，必须全程记录**
   学校报告模板的 Schedule 与 Cost 都有 Planned / Actual 两列，且每人须写个人报告与反思。这些无法最后补——建议建 `progress/` 目录，每周例会后更新实际完成日期与范围变更。详见 [01 §7.4](01-技术方案与里程碑-CN.md)。
   *The report template requires planned-vs-actual columns and individual reflections. These cannot be reconstructed at the end — record them weekly.*

4. **不要四个维度平均用力**
   一学期内四维全做到高质量几乎不可能。建议主攻 Workers + Machinery，Terrain 与 Materials 做到可用即可，并在报告中诚实说明范围界定。
   *Do not spread effort evenly across all four dimensions. Focus on Workers + Machinery; keep Terrain and Materials merely functional, and state the scope boundary honestly in the report.*

---

## 待办事项 / Open Items Requiring Human Decision

- [ ] 召开首次团队会议，认领 A–E 五个角色并**选举队长**（照文档 06 §10 议程执行；队长按 06 §3.2 的提名标准投票产生）
      *Hold the first team meeting: claim roles A–E and **elect the team leader** (follow the agenda in 06 §10; the leader is elected against the criteria in 06 §3.2)*
- [ ] 把真实姓名填入文档 06 §2.1 与文档 07 §8.1 的角色表
      *Fill real names into the role tables in 06 §2.1 and 07 §8.1*
- [ ] 完成项目章程签署（文档 07 §14 附签署前确认清单）
      *Complete charter signature (document 07 §14 includes a pre-signature checklist)*
- [ ] 确认项目周期是 12 周还是 16 周（文档 01 按 16 周编排，含 12 周压缩建议）
      *Confirm whether the project runs 12 or 16 weeks (document 01 assumes 16, with a 12-week compression note)*
- [ ] 确认可用算力（文档 01 §六列了建议与最低配置）
      *Confirm available compute (document 01 §6 lists recommended and minimum configurations)*
- [ ] 与导师确认「电信施工」的具体细分场景范围（铁塔？光缆？机房？全部？）
      *Confirm with the supervisor which telecommunication construction scenarios are in scope (towers? optical cable? equipment rooms? all?)*
- [ ] **核实文献引用**——文档 04 §8 列出了每条参考文献的核实状态，标记为 ❗ 的条目必须补全作者信息后才能正式引用（中英两版核实状态表内容一致，核对一次即可）
      ***Verify citations*** — *document 04 §8 gives per-reference verification status; entries marked ❗ need author details completed before formal citation. The status table is identical in both language versions, so verify once.*
