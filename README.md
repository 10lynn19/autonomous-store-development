# Autonomous Store Development

An experimental autonomous-store product detection project built with YOLO12. The repository currently contains two controlled experiment series:

- **A series:** Coke, Think Protein Bar, and Ziploc
- **B series:** Coke Zero, Oreo, and Goodwipes

The project covers dataset preparation, manual annotation, model training, evaluation on fixed test sets, pickup-event demonstrations, and live camera detection. Experiment branches keep their initialization, training parameters, and evaluation data consistent wherever possible so that the effect of each added data source can be compared fairly.

## Project Structure

```text
.
├── configs/       # YOLO dataset configurations
├── docs/          # Experiment, annotation, and demo documentation
├── models/        # Pretrained models
├── scripts/       # macOS and Windows launch scripts
├── src/           # Data preparation, training, testing, and demo programs
├── data/          # Local videos and datasets (ignored by Git)
├── outputs/       # Training and test results (ignored by Git)
├── logs/          # Runtime logs (ignored by Git)
└── requirements.txt
```

## Installation

Use an isolated Python virtual environment.

### Windows PowerShell

```powershell
git clone git@github.com:10lynn19/autonomous-store-development.git C:\Market\autonomous-store-development
cd C:\Market\autonomous-store-development
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> The files in `configs/` and some cross-machine scripts currently use the Windows path `C:\Market\autonomous-store-development`. Update those paths before running the project from another location.

## Quick Start

### A-Series Baseline

```bash
python src/prepare_a0_base.py
python src/train_a0_base.py
python src/test_a0.py
```

Before training, review the labels in `data/datasets_A/a0_base/review/labels_preview.jpg`. See the [A-series experiment notes](docs/REBUILD_EXPERIMENT.md) for the complete experiment sequence and recorded results.

### B Series

```bash
python src/prepare_b0_base.py
python src/train_b0_base.py
python src/test_b_branches.py
```

See the [B-series experiment plan](docs/B_SERIES_EXPERIMENT.md) for class definitions, dataset boundaries, and the recommended experiment sequence. `data/videos_B/test/` is the fixed held-out test set and must not be included in training data.

### Windows Launch Scripts

Common tasks are also available as scripts in `scripts/windows/`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows\run_train_a0.ps1
powershell -ExecutionPolicy Bypass -File scripts\windows\run_train_b0.ps1
powershell -ExecutionPolicy Bypass -File scripts\windows\run_test_b0_b1.ps1
```

Training monitors are stored in the same directory with filenames beginning with `watch_`. macOS launchers for remote Windows training and monitoring are available in `scripts/mac/`.

## Pickup-Event and Live Demos

Run the B-series pickup-event demo with:

```bash
python src/run_b_pickup_demo.py --help
```

Run the live camera web demo with:

```bash
python src/live_detection_web.py --help
```

See the [pickup-event demo documentation](docs/B_PICKUP_EVENT_DEMO.md) for the event logic, available parameters, and output format. Detection results are raw model outputs and should not be treated as final inventory or checkout decisions.

## Data and Generated Outputs

The repository does not commit the following locally generated content:

- `data/`: source videos, extracted frames, and YOLO datasets
- `outputs/`: trained weights, metrics, and rendered videos
- `logs/`: training and monitoring logs
- Local virtual environments, archives, and temporary build files

When running the project across multiple machines, synchronize these directories separately and make sure the paths in `configs/` match their actual location.

## Additional Documentation

- [A/B series directory layout](docs/SERIES_DIRECTORY_STRUCTURE.md)
- [Test-set annotation guide](docs/TEST_ANNOTATION_GUIDE.md)
- [B-series augmentation and occlusion plan](docs/B_AUGMENTATION_OCCLUSION_PLAN.md)
- [Camera More annotation guide](docs/CAMERA_MORE_ANNOTATION_GUIDE.md)
