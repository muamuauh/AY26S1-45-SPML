# Project status and next steps (12 Oct 2026)

A short update for the team: what is done, and the two things that come next: **(1) finish TelecomEval** and **(2) start phase 2**.

## What is done

**Phase 1 baseline (frozen 6 Oct, tag `phase1-baseline-v2`)**

- **Data:** 6 public datasets, 7,475 training images after de-duplication; 8 classes (person, helmet, no_helmet, vest, no_vest, harness, machinery, vehicle). Sources and licences: [docs/datasets/README.md](../datasets/README.md).
- **Model:** YOLO11s at 640 px, kept after comparing it with 11m. An input size of 960 was also tried and not adopted.
- **Results on the validation set:**

  | Experiment | mAP50 |
  |---|---|
  | E1 (no augmentation) | 0.596 |
  | E2 (default augmentation, 3 seeds) | **0.737 ± 0.007** |

  E2 is better than E1 on every class. The weakest classes are **vehicle (0.40)** and **no_helmet (0.42)**. Full report: [docs/results/phase1/README-EN.md](../results/phase1/README-EN.md).
- **Rule-based risk judgement and Demo v1 (Gradio):** double-click `start_demo.bat`. The weights download automatically from the GitHub Release.
- **Reproduction guide:** [docs/08-Phase1-Training-Guide-EN.md](../guides/08-Phase1-Training-Guide-EN.md).

**TelecomEval (our telecom test set)**

- 1,930 candidate images were collected from Openverse, Wikimedia Commons and CC-licensed YouTube frames, and all of them were screened by hand.
- **167 images were kept: 95 telecom and 72 near** (power-line work, reported separately).
- The images are pre-labelled by the E2 model and packed as an annotation package. **They are not annotated yet.**
- The training set is already de-duplicated against these 167 images, so freezing TelecomEval will not require retraining.

**Phase 2 pre-study (local branch, not pushed yet)**

- A generation environment is set up (SDXL Inpainting, SAM 2, CLIP), together with automatic quality gates (de-duplication against TelecomEval, CLIP, and an E2 detector check) and a human-rating page.
- **Remove helmet / remove vest** (inpainting) works: they create no_helmet and no_vest examples, and the labels carry over. About half of the helmet edits and most of the vest edits pass the automatic gates. We have not rated them by hand yet.
- **Put workers into telecom scenes:** two methods were tried and both failed the human check.

  | Method | Rated natural |
  |---|---|
  | Cut-and-paste of real workers | 9 of 99 |
  | Painting a worker into the background with SDXL | 2 of 27 |

  The person's size and the lighting did not match the scene. Next options: a commercial image-editing model (a pilot of about USD 5) or a stronger local model.
- **Add vehicle / machinery:** paused because too few images passed. Vehicle is still a weak class, so this needs another approach.

## Next step 1: finish TelecomEval (needed for the TGB meeting in W7, week of 19 Oct)

1. **Annotate the 167 images.** Correct the E2 pre-labels in Label Studio; the annotation package includes a one-click start script.
2. **Bring the annotations into the project** with `python -m telecomsafe.data.package intake-annotations <annotations.json>` (the file exported from the package), then check the spot-check sheet it produces.
3. **Freeze TelecomEval** with `python -m telecomsafe.data.freeze_eval --create`. After this the test set is read-only.
4. **Evaluate on TelecomEval** with `python -m telecomsafe.evaluate`. This scores E1 and the 3 E2 seeds, reporting telecom and near separately, and updates the weak-class list.
5. **Too few telecom images:** we have 95 telecom images, below the target of 100. Either add a few more (Flickr / DVIDS need API keys; images from the supervisor would also help), or apply fallback D1 and state it in the report.
6. **Prepare the TGB meeting:** slides and a demo recording.

## Next step 2: start phase 2

1. **Choose how to generate telecom scenes.** Run the paid pilot: about 30 images each from GPT Image 2 and Gemini (Nano Banana 2), then rate them blind. If more than half look natural, generate the full set (roughly USD 50–100). Otherwise try a stronger local model.
2. **Rate and scale up remove helmet / remove vest.** Hand-rate a sample of 100 images per scenario, then generate up to the targets for no_helmet and no_vest.
3. **Find a new approach for vehicles**, for example text-to-image of whole scenes with automatic labelling.
4. **Train E3** (E2 data plus synthetic images, 3 seeds) and compare it with E2 on TelecomEval.
   - **TG2 (W10):** generation quality.
   - **TG3 (W12):** E3 must beat E2 by at least 2.0 mAP. This is about 3× the seed-to-seed spread, so a gain that size is unlikely to be noise.

## Where help is welcome

- **Annotation:** the TelecomEval annotation package can be split between people.
- **Images:** any telecom work photos we are allowed to use (towers, rooftop antennas, street cabinets, cable trenches).
- **TGB meeting:** reviewing the slides and the demo.
