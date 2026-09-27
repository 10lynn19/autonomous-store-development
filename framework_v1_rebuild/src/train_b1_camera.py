#!/usr/bin/env python3
"""Train B1: B0 plus labeled clean deployment-camera frames."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("b1_camera", "dataset_b1_camera.yaml", series="B_series")
