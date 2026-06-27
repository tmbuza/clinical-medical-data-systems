#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/15-clinical-model-evaluation.log"

{
  echo "Starting Chapter 15 clinical model evaluation workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/15-clinical-model-evaluation-safe.py

  echo
  Rscript scripts/R/15-visualize-clinical-model-evaluation-safe.R

  echo
  echo "Expected outputs:"
  echo "results/clinical-model-evaluation-metrics.tsv"
  echo "results/clinical-model-threshold-evaluation.tsv"
  echo "results/clinical-model-risk-group-evaluation.tsv"
  echo "results/clinical-model-calibration-table.tsv"
  echo "results/clinical-model-evaluation-summary.txt"
  echo "results/figures/model-risk-by-outcome.png"
  echo "results/figures/model-calibration-plot.png"
  echo "results/figures/model-threshold-sensitivity-specificity.png"

  echo
  echo "Completed Chapter 15 workflow"
} 2>&1 | tee "${LOG_FILE}"
