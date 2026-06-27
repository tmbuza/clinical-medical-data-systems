#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/11-clinical-variable-engineering.log"

{
  echo "Running Chapter 11 clinical variable engineering workflow"
  echo "Started: $(date)"
  echo

  python scripts/python/11-engineer-clinical-variables.py
  echo

  Rscript scripts/R/11-visualize-clinical-variables.R
  echo

  echo "Completed: $(date)"
} 2>&1 | tee "${LOG_FILE}"
