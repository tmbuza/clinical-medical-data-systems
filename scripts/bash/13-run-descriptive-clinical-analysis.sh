#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/13-descriptive-clinical-analysis.log"

{
  echo "Starting Chapter 13 descriptive clinical analysis workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/13-run-descriptive-clinical-analysis.py

  echo
  Rscript scripts/R/13-visualize-descriptive-clinical-analysis.R

  echo
  echo "Expected outputs:"
  echo "results/descriptive-clinical-cohort-summary.tsv"
  echo "results/descriptive-clinical-variable-summary.tsv"
  echo "results/descriptive-clinical-outcome-summary.tsv"
  echo "results/descriptive-clinical-table-one.tsv"
  echo "results/descriptive-clinical-analysis-summary.txt"
  echo "results/figures/descriptive-age-distribution.png"
  echo "results/figures/descriptive-outcome-summary.png"
  echo "results/figures/descriptive-follow-up-by-outcome.png"

  echo
  echo "Completed Chapter 13 workflow"
} 2>&1 | tee "${LOG_FILE}"
