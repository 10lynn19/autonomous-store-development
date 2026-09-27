# Clean rebuild experiment

The new Windows workspace is `C:\Market\framework_v1_rebuild`. It must not
read checkpoints, datasets, or outputs from the archived V1-V8.1 project.

## A0 baseline

1. Run `python src/prepare_a0_base.py`.
2. Review `data/datasets_A/a0_base/review/labels_preview.jpg` and correct labels.
3. Only after label review, run `python src/train_a0_base.py`.

All later A-series branches must start from the same initialization and keep
training parameters fixed. The only experimental variable is the added data:

- A1: computer-generated scale/noise data
- A2: phone small-object data
- A3: clean deployment-camera data
- A4: selected combinations

Pickup/occlusion data and background subtraction are later stages and must not
enter the A-series comparison.

## A5 balanced Camera branch

A5 keeps the same pretrained `yolo12n.pt`, A0 validation split, random seed,
and training hyperparameters as A3. Its only additional input is the manually
reviewed `camera_more_thinkbar_ziploc` dataset: 240 deployment-camera images
containing 300 Think and 300 Ziploc boxes. A5 trains on A0, the original A3
Camera addition, and this new dataset. Existing A3 and A4 checkpoints remain
unchanged and serve as historical controls.

## A6-P balanced Camera + Phone branch

A6-P starts independently from the same `yolo12n.pt` and keeps all A5
hyperparameters fixed. It uses the complete A5 training set plus the reviewed
`a2_phone_addition` images. The only variable relative to A5 is the Phone
addition, allowing a direct test of whether Phone viewpoints complement the
balanced deployment-Camera data.

## Controlled A1-A3 branches

Every branch starts independently from `models/pretrained/yolo12n.pt`; A2 and
A3 do not continue from A1. All branches use A0's 288 clean training frames,
the same A0 validation split, 144 added frames (48 per class), and the exact
same optimization parameters in `src/train_common.py`.

- A1 adds 144 computer-synthesized small-object images. Object pixels come
  from A0; scale/position match the Phone annotation distribution; rotation is
  within +/-15 degrees and Gaussian noise sigma is 2-10.
- A2 adds the 144 reviewed Phone frames from six small-object videos.
- A3 adds 144 clean deployment-camera frames from the three `camera_clean_*`
  videos. These frames require manual review/annotation before training.

The fixed annotated test set remains completely outside all training and model
selection. Pickup videos are not used by A3.

## A1/A2 completed results (2026-09-10)

Both jobs exited successfully. A1 selected epoch 18 and stopped after epoch 26;
A2 selected epoch 10 and stopped after epoch 18. On the shared A0 validation
split, A1 achieved mAP50 0.995 and mAP50-95 0.933, while A2 achieved mAP50
0.995 and mAP50-95 0.923.

On the fixed deployment test set (241 images, 1,031 boxes), both models scored
zero precision, recall, mAP50, and mAP50-95. At video confidence 0.35, A2 made
no detections in 3,574 frames. A1 produced 141 detections in 3,574 frames
(3.95% of frames), all as `think_protein_bar`, but none matched the annotated
ground truth. This is false-positive behavior, not an accuracy improvement.

Conclusion: synthetic/Phone small-object additions improve or preserve the
white-background validation score but do not bridge the deployment-camera
domain gap. A3 clean-camera data is therefore the next controlled branch.

## A3 training completed (2026-09-10)

A3 used 144 manually reviewed clean-camera frames containing 792 labeled
instances (Coke 422, Think 51, Ziploc 319), plus the same 288 A0 training
frames. It started independently from `yolo12n.pt` with the fixed A-series
configuration. The run selected epoch 24, stopped early after epoch 32, and
exited successfully. On the shared A0 validation split, `best.pt` achieved
precision 0.997, recall 1.000, mAP50 0.995, and mAP50-95 0.925. Deployment
performance must still be measured using the fixed ground-truth test set.

## A3 fixed-test result (2026-09-10)

Using the same 241 annotated images, 1,031 boxes, and `imgsz=1024` evaluation
as A0-A2, A3 achieved precision 0.279, recall 0.226, mAP50 0.280, and
mAP50-95 0.113. Per-class mAP50 was 0.785 for Coke, 0.000251 for Think, and
0.0554 for Ziploc. Camera-clean training therefore bridges part of the domain
gap, but the improvement is overwhelmingly concentrated in Coke.

At video display confidence 0.35, static Coke cans cause detections in many
frames even in Think/Ziploc videos. Consequently `any_detection_rate` is not
the success rate for the item being manipulated; ground-truth matching and
per-class metrics remain the primary comparison.

## A4-P Camera + Phone training completed (2026-09-10)

A4-P combines the 288 A0 clean frames, 144 A3 clean-camera frames, and 144 A2
Phone small-object frames (576 training images total). It starts independently
from `yolo12n.pt` and uses the same A-series hyperparameters and shared A0
validation split. The run completed all 40 epochs with exit code 0; the final
epoch produced the best checkpoint. Re-evaluation of `best.pt` on the shared
validation split yielded precision 0.997, recall 1.000, mAP50 0.995, and
mAP50-95 0.928. A fixed deployment test is still required before comparing it
with A3.

## A4-S fixed-test result (2026-09-10)

On the fixed deployment test, A4-S achieved precision 0.641, recall 0.319,
mAP50 0.362, and mAP50-95 0.154. Per-class mAP50 was 0.883 for Coke, 0.128
for Think, and 0.0743 for Ziploc. Compared with A4-P, Synthetic helps Think
ranked AP but hurts Ziploc, while overall mAP50 is nearly tied (0.362 versus
0.368).

Visual inspection changes the interpretation: A4-S frequently predicts a
single large, high-confidence Think box around the entire left-side snack
cluster in clean videos. This structured false positive appears in every frame
of several videos. Therefore A4-S is not deployment-ready despite its improved
Think AP; future synthetic data must include shelf hard negatives and should
avoid encouraging generic snack-cluster/elongated-shape shortcuts.

## A4-P fixed-test result (2026-09-10)

On the same 241-image, 1,031-box deployment test, A4-P achieved precision
0.515, recall 0.329, mAP50 0.368, and mAP50-95 0.148. This improves A3's
0.280 mAP50 and 0.113 mAP50-95. Per-class mAP50 changed from A3 to A4-P as
follows: Coke 0.785 to 0.865, Think 0.000251 to 0.0437, and Ziploc 0.0554 to
0.193. The result supports complementarity between deployment-camera context
and clearer Phone product appearance.

The main remaining failure is Think recall (0.0227). At the 0.35 rendered-video
threshold, no Think detections survive, despite non-zero ranked AP at the lower
evaluation confidence floor. Static Coke detections also continue to inflate
video-level any-detection rates.

## A4-S Camera + Synthetic training completed (2026-09-10)

A4-S combines the 288 A0 clean frames, 144 A3 clean-camera frames, and 144 A1
synthetic scale/noise/rotation frames (576 training images total). It starts
independently from `yolo12n.pt` with the same A-series hyperparameters and
shared A0 validation split. The run selected epoch 29, stopped early after
epoch 37, and exited successfully. Re-evaluation of `best.pt` on the shared
validation split yielded precision 0.997, recall 1.000, mAP50 0.995, and
mAP50-95 0.930. A fixed deployment test is required for comparison with A3
and A4-P.
