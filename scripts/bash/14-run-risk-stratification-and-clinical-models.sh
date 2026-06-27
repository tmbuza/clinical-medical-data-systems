#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/14-risk-stratification-and-clinical-models.log"

{
  echo "Starting Chapter 14 risk stratification and clinical models workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/14-risk-stratification-and-clinical-models-safe.py

  echo
  Rscript scripts/R/14-visualize-risk-stratification-safe.R

  echo
  echo "Expected outputs:"
  echo "results/clinical-risk-stratification-results.tsv"
  echo "results/clinical-risk-model-feature-summary.tsv"
  echo "results/clinical-risk-model-summary.txt"
  echo "results/figures/risk-score-distribution.png"
  echo "results/figures/risk-group-summary.png"

  echo
  echo "Completed Chapter 14 workflow"
} 2>&1 | tee "${LOG_FILE}"
