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
| 02 | [数据集与预训练模型调研](02-数据集与预训练模型调研-CN.md) | [Datasets & Pretrained Models](02-Datasets-and-Pretrained-Models-EN.md) | 公开数据集清单与评级、生成模型选型对比、感知模型选型、许可证合规、M1 行动清单 |
| 03 | [生成式数据增广 Pipeline 设计](03-生成式数据增广Pipeline设计-CN.md) | [Generative Augmentation Pipeline](03-Generative-Augmentation-Pipeline-EN.md) | 六阶段 pipeline、风险场景规格库、四路生成引擎、四道质量闸门、混合训练策略、失败模式对策 |
| 04 | [文献综述](04-文献综述-CN.md) | [Literature Survey](04-Literature-Survey-EN.md) | 四条文献主线、50 条参考文献、5 个研究空白（G1–G5）、定位陈述、引文核实状态表 |

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

---

## 三条最关键的提醒 / Three Critical Reminders

1. **先定风险分类体系（Risk Taxonomy），再做别的**
   后续所有标注、生成、评估都依赖它。M0 第一周必须产出。
   *Define the Risk Taxonomy first. All subsequent annotation, generation and evaluation depend on it; deliver it in week 1 of M0.*

2. **测试集只用真实电信图像，且严格隔离**
   不得参与生成模型微调，不得混入合成数据。这条一旦破坏，所有实验结论作废。
   *The test set must contain only real telecommunication imagery, strictly isolated — never used in generative fine-tuning, never mixed with synthetic data. Breaking this invalidates every experimental conclusion.*

3. **不要四个维度平均用力**
   一学期内四维全做到高质量几乎不可能。建议主攻 Workers + Machinery，Terrain 与 Materials 做到可用即可，并在报告中诚实说明范围界定。
   *Do not spread effort evenly across all four dimensions. Focus on Workers + Machinery; keep Terrain and Materials merely functional, and state the scope boundary honestly in the report.*

---

## 待办事项 / Open Items Requiring Human Decision

- [ ] 确认团队人数与分工（文档 00 §六给了 3–4 人的建议方案）
      *Confirm team size and role assignment (document 00 §6 proposes a 3–4 person split)*
- [ ] 确认项目周期是 12 周还是 16 周（文档 01 按 16 周编排，含 12 周压缩建议）
      *Confirm whether the project runs 12 or 16 weeks (document 01 assumes 16, with a 12-week compression note)*
- [ ] 确认可用算力（文档 01 §六列了建议与最低配置）
      *Confirm available compute (document 01 §6 lists recommended and minimum configurations)*
- [ ] 与导师确认「电信施工」的具体细分场景范围（铁塔？光缆？机房？全部？）
      *Confirm with the supervisor which telecommunication construction scenarios are in scope (towers? optical cable? equipment rooms? all?)*
- [ ] **核实文献引用**——文档 04 §8 列出了每条参考文献的核实状态，标记为 ❗ 的条目必须补全作者信息后才能正式引用（中英两版核实状态表内容一致，核对一次即可）
      ***Verify citations*** — *document 04 §8 gives per-reference verification status; entries marked ❗ need author details completed before formal citation. The status table is identical in both language versions, so verify once.*
