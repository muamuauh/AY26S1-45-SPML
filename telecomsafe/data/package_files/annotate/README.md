# TelecomEval 标注任务 / Annotation Task

> 仅限 TelecomSafe 项目组内使用，请勿外传。图片均为开放许可，逐图署名见 `ATTRIBUTION.csv`。
> For the TelecomSafe team only — please do not share. All images are openly licensed; per-image credits are in `ATTRIBUTION.csv`.

| | |
|---|---|
| 图片 / Images | **{n_images}** 张：电信施工 {n_telecom} · 电力线路作业 {n_near} / telecom {n_telecom} · power-line {n_near} |
| 预计耗时 / Effort | 约 {hours} 小时，可以分多次完成 / about {hours} hours, can be split over several sessions |
| 交付 / Deliverable | `deliverable/annotations.json`（由 export 脚本生成 / created by the export script） |
| 生成日期 / Built | {date} |

---

## 中文

### 要做什么
这些图片将组成 TelecomEval，即项目的**测试集**：它是衡量模型好坏的唯一标尺，标得准不准直接决定评估结果是否可信。

每张图都已经有模型生成的**预标注框**，你的工作是逐张：
1. **检查**每个预标注框：类别对不对、框得紧不紧；错的改掉，多余的删掉。
2. **补画**漏掉的框。**安全带（harness）和工程机械（machinery）基本没有预标注，需要你手画**。
3. 点 **Submit** 提交；图片不能用（看不清、没有人在作业、重复）就点 **Skip**。

具体怎么框、框哪些，见 **[GUIDELINES.md](GUIDELINES.md)**，开始前请完整读一遍。

### 怎么开始
先把压缩包**完整解压**到本地文件夹（例如 `D:\TelecomEval` 或桌面）。不要在压缩包里直接双击，也不要放在 OneDrive 等同步目录中。

| 系统 | 操作 |
|---|---|
| Windows | 双击 `start.bat` |
| macOS | 第一次：右键 `start.command` → 打开 → 再点"打开"（绕过"无法验证开发者"的提示）；之后直接双击 |

- **第一次**会自动安装 Python 3.12 和 Label Studio，约 5–10 分钟，需要联网，占用约 1.5 GB（装在 Windows 的 `%LOCALAPPDATA%\TelecomEval`、macOS 的 `~/.telecomeval`，不在本文件夹里）；之后启动只要几十秒。
- 启动后浏览器会自动打开登录页，**账号和密码显示在黑色窗口里**（每个人的包各不相同）。
- **标注期间不要关闭黑色窗口**，关闭它就会停止 Label Studio。下次再双击 `start` 即可从上次的进度继续，已提交的内容都会保留。
- 所有数据都保存在本文件夹的 `ls_data/` 里：**不要删除或移动这个文件夹**，否则进度会丢失。

### Label Studio 基本操作
| 操作 | 方法 |
|---|---|
| 画框 | 按类别对应的数字键（或点下方类别按钮），再在图上拖动 |
| 改类别 | 点选框 → 点另一个类别 |
| 删除框 | 点选框 → `Backspace` / `Delete` |
| 调整框 | 拖动框的边角 |
| 缩放 / 平移 | 鼠标滚轮缩放；按住空格拖动 |
| 提交 | `Submit`（`Ctrl + Enter`）；已提交后再修改点 `Update` |
| 跳过 | `Skip`（图片不可用时） |
| 下一张 | 提交后自动跳到下一张；也可以回到列表页（Data Manager）任意选择 |

### 交付
1. 全部完成后，**关闭黑色窗口**，然后双击 `export.bat`（macOS：`export.command`）。
2. 窗口里会显示进度：已标注、已跳过、未完成的张数，以及各类别的框数。"未完成"应为 0。
3. 把生成的 **`deliverable/annotations.json`** 上传到组内共享文件夹（或发给项目负责人）。

中途也可以随时导出，用来汇报进度。

### 常见问题
| 问题 | 解决 |
|---|---|
| 第一次安装失败 | 检查网络后重新双击 `start`。仍失败：删掉 `%LOCALAPPDATA%\TelecomEval`（macOS：`~/.telecomeval`）再试，并把窗口截图发给项目负责人 |
| 浏览器没有自动打开 | 手动打开窗口里显示的地址 |
| 忘记密码 | 再双击一次 `start`，窗口会重新显示；也保存在 `ls_data/package_state.json` |
| 提示端口 8089 被占用 | 已经有一个 Label Studio 在运行：关掉之前的黑色窗口再启动 |
| 某张图没有预标注框 | 正常：约 1/10 的图模型什么都没检出，直接手画即可。如果所有图都没有，把截图发给项目负责人 |
| macOS 提示"无法打开，因为无法验证开发者" | 右键 → 打开 → 打开；或在"系统设置 → 隐私与安全性"里点"仍要打开" |

---

## English

### What to do
These images will become TelecomEval, the project's **test set** — the single yardstick for the model, so careful labels make the evaluation trustworthy.

Every image already has **pre-labels** from the model. For each image:
1. **Check** every pre-label: right class, tight box. Fix the wrong ones, delete the extra ones.
2. **Add** missing boxes. **Harness and machinery are almost never pre-labelled — draw them yourself.**
3. Click **Submit**. If an image is unusable (unreadable, nobody working, duplicate), click **Skip**.

What to box and how is in **[GUIDELINES.md](GUIDELINES.md)** — please read it fully before you start.

### Getting started
First **extract the whole zip** to a local folder (e.g. `D:\TelecomEval` or the desktop). Do not double-click inside the zip, and do not use a OneDrive (or other synced) folder.

| System | Action |
|---|---|
| Windows | Double-click `start.bat` |
| macOS | First time: right-click `start.command` → Open → Open (gets past "unidentified developer"); afterwards just double-click |

- The **first run** installs Python 3.12 and Label Studio automatically: 5–10 minutes, internet needed, about 1.5 GB (in `%LOCALAPPDATA%\TelecomEval` on Windows, `~/.telecomeval` on macOS — not in this folder). Later starts take seconds.
- The browser opens the login page; **the email and password are shown in the black window** (each package has its own).
- **Keep the black window open while annotating** — closing it stops Label Studio. Double-click `start` again to continue where you left off; submitted work is kept.
- Everything is stored in this folder's `ls_data/`: **do not delete or move it**, or your progress is lost.

### Label Studio basics
| Action | How |
|---|---|
| Draw a box | Press the class's number key (or click the class button), then drag on the image |
| Change class | Select the box → click another class |
| Delete a box | Select the box → `Backspace` / `Delete` |
| Adjust a box | Drag its corners |
| Zoom / pan | Mouse wheel to zoom; hold Space and drag |
| Submit | `Submit` (`Ctrl + Enter`); after submitting, edits are saved with `Update` |
| Skip | `Skip` (unusable image) |
| Next image | Opens automatically after submitting; or go back to the list (Data Manager) |

### Hand-in
1. When everything is done, **close the black window**, then double-click `export.bat` (macOS: `export.command`).
2. The window shows annotated / skipped / not done counts and boxes per class. "Not done" should be 0.
3. Upload **`deliverable/annotations.json`** to the team's shared folder (or send it to the project lead).

You can export at any time to report progress.

### FAQ
| Problem | Fix |
|---|---|
| First-time setup fails | Check the internet connection and double-click `start` again. Still failing: delete `%LOCALAPPDATA%\TelecomEval` (macOS: `~/.telecomeval`), retry, and send a screenshot of the window to the project lead |
| The browser did not open | Open the address shown in the window |
| Forgot the password | Double-click `start` again — the window shows it; it is also in `ls_data/package_state.json` |
| Port 8089 already in use | Label Studio is already running: close the old black window and start again |
| An image has no pre-labels | Normal: the model found nothing in about 1 in 10 images — draw the boxes yourself. If no image has any, send a screenshot to the project lead |
| macOS: "cannot be opened because the developer cannot be verified" | Right-click → Open → Open, or System Settings → Privacy & Security → "Open Anyway" |
