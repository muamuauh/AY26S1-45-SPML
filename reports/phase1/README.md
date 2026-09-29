# 阶段一成果总结 · Baseline Demo v1

> 状态（2026-09-29）：Baseline 模型、规则判断与 Demo v1 已完成；**TelecomEval 暂缓**（见 [progress/milestones.md](../../progress/milestones.md#暂缓事项)），
> 下列指标都在**验证集**上测得。验证集与训练集同源，数字偏乐观，仅作开发参考；TelecomEval 建好后需重新评估并更新本页。

## 一句话结论

用 5 个公开数据集去重后的 5,537 张图训练的 YOLO11s baseline，在验证集上 mAP50 = **0.756**（E2）；Ultralytics 默认的传统增广比完全不增广（E1，0.611）提升 **+14.5 个点**，8 个类别全部提升。最弱的是车辆、未戴安全帽与工程机械；安全带在验证集上看似很高，但在电信施工图上几乎检不出来——这是阶段二生成式增广的首要目标。

## 数据

- 数据集来源、链接、许可与实际张数：[`data/README.md`](../../data/README.md)
- 统计：[`dataset_stats.csv`](dataset_stats.csv) ｜ 标注覆盖：[`coverage.csv`](coverage.csv) ｜ 许可：[`dataset_licences.csv`](dataset_licences.csv)

| 数据集 | 训练 / 验证 | 主要贡献 |
|---|---|---|
| Construction Site Safety（Roboflow v30，未增广） | 615 / 68 | 全部 7 类；工程机械与车辆的唯一来源 |
| APD（他人分享，仅内部训练） | 2,033 / 226 | 未穿反光衣（真实国内工地） |
| Ultralytics Construction-PPE | 1,187 / 132 | 人员、安全帽、反光衣 |
| construction safety v2 | 1,010 / 112 | 人员、安全帽 |
| body_harness | 139 / 15 | 安全带（唯一来源） |

- 去重（pHash）删除 898 张：主要是视频相邻帧与跨 split 的重复。
- 各数据集没有标注的类别由 teacher 模型补伪标签，伪标签占全部标注框的 **18.0%**（5,495 / 30,535）。

![训练集各类别实例数](class_distribution.png)

## 实验（验证集，553 张）

| 实验 | 训练数据 | mAP50 | mAP50-95 | Precision | Recall |
|---|---|---|---|---|---|
| E1 | 公开数据，关闭全部内置增广 | 0.611 | 0.350 | 0.690 | 0.630 |
| E2 | 公开数据 + Ultralytics 默认传统增广 | **0.756** | **0.499** | 0.825 | 0.711 |

训练配置见 [`configs/baseline.yaml`](../../configs/baseline.yaml)（YOLO11s，640px，100 epoch，seed 0）。E1 在第 42 个 epoch 早停，E2 跑满 100 个 epoch。逐类结果：[`per_class_ap.csv`](per_class_ap.csv)

![逐类 AP50：E1 vs E2](per_class_ap.png)

混淆矩阵：[E1](e1_confusion_matrix.png) ｜ [E2](e2_confusion_matrix.png)

## Demo v1

```
python -m telecomsafe.demo.app --weights runs/phase1/e2/weights/best.pt
```

检测 → 规则判断 → 风险等级，单图推理 0.5–1.4 秒（RTX 4070 SUPER，启动时预热模型）。示例图来源与许可见 [`demo_examples/ATTRIBUTION.md`](demo_examples/ATTRIBUTION.md)，均未参与训练。

| 案例 | 预期 | 实际 | 结果 |
|---|---|---|---|
| 合规作业（电信施工） | 低 | 低 · 未发现违规 | [截图](demo_results/1_compliant.jpg) |
| 未戴安全帽 | 中 | 中（R1、R2） | [截图](demo_results/2_no_helmet.jpg) |
| 人员靠近作业机械 | 高 | 高（R4） | [截图](demo_results/3_near_machinery.jpg) |
| 杆上作业未穿反光衣 | 低 | 低（R2）；安全带漏检 | [截图](demo_results/4_no_vest_on_pole.jpg) |
| **失败案例**：爬杆工人未戴安全帽、系安全带 | 中 | 低 · 未发现违规；两者均漏检 | [截图](demo_results/5_failure_pole_climber.jpg) |

## 弱类别清单（阶段二生成目标）

见 [`weak_classes.md`](weak_classes.md)。建议生成优先级：**安全带 ≈ 车辆 > 工程机械（电信专用车辆与设备） > 未戴安全帽 > 未穿反光衣**。

## 过程中发现并修正的问题

- **数据集标注与名称不符**：harness（vgg2coco）标成"安全带"的其实是反光背心 → 停用。
- **数据集内置增广**：Construction Site Safety 的 Kaggle 版本（= Roboflow v28）训练集全部是马赛克拼图，E1 因此不再是"无增广"对照，规则还会把不同子图里的人和机械误判为相邻 → 换成未增广的 v30，teacher、E1、E2 全部重训。修正前的 E2 mAP50 为 0.869，修正后 0.756，下降部分来自拼图带来的虚高。
- **规则误报**：驾驶室里的操作员被判为"靠近机械"→ 规则 R4 排除"人框在机械框内且脚明显高于机械底部"的情况。

## 局限性

- **评估**：尚未在 TelecomEval 上评估；验证集与训练集同源，指标偏乐观。
- **安全带**：训练实例仅 143 个、来源单一，验证集 AP50 = 0.984 不可信；在 31 张电信施工图上一个都没检出。
- **伪标签**：占 18%；teacher 在见过的图上很少补出原本就缺的类别（Construction-PPE 几乎没有补出未穿反光衣）。
- **规则**：人机距离按人框高度换算，是不考虑景深的单目近似。
- **数据来源**：APD 为他人分享的私有数据，图片来自新闻网站，仅用于内部训练、不再分发。

## 下一步

1. 恢复 TelecomEval：补搜、标注、冻结，然后在 TelecomEval 上重新评估 E1 / E2 并更新本页。
2. TGB 会议（W7 末）：按阶段一计划中的展示方案汇报，现场运行 Demo，同时准备录屏作为备份。
3. 进入阶段二（M3，W8–W10）：以弱类别清单为目标做生成式增广；E3 沿用 `configs/baseline.yaml`，只改训练数据。
