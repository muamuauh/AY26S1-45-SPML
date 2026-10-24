# 第二阶段：为弱类别生成训练图（TelecomSynth）

> English version: [Phase2-Synth-Task-EN.md](Phase2-Synth-Task-EN.md)

**目标：** 第二阶段**只用生成图**来增强检测器。每位组员认领阶段一的一个弱类别，为它生成并标注 **300–400 张图**。所有人的图合起来称为 TelecomSynth，加入训练集训练 E3，再在冻结的 TelecomEval 上和 E2 比较。

## 1. 弱类别与认领

排序依据是 E2 在 TelecomEval 上的 AP50。认领人和截止时间在群里商定。

| 类别 | TelecomEval AP50 | 图里必须有什么 | 认领人 |
|---|---|---|---|
| `no_helmet` | 14.1% | 电信现场**没戴**安全帽的工人（光头、普通帽子、兜帽、头巾），包括远处、高处的小目标 | |
| `vehicle` | 26.4% | 电信现场的普通车辆：面包车、皮卡、轿车、普通货车，停在或行驶在作业点附近 | |
| `machinery` | 26.9% | 电信专用机械：斗臂车、高空作业平台、放线机（牵引机）、电缆盘拖车、小吊车、挖光缆沟的小挖掘机 | |
| `harness` | 29.9% | 爬**电线杆、铁塔**或在屋顶作业的工人身上的全身式安全带，远近、角度都要有变化 | |
| `no_vest` | 32.7% | **没穿**反光衣的工人：普通夹克、T 恤、迷彩服、没有反光条的雨衣 | |

**截止时间：** 群里商定。

## 2. 每张图的要求

1. **图里有你负责的类别。** 至少 80% 的图要有该类别的框，否则检查不通过。
2. **图里看得见的 8 类目标全部要标**，不只标你负责的那一类。漏标的目标会被模型当成“背景”，危害很大。类别表和一致性规则见 [TelecomEval-贡献规范-CN.md §3](TelecomEval-贡献规范-CN.md)：
   - 每个能看到头部的人，必须且只能标一个 `helmet` 或 `no_helmet`；
   - 每个能看到躯干的人，必须且只能标一个 `vest` 或 `no_vest`。
3. **每张单独生成，短边至少 1024 像素。**
   - 不要从拼图或多宫格里裁剪；
   - 不要拉伸或放大，按原图尺寸导出（Roboflow 导出时不要选 Resize）。
4. **写实的室外电信或电力线路作业。** 不要室内机房、插画或卡通。
5. **多样性：**
   - 地区（国家、城市或乡村）、天气、时间、机位远近和角度、人数都要变化；
   - **同一个场景或提示词最多 3 张变体**；
   - 合适的话同时包含“正”“负”两种 PPE 状态，例如 `harness` 那组里也要有人穿反光衣、有人不穿。
6. **不能碰 TelecomEval：**
   - 不要把 TelecomEval 的图当参考图或输入；
   - 不要复用生成 TelecomEval 那批图的提示词。

   合并时会把每张图和 TelecomEval 做比对，近似重复的会被拒绝。
7. **记录每张图怎么来的：** `sources.csv` 里 `creator` 填模型名（如 `gpt-image-2.5`、`Midjourney v7`），`notes` 填完整提示词。

## 3. 文件夹格式

格式和 TelecomEval 的贡献格式相同：

```
Phase2_<类别>_<你的名字>/
  images/        每张生成图一个文件（png / jpg / webp）
  labels/        每张图一个 YOLO 标注文件（类别 id：0 person、1 helmet、2 no_helmet、3 vest、
                 4 no_vest、5 harness、6 machinery、7 vehicle）
  sources.csv    file, subset, method, source_url, title, creator, licence, licence_version, licence_url, notes
```

`sources.csv` 里，`subset` 填 `telecom` 或 `near`（电力线路作业），`method` 填 `generated`，`licence` 填 `GENERATED`，`creator` 填模型名，`notes` 填提示词，其余列留空。

## 4. 各类别的提示词建议

从纪实摄影风格起步，再变换细节，例如：

> Candid documentary photograph, realistic and unstaged, people busy with the work and not looking at the camera, natural imperfections, no text or logos. *[发生了什么]*. Setting: *[地区]*. *[光线、天气]*, *[机位远近和角度]*.

| 类别 | *[发生了什么]* 的思路 | 标注易错点 |
|---|---|---|
| `no_helmet` | 戴棒球帽的技术员在路边机柜作业；两人没戴安全帽在拉线；戴兜帽的工人在线杆旁的梯子上；远处铁塔上有一人没戴安全帽 | 框住**整个头部**，包括头发和帽子，不只框脸。普通帽子、兜帽也算 `no_helmet` |
| `vehicle` | 光缆熔接帐篷旁停着开着车门的面包车；光缆沟边停着几辆皮卡；车辆驶过路边机柜施工点 | 看得见的车都要标，包括停着的、被挡住一部分的。斗臂车、吊车是 `machinery`，不是 `vehicle` |
| `machinery` | 斗臂车把线路工送到杆顶；电缆盘拖车往管道里放光缆；小挖掘机挖沟；高空作业平台靠近屋顶天线 | 框住机械整体，包括升起的臂架和斗。斗里的工人另外标 `person` |
| `harness` | 攀爬角钢塔并挂好安全绳的工人；用围杆带在木杆上作业的线路工；在屋顶边缘系好安全带的工人；从地面仰视、从旁边建筑平视等不同视角 | 框住身上的安全带主体（肩带、胸带、腿带），不框绳子和挂钩。没系安全带不画框 |
| `no_vest` | 穿普通工作服的班组在人井旁作业；穿 T 恤的技术员在梯子上；穿没有反光条雨衣的工人 | 每个没穿反光衣、能看到躯干的人都标 `no_vest`。带反光条的高可视性外套算 `vest` |

## 5. 标注与可选的预标注

标注工具不限，只要能按上面的 id 导出 YOLO 格式即可（Roboflow、CVAT、Label Studio 等）。

**可选：** 把**未标注**的图交给负责人，用阶段一的检测器做预标注：

```
python -m telecomsafe.data.synth prelabel <文件夹>      # 写出 <文件夹>/labels/，以及一个待填写的 sources.csv
```

拿回去后要**逐框检查修正**，补上漏标的框。预标注经常漏掉小目标和安全带，`no_helmet` 也常常判错。这一步只是为了省事，不是必须的流程。

## 6. 检查与提交

1. 如果你配好了本仓库的环境，运行：

   ```
   python -m telecomsafe.data.synth check <文件夹> --target <类别>
   ```

   把所有 ERROR 改掉。没有环境的话由负责人检查。
2. 把文件夹压缩成 `Phase2_<类别>_<你的名字>.zip`，放到组内共享文件夹。
3. 负责人用下面的命令合并：

   ```
   python -m telecomsafe.data.synth intake <文件夹> --contributor <名字> --target <类别>
   ```

   文件名会加上 `__<名字>` 后缀，保证每张图都能溯源。重新提交时只替换你这个类别的图。

## 7. 之后会怎样

负责人接下来会：

1. 组装 E3 训练集（`python -m telecomsafe.data.synth dataset`）；
2. 用 E2 的原配置训练 3 个种子（`python -m telecomsafe.train --exp e3 --seed 0/1/2 --name e3[_s1/_s2]`）；
3. 在 TelecomEval 上评测。

判断是否有提升**只看 TelecomEval 的真实照片**。TelecomEval 里也有生成图，在那部分上涨分可能只是模型学会了生成图的风格。
