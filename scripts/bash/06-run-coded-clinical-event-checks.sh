#!/usr/bin/env bash
set -euo pipefail

# Run from the project root:
#   bash scripts/bash/06-run-coded-clinical-event-checks.sh

mkdir -p data/example results logs

LOG_FILE="logs/06-coded-clinical-event-checks.log"

{
  echo "Starting Chapter 06 coded clinical event workflow"
  date
  echo

  python scripts/python/06-create-example-coded-clinical-events.py
  echo

  python scripts/python/06-check-coded-clinical-events.py
  echo

  echo "Expected outputs:"
  echo "- data/example/diagnoses.csv"
  echo "- data/example/procedures.csv"
  echo "- data/example/medications.csv"
  echo "- data/example/coded-clinical-events.csv"
  echo "- results/coded-event-quality-checks.tsv"
  echo "- results/coded-event-domain-summary.tsv"
  echo "- results/coded-event-readiness-summary.txt"
  echo
  echo "Finished Chapter 06 coded clinical event workflow"
  date
} | tee "$LOG_FILE"
