# TelecomEval 标注规范 / Annotation Guidelines

> 标准与项目的 `configs/taxonomy.yaml` 一致，两者有出入时以它为准。示例图来自公开数据集（Construction Site Safety v30、body_harness，均为 CC BY 4.0），框是数据集原有的人工标注。
> These rules follow the project's `configs/taxonomy.yaml`, which wins if they ever differ. Example images come from public datasets (Construction Site Safety v30, body_harness, both CC BY 4.0) with their original human labels.

## 1. 类别 / Classes

| 键 Key | 类别 Class | 框什么 What to box | 判定标准 Criterion |
|---|---|---|---|
{class_rows}

## 2. 一致性规则 / Consistency rules

后面的风险规则依赖这些标注之间的关系，所以请严格遵守：
The risk rules depend on how these labels relate, so please follow them strictly:

1. **每个能看到头部的人，头部必须且只能标一个 `helmet` 或 `no_helmet`。** 戴普通帽子、头巾、兜帽都算 `no_helmet`。看不到头部（被挡住、出画）就都不标。
   **Every person whose head is visible gets exactly one `helmet` or `no_helmet` on the head.** Caps, headscarves and hoods count as `no_helmet`. If the head is not visible (occluded, out of frame), label neither.
2. **每个能看到躯干的人，必须且只能标一个 `vest` 或 `no_vest`。** 只有带反光条的高可视性背心或工作服才算 `vest`；普通彩色衣服是 `no_vest`。
   **Every person whose torso is visible gets exactly one `vest` or `no_vest`.** Only high-visibility garments with reflective strips count as `vest`; ordinary coloured clothes are `no_vest`.
3. **`harness` 只标穿在身上的全身式安全带**（肩带、胸带、腿带）。框住身上安全带的主体部分；只挂在塔或杆上的绳子、挂钩不标。没有安全带**不需要**画任何"无安全带"的框。
   **`harness` is only a full-body harness worn on the body** (shoulder, chest and leg straps). Box the harness on the body; ropes or hooks hanging on the structure are not labelled. A missing harness needs **no** box.
4. **人员框 `person` 框住整个人可见的部分**，包括被挡住后露出来的部分。可见部分不到一半，或者小到在 100% 缩放下认不出是人，就不标。
   **`person` boxes the whole visible person**, including parts showing around occlusions. Skip people less than half visible, or too small to recognise as a person at 100% zoom.
5. **斗臂车、高空作业平台、吊车、放线车、电缆盘拖车都算 `machinery`**；普通轿车、皮卡、面包车、普通货车算 `vehicle`。
   **Bucket trucks, aerial work platforms, cranes, cable-pulling rigs and cable-drum trailers are `machinery`**; ordinary cars, pickups, vans and plain trucks are `vehicle`.
6. **铁塔、电线杆、天线本身都不标。**
   **Towers, poles and antennas themselves are not labelled.**

## 3. 画框要求 / Box quality

- **贴紧**可见部分的边缘，不要留大片空白，也不要切掉一部分。
  **Tight** around the visible pixels — no large margins, nothing cut off.
- 被遮挡时只框**看得见的部分**；同一个物体被遮成两截时，画一个框覆盖两截。
  For occlusion, box **what is visible**; if one object is split in two by an occluder, one box covers both parts.
- 人挨在一起时，**每个人各画各的框**。
  When people overlap, **each gets their own box**.
- 远处的小目标：放大到能看清再画；实在分辨不出是否戴安全帽，`helmet` / `no_helmet` 都不标，但 `person` 照常标。
  Small, distant targets: zoom in before drawing. If you truly cannot tell whether a helmet is worn, label neither `helmet` nor `no_helmet`, but still label the `person`.

## 4. 什么时候点 Skip / When to Skip

- 画面里没有人在作业（只有设备、风景），或者是示意图、插画、截图。
  Nobody is working in the picture (only equipment or scenery), or it is a diagram, illustration or screenshot.
- 图片模糊到无法判断，或者与已经标过的图几乎一样。
  The image is too blurry to judge, or nearly identical to one you have already labelled.

拿不准的情况，先按最接近的规则标，并在该图的评论（Comments）里写一句说明，方便复核。
When unsure, label by the closest rule and leave a comment on the task (Comments) so it can be reviewed.

## 5. 示例 / Examples

{examples}
