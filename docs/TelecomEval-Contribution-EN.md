# TelecomEval contribution: what each of us hands in (16 Oct 2026)

> 中文版：[TelecomEval-贡献规范-CN.md](TelecomEval-贡献规范-CN.md)

**The plan:** each team member delivers **at least 50 labelled images**, collected or made with any method they like. Together they form TelecomEval, our real-world telecom test set, which will be frozen and never changed afterwards. Every contribution uses the same folder format so they can be merged and checked automatically.

## 1. Which images

- **Scene:** people **working outdoors on telecom infrastructure**:
  - towers and masts
  - rooftop antennas and dishes
  - street cabinets
  - cable trenches and manholes
  - overhead telecom cable

  Power-line work (poles, bucket trucks, transmission lines) is welcome as the separate **near** subset. Aim for at least 35 of your 50 as telecom.
- **All 8 classes must appear** in your set (see section 3). Make sure you have:
  - at least 5 images with a **harness**, 5 with **machinery** (bucket truck, crane, excavator, cable-drum trailer, aerial platform) and 5 with an ordinary **vehicle**;
  - **non-compliant workers too**: no helmet, no harness, no hi-vis vest. Those are the risks the model must catch.
- **Quality:**
  - short side **≥ 1000 px** recommended (640 px is the hard minimum);
  - the workers clearly visible (about ≥ 80 px tall);
  - no indoor offices, labs or hangars; no posed group photos, ceremonies or portraits;
  - no illustrations, screenshots or large watermarks;
  - at most 2–3 photos from the same event.
- **Methods (any; declare each image's method in `sources.csv`):**

  | `method` | What | Licence to enter |
  |---|---|---|
  | `collected` | An openly licensed photo found online, e.g. Wikimedia Commons, Openverse, Flickr, US government sites | `CC0`, `PDM`, `US-GOV`, `CC-BY` or `CC-BY-SA` (with creator and source URL), checked on the source page |
  | `own_photo` | A photo you took yourself and agree to share under CC BY 4.0 | `OWN` |
  | `generated` | Made with an image model (e.g. GPT Image) | `GENERATED`; put the model and the full prompt in `creator` / `notes` |

  Generated images are reported as their own subset. Please keep them **at most about half** of your 50, so that most of TelecomEval stays real.
- **Not allowed:**
  - **Images from public detection datasets** (Roboflow Universe, Kaggle and similar): our training data came from such sets, so they would leak. The merge step checks every image against the training set and refuses near-duplicates.
  - CC licences with NC (non-commercial) or ND (no derivatives).
  - Pexels, Unsplash, Pixabay, stock libraries, news sites and social media.

## 2. Folder format

```
TelecomEval_<yourname>/
  images/        a.jpg, b.png ...
  labels/        a.txt, b.txt ...     one YOLO file per image (same name, .txt)
  sources.csv    one row per image
```

**YOLO label files:** one line per box, `class_id x_center y_center width height`, all normalised to 0–1. The class ids **must** follow this order. In Roboflow, CVAT, LabelImg and similar tools, create the classes in exactly this order before exporting.

| id | class | id | class |
|---|---|---|---|
| 0 | `person` | 4 | `no_vest` |
| 1 | `helmet` | 5 | `harness` |
| 2 | `no_helmet` | 6 | `machinery` |
| 3 | `vest` | 7 | `vehicle` |

**`sources.csv`** (UTF-8; in Excel use "Save As → CSV UTF-8") has these columns:

```
file,subset,method,source_url,title,creator,licence,licence_version,licence_url,notes
tower_01.jpg,telecom,collected,https://commons.wikimedia.org/wiki/File:...,Tower climb,Jane Doe,CC-BY-SA,4.0,https://creativecommons.org/licenses/by-sa/4.0/,
pole_02.jpg,near,own_photo,,,Your Name,OWN,,,taken in Jurong 2026-10-18
gen_03.png,telecom,generated,openai:gpt-image-2,,gpt-image-2 (medium),GENERATED,,,"<the full prompt>"
```

`subset` is `telecom` or `near`.

## 3. How to label

The source of truth is `configs/taxonomy.yaml`.

| Class | Box | Rule |
|---|---|---|
| `person` | The whole visible person | Label when more than half of the body is visible |
| `helmet` | A safety helmet worn on the head | Not helmets on the ground or in the hand |
| `no_helmet` | A head without a safety helmet | Caps, headscarves and hoods count as `no_helmet` |
| `vest` | The worn hi-vis vest or hi-vis workwear (upper body) | Only garments with reflective strips |
| `no_vest` | The torso of a person without a hi-vis vest | Ordinary or camouflage clothes |
| `harness` | A full-body harness worn on the body | Not ropes and hooks on the structure; a missing harness gets no box |
| `machinery` | The whole machine incl. booms | Excavators, cranes, bucket trucks, aerial work platforms, cable-pulling rigs, cable-drum trailers |
| `vehicle` | The whole vehicle | Ordinary cars, pickups, vans, plain trucks |

**Consistency rules:**
- Every person whose head is visible gets **exactly one** `helmet` or `no_helmet`.
- Every person whose torso is visible gets **exactly one** `vest` or `no_vest`.
- Towers, poles and antennas themselves are not labelled.

**Box rules:**
- Boxes are **tight** around the visible part.
- People who overlap each get their own box.
- If you cannot tell whether a distant worker wears a helmet, still label the `person` but neither helmet class.
- Interim rule for **combat helmets** (military photos): label as `helmet` and mention `combat helmet` in `notes`.

Any labelling tool is fine, as long as it exports YOLO with the ids above. If you use this repository's Label Studio:

```
python -m telecomsafe.data.contrib annotate <folder>      # E2 pre-labels → a Label Studio project
python -m telecomsafe.data.contrib export <folder>        # writes labels/ and runs the check
```

**Pre-labels are only a starting point:** check every box.

## 4. Check and hand in

1. If you have the repository set up, run `python -m telecomsafe.data.contrib check <folder>` and fix every ERROR. WARNINGs are advice. Otherwise the lead runs it for you.
2. Zip the folder as `TelecomEval_<yourname>.zip` and put it in the team's shared folder.
3. The lead merges each contribution with `python -m telecomsafe.data.contrib intake <folder> --contributor <name>`. This re-checks the folder, refuses near-duplicates of training images or of other contributions, and copies everything into `data/raw/telecom_eval/`. After all four are in, TelecomEval is frozen and evaluated.

**Deadline:** to be agreed in the group chat. The TGB meeting is in W7 (week of 19 Oct).
