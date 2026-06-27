#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/10-missingness-and-completeness.log"

{
  echo "Running Chapter 10 missingness and completeness workflow"
  echo "Started: $(date)"
  echo

  python scripts/python/10-profile-missingness-and-completeness.py
  echo

  Rscript scripts/R/10-visualize-missingness-and-completeness.R
  echo

  echo "Completed: $(date)"
} 2>&1 | tee "${LOG_FILE}"
