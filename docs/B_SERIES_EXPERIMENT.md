# B-series experiment plan

The B series uses three classes in this fixed order:

```text
0 coke_zero
1 oreo
2 goodwipes
```

All filenames, YOLO labels, and dataset YAML files use the canonical class
name `goodwipes`.

## Data boundaries

- `data/videos_B/clean_background/`: isolated-product source videos.
- `data/videos_B/phone_video/`: phone small-object source videos.
- `data/videos_B/camera/`: deployment-camera clean and pickup source videos.
- `data/videos_B/test/`: held-out evaluation videos; never use these for training.
- `data/datasets_B/`: generated YOLO datasets and labels.
- `outputs/B_series/training/`: B training runs and checkpoints.
- `outputs/B_series/tests/`: B fixed-test metrics and rendered videos.

All B-series test runs use `imgsz=1024`, video confidence `0.35`, and NMS IoU
`0.7`. Rendered Windows AVI files are automatically converted to H.264 MP4;
the MP4 files are the canonical videos to sync back to the Mac.

## Suggested sequence

1. **B0 Base:** clean-background Coke, Oreo, and Goodwipes only.
2. **B1 Camera:** B0 plus clean deployment-camera data.
3. **B2 Phone (optional):** B0 plus phone small-object data.
4. **B4 Camera + Phone:** B0 plus clean camera and phone data.
5. **B5 Occlusion:** start from the best clean B checkpoint and add labeled
   pickup/occlusion data.

Use the same fixed held-out B test set and the same hyperparameters when
comparing branches. This keeps the added data source as the principal changed
variable.
