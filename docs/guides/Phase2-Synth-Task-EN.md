# Phase 2: generated training images for the weak classes (TelecomSynth)

> 中文版：[第二阶段合成数据任务-CN.md](第二阶段合成数据任务-CN.md)

**Goal:** phase 2 improves the detector with **generated images only**. Each team member takes one weak class from phase 1 and produces **300–400 labelled images** for it. Together these form TelecomSynth, which is added to the training set to train E3, and E3 is compared with E2 on the frozen TelecomEval.

## 1. Weak classes and who takes them

The ranking comes from E2 on TelecomEval (AP50). Owners and the deadline will be agreed in the group.

| Class | TelecomEval AP50 | What the images must show | Owner |
|---|---|---|---|
| `no_helmet` | 14.1% | Workers **without** a safety helmet (bare head, cap, hood, headscarf) at telecom sites, including small, distant and elevated workers | |
| `vehicle` | 26.4% | Ordinary vehicles at telecom sites: vans, pickups, cars, plain trucks parked or moving near the work | |
| `machinery` | 26.9% | Telecom-specific machinery: bucket trucks, aerial work platforms, cable-pulling winches, cable-drum trailers, small cranes, mini excavators digging cable trenches | |
| `harness` | 29.9% | Full-body harnesses on workers climbing **poles and towers** or working on rooftops, seen from different distances and angles | |
| `no_vest` | 32.7% | Workers **without** a hi-vis vest: ordinary jackets, T-shirts, camouflage, rain jackets without reflective strips | |

**Deadline:** to be agreed in the group.

## 2. Requirements for every image

1. **The image contains your class.** At least 80% of your images must contain at least one box of your class; the check refuses the set otherwise.
2. **Every visible object of all 8 classes is labelled**, not only your class. A missing box teaches the model that the object is background, which does real harm. Follow the class table and consistency rules in [TelecomEval-Contribution-EN.md §3](TelecomEval-Contribution-EN.md):
   - every visible head gets exactly one `helmet` or `no_helmet`;
   - every visible torso gets exactly one `vest` or `no_vest`.
3. **One image per generation, at least 1024 px on the short side.**
   - Don't crop panels from a grid or montage.
   - Don't stretch or upscale; export at the original size (in Roboflow: no "Resize").
4. **Photorealistic outdoor telecom or power-line work.** No indoor server rooms, illustrations or cartoons.
5. **Variety:**
   - Change the setting (country or region, city or countryside), weather, time of day, camera distance and angle, and the number of people.
   - Keep **at most 3 variants of one scene or prompt.**
   - Include both the "positive" and "negative" PPE states where they fit; for example, the `harness` set also needs some workers in vests and some without.
6. **Keep TelecomEval unseen:**
   - Don't use TelecomEval images as references or inputs.
   - Don't reuse the prompts that produced TelecomEval's generated images.

   The merge step compares every image with TelecomEval and refuses near-duplicates.
7. **Record how each image was made:** in `sources.csv`, `creator` = the model (e.g. `gpt-image-2.5`, `Midjourney v7`) and `notes` = the full prompt.

## 3. Folder format

The format is the same as for TelecomEval contributions:

```
Phase2_<class>_<yourname>/
  images/        one generated image per file (png / jpg / webp)
  labels/        one YOLO file per image (class ids: 0 person, 1 helmet, 2 no_helmet, 3 vest,
                 4 no_vest, 5 harness, 6 machinery, 7 vehicle)
  sources.csv    file, subset, method, source_url, title, creator, licence, licence_version, licence_url, notes
```

In `sources.csv`, set `subset` to `telecom` or `near` (power-line work), `method` to `generated`, `licence` to `GENERATED`, `creator` to the model and `notes` to the prompt. Leave the other columns empty.

## 4. Prompt tips per class

Start from a documentary-photo style and vary the details. For example:

> Candid documentary photograph, realistic and unstaged, people busy with the work and not looking at the camera, natural imperfections, no text or logos. *[what happens]*. Setting: *[region]*. *[light / weather]*, *[camera distance and angle]*.

| Class | Ideas for *[what happens]* | Labelling pitfalls |
|---|---|---|
| `no_helmet` | Technician at a street cabinet wearing a cap; crew pulling cable, two bareheaded; worker on a ladder at a pole with a hood up; distant figures on a tower, one without a helmet | Box the **whole head**, including hair and cap, not just the face. A cap or hood is still `no_helmet` |
| `vehicle` | Van with its doors open next to a fibre splicing tent; pickups parked along a cable trench; cars passing a roadside cabinet job | Label every visible car, including parked and partly hidden ones. Bucket trucks and crane trucks are `machinery`, not `vehicle` |
| `machinery` | Bucket truck lifting a lineman to a pole; cable-drum trailer feeding fibre into a duct; mini excavator digging a trench; aerial platform at a rooftop antenna | Box the whole machine including the raised boom and bucket. The worker inside the bucket is a separate `person` |
| `harness` | Climber clipped to a lattice tower; lineman on a wooden pole with a pole strap; rigger at a rooftop edge tied off; views from the ground and from a nearby structure | Box the harness on the body (shoulder, chest and leg straps), not the rope or lanyard. A missing harness gets no box |
| `no_vest` | Crew in ordinary work jackets at a manhole; technician in a T-shirt on a ladder; workers in rain jackets without reflective strips | Every visible torso without hi-vis is `no_vest`. Hi-vis jackets with reflective strips count as `vest` |

## 5. Labelling and the optional pre-labels

Label with any tool that exports YOLO with the ids above (Roboflow, CVAT, Label Studio and so on).

**Optional:** send your **unlabelled** images, and the coordinator runs the phase 1 detector to pre-label them:

```
python -m telecomsafe.data.synth prelabel <folder>      # writes <folder>/labels/ and a sources.csv to fill in
```

You then **check and correct every box** and add the missing ones. Pre-labels miss small objects and harnesses, and they are often wrong for `no_helmet`. This step is a convenience, not a requirement.

## 6. Check and hand in

1. If you have the repository set up, run:

   ```
   python -m telecomsafe.data.synth check <folder> --target <class>
   ```

   Fix every ERROR. Otherwise the coordinator runs the check.
2. Zip the folder as `Phase2_<class>_<yourname>.zip` and put it in the team folder.
3. The coordinator merges it with:

   ```
   python -m telecomsafe.data.synth intake <folder> --contributor <name> --target <class>
   ```

   File names get a `__<name>` suffix, so every image stays traceable. Handing in again replaces only your images for that class.

## 7. What happens next

The coordinator then:

1. builds the E3 training set (`python -m telecomsafe.data.synth dataset`);
2. trains E3 with E2's unchanged configuration and 3 seeds (`python -m telecomsafe.train --exp e3 --seed 0/1/2 --name e3[_s1/_s2]`);
3. evaluates E3 on TelecomEval.

Improvement is judged on **TelecomEval's real photos**. TelecomEval also contains generated images, and gains there could come from learning the generators' style.
