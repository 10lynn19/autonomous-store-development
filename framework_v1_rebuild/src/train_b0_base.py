#!/usr/bin/env python3
"""Train B0: isolated Coke Zero, Oreo, and Goodwipes."""

from train_common import train_branch


if __name__ == "__main__":
    train_branch("b0_base", "dataset_b0_base.yaml", series="B_series")
