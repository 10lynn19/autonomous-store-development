# Test video annotation guide

## Scope

Annotate only the three exact target SKUs:

1. `coke_zero`
2. `think_protein_bar`
3. `ziploc_box`

Similar packages that are not the exact target product remain unlabeled. Every
visible instance of an exact target SKU must be labeled, including background
instances on the shelf.

## Bounding-box rule

- Draw a tight box around the product package.
- Exclude hands, shadows, shelves, and surrounding products.
- For partial hand occlusion, estimate the full product extent when its identity
  and extent are still clear from the video sequence.
- If less than roughly 15% is visible and the product cannot be localized
  reliably, do not label that instance.
- If the product leaves the image, stop the box at the image boundary.
- Use the same rule in every video.

## Fast workflow

- Press `1`, `2`, or `3` to choose the class.
- Drag a box around each target instance.
- Press `Enter` to save and move to the next frame.
- Press `E` only when no target SKU is present.
- Use **Copy previous** for adjacent frames from the same video, then adjust.
- Press `U` to undo the newest box or `Delete` to remove the selected box.

An empty label file is intentional: it records that the frame was reviewed and
contains no target. A missing label file means the frame has not been reviewed.

## Output

Images and YOLO labels are stored in:

```text
data/datasets_A/test_ground_truth/
├── manifest.json
├── images/test/
└── labels/test/
```

Do not copy this dataset into any training or validation split. It is the fixed
ground-truth test set for A0, A1, A2, A3, and later models.
