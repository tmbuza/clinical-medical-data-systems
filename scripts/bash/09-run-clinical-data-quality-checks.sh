#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results

LOG_FILE="logs/09-clinical-data-quality-checks.log"

{
  echo "Clinical data quality checks"
  echo "Started: $(date)"
  echo

  python scripts/python/09-run-clinical-data-quality-checks.py

  echo
  echo "Finished: $(date)"
} | tee "$LOG_FILE"
