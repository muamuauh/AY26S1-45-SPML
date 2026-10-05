# TelecomEval 图片收集任务：{title_zh} / Image Collection: {title_en}

> 仅限 TelecomSafe 项目组内使用，请勿外传。 / For the TelecomSafe team only — please do not share.

| | |
|---|---|
| 目标数量 / Target | **{target}** 张 / images |
| 预计耗时 / Effort | 约 {hours} 小时 / about {hours} hours |
| 交付 / Deliverable | `deliverable/TelecomEval_collect_{domain}_<日期 date>.zip`（由 check 脚本生成 / created by the check script） |
| 生成日期 / Built | {date} |

---

## 中文

### 为什么要收集
TelecomEval 是项目的测试集，用来衡量模型在**真实施工场景**中的表现。网上公开、并且许可允许使用的这类照片很少，目前{have_zh}。这次需要再找一批**{title_zh}**的照片。

### 要找什么样的图
**入选**：画面里**有人正在作业**，并且属于下面的场景之一。人要能看清楚（全身或大半身），能判断是否戴安全帽、穿反光衣、系安全带。

{scene_table_zh}

**不要**：只有设备没有人的照片；室内实验室、办公室、教室、培训中心；摆拍的人像；插画、示意图、截图、AI 生成图；带大块水印或文字的图；分辨率太低（短边不足 480 像素）；同一组照片里几乎一样的多张（每组最多选 3 张差异明显的）。

例图和更细的判断方法见 **[CRITERIA.md](CRITERIA.md)**，在哪里找、怎么确认许可见 **[SOURCES.md](SOURCES.md)**。

### 许可（最重要）
**只收以下许可**，并且要在图片的来源页面上**亲眼确认**：

| `licence` 填写 | 含义 | 还需填写 |
|---|---|---|
| `CC0` | CC0 公共领域贡献 | — |
| `PDM` | 公有领域标记 / "No known copyright restrictions" | — |
| `US-GOV` | 美国联邦政府作品（如 DVIDS、美国政府机构账号） | — |
| `CC-BY` | 署名 | 版本号、作者、许可链接 |
| `CC-BY-SA` | 署名-相同方式共享 | 版本号、作者、许可链接 |

**带 NC（非商业）或 ND（禁止演绎）的 CC 许可一律不收**。Pexels、Unsplash、Pixabay 等图库用的是自家许可，也不收；新闻网站、社交媒体、商业图库（Getty、Shutterstock 等）的图不收；自己拍的照片也先不收。

### 怎么做
1. 在本文件夹里新建 `submission/images/`，把找到的图片放进去。文件名用英文、数字、下划线，例如 `tower_climber_01.jpg`。
2. 把 `manifest_template.csv` 复制为 `submission/manifest.csv`，删掉示例行，**每张图填一行**：

| 列 | 填什么 |
|---|---|
| `file` | `images/` 里的文件名 |
| `source_url` | 图片所在的**页面**链接（不是图片文件本身的链接） |
| `title` | 页面上的标题 |
| `creator` | 作者名（CC-BY / CC-BY-SA 必填） |
| `licence` | 上表中的代码 |
| `licence_version` | 例如 `4.0`、`2.0`（CC-BY / CC-BY-SA 必填） |
| `licence_url` | 例如 `https://creativecommons.org/licenses/by/4.0/`（CC-BY / CC-BY-SA 必填） |
| `scene` | 场景代码：{scene_codes} |
| `notes` | 可选，备注 |

   用 Excel 编辑时请"另存为 → CSV UTF-8"。
3. 双击 `check.bat`（macOS：`check.command`，第一次右键 → 打开）。它会检查许可、必填项、分辨率，以及是否与项目里已有的 {n_seen} 张图重复（`data/seen.txt`）。第一次运行会自动安装所需工具，约 1–2 分钟。
4. 按报告修正错误，直到显示 **✓ All checks passed**。通过后会在 `deliverable/` 里生成压缩包，把它上传到组内共享文件夹（或发给项目负责人）。

可以分几次提交，每次检查通过就交一个压缩包。

### 之后会怎样
项目负责人会把你提交的图放进统一的审阅流程（自动打分 + 人工复核）。通过的图会进入标注，最终成为 TelecomEval 的一部分，你的署名信息会随图保存。

### 常见问题
| 问题 | 解决 |
|---|---|
| 报 "already in the project" | 这张图项目里已经有了（或被剔除过），换一张 |
| 报 "too small" | 在来源页面下载更大的尺寸（Wikimedia 点"原始文件"，Flickr 选"下载 → 大尺寸"） |
| 不确定许可 | 不确定就不要收 |
| `check` 窗口一闪而过或安装失败 | 检查网络后重试；仍失败把窗口截图发给项目负责人 |

---

## English

### Why
TelecomEval is the project's test set: it measures the model on **real construction scenes**. Openly licensed photos of this kind are scarce; at the moment {have_en}. This task collects more photos of **{title_en}**.

### What to look for
**Keep**: **people actively working** in one of the scenes below, visible enough (whole or most of the body) to tell whether they wear a helmet, a hi-vis vest and a harness.

{scene_table_en}

**Do not keep**: equipment without people; indoor labs, offices, classrooms or training centres; posed portraits; illustrations, diagrams, screenshots or AI-generated images; large watermarks or captions; low resolution (short side under 480 px); several near-identical shots from one series (at most 3 clearly different ones per series).

Examples and finer judgement calls are in **[CRITERIA.md](CRITERIA.md)**; where to search and how to confirm a licence is in **[SOURCES.md](SOURCES.md)**.

### Licences (most important)
**Only these licences**, each **confirmed by you on the image's source page**:

| `licence` code | Meaning | Also required |
|---|---|---|
| `CC0` | CC0 public domain dedication | — |
| `PDM` | Public Domain Mark / "No known copyright restrictions" | — |
| `US-GOV` | US federal government work (e.g. DVIDS, US agency accounts) | — |
| `CC-BY` | Attribution | version, creator, licence URL |
| `CC-BY-SA` | Attribution-ShareAlike | version, creator, licence URL |

**No CC licence with NC (non-commercial) or ND (no derivatives).** Pexels, Unsplash, Pixabay and similar sites use their own licences — not accepted; nor are images from news sites, social media or commercial stock libraries (Getty, Shutterstock...), nor your own photos for now.

### Steps
1. Create `submission/images/` in this folder and put the images there. Use English letters, digits and underscores in file names, e.g. `tower_climber_01.jpg`.
2. Copy `manifest_template.csv` to `submission/manifest.csv`, delete the example row and **add one row per image**:

| Column | Content |
|---|---|
| `file` | file name in `images/` |
| `source_url` | link to the **page** the image is on (not the image file itself) |
| `title` | title on that page |
| `creator` | author's name (required for CC-BY / CC-BY-SA) |
| `licence` | code from the table above |
| `licence_version` | e.g. `4.0`, `2.0` (required for CC-BY / CC-BY-SA) |
| `licence_url` | e.g. `https://creativecommons.org/licenses/by/4.0/` (required for CC-BY / CC-BY-SA) |
| `scene` | scene code: {scene_codes} |
| `notes` | optional |

   In Excel, use "Save As → CSV UTF-8".
3. Double-click `check.bat` (macOS: `check.command`; first time right-click → Open). It checks licences, required fields, resolution and duplicates against the {n_seen} images the project already has (`data/seen.txt`). The first run installs what it needs, 1–2 minutes.
4. Fix what the report lists until it says **✓ All checks passed**. A zip then appears in `deliverable/`; upload it to the team's shared folder (or send it to the project lead).

You can hand in several batches — one zip each time the check passes.

### What happens next
The project lead puts your images through the common review (automatic scoring plus a manual check). Accepted images are annotated and become part of TelecomEval, keeping your attribution data.

### FAQ
| Problem | Fix |
|---|---|
| "already in the project" | The project already has (or rejected) this image — pick another |
| "too small" | Download a larger size from the source page (Wikimedia: "Original file"; Flickr: Download → a large size) |
| Unsure about the licence | If unsure, leave it out |
| The `check` window flashes or setup fails | Check the internet connection and retry; otherwise send a screenshot to the project lead |
