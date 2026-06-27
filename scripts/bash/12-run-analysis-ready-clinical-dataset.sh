#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/12-analysis-ready-clinical-dataset.log"

{
  echo "Starting Chapter 12 analysis-ready clinical dataset workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/12-build-analysis-ready-clinical-dataset.py

  echo
  Rscript scripts/R/12-visualize-analysis-ready-clinical-dataset.R

  echo
  echo "Expected outputs:"
  echo "results/analysis-ready-clinical-dataset.tsv"
  echo "results/analysis-ready-clinical-dataset-data-dictionary.tsv"
  echo "results/analysis-ready-clinical-dataset-readiness-summary.txt"
  echo "results/figures/analysis-ready-age-group-distribution.png"
  echo "results/figures/analysis-ready-follow-up-distribution.png"

  echo
  echo "Completed Chapter 12 workflow"
} 2>&1 | tee "${LOG_FILE}"
