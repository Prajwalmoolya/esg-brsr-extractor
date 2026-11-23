"""
Measure accuracy against values you checked by hand.
ground_truth.csv columns: source_file, metric, true_value  (leave true_value empty if not reported)
Usage: python evaluate.py esg_metrics.csv
"""
import sys

import pandas as pd

truth = pd.read_csv("ground_truth.csv")
pred = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "esg_metrics.csv")

merged = truth.merge(pred[["source_file", "metric", "value"]], on=["source_file", "metric"], how="left")


def is_correct(row):
    if pd.isna(row.true_value):
        return pd.isna(row.value)
    if pd.isna(row.value):
        return False
    return abs(row.value - row.true_value) <= abs(row.true_value) * 0.01


merged["correct"] = merged.apply(is_correct, axis=1)

print(merged.to_string(index=False))
print(f"\nField-level accuracy: {merged.correct.mean():.1%} ({merged.correct.sum()}/{len(merged)})")
print("\nAccuracy by metric:")
print(merged.groupby("metric").correct.mean().map("{:.0%}".format))
