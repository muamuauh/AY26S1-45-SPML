# TelecomEval: status, remaining work and classes (16 Oct 2026)

> **Plan changed on 16 Oct 2026:** each member now collects and labels at least 50 images by any method — see [TelecomEval-Contribution-EN.md](../guides/TelecomEval-Contribution-EN.md). The screening / annotation / collection packages below were withdrawn; this page is kept for the background and the class definitions.

> 中文版：[TelecomEval-进展与待办-CN.md](TelecomEval-进展与待办-CN.md)

TelecomEval is our **real-world telecom test set**. It answers one question: how well does the detector work on telecom sites (towers, rooftop antennas, street cabinets, cable trenches, manholes, poles)? The baseline was trained only on construction-site data, and the TGB meeting (W7, week of 19 Oct) and the phase 2 gate TG3 (E3 must beat E2 by ≥ 2.0 mAP) are both judged on this set. **Once frozen, it never changes.**

## 1. Where we are

The pipeline is: collect candidates → screen by hand → pre-label with the E2 model → annotate in Label Studio → bring the labels in → freeze → evaluate. Every image keeps its licence and attribution in a manifest.

| Step | Status |
|---|---|
| **Round 1 collection** (Openverse, Wikimedia Commons, frames from CC-licensed YouTube videos) | Done: 1,930 candidates |
| **Round 1 screening** | Done: **167 kept (95 telecom + 72 near)**. "Near" means power-line work: poles and bucket trucks with the same climbing and harness hazards, reported as a separate subset |
| **Concern about round 1** | Many images are low-resolution video frames, and the scenes and workers are repetitive. We are not happy using them as they are |
| **Round 2 collection** (14 Oct) | Done: **1,700 new public-domain photos**, from US Department of Defense (DVIDS) images mirrored on Wikimedia Commons. Most are 1280 × 853 or larger, with more varied scenes |
| **Round 2 automatic scoring** | Done. **486** show people and look like a work scene (cable / fibre work 203, cabinets 62, rooftop antennas 61, towers 52, poles 31, bucket trucks 28, trenches 20, manholes 16). 284 were auto-rejected (no person, not a work scene) |
| **Round 2 screening by hand** | **Not started** |
| Pre-labelling, annotation, freezing, evaluation | Not started for the final set. The tools are ready (see section 2) |

**Options we looked at and dropped:**
- **Generating the test set with image models** (e.g. GPT Image): this would measure performance on AI images, not real sites. Phase 2 also trains on generated images, so the TG3 comparison would be biased. The images would still need hand labelling, because auto-labels from E2 would mean grading E2 with its own answers.
- **Existing public datasets:** none covers telecom workers with PPE labels.
  - The closest is the Guangdong power-grid work-at-height set (Tianchi competition), but its licence for academic reuse is unclear and its labels differ from ours.
  - The "construction safety v2" Roboflow export we checked is mosaic-augmented, stretched to 640 × 640, and overlaps our training data (Construction Site Safety). Not usable.
- **Mixing parts of other construction datasets into TelecomEval:** this would mostly measure construction-site performance, which our validation set already covers. A separate cross-dataset set (e.g. from CHV and SHEL5K, which were not used in training) is possible as an extra, reported on its own.

## 2. What needs to be done

1. **Screen the 1,700 round-2 candidates** in the browser screening page. Press 1 = telecom, 2 = near, X = reject. The images are sorted best-first, and almost everything useful is in the first ~500.
2. **Re-screen the 167 round-1 images** with the same, stricter criteria (section 3), and drop the weak ones.
3. **Balance the final set.** Aim for **≥ 150 telecom images (ideally 200)** plus a near subset, spread over the scene types. Keep at most 2–3 photos from the same event, since DVIDS often has a series of near-identical shots.
4. **Pre-label** the kept images with E2 (a COCO model adds vehicles):

   ```
   python -m telecomsafe.data.pseudo_label --weights runs/phase1/e2/weights/best.pt --images data/raw/t3_candidates/images --yolo-out data/raw/t3_candidates/prelabels
   ```

5. **Build the annotation package** with `python -m telecomsafe.data.package annotate`. It has one-click start scripts for Windows and macOS.
6. **Annotate in Label Studio** following the annotation guidelines and the class table in section 4. A second person should re-check about 10% of the images.
7. **Bring the labels in and freeze:**

   ```
   python -m telecomsafe.data.package intake-annotations <annotations.json>
   python -m telecomsafe.data.freeze_eval --create
   ```

   Look through the spot-check sheet that intake produces before freezing.
8. **Evaluate** E1 and the 3 E2 seeds with `python -m telecomsafe.evaluate`, reporting telecom and near separately. Then update the weak-class list that phase 2 targets.
9. **If time runs out before TGB:** evaluate on the round-1 set as a "v0" with the caveats stated, and freeze the final set before any phase 2 comparison.

**Effort estimate:**

| Task | Time |
|---|---|
| Screening | 1.5–2 h |
| Re-screening the 167 | ~0.5 h |
| Annotating 200 images (correcting pre-labels, ~1.5–2 min each) | 4–6 h |
| Intake, freeze and evaluation | ~1 h |

Screening and annotation can be split between people by image range.

## 3. Screening criteria (stricter than round 1)

**Keep** (as telecom, or near for power-line work):
- Someone is actually working **outdoors** on telecom infrastructure: climbing a tower or pole, installing antennas or dishes, working at a street cabinet, pulling or splicing cable in a trench or manhole.
- The image is **sharp**: short side ≥ 1000 px for photos, and at least one worker about ≥ 80 px tall.
- Prefer images where PPE can be judged, such as hard hats, climbing helmets, harnesses, hi-vis vests, and also workers **without** them, which are the cases we most need.

**Reject:**
- Indoor offices, labs, tents and hangars.
- Posed group photos, ceremonies and portraits.
- Diagrams, screenshots and illustrations.
- Images with nobody working.
- Near-duplicates of an image already kept.
- Scenes that are purely military (combat gear, weapons, vehicles) with no telecom work.

## 4. Classes (phase 1, 8 classes)

The source of truth is `configs/taxonomy.yaml`; the annotation guidelines in the package follow it.

| Class | What to box | Criterion |
|---|---|---|
| `person` | The whole visible person | Label when more than half of the body is visible; skip people too small to recognise |
| `helmet` | A safety helmet worn on the head | Not helmets on the ground or held in the hand |
| `no_helmet` | A head **without** a safety helmet | Ordinary caps, headscarves and hoods count as `no_helmet` |
| `vest` | The worn hi-vis vest or hi-vis workwear (upper body) | Only garments with reflective strips count |
| `no_vest` | The torso of a person without a hi-vis vest | Ordinary coloured clothes are `no_vest` |
| `harness` | A full-body harness worn on the body (shoulder, chest and leg straps) | Ropes and hooks hanging on the structure are not labelled; a missing harness gets no box |
| `machinery` | The whole machine, including booms and buckets | Excavators, cranes, loaders, **bucket trucks, aerial work platforms, cable-pulling rigs, cable-drum trailers** |
| `vehicle` | The whole vehicle | Ordinary cars, pickups, vans and plain trucks |

**Consistency rules** (the risk rules depend on them):
- Every person whose head is visible gets **exactly one** `helmet` or `no_helmet`.
- Every person whose torso is visible gets **exactly one** `vest` or `no_vest`.
- Towers, poles and antennas themselves are **not** labelled. A `tower` class exists in the taxonomy but is off in phase 1; it is reserved for the optional tower rule R3.

**Current weak classes** (validation set, E2): `vehicle` (AP50 0.40) and `no_helmet` (0.42). Everything else is ≥ 0.80. TelecomEval will show whether this changes on telecom sites.

## 5. Open questions for the team

1. **Military helmets and camouflage in DVIDS photos:** does a combat helmet count as `helmet` (it is protective headgear, but not a safety helmet)? Is camouflage simply `no_vest`? We should decide before annotating. Otherwise, prefer images with hard hats or climbing helmets.
2. **Size of the near subset:** should near images count toward the 150 target, or be kept strictly separate? Keeping them separate is the current plan.
3. **Who screens and annotates which ranges**, and who does the 10% re-check.

The candidate images and the screening page are not in git (`data/` is ignored). They will be shared through the team folder.
