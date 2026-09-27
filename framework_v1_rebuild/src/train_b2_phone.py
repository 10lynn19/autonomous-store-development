#!/usr/bin/env python3
"""Train B2: B0 plus labeled phone small-object frames."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("b2_phone", "dataset_b2_phone.yaml", series="B_series")
