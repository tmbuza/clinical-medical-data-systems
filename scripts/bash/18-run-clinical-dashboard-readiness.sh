#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results/dashboard results/figures

LOG_FILE="logs/18-clinical-dashboard-readiness.log"

{
  echo "Starting Chapter 18 clinical dashboard readiness workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/18-build-clinical-dashboard-readiness-safe.py

  echo
  Rscript scripts/R/18-visualize-dashboard-readiness-safe.R

  echo
  echo "Expected outputs:"
  echo "results/dashboard/dashboard-metric-catalog.tsv"
  echo "results/dashboard/dashboard-kpi-summary.tsv"
  echo "results/dashboard/dashboard-risk-group-summary.tsv"
  echo "results/dashboard/dashboard-readiness-issues.tsv"
  echo "results/dashboard/clinical-dashboard-prototype.html"
  echo "results/figures/dashboard-kpi-readiness-summary.png"

  echo
  echo "Completed Chapter 18 workflow"
} 2>&1 | tee "${LOG_FILE}"
