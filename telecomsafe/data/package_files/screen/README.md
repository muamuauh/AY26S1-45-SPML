# TelecomEval 候选图筛选任务 / Screening Task

> 仅限 TelecomSafe 项目组内使用，请勿外传。图片均为开放许可，逐图署名见 `ATTRIBUTION.csv`。
> For the TelecomSafe team only — please do not share. All images are openly licensed; per-image credits are in `ATTRIBUTION.csv`.

| | |
|---|---|
| 本包 / This package | 第 {part} 份 / share {part} |
| 图片 / Images | **{n_images}** 张：新候选 {n_new} · 第一轮已保留、需按新标准重筛 {n_round1} / new {n_new} · kept in round 1, to re-check {n_round1} |
| 预计耗时 / Effort | 约 {hours} 小时 / about {hours} hours |
| 交付 / Deliverable | 浏览器导出的 `{export}` / the exported `{export}` |
| 生成日期 / Built | {date} |

---

## 中文

### 要做什么
TelecomEval 是项目的**真实电信场景测试集**，第一轮筛出的图很多分辨率低、场景单一。这次要从新收集的高清候选图里重新挑选，并把第一轮保留的图按同样的新标准再过一遍。

你只需要**逐张做判断**：电信（1）、相邻领域（2）或排除（X）。不用画框，标注是下一个任务。

### 怎么开始
1. 把压缩包**完整解压**到本地文件夹。
2. 双击 `open_review.bat`（macOS：`open_review.command`，第一次右键 → 打开），或者直接用 Chrome / Edge / Firefox 打开 `review.html`。不需要联网，也不需要安装任何东西。
3. 页面上方有判断标准的简要说明，下面是完整版。

### 判断标准
**电信（按 1）**：有人在**室外**对电信设施作业：
- 爬铁塔、在塔上作业（角钢塔、单管塔）
- 安装屋顶天线、卫星天线
- 在路边通信机柜作业
- 在线缆沟槽、人井里拉线或熔接光纤
- 架设或维修架空通信线缆

**相邻领域（按 2）**：电力线路作业，例如爬电线杆、在斗臂车或高空作业平台上作业、输电线路作业。分不清是通信线还是电力线时，选相邻领域。

**排除（按 X）**：
- 室内：办公室、实验室、教室、帐篷、机库
- 摆拍的合影、仪式、人像
- 插画、示意图、截图
- 画面里没有人在作业
- 纯军事场景（作战装备、武器、军车），且没有电信作业
- 模糊，或工人太小：身高不到约 80 像素。每张卡片上的尺寸标签是原图大小，可按空格放大查看
- 和已保留的图几乎一样：同一次活动的一组照片**最多留 2–3 张**差异明显的

**优先保留**能看清 PPE 的图：安全帽、登高头盔、安全带、反光衣；**没有**佩戴这些的工人同样重要，它们正是模型要识别的风险。

**关于军用头盔：** 很多照片里的人戴作战头盔、穿迷彩服。只要确实是室外电信作业就保留，标注时怎么处理由组内另行决定。

### 页面操作
| 操作 | 方法 |
|---|---|
| 判断 | 按 `1` 电信 · `2` 相邻领域 · `X` 排除；或点卡片下方按钮 |
| 移动 | `←` `→`（判断后自动跳到下一张） |
| 放大 | 空格；再按空格或点图片关闭 |
| 清除判断 | `0` |
| 筛选显示 | 顶部的 Pending / Telecom / Near / Reject / All 按钮 |

- 卡片上的标签：`with head` 是模型检测到能看见头部的人数；`round 1: telecom/near` 表示第一轮保留过，**请按新标准重新判断**。
- 有些卡片一开始就标成 Reject（`auto: no person, low score`）：模型认为没有人、也不像作业场景。看到误判就改掉。
- 判断会**自动保存在当前浏览器里**，可以分多次完成；请始终用同一个浏览器打开，并且不要清除浏览器数据。

### 交付
1. 全部判断完后（`Pending` 为 0），点右上角 **Export decisions**。
2. 浏览器会下载 `{export}`。把它上传到组内共享文件夹，或发给项目负责人。

中途也可以导出，用来汇报进度；以最后一次导出为准。

---

## English

### What to do
TelecomEval is the project's **real-world telecom test set**. Many images kept in round 1 are low-resolution and repetitive, so we are choosing again from new high-resolution candidates, and re-checking the round-1 images against the same, stricter criteria.

You only **decide per image**: telecom (1), near (2) or reject (X). No boxes — annotation is a separate task.

### Getting started
1. **Extract the whole zip** to a local folder.
2. Double-click `open_review.bat` (macOS: `open_review.command`; first time right-click → Open), or open `review.html` in Chrome, Edge or Firefox. No internet or installation needed.
3. The page header has a short version of the criteria; the full version is below.

### Criteria
**Telecom (press 1):** someone working **outdoors** on telecom infrastructure:
- climbing or working on a lattice tower or monopole
- installing rooftop antennas or satellite dishes
- working at a roadside telecom cabinet
- pulling or splicing cable in a trench or manhole
- stringing or repairing overhead telecom cable

**Near (press 2):** power-line work, e.g. climbing utility poles, working from a bucket truck or aerial work platform, transmission-line work. If you cannot tell telecom cable from power line, choose near.

**Reject (press X):**
- Indoors: offices, labs, classrooms, tents, hangars
- Posed group photos, ceremonies, portraits
- Illustrations, diagrams, screenshots
- Nobody working in the picture
- Purely military scenes (combat gear, weapons, military vehicles) with no telecom work
- Blurry, or the workers are tiny: under about 80 px tall. The size tag on each card is the original size; press Space to enlarge
- Near-duplicates of an image already kept: keep **at most 2–3 clearly different** photos from one event

**Prefer** images where PPE can be judged: hard hats, climbing helmets, harnesses, hi-vis vests. Workers **without** them matter just as much — those are the risks the model must recognise.

**Military helmets:** many photos show combat helmets and camouflage. Keep them if they really show outdoor telecom work; how to label them will be decided by the team.

### Using the page
| Action | How |
|---|---|
| Decide | `1` telecom · `2` near · `X` reject, or the buttons under each card |
| Move | `←` `→` (moves on automatically after a decision) |
| Enlarge | Space; Space again or click the image to close |
| Clear a decision | `0` |
| Filter | Pending / Telecom / Near / Reject / All buttons at the top |

- Card tags: `with head` is the number of people with a visible head found by the model; `round 1: telecom/near` means it was kept in round 1 — **please judge it again with the new criteria**.
- Some cards start as Reject (`auto: no person, low score`): the model saw nobody and no work scene. Change any it got wrong.
- Decisions are **saved automatically in this browser**, so you can work in several sessions. Always use the same browser and do not clear its data.

### Hand-in
1. When everything is decided (`Pending` is 0), click **Export decisions** at the top right.
2. The browser downloads `{export}`. Upload it to the team's shared folder, or send it to the project lead.

You can export at any time to report progress; the last export counts.
