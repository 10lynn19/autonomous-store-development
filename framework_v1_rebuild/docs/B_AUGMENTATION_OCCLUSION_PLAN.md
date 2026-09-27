# B-series augmentation and occlusion plan

## Controlled augmentation comparison

All branches use exactly the B1 Camera training data and the unchanged B0
validation split. Both new branches initialize independently from
`models/pretrained/yolo12n.pt`; neither fine-tunes the existing B1 checkpoint.
The fixed B test set remains evaluation-only.

| Branch | Training data | Online augmentation |
|---|---|---|
| B1 Camera (control) | B0 + clean camera | all disabled |
| B-AUG1 Light | same as B1 | small color, rotation, translation and scale changes |
| B-AUG2 Mosaic/Copy | same as B1 | B-AUG1 plus limited Mosaic and Copy-Paste |

The winning clean model is selected using fixed-test ground-truth metrics,
with mAP50-95 as the primary measure and class/scene failure modes as checks.
Video frame coverage is descriptive only.

## Real pickup/occlusion annotation

The annotation task samples 60 frames from each of the three training-source
`camera_pickup_*` videos (180 frames total) into
`data/datasets_B/b5_occlusion_addition`. Files under `data/videos_B/test` are
never included.

Label every reliably identifiable target instance. For partial occlusion, draw
the object's full package extent when its boundaries can be reasonably inferred;
otherwise draw the visible extent. Skip an object if its class or location is
not reliable. Save true no-target or fully unidentifiable frames as empty labels;
these provide useful hard negatives.

After the augmentation comparison, the best clean augmentation checkpoint can
be used as the common initialization for separate C0/C1/C2/C3 occlusion
experiments, without mixing real and synthetic occlusion in the first comparison.

## Real pickup experiment completed (2026-09-22)

The 180 pickup frames were fully annotated: 60 from each of Coke, Oreo, and
Goodwipes; 376 total boxes and no empty labels. C0 and C2 both initialized
from `b_aug2_mosaic_copy/weights/best.pt` and used the same online augmentation,
40-epoch limit, hyperparameters, and B0 validation split. C0 used the original
B1 data; C2 added the 180 pickup frames.

| Model | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| B-AUG2, before fine-tuning | 0.923 | 0.831 | 0.868 | 0.432 |
| C0 clean fine-tune | 0.879 | 0.786 | 0.835 | 0.382 |
| C2 real pickup fine-tune | 0.943 | 0.813 | 0.888 | 0.478 |

These are from the fixed 439-image, 976-box B test set, not the white-background
validation split. C2 improves mAP50-95 by 0.096 over the matched C0 and by
0.046 over B-AUG2. Manual review of the rendered videos favors B-AUG2 for an
initial demo. The Goodwipes beside Coke in `test_clean_coke` is a real object:
B-AUG2 correctly detects it, while C2 often misses it. The prior description
of B-AUG2's Goodwipes detections as false positives was incorrect. At video
confidence 0.35, C2's pickup Goodwipes target-class frame coverage is 86.4%,
versus 98.4% for B-AUG2. This coverage is only a visualization statistic, not
detection accuracy. Ground-truth metrics and manual video review disagree on
model preference, so B-AUG2 is the current demo choice and C2 remains an
experimental comparison.
