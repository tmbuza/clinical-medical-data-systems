#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs

LOG_FILE="logs/08-outcomes-and-follow-up-checks.log"

{
  echo "Clinical outcomes and follow-up workflow"
  echo "Started: $(date)"
  echo

  python scripts/python/08-create-example-clinical-outcomes.py
  python scripts/python/08-check-clinical-outcomes.py

  echo
  echo "Finished: $(date)"
  echo "Outputs:"
  echo "- data/example/clinical-outcomes.csv"
  echo "- results/outcome-quality-checks.tsv"
  echo "- results/outcome-summary.tsv"
  echo "- results/outcome-readiness-summary.txt"
} | tee "$LOG_FILE"
