#!/usr/bin/env python3
"""Train A5: A0 plus original Camera data plus added Think/Ziploc Camera data."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("a5_balanced_camera", "dataset_a5_balanced_camera.yaml")
