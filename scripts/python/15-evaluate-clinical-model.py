#!/usr/bin/env python3

"""
Placeholder clinical model evaluation script.

This first version does not train a real model.
It checks that the analysis-ready table exists and writes a simple model-readiness report.
"""

from pathlib import Path
import pandas as pd

input_path = Path("data/intermediate/analysis-ready-clinical-dataset.tsv")
output_dir = Path("results/models")
output_dir.mkdir(parents=True, exist_ok=True)

report_path = output_dir / "model-readiness-summary.tsv"

if not input_path.exists():
    raise FileNotFoundError(
        "Missing analysis-ready dataset. Run scripts/R/12-build-analysis-ready-dataset.R first."
    )

df = pd.read_csv(input_path, sep="\t")

summary = pd.DataFrame(
    {
        "metric": [
            "rows",
            "columns",
            "unique_patients",
            "has_outcome_status",
        ],
        "value": [
            df.shape[0],
            df.shape[1],
            df["patient_id"].nunique() if "patient_id" in df.columns else None,
            "outcome_status" in df.columns,
        ],
    }
)

summary.to_csv(report_path, sep="\t", index=False)

print(f"Model-readiness summary written to {report_path}")
