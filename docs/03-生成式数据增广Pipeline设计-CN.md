# 生成式数据增广 Pipeline 设计

> 文档版本：v1.0 ｜ 生成日期：2026-08-18
> 英文对照版：[03-Generative-Augmentation-Pipeline-EN.md](03-Generative-Augmentation-Pipeline-EN.md)
> 这是 TelecomSafe 的**核心创新模块**，对应项目简介中 `generative AI is introduced to address the scarcity of training data`

---

## 一、设计原则

在写任何代码前，先确立四条原则，它们决定了这个 pipeline 是"学术贡献"还是"调用 API 生成一堆图"：

| # | 原则 | 说明 |
|---|------|------|
| 1 | **标注必须自带** | 合成图像若还要人工标注，就失去了解决数据稀缺的意义。所有生成路线都必须设计成"生成即标注" |
| 2 | **质量必须可筛** | 生成模型会产生幻觉（六指工人、悬浮安全帽、结构错乱的铁塔）。**必须有自动闸门**，宁可丢弃 50% 也不能污染训练集 |
| 3 | **优先补长尾** | 生成数据的价值在于**真实世界拍不到的场景**（工人未系安全带在塔上探身），而不是复制常见样本。这也是提升最显著的地方 |
| 4 | **真实测试集不可污染** | 测试集全程只用真实图像，且这些图像不得参与生成模型的微调，否则实验结论无效 |

---

## 二、Pipeline 总览

```
                        ┌─────────────────────────┐
                        │  Stage 0: 风险场景规格库  │
                        │  Risk Scenario Spec      │
                        │  (风险类别 × 场景 × 条件) │
                        └───────────┬─────────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                ▼                   ▼                   ▼
    ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
    │ Stage 1        │  │ Stage 1'       │  │ Stage 1''      │
    │ 领域适配        │  │ 条件图构建      │  │ 提示词合成      │
    │ LoRA 微调       │  │ Seg/Pose/Depth │  │ Prompt Builder │
    └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
            └───────────────────┼───────────────────┘
                                ▼
              ┌──────────────────────────────────────┐
              │  Stage 2: 四路生成引擎                 │
              │  ① T2I 全新场景  ② ControlNet 布局控制  │
              │  ③ Inpainting 局部编辑  ④ 背景替换      │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │  Stage 3: 标注自动生成                 │
              │  布局图直转 / 掩码继承 / GDINO+SAM 兜底 │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │  Stage 4: 四道质量闸门 ★关键★          │
              │  G1 语义 → G2 分布 → G3 标注 → G4 抽检 │
              └──────────────────┬───────────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │  Stage 5: 配比与课程式混合训练          │
              │  Real : Synth 比例调度 + 损失加权       │
              └──────────────────────────────────────┘
```

---

## 三、Stage 0：风险场景规格库（最容易被跳过，但最重要）

不要"想到什么生成什么"。先建一张**结构化规格表**，让生成过程可枚举、可覆盖、可统计。

### 规格维度

```yaml
risk_scenario:
  id: TS-W-003
  dimension: workers            # terrain | machinery | materials | workers
  risk_type: missing_fall_arrest
  description: "工人在铁塔高处作业未系安全带"
  severity: critical

  scene_context:                # 场景上下文（决定背景）
    - cell_tower_lattice        # 格构式通信塔
    - monopole_tower            # 单管塔
    - rooftop_antenna           # 楼顶天线
    - cable_trench              # 光缆沟槽
    - equipment_room            # 机房

  environment:                  # 环境变量（决定鲁棒性覆盖）
    weather:  [sunny, overcast, rain, fog, snow]
    lighting: [daylight, dusk, night_floodlight, backlight]
    season:   [summer, winter]

  viewpoint:                    # 视角
    - ground_upward
    - drone_level
    - drone_top_down
    - tower_mounted_camera
    - handheld_close

  target_count: 120             # 该场景目标生成数量
```

### 覆盖矩阵设计

| 维度 | 细类数量（建议） | 说明 |
|------|---------------|------|
| Terrain | 5–6 | 平整 / 坑洼 / 积水 / 开放沟槽 / 斜坡 / 松软回填 |
| Machinery | 6–8 | 挖掘机 / 吊车 / 钻孔机 / 牵引机 / 发电机 / 高空作业车 + 违规状态 |
| Materials | 5–6 | 线缆盘 / 钢材 / 塔材 / 水泥件 / 工具箱 + 堆放不当状态 |
| Workers | 8–10 | 无安全帽 / 无反光衣 / 无安全带 / 无手套 / 攀爬违规 / 探身 / 单人高空作业 / 违规站位 |

> **总规格数目标：25–30 个风险场景 × 环境组合**。每个场景生成 100–150 张（这个数量有实证依据：Lee 等人 2025 年的研究发现最优增广规模在 100–150 张/类别区间）。

---

## 四、Stage 1：领域适配（LoRA 微调）

### 目标
让基础模型"认识"电信施工的视觉特征——格构塔、天线抱杆、馈线、光缆盘、机房机柜、爬梯，这些在通用模型里通常生成得很失真。

### 配置建议

```python
# LoRA 微调关键超参
base_model     = "stabilityai/stable-diffusion-xl-base-1.0"
lora_rank      = 32              # 16–32，数据少取小
lora_alpha     = 32
learning_rate  = 1e-4
train_steps    = 1500-3000       # 500 张数据约 2000 步
resolution     = 1024
batch_size     = 1
grad_accum     = 4
mixed_precision= "fp16"
# 训练目标：注入领域外观，不要过拟合到具体某张图
```

### 数据准备要点

| 要点 | 做法 |
|------|------|
| 数据来源 | **只用不属于测试集的真实电信图像**（200–500 张） |
| 字幕生成 | 用 BLIP-2 或 Qwen2-VL 自动生成 caption，再人工修正关键术语 |
| 触发词 | 设一个稀有触发词（如 `tlcmsite`），推理时加入以激活领域风格 |
| 过拟合监控 | 每 500 步生成一批样本，人工看是否开始复刻训练图 |

### 分层 LoRA 策略（进阶）

训练 2–3 个独立 LoRA 并在推理时组合，比单个大 LoRA 更可控：

- `lora_scene`：电信场地整体风格（塔、机房、沟槽）
- `lora_ppe`：PPE 外观细节（安全帽、反光衣、安全带）
- `lora_machinery`：施工机械

推理时按场景需要加权叠加：`scene(0.8) + ppe(0.6)`。

---

## 五、Stage 2：四路生成引擎

### 路线 ①：Text-to-Image（全新场景）

**用途**：生成真实世界完全缺失的稀有危险场景
**标注成本**：需 Stage 3 自动标注兜底
**产出占比建议**：20%

**结构化提示词模板**（比自由写更稳定，也便于消融实验）：

```
[TRIGGER] [VIEWPOINT], [SUBJECT + STATE], [CONTEXT], [ENVIRONMENT], [STYLE], [QUALITY]

示例：
tlcmsite, ground-level upward view, a construction worker climbing a lattice
telecommunication tower without a fall-arrest harness, wearing an orange
high-visibility vest but no safety helmet, steel lattice structure with antennas,
overcast sky, light rain, photorealistic documentary photograph, 
sharp focus, natural lighting, 35mm lens

Negative: cartoon, illustration, 3d render, deformed hands, extra limbs,
floating objects, distorted metal structure, watermark, text, blurry
```

**三种提示策略（建议做对比实验，这是一个现成的消融点）**：

| 策略 | 说明 | 预期效果 |
|------|------|---------|
| Zero-shot | 单句自然语言描述 | 基线，多样性高但可控性差 |
| Structured | 上述结构化模板 | 一致性明显更好 |
| **Image-guided structured** | 结构化模板 + IP-Adapter 参考真实图 | **最优**（已有研究支持此结论） |

### 路线 ②：ControlNet 布局控制 🌟 强烈推荐

**用途**：精确控制目标位置与结构
**标注成本**：**零**（布局图直接就是标注）
**产出占比建议**：40%

```
工作流：
  1. 从真实图像提取条件图（Canny / Depth / Seg / OpenPose）
     或 程序化生成语义布局图（随机放置目标框 → 填色）
  2. 语义布局图 → ControlNet-Seg → 生成写实图像
  3. 布局图的每个色块 = 一个实例的分割掩码 = 标注 GT
  4. 从掩码反算边界框 → COCO 格式标注
```

**关键技巧**：
- **姿态控制生成不安全行为**：用 OpenPose 骨架图指定"攀爬""探身""下蹲"的关键点，生成对应图像。骨架本身就是姿态标注，可直接喂给 ST-GCN 训练
- **深度控制生成地形**：用程序化生成的深度图（加入坑洼、沟槽起伏）→ ControlNet-Depth → 得到带地形分割 GT 的图像
- **组合控制**：Seg（布局）+ Depth（地形）+ Pose（人物）多 ControlNet 并联，条件越强，标注越准

### 路线 ③：Inpainting 局部编辑 🌟 性价比最高

**用途**：在真实图像上做**最小改动**产生新样本
**标注成本**：**近乎零**（标注可继承）
**产出占比建议**：30%

**四种高价值编辑操作**：

| 操作 | 做法 | 得到的样本 |
|------|------|-----------|
| **PPE 移除** | SAM 分割出安全帽区域 → inpaint 为头部 | 未戴安全帽的正样本，人框位置不变 |
| **PPE 添加/换色** | 在头部区域 inpaint 生成不同颜色安全帽 | 增加 PPE 颜色多样性 |
| **对象注入** | 在指定位置 inpaint 一台挖掘机 | 新增机械实例，框位置由掩码给出 |
| **状态转换** | 把整齐的材料堆 inpaint 成倾斜杂乱堆 | 材料堆放不当样本 |

```python
# PPE 移除示例逻辑
mask = SAM.segment(image, point_prompt=helmet_center)   # 得到安全帽掩码
mask = dilate(mask, kernel=5)                            # 略微扩张避免边缘残留
new_image = sd_inpaint(
    image, mask,
    prompt="a construction worker's bare head with short dark hair, "
           "no helmet, natural skin, photorealistic",
    strength=0.95
)
# 标注变更：person 框不变；helmet 实例删除；label: no_helmet
```

> **为什么这条路线最值得投入**：它保留了真实图像的背景、光照、噪声分布，域间隙最小，同时精确产生了最难获取的**违规样本**。真实世界里工人违规的照片本就稀少且难以合法拍摄——生成式方案在这里既解决数据问题又规避了伦理问题，这个论点在论文里非常有力。

### 路线 ④：背景替换 / 环境迁移

**用途**：鲁棒性数据（同一场景的雨、雾、夜间、逆光版本）
**产出占比建议**：10%

- 用 SAM 分离前景（人/机械）→ inpaint 替换背景
- 或用 img2img 低强度（strength 0.3–0.5）+ 环境提示词做整体风格迁移
- 标注完全不变，**这是构建 E7 鲁棒性测试集的最经济方式**

---

## 六、Stage 3：标注自动生成

| 生成路线 | 标注来源 | 可靠性 |
|---------|---------|--------|
| ② ControlNet-Seg | 输入布局图直接转换 | ⭐⭐⭐⭐⭐ 完美 |
| ② ControlNet-Pose | 输入骨架即关键点 GT | ⭐⭐⭐⭐⭐ 完美 |
| ③ Inpainting | 从原图标注继承 + 掩码修正 | ⭐⭐⭐⭐⭐ 很好 |
| ④ 背景替换 | 原标注不变 | ⭐⭐⭐⭐⭐ 完美 |
| ① T2I | **需要自动标注器** | ⭐⭐⭐ 需过滤 |

**T2I 路线的自动标注方案**：

```
Grounding DINO (文本提示 = 该场景规格中的类别列表)
        ↓  得到边界框 + 置信度
     置信度阈值过滤 (>0.35)
        ↓
     SAM 2 (框提示) → 精细掩码
        ↓
     与生成提示词做一致性核对：
       提示说"无安全帽"却检出 helmet → 丢弃该图
        ↓
     输出 COCO 标注
```

> **一致性核对这一步是关键**：生成模型经常"不听话"——你要求无安全帽，它照样画一顶。不做这个核对，会引入大量标签噪声，直接导致 E3 实验失败。

---

## 七、Stage 4：四道质量闸门 ★项目成败在此★

```
生成图像
   │
   ├─ G1 语义一致性闸门 ──────────────────────────────────
   │    CLIP-Score(image, prompt) > 0.28
   │    VLM 语义审核：问 Qwen2.5-VL"图中工人戴安全帽了吗"
   │    → 与规格标签不符则丢弃
   │    预期淘汰率：15–25%
   │
   ├─ G2 分布一致性闸门 ──────────────────────────────────
   │    单图：与真实图像集的最近邻特征距离 < 阈值
   │    整批：FID(synth_set, real_set) < 50
   │         KID < 0.05
   │    → 超标则回退调整提示词/LoRA 强度
   │    预期淘汰率：10–15%
   │
   ├─ G3 标注可靠性闸门 ──────────────────────────────────
   │    用真实数据训练的 baseline 检测器推理该合成图
   │    · 检测结果与自动标注 IoU > 0.5 的比例 > 70% → 通过
   │    · 完全检不出任何目标 → 图像失真，丢弃
   │    · 检出大量标注中没有的目标 → 标注漏标，丢弃
   │    预期淘汰率：10–20%
   │
   ├─ G4 人工抽检闸门 ────────────────────────────────────
   │    随机抽 5% 人工评分（真实性 1–5 分，标注正确性 Y/N）
   │    平均真实性 < 3.0 → 整批退回
   │    标注正确率 < 90% → 整批退回
   │    ≥3 名评分者，报告一致性 Kappa
   │
   ▼
最终合成数据集（预期总保留率 50–65%）
```

**重要提示**：G3 存在一个微妙的循环论证风险——用 baseline 检测器筛选数据，再用筛后数据训练检测器，可能只保留了"模型已经会的"样本，反而削弱增广效果。**缓解办法**：G3 只用于剔除**极端失败**（完全检不出 / 大量幻觉目标），阈值设宽松，不要用它做精细筛选。这个讨论本身也值得写进论文的 Limitations。

---

## 八、Stage 5：混合训练策略

### 5.1 配比调度

| 策略 | 说明 | 推荐 |
|------|------|------|
| 固定配比 | Real : Synth = 1 : 0.5 / 1 : 1 / 1 : 2 | ⭐⭐⭐⭐ 简单，做 E5 扫描 |
| **课程式（Curriculum）** | 前期高合成比例（学特征）→ 后期降至纯真实（对齐分布） | ⭐⭐⭐⭐⭐ **推荐**，通常最优 |
| 类别自适应 | 长尾类别合成比例高，常见类别低 | ⭐⭐⭐⭐⭐ **与原则 3 一致，强烈推荐** |
| 两阶段 | 阶段一：合成数据预训练；阶段二：真实数据微调 | ⭐⭐⭐⭐ 稳健，易实现 |

**推荐组合：类别自适应配比 + 两阶段训练**

```python
# 类别自适应合成配比
for cls in classes:
    n_real = count_real(cls)
    # 长尾类别补更多，但设上限避免合成数据主导
    n_synth = min(max(0, TARGET_PER_CLASS - n_real), 3 * n_real + 100)
```

### 5.2 损失加权

给合成样本一个略低的损失权重，降低标签噪声的影响：

```python
loss = loss_real + lambda_synth * loss_synth     # lambda_synth ≈ 0.7–0.9
```

也可用**置信度加权**：Stage 4 中 CLIP-Score 越高的样本权重越大。

### 5.3 验证纪律（必须严格遵守）

```
train:  真实数据 + 合成数据
val:    仅真实数据          ← 用于早停与超参选择
test:   仅真实数据，严格隔离 ← 只在最终评估时使用一次
```

⚠️ **合成数据绝不可进入 val 或 test**。这是最容易犯、也最致命的实验错误。

---

## 九、Pipeline 消融实验设计（论文的重要组成）

| 消融项 | 对比设置 | 回答的问题 |
|--------|---------|-----------|
| A1 | 无 LoRA vs 有 LoRA | 领域适配是否必要？ |
| A2 | Zero-shot vs Structured vs Image-guided prompt | 提示策略的影响 |
| A3 | 单路生成 vs 四路混合 | 生成路线多样性的价值 |
| A4 | 无闸门 vs G1 vs G1+G2 vs 全闸门 | **质量闸门的贡献（重要）** |
| A5 | 固定配比 vs 类别自适应 | 配比策略的影响 |
| A6 | 各基础模型（SDXL/SD3.5/FLUX） | 生成模型选型的影响 |
| A7 | 合成数据规模（500/1k/3k/5k/10k） | 边际收益曲线，找拐点 |

> A4 通常能得到最漂亮的结果：**无闸门的合成数据往往让性能下降**，加上闸门后由降转升。这个反转是论证质量控制必要性的最强证据。

---

## 十、工程实现建议

### 目录结构

```
telecomsafe/
├── data/
│   ├── real/              # 真实数据（DVC 管理）
│   │   ├── seed/          # LoRA 微调用
│   │   ├── train/
│   │   ├── val/
│   │   └── test/          # 🔒 严格隔离
│   └── synth/
│       ├── raw/           # 生成原始输出
│       ├── filtered/      # 通过闸门
│       └── rejected/      # 被拒样本（保留用于分析与论文图表）
├── specs/
│   └── risk_scenarios.yaml    # Stage 0 规格库
├── gen/
│   ├── lora_train.py
│   ├── prompt_builder.py
│   ├── engines/           # t2i / controlnet / inpaint / bg_replace
│   ├── auto_label.py
│   └── gates/             # g1_semantic / g2_distribution / g3_detector / g4_human
├── perception/
├── fusion/
├── eval/
└── configs/
```

### 生成吞吐估算

| 配置 | 单图耗时 | 3000 张耗时 |
|------|---------|------------|
| SDXL 30 步 @1024 (RTX 4090) | 约 6–8 秒 | 约 6 小时 |
| SDXL-Turbo 4 步 @1024 | 约 1 秒 | 约 1 小时 |
| + ControlNet | ×1.3–1.5 | 相应增加 |
| + 闸门筛选（CLIP/FID/检测） | 约 0.3 秒/图 | 约 15 分钟 |

> 结论：**批量生成用 SDXL-Turbo，最终成品用完整 SDXL**。3000 张合成数据在单张 4090 上一晚上可以跑完，算力不是瓶颈——**瓶颈是规格库设计与闸门调优**。

### 可复现性清单

- 固定随机种子并记录每张图的 `(seed, prompt, control_image_hash, lora_weights)`
- 每张合成图的元数据存为 JSON 旁文件，便于追溯与论文附录
- 生成配置纳入 Git，数据纳入 DVC

---

## 十一、常见失败模式与对策

| 失败模式 | 表现 | 对策 |
|---------|------|------|
| 结构幻觉 | 铁塔结构错乱、钢架断裂悬浮 | 用 ControlNet-Canny 锁定结构；负面提示加 `distorted metal structure` |
| 人体畸形 | 多手指、多肢体 | 负面提示；用 OpenPose 约束；G4 人工抽检重点关注 |
| 提示不遵从 | 要求"无安全帽"仍生成安全帽 | 提高 CFG scale（7–9）；改用 Inpainting 路线强制移除；G1 语义核对拦截 |
| 模式坍缩 | 生成图高度相似，多样性不足 | 提高提示词随机化程度；降低 LoRA 权重；变化 seed 与环境条件 |
| 域间隙过大 | E4 纯合成训练性能崩塌 | 增强 IP-Adapter 参考；增加 Inpainting 路线占比；加入真实背景 |
| 标签噪声 | E3 不涨反跌 | 检查 G3 与一致性核对；降低 `lambda_synth`；缩小合成比例 |
| 过拟合到 LoRA 数据 | 合成图与种子图高度相似 | 减少训练步数；降低 rank；检查最近邻距离 |

---

## 十二、里程碑对应

本文档对应 `01-技术方案与里程碑-CN.md` 中的 **M2（W4–W6）**，建议内部拆分：

| 周 | 任务 |
|----|------|
| W4 上 | Stage 0 规格库定稿（25–30 个场景）+ 基础模型选型试跑 |
| W4 下 | Stage 1 LoRA 微调 + 效果目视验证 |
| W5 上 | Stage 2 四路引擎实现（优先 ② ControlNet 与 ③ Inpainting） |
| W5 下 | Stage 3 自动标注 + 一致性核对 |
| W6 上 | Stage 4 四道闸门实现与阈值标定 |
| W6 下 | 批量生成 3000+ 张 + 质量报告 + **决定是否进入 M3** |
