# A/B series directory structure

Shared code, environments, pretrained models, scripts, and documentation stay
at the project root. Data and generated results are separated by experiment
series:

```text
framework_v1_rebuild/
├── src/                         # shared Python code
├── configs/                     # A configs now; B configs will be added here
├── models/                      # shared pretrained checkpoints
├── scripts/                     # shared Mac/Windows launchers
├── data/
│   ├── videos_A/                # Coke + Think + Ziploc
│   ├── videos_B/                # Coke + Oreo + Goodwipes
│   ├── datasets_A/              # all completed A YOLO datasets
│   └── datasets_B/              # future B YOLO datasets
├── outputs/
│   ├── A_series/                # all completed A training/test results
│   └── B_series/                # future B training/test results
└── logs/
    ├── A_series/
    └── B_series/
```

The B-series held-out `test/` videos must never be sampled into a training
dataset. Camera pickup videos outside `test/` are reserved for the later B
occlusion branch, not the initial clean branch.
