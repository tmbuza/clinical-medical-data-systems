#!/usr/bin/env bash
###############################################################################
# Clinical & Medical Data Systems
# End-to-End Case Study
###############################################################################

set -euo pipefail

echo "========================================"
echo "Clinical & Medical Data Systems"
echo "End-to-End Case Study"
echo "========================================"

bash scripts/bash/01-create-example-clinical-data.sh
bash scripts/bash/09-check-clinical-data-quality.sh

if command -v Rscript >/dev/null 2>&1; then
  Rscript scripts/R/12-build-analysis-ready-dataset.R
  Rscript scripts/R/13-run-descriptive-clinical-analysis.R
else
  echo "Rscript not found. Skipping R-based analysis steps."
fi

if command -v python3 >/dev/null 2>&1; then
  python3 scripts/python/15-evaluate-clinical-model.py
else
  echo "python3 not found. Skipping Python-based model step."
fi

echo "End-to-end case study complete."
