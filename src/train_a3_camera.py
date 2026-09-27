#!/usr/bin/env python3
"""Train A3: A0 clean data plus clean deployment-camera frames."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a3_camera", "dataset_a3_camera.yaml")
