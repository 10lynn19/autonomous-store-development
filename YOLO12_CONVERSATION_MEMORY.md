# YOLO12 项目对话记忆（供新对话接手）

> 更新时间：2026-09-21
>
> 来源说明：原任务“用YOLO12做物体识别”的最近多轮正文在任务索引中为空，最后一轮状态为 `interrupted`。本文件根据可读取的任务元数据、项目文档、代码、模型、日志、测试指标和最新产物重建；数值均来自当前工作区文件。

## 1. 项目目标与工作环境

- 目标：用 YOLO12 对无人商店场景中的商品做目标检测，重点测试从白底旋转视频训练到真实部署摄像头场景的迁移能力。
- 当前有效工作区：`autonomous-store-development/`
- Windows 主训练路径：`C:\Market\autonomous-store-development`
- Mac 当前同步副本：`/Users/lynn/Documents/Autonomous store development/autonomous-store-development`
- 当前模型：Ultralytics `yolo12n.pt`。
- `autonomous-store-development` 是与旧 V1–V8.1 隔离的干净重建实验；不要读取或混用旧项目的 checkpoint、dataset 或 output。
- 训练主要在 Windows GPU 上完成，Mac 用于整理、查看、同步结果和制作汇报。

## 2. 必须保持的实验规范

- 每个对照分支都从同一个 `models/pretrained/yolo12n.pt` 独立开始，不能从前一个分支继续训练。
- 固定训练参数：40 epochs、`imgsz=1024`、batch 4、patience 8、AdamW、`lr0=0.0003`、seed 2026。
- 为确保只比较数据来源，训练时关闭颜色、旋转、平移、缩放、翻转、mosaic、mixup、cutmix、erasing 等增强。
- A 系列始终使用同一个 A0 validation split；B 系列始终使用同一个 B0 validation split。
- 固定测试集绝不能进入训练或模型选择。
- 固定测试评估：`imgsz=1024`、AP confidence floor `0.001`、NMS IoU `0.7`。
- 视频可视化阈值：confidence `0.35`、NMS IoU `0.7`。
- `video_summary.csv` 的 frame rate 只是可视化统计，不等于真实准确率；货架中静止商品会造成“检测到任意物体”的比例虚高。模型比较应以固定标注测试集的 ground-truth metrics 和 per-class metrics 为主。

## 3. A 系列：旧商品组合，已完成

类别顺序必须固定：

```text
0 coke_zero
1 think_protein_bar
2 ziploc_box
```

各分支：

- A0 Base：仅白底旋转视频帧。
- A1 Synthetic：A0 + 计算机合成的小物体缩放/噪声数据。
- A2 Phone：A0 + 手机小物体视频帧。
- A3 Camera：A0 + 部署摄像头 clean 场景帧。
- A4-P Camera + Phone：A0 + Camera + Phone。
- A4-S Camera + Synthetic：A0 + Camera + Synthetic。
- A5 Balanced Camera：A0 + 原 Camera + 额外人工复核的 Think/Ziploc 摄像头数据。
- A6-P Balanced Camera + Phone：A5 全部数据 + Phone。

固定 A 测试集规模：241 张部署摄像头图片，1,031 个标注框。

### A 系列固定测试集总指标

| 分支 | Precision | Recall | mAP50 | mAP50-95 | 结论 |
|---|---:|---:|---:|---:|---|
| A0 Base | 0.000 | 0.000 | 0.000 | 0.000 | 白底训练完全无法迁移到真实摄像头 |
| A1 Synthetic | 0.000 | 0.000 | 0.000 | 0.000 | 合成缩放/噪声没有弥合 domain gap |
| A2 Phone | 0.000 | 0.000 | 0.000 | 0.000 | 仅手机小物体数据也没有弥合 domain gap |
| A3 Camera | 0.279 | 0.226 | 0.280 | 0.113 | 摄像头上下文首次带来有效迁移，但主要靠 Coke |
| A4-P Camera+Phone | 0.515 | 0.329 | 0.368 | 0.148 | Phone 与 Camera 有互补性，Think/Ziploc 改善 |
| A4-S Camera+Synthetic | 0.641 | 0.319 | 0.362 | 0.154 | 指标略升，但出现整片零食区域被误判为 Think 的结构性假阳性 |
| A5 Balanced Camera | 0.649 | 0.426 | 0.503 | **0.244** | 额外平衡 Camera 数据显著改善 Think/Ziploc；A 系列最佳 mAP50-95 |
| A6-P Balanced Camera+Phone | **0.657** | **0.501** | **0.540** | 0.229 | A 系列最佳 mAP50/recall；Phone 显著提高 Think，但定位精度略降 |

### A5 与 A6-P 的关键 per-class 结论

- A5：Coke / Think / Ziploc mAP50 = `0.842 / 0.279 / 0.389`。
- A6-P：Coke / Think / Ziploc mAP50 = `0.779 / 0.450 / 0.391`。
- A6-P 相比 A5：整体 recall `0.426 → 0.501`，mAP50 `0.503 → 0.540`；Think 提升最大。
- 代价：Coke mAP50 下降，整体 mAP50-95 `0.244 → 0.229`。
- A6-P 仍未解决遮挡：在 0.35 视频阈值下，pickup Think 仍检测不到；pickup Ziploc 覆盖也比 A5 差。Phone 数据不能替代 pickup/occlusion 训练。

## 4. B 系列：新商品组合，已完成 B0/B1/B2/B4

类别顺序必须固定：

```text
0 coke_zero
1 oreo
2 goodwipes
```

注意：所有文件名、YOLO label 和 YAML 中统一使用 `goodwipes`，不要写成其他拼法。

各分支：

- B0 Base：白底 Coke/Oreo/Goodwipes。
- B1 Camera：B0 + clean deployment-camera 数据。
- B2 Phone：B0 + phone small-object 数据。
- B4 Camera + Phone：B0 + Camera + Phone。
- 建议未来 B5 Occlusion：从最佳 clean B checkpoint 出发，加入人工标注的 pickup/occlusion 数据。

固定 B 测试集规模：439 张图片，976 个标注框。

### B 系列固定测试集总指标

| 分支 | Precision | Recall | mAP50 | mAP50-95 | 结论 |
|---|---:|---:|---:|---:|---|
| B0 Base | 0.000 | 0.000 | 0.000 | 0.000 | 白底数据无法迁移 |
| B1 Camera | **0.870** | 0.605 | **0.753** | **0.332** | 当前 B 系列 ground-truth 指标最佳 |
| B2 Phone | 0.000 | 0.000 | 0.000 | 0.000 | Phone-only addition 无真实部署迁移能力 |
| B4 Camera+Phone | 0.839 | **0.652** | 0.713 | 0.320 | recall 更高，但整体 AP 略低于 B1 |

视频现象：

- B1 对 `test_pickup_goodwipes` 很强（0.35 阈值下目标类 frame coverage 约 95.7%），但 pickup Oreo 约 12.2%，pickup Coke 约 17.4%。
- B4 对 pickup Oreo 明显更强（约 77.4%），pickup Goodwipes 约 40.8%，但 pickup Coke 几乎失败（约 0.3%）。
- B4 在 `test_clean_coke` 中也大量预测 Goodwipes，说明仍有场景共现/背景捷径和类别混淆。
- 因此不能只说“B4 比 B1 好”：B1 的整体 AP 更好，B4 的 recall 和 Oreo pickup 更好。模型选择取决于部署优先级。

## 5. 最重要的科学结论

1. 白底 validation 接近完美（很多分支约 mAP50 0.995）并不代表真实部署有效；A0/A1/A2、B0/B2 在真实固定测试上都是 0。
2. 真正决定迁移能力的是 deployment-camera domain 数据，而不是单纯增加白底、合成或手机图。
3. Phone 数据只有和 Camera 数据组合后才可能带来互补收益，并且收益强烈依赖类别。
4. 类别平衡很重要：A5 补充 Think/Ziploc 的 Camera 标注后，A 系列 mAP50 从 A3 的 0.280 提升到 0.503。
5. 合成数据可能提高表面指标但制造结构性 false positive；A4-S 会把左侧零食簇整体框成 Think。未来合成数据要包含 shelf hard negatives，避免学习“长条/零食簇”捷径。
6. 遮挡仍是主要未解决问题。下一阶段不应继续只堆 clean/phone 数据，应建设 pickup/occlusion 标注训练分支，并加入无目标/易混淆货架区域 hard negatives。

## 6. 当前关键文件位置

- 总实验说明：`autonomous-store-development/docs/REBUILD_EXPERIMENT.md`
- B 系列计划：`autonomous-store-development/docs/B_SERIES_EXPERIMENT.md`
- 目录说明：`autonomous-store-development/docs/SERIES_DIRECTORY_STRUCTURE.md`
- 固定训练配置：`autonomous-store-development/src/train_common.py`
- A 测试程序：`autonomous-store-development/src/test_branches.py`
- B 测试程序：`autonomous-store-development/src/test_b_branches.py`
- A 数据配置：`autonomous-store-development/configs/dataset_a*.yaml`
- B 数据配置：`autonomous-store-development/configs/dataset_b*.yaml`
- A checkpoint：`autonomous-store-development/outputs/A_series/training/<branch>/weights/best.pt`
- B checkpoint：`autonomous-store-development/outputs/B_series/training/<branch>/weights/best.pt`
- A 测试结果：`autonomous-store-development/outputs/A_series/tests/<branch>_img1024_conf035/`
- B 测试结果：`autonomous-store-development/outputs/B_series/tests/<branch>_img1024_conf035/`
- 视频统计：每个测试结果目录中的 `video_summary.csv`
- Ground-truth 总指标：每个测试结果目录中的 `ground_truth_metrics.json`
- A5/A6-P 的 per-class 指标：对应测试目录中的 `class_metrics.csv` 和 `README.md`

## 7. 最新完成产物（2026-09-21）

- 已生成并通过渲染检查的 6 页汇报 PPT：
  `autonomous-store-development/docs/presentation/AB_series_new_video_results.pptx`
- PPT 内容比较 A5、A6-P、B1、B4，并嵌入 multiple1/multiple2 的结果 GIF。
- 最终渲染预览：
  `autonomous-store-development/.ppt_build/ab_series_new_videos/final_render/`
- 最新产物时间约为 2026-09-21 12:53，本次原对话最后一轮随后被中断；因此 PPT 本体很可能已经完成，只是原任务没有正常返回最终消息。

## 8. 建议新对话从这里继续

优先顺序建议：

1. 先查看最新 PPT 和 A5/A6-P/B1/B4 的视频结果，确认汇报叙述是否符合预期。
2. 如果目标是提升真实拿取识别，建立 A7/B5 Occlusion 分支：人工标注 pickup/occlusion 帧，同时加入货架 hard negatives。
3. 保留 fixed test set 完全隔离；新分支仍保持同一初始化与相同超参数，避免比较失真。
4. 对候选部署模型补充按场景、按类别、按遮挡程度的指标；不要只用总 mAP 或 any-detection frame rate。
5. 如果要部署，明确取舍：A5 偏定位质量，A6-P 偏 recall/Think；B1 偏总体 AP，B4 偏 recall/Oreo pickup。

## 9. 可直接贴到新对话的接手提示词

```text
请接手 /Users/lynn/Documents/Autonomous store development/autonomous-store-development 的 YOLO12 无人商店商品检测项目。先完整阅读 /Users/lynn/Documents/Autonomous store development/YOLO12_CONVERSATION_MEMORY.md，再检查相关项目文件后继续，不要重新发明已经完成的流程。

重要约束：不要混用旧 V1–V8.1 项目；每个实验分支必须从同一个 yolo12n.pt 独立训练；固定 validation/test split 和训练参数；test set 绝不能进入训练；视频 frame-rate 不是准确率，模型比较以 ground-truth metrics 和 per-class metrics 为准。

当前已完成 A0/A1/A2/A3/A4-P/A4-S/A5/A6-P 和 B0/B1/B2/B4。最新汇报 PPT 在 autonomous-store-development/docs/presentation/AB_series_new_video_results.pptx。下一阶段重点是 pickup/occlusion 与 shelf hard negatives，而不是继续只堆 clean/phone 数据。
```
