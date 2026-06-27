#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results results/figures

LOG_FILE="logs/16-clinical-interpretation-and-decision-support.log"

{
  echo "Starting Chapter 16 clinical interpretation and decision support workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/16-clinical-interpretation-and-decision-support-safe.py

  echo
  Rscript scripts/R/16-visualize-decision-support-readiness-safe.R

  echo
  echo "Expected outputs:"
  echo "results/clinical-decision-support-readiness.tsv"
  echo "results/clinical-risk-interpretation-statements.tsv"
  echo "results/clinical-decision-support-action-map.tsv"
  echo "results/clinical-interpretation-and-decision-support-summary.txt"
  echo "results/figures/decision-support-risk-group-action-map.png"

  echo
  echo "Completed Chapter 16 workflow"
} 2>&1 | tee "${LOG_FILE}"
