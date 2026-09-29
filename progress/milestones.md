# 里程碑：计划 vs 实际

EE6008 报告模板 §4 Schedule 需要计划与实际日期对照，§3 Scope 需要记录范围变更。每完成一个里程碑、每触发一次降级路径，就在这里补一行，不要等到最后。

周次按 docs/05 §5 的占位换算（W1 = 2026-09-07）；确认学期日历后统一替换。

## 里程碑

| 里程碑 | 内容 | 计划完成 | 实际完成 | 备注 |
|---|---|---|---|---|
| M0 | 立项与 Risk Taxonomy | W1 | `<<日期>>` | 线下完成 |
| M1 | 公开数据整编（TG1） | W3 | `<<日期>>` | 线下完成数据调研；阶段一重新按 configs/sources.yaml 收集。TG1 实际张数：TelecomSeed `<<n>>` / TelecomEval `<<n>>` |
| M2 | Baseline Demo（TGB） | W7 | 进行中 | 2026-09-29：baseline（E1/E2）、规则判断、Demo v1 完成，验证集 mAP50 E1 0.611 / E2 0.756；待 TelecomEval 评估与 TGB 会议 |
| M3 | 生成式增广（TG2） | W10 | | |
| M4 | 同配置再训练（TG3） | W12 | | |
| M5 | 融合升级（TG4） | W14 | | |
| M6 | 完整评估（TG5） | W15 | | |
| M7 | 交付 | W16 | | |

## 暂缓事项

| 记录日期 | 事项 | 当前状态 | 何时恢复 |
|---|---|---|---|
| 2026-09-28 | **TelecomEval 标注与冻结** | 候选图已人工筛选、去重，剩 31 张（`data/raw/t3_candidates/images/`，许可见 `data/licence_manifest.csv`）；已用临时 teacher（仅 Construction-PPE 训练）预标注 133 个框，并导入 Label Studio 项目 1（`python -m telecomsafe.data.labelstudio serve` 启动）。**尚未人工标注、未冻结**。张数远低于 150 的目标 | Demo v1 完成之后。恢复时：① 换更精准的检索词补搜一轮；② 不足 100 张则启用 D1，用安全带数据集留出部分补充高处作业场景；③ 标注 → `labelstudio pull` → `freeze_eval --create`；④ 用 TelecomEval 重新评估 E1/E2（在此之前评估暂用 val 集，结果只作开发参考） |

## 范围变更记录

| 日期 | 变更 | 原因 | 影响 |
|---|---|---|---|
| 2026-08-24 | 取消现场采集，改为纯公开数据来源 | 安全风险与成本过高（导师确认） | 真实数据量下降，更依赖生成式增广 |
| 2026-09-28 | 改为两阶段：先 Baseline Demo，后生成式增广 | 导师建议 | 生成式增广移到 W8–W10；新增决策门 TGB |
| 2026-09-28 | 阶段一只做 Workers + Machinery（默认执行 D8） | 单人完成，范围控制 | Terrain / Materials 阶段二视进度再加 |
| 2026-09-28 | 停用 harness（vgg2coco）数据集 | 下载后核对：标成 harness 的其实是反光背心，且为同一室内场景的摆拍视频帧 | 安全带只剩 body_harness 一个来源（去重后约 150 个实例） |
| 2026-09-28 | 停用 3 Construction Workers 数据集 | Roboflow 项目没有发布任何版本，无法导出 | 无 |
| 2026-09-28 | 新增 APD、construction safety v2（用户提供） | APD 提供大量真实工地的未穿反光衣样本；v2 补充安全帽与人员多样性 | APD 为他人分享的私有数据，仅限内部训练、不再分发 |
| 2026-09-29 | Construction Site Safety 从 Kaggle 镜像（Roboflow v28）换成 Roboflow v30 | Kaggle 版训练集全部是马赛克增广拼图：E1 不再是"无增广"对照，规则会把不同子图中的人和机械误判为相邻 | 该数据集从约 2,800 张降为 717 张原图；teacher、E1、E2 全部重训 |
