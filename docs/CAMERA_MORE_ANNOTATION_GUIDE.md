# 新增 Camera 数据标注 / Additional Camera Data Annotation

## 启动 / Start

双击 `scripts/mac/start_camera_more_tz_annotator.command`，或在 Terminal 中运行：

```bash
./scripts/mac/start_camera_more_tz_annotator.command
```

浏览器地址 / Browser URL: `http://127.0.0.1:8767`

## 数据范围 / Dataset scope

- Think Protein Bar: 4 videos, about 33 seconds total.
- Ziploc Box: 4 videos, about 32 seconds total.
- 30 frames are sampled from each video, approximately 240 frames total.
- Labels are saved in YOLO format under `data/datasets_A/camera_more_thinkbar_ziploc/labels/train`.

## 规则 / Rules

1. 只标注完全匹配的 Coke Zero、Think Protein Bar 与 Ziploc Box；相似商品不标。 / Label only the three exact target SKUs; do not label similar products.
2. 标注画面里所有可辨认的目标，包括货架与背景中的目标。 / Label every visible target, including shelf and background instances.
3. 框紧贴商品包装，不包含手、阴影、货架或相邻商品。 / Keep boxes tight to the package; exclude hands, shadows, shelves, and neighboring products.
4. 遮挡时，仅在类别和位置仍可可靠判断时标注；可见不足约 15% 或位置不确定时不标。 / Under occlusion, annotate only if class and location remain reliable; skip when less than about 15% is visible or localization is uncertain.
5. 商品被画面边缘截断时，框止于图像边缘。 / For image-boundary truncation, stop the box at the image edge.
6. 只有画面中没有任何目标商品时，才使用“标记为空”。 / Use “Mark empty” only when no target SKU is present.

