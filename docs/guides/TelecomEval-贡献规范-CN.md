# TelecomEval 贡献规范：每个人要交什么（2026-10-16）

> English version: [TelecomEval-Contribution-EN.md](TelecomEval-Contribution-EN.md)

**做法：** 每位组员交**至少 50 张已标注的图**，图片可以用任何方法收集或生成。所有人的图合起来组成 TelecomEval，也就是我们的真实电信场景测试集，冻结后不再改动。为了能自动合并和检查，每份贡献都使用同一种文件夹格式。

## 1. 要什么样的图

- **场景：** 有人在**室外对电信设施作业**：
  - 铁塔和桅杆
  - 屋顶天线和卫星天线
  - 路边机柜
  - 线缆沟槽和人井
  - 架空通信线

  电力线路作业（线杆、斗臂车、输电线路）也可以，作为单独的**相邻领域（near）**子集。50 张里最好至少 35 张是电信。
- **8 个类别都要出现**（见第 3 节），并且要做到：
  - 至少 5 张有**安全带**、5 张有**工程机械**（斗臂车、吊车、挖掘机、电缆盘拖车、高空作业平台）、5 张有普通**车辆**；
  - **也要有不合规的工人**：没戴安全帽、没系安全带、没穿反光衣。这正是模型要识别的风险。
- **质量：**
  - 建议短边**至少 1000 像素**（硬性下限 640 像素）；
  - 工人要看得清（身高约 80 像素以上）；
  - 不要室内办公室、实验室、机库，不要摆拍的合影、仪式、人像；
  - 不要插画、截图、带大块水印的图；
  - 同一次活动最多 2–3 张。
- **方法（任选，每张图都要在 `sources.csv` 里注明）：**

  | `method` | 含义 | 许可填写 |
  |---|---|---|
  | `collected` | 网上找到的开放许可照片，比如 Wikimedia Commons、Openverse、Flickr、美国政府网站 | `CC0`、`PDM`、`US-GOV`、`CC-BY` 或 `CC-BY-SA`（要填作者和来源链接），并在来源页面上确认过 |
  | `own_photo` | 自己拍的照片，同意以 CC BY 4.0 共享 | `OWN` |
  | `generated` | 用生图模型生成（如 GPT Image） | `GENERATED`，在 `creator` / `notes` 里写明模型和完整提示词 |

  生成图会作为单独的子集报告。为了让 TelecomEval 的大部分是真实照片，请把生成图控制在 50 张的**一半左右以内**。
- **不允许：**
  - **公开检测数据集里的图**（Roboflow Universe、Kaggle 等）：我们的训练数据就来自这类数据集，用了会造成泄漏。合并时会把每张图和训练集比对，近似重复的会被拒绝。
  - 带 NC（非商业）或 ND（禁止演绎）的 CC 许可。
  - Pexels、Unsplash、Pixabay、商业图库、新闻网站、社交媒体上的图。

## 2. 文件夹格式

```
TelecomEval_<你的名字>/
  images/        a.jpg, b.png ...
  labels/        a.txt, b.txt ...     每张图一个 YOLO 标注文件（同名，扩展名 .txt）
  sources.csv    每张图一行
```

**YOLO 标注文件：** 每个框一行，格式为 `类别id x中心 y中心 宽 高`，都归一化到 0–1。类别 id **必须**按下表的顺序。用 Roboflow、CVAT、LabelImg 等工具时，先按这个顺序建好类别再导出。

| id | 类别 | id | 类别 |
|---|---|---|---|
| 0 | `person` 人员 | 4 | `no_vest` 未穿反光衣 |
| 1 | `helmet` 安全帽 | 5 | `harness` 安全带 |
| 2 | `no_helmet` 未戴安全帽 | 6 | `machinery` 工程机械 |
| 3 | `vest` 反光衣 | 7 | `vehicle` 普通车辆 |

**`sources.csv`**（UTF-8 编码；用 Excel 编辑时选“另存为 → CSV UTF-8”）包含以下列：

```
file,subset,method,source_url,title,creator,licence,licence_version,licence_url,notes
tower_01.jpg,telecom,collected,https://commons.wikimedia.org/wiki/File:...,Tower climb,Jane Doe,CC-BY-SA,4.0,https://creativecommons.org/licenses/by-sa/4.0/,
pole_02.jpg,near,own_photo,,,你的名字,OWN,,,2026-10-18 摄于 Jurong
gen_03.png,telecom,generated,openai:gpt-image-2,,gpt-image-2 (medium),GENERATED,,,"<完整提示词>"
```

`subset` 填 `telecom` 或 `near`。

## 3. 怎么标注

以 `configs/taxonomy.yaml` 为准。

| 类别 | 框什么 | 规则 |
|---|---|---|
| `person` | 整个人可见的部分 | 身体可见部分超过一半才标 |
| `helmet` | 戴在头上的安全帽 | 放在地上、拿在手里的不标 |
| `no_helmet` | 没戴安全帽的头部 | 普通帽子、头巾、兜帽都算 `no_helmet` |
| `vest` | 穿着的反光背心或高可视性工作服（上身） | 只有带反光条的才算 |
| `no_vest` | 没穿反光衣的人的躯干 | 普通衣服、迷彩服 |
| `harness` | 穿在身上的全身式安全带 | 挂在结构上的绳子和挂钩不标；没系安全带不画框 |
| `machinery` | 机械整体，包括臂架 | 挖掘机、吊车、斗臂车、高空作业平台、放线车、电缆盘拖车 |
| `vehicle` | 车辆整体 | 普通轿车、皮卡、面包车、普通货车 |

**一致性规则：**
- 每个能看到头部的人，必须且只能标**一个** `helmet` 或 `no_helmet`。
- 每个能看到躯干的人，必须且只能标**一个** `vest` 或 `no_vest`。
- 铁塔、电线杆、天线本身不标。

**画框规则：**
- 框要**贴紧**可见部分。
- 人挨在一起时，每个人各画各的框。
- 远处的人看不清戴没戴安全帽时，照常标 `person`，但两种安全帽类别都不标。
- **作战头盔**（军用照片）的暂行规则：标 `helmet`，并在 `notes` 里写 `combat helmet`。

标注工具不限，只要能按上面的 id 导出 YOLO 格式即可。如果用本仓库的 Label Studio：

```
python -m telecomsafe.data.contrib annotate <文件夹>     # 用 E2 预标注，并建好 Label Studio 项目
python -m telecomsafe.data.contrib export <文件夹>       # 写出 labels/，并自动检查
```

**预标注只是起点：** 每个框都要人工检查。

## 4. 检查和提交

1. 如果你配好了本仓库的环境，运行 `python -m telecomsafe.data.contrib check <文件夹>`，把所有 ERROR 改掉；WARNING 是建议。没有环境的话，由负责人帮你检查。
2. 把文件夹压缩成 `TelecomEval_<你的名字>.zip`，放到组内共享文件夹。
3. 负责人用 `python -m telecomsafe.data.contrib intake <文件夹> --contributor <名字>` 合并每份贡献。这一步会重新检查，拒绝和训练集或其他人的图近似重复的图，再把全部内容复制到 `data/raw/telecom_eval/`。四个人的都合并后，冻结 TelecomEval 并开始评测。

**截止时间：** 在群里商定。TGB 会议在 W7（10 月 19 日那一周）。
