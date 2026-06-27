#!/usr/bin/env bash
set -euo pipefail

mkdir -p logs results data/example

LOG_FILE="logs/07-labs-and-vitals-checks.log"

{
  echo "Running Chapter 07 laboratory and vital sign workflow"
  echo "Started: $(date)"
  echo

  python scripts/python/07-create-example-labs-and-vitals.py
  python scripts/python/07-check-labs-and-vitals.py

  echo
  echo "Finished: $(date)"
  echo "Outputs:"
  echo "- data/example/laboratory-results.csv"
  echo "- data/example/vital-sign-results.csv"
  echo "- data/example/clinical-results-combined.csv"
  echo "- results/clinical-result-quality-checks.tsv"
  echo "- results/clinical-result-domain-summary.tsv"
  echo "- results/clinical-result-readiness-summary.txt"
} | tee "$LOG_FILE"
