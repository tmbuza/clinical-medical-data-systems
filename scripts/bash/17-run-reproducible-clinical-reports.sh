#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results/reports

LOG_FILE="logs/17-reproducible-clinical-reports.log"

{
  echo "Starting Chapter 17 reproducible clinical reports workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/17-build-reproducible-clinical-report-safe.py

  echo
  echo "Expected outputs:"
  echo "results/reports/reproducible-clinical-report.md"
  echo "results/reports/reproducible-clinical-report-summary.tsv"
  echo "results/reports/reproducible-clinical-report-file-inventory.tsv"

  echo
  echo "Completed Chapter 17 workflow"
} 2>&1 | tee "${LOG_FILE}"
