# Phase 2 results: E3 (with generated images) versus E2

> 中文版：[README.md](README.md)
> Status (2026-11-07): TelecomSynth holds 1,724 images, and E3 has been trained with 3 seeds. Evaluation uses **TelecomEval v2**, whose labels were revised (see below). The results on v1 are kept in [`telecom_eval_v1/`](telecom_eval_v1/).

## Summary

Adding 1,724 generated images (TelecomSynth) to the training set raises mAP50 on TelecomEval v2's **real photos** from **37.0 ± 2.7%** to **45.4 ± 0.6%** (+8.4). The headline metric, real telecom photos, rises from **44.2 ± 4.0%** to **50.1 ± 0.9%** (+5.9). Each of E3's three seeds (49.6–51.0) scores above each of E2's (40.5–48.5). On real photos, 7 of the 8 classes improve, including all 5 weak classes we generated for; person is unchanged.

## Setup

- **E2**: the phase 1 baseline, 6,728 training images from public data, Ultralytics' default augmentation.
- **E3**: E2's training images + TelecomSynth's 1,724 (8,452 in total), **with everything else identical to E2** ([`configs/baseline.yaml`](../../../configs/baseline.yaml): YOLO11s, 640 px, 100 epochs, patience 20). The validation set is unchanged and holds only real images.
- Each experiment was trained once with seeds 0, 1 and 2. The E3 runs stopped at epochs 98, 88 and 88. E1 (no augmentation, 1 seed) is listed for reference.
- Test set: the frozen TelecomEval v2 (222 images: 124 real photos, 98 generated).

| Weak class | Member | Images | How they were made |
|---|---|---|---|
| `harness` | Guo | 380 | gpt-image; boxes from detectors, classes from a vision-language model, CLIP near-repeat cut, human spot checks |
| `machinery` | LU | 350 | gpt-image; labelled by the member in Roboflow, corrected by the coordinator |
| `no_vest` | Guo 344 + Sneha 50 | 394 | Guo's part as for harness; Sneha's part labelled by hand |
| `no_helmet` | linyuxuan | 300 | Doubao (watermark cropped); labelled by the member, vehicles and machinery added by the coordinator |
| `vehicle` | mengxiangyu | 300 | generated and labelled by the member; the coordinator removed wrong boxes and fixed PPE classes |

Training instances added by TelecomSynth: vehicle +1,798 (276 real), no_helmet +1,401 (1,069 real), no_vest +1,756, helmet +1,701, vest +1,360, harness +854, machinery +555, person +3,381.

## TelecomEval v2 results (percentages; E2 and E3 are the mean ± std of 3 seeds)

| Subset | Images | E1 | E2 mAP50 | E3 mAP50 | E3 − E2 | E2 mAP50-95 | E3 mAP50-95 |
|---|---|---|---|---|---|---|---|
| **Real photos, telecom work (headline)** | 77 | 32.9 | 44.2 ± 4.0 | 50.1 ± 0.9 | **+5.9** | 26.3 ± 4.3 | 27.1 ± 0.7 |
| Real photos, power-line work | 47 | 25.2 | 29.0 ± 1.0 | 40.2 ± 0.2 | +11.2 | 11.8 ± 1.0 | 15.4 ± 0.2 |
| Real photos, all | 124 | 30.2 | 37.0 ± 2.7 | 45.4 ± 0.6 | +8.4 | 18.9 ± 2.4 | 21.1 ± 0.4 |
| Generated images (reference only) | 98 | 44.2 | 54.2 ± 1.0 | 73.5 ± 1.1 | +19.3 | 30.1 ± 1.2 | 43.7 ± 1.0 |
| All | 222 | 36.4 | 44.3 ± 1.5 | 58.9 ± 0.8 | +14.6 | 23.4 ± 1.5 | 32.0 ± 0.5 |

Validation set (same sources as training, for development only): E2 73.7 ± 0.7%, E3 74.6 ± 0.1% (best epoch of each seed, from the training logs). The generated images did not hurt performance on the original domain.

### Per-class AP50 on real photos

| Class | E1 | E2 | E3 | E3 − E2 |
|---|---|---|---|---|
| person | 60.8 | 74.9 ± 1.2 | 74.9 ± 1.0 | 0.0 |
| helmet | 49.6 | 51.6 ± 1.2 | 60.9 ± 2.1 | +9.4 |
| no_helmet | 15.1 | 18.7 ± 4.9 | 31.9 ± 1.1 | **+13.2** |
| vest | 45.1 | 54.8 ± 1.0 | 63.3 ± 1.1 | +8.5 |
| no_vest | 24.6 | 24.6 ± 4.6 | 35.7 ± 3.6 | **+11.1** |
| harness | 27.1 | 33.2 ± 7.0 | 38.7 ± 4.0 | **+5.6** |
| machinery | 13.7 | 21.1 ± 3.0 | 27.9 ± 2.8 | **+6.8** |
| vehicle | 5.5 | 17.5 ± 5.8 | 29.6 ± 1.2 | **+12.1** |

The 5 weak classes we generated for are in bold.

![Per-class AP50 on TelecomEval v2 real photos](telecom_eval/per_class_ap_real.png)

Per-class figures for every subset: [`per_class_by_subset.csv`](telecom_eval/per_class_by_subset.csv). Full subset results: [`telecom_eval/results-EN.md`](telecom_eval/results-EN.md).

## Reading the results

1. **The generated images give a steady gain on real photos.** The headline metric gains 5.9 points, more than E2's seed standard deviation (4.0), and every E3 seed beats every E2 seed. The spread between seeds also falls from ±4.0 to ±0.9. The gain is larger on power-line photos (+11.2).
2. **The four helmet and vest classes improve most steadily** (+8 to +13), in the same direction for all three seeds.
3. **Machinery and vehicle also improve on real photos** (+6.8 and +12.1), but much less than on generated images (+34.8 and +58.1). Part of the large gain on generated images may come from learning the generators' style, so only the real photos count.
4. **mAP50-95 gains less than mAP50** (+2.2 on real photos), so box placement improves only a little.
5. **Single classes still have few samples:** the real telecom photos hold 18 machinery, 30 vehicle and 40 harness instances, so single-class figures vary a lot.

## TelecomEval v2: why the labels were revised

On v1, E3's harness AP was 6.5 points below E2's. Checking every case showed that this came mainly from TelecomEval's labels, not from wrong labels in the generated images:
- 20 people clearly wearing harnesses had no harness label;
- linemen's waist belts were boxed as thin strips that no model can match;
- many roadside vehicles were unlabelled, so detecting them counted as false positives.

We therefore checked all 222 images and froze the result as v2 (total hash `73cfb8df…`):
1. A vision-language model judged every person and vehicle, and detectors proposed people and vehicles that might be missing.
2. **A person decided every disagreement by looking at the image.** Where the model said a label was wrong but the image showed it was right, the label was kept.
3. A script applies the changes to v1, so the revision can be reproduced.

All changes are in [`telecom_eval_v2_fixes.csv`](telecom_eval_v2_fixes.csv) (314 changes in 139 images). The main ones:

| Change | Count | Notes |
|---|---|---|
| Harness relabelled by the definition | 19 removed, 19 added, 72 re-boxed | Only full-body harnesses count (the contribution guide's definition); linemen wearing only a waist belt get no harness box (12 in `lu_046`, 2 in `lu_029`, and others). 19 missed harnesses were added. Boxes are drawn from body keypoints, from the shoulder straps to the upper thighs, as for the generated images. Where the keypoint box reached the head (workers in a bucket, visible only above the waist), the torso box is used instead |
| People added | +45 people with their head and torso boxes; 9 more head or torso boxes for existing people | Whole workers missing in some of Lin's images; passers-by missing in generated images |
| Vehicles added | +44 vehicles, +4 machinery | Vehicles by the roadside and in night scenes |
| Bucket and crane trucks merged | 9 | Lu labelled the truck body `vehicle` and the boom `machinery`; following the guide, they are now one `machinery` box that includes the boom |
| Classes and duplicate boxes | 17 | A motorcycle helmet labelled as a safety helmet, a jacket with reflective strips labelled `no_vest`, a van labelled as machinery, a whole-person box labelled `no_helmet`, and others |

**Ways this revision could favour E3:**
- The new harness boxes are drawn the same way as the harness boxes in Guo's generated images.
- Candidate people and vehicles came from a COCO detector and the vision-language model, the same kind of tools used to label the generated images.

To keep the evaluated models from shaping the answers, **no E1, E2 or E3 detections were used to change any label**. The harness box convention is also close to that of the Work at Height training data, which E2 uses too: box height about 0.46 of the person's height, top edge about 0.18 of the person's height below the top of the person.

Results on v1: real photos 36.4 ± 2.9 → 41.1 ± 0.9, headline 46.9 ± 4.1 → 48.1 ± 1.7, harness 25.4 → 18.9. See [`telecom_eval_v1/results-EN.md`](telecom_eval_v1/results-EN.md).

## Known issues and limits

- **Freeze check:**
  - 10 of Lu's JPEGs lacked the end-of-image marker. One minute after the freeze, during the first phase 1 evaluation, Ultralytics rotated them by their EXIF orientation and saved them again in place. Pixels differ by at most 4/255 and the labels are unchanged; the phase 1 figures were already computed on the re-saved files. The manifest was updated to match (`bfc4921`).
  - All JPEGs now carry the marker, so no file will be rewritten again. The manifest was frozen once more after the v2 label revision.
- **The phase 1 report still shows v1 figures.** The v2 figures for E1 and E2 are on this page.
- **Incomplete source records:** mengxiangyu (300 images) and Sneha (50) did not supply prompts; their model and prompt fields in `sources.csv` read `PENDING`.
- **Mixed labelling methods:** in TelecomSynth, harness and Guo's no_vest images were labelled automatically with human spot checks, and the rest by hand. Passers-by in the generated images are labelled `person` only (the phase 2 rule); TelecomEval keeps the phase 1 rules, under which passers-by also get PPE labels.
