#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results/case-study

LOG_FILE="logs/20-end-to-end-case-study.log"

run_step() {
  local label="$1"
  shift

  echo
  echo "============================================================"
  echo "Running: ${label}"
  echo "Command: $*"
  echo "============================================================"
  "$@"
}

{
  echo "Starting Chapter 20 end-to-end clinical data systems case study"
  echo "Timestamp: $(date)"

  run_step "Chapter 05 example demographics and encounters" \
    python scripts/python/05-create-example-patient-encounter-data.py

  run_step "Chapter 05 patient encounter checks" \
    python scripts/python/05-check-patient-encounter-data.py

  run_step "Chapter 06 example coded clinical events" \
    python scripts/python/06-create-example-coded-clinical-events.py

  run_step "Chapter 06 coded clinical event checks" \
    python scripts/python/06-check-coded-clinical-events.py

  run_step "Chapter 07 example labs and vitals" \
    python scripts/python/07-create-example-labs-and-vitals.py

  run_step "Chapter 07 labs and vitals checks" \
    python scripts/python/07-check-labs-and-vitals.py

  run_step "Chapter 08 example outcomes" \
    python scripts/python/08-create-example-clinical-outcomes.py

  run_step "Chapter 08 outcome checks" \
    python scripts/python/08-check-clinical-outcomes.py

  run_step "Chapter 09 clinical data quality checks" \
    python scripts/python/09-run-clinical-data-quality-checks.py

  run_step "Chapter 10 missingness profile" \
    python scripts/python/10-profile-missingness-and-completeness.py

  run_step "Chapter 10 missingness visualization" \
    Rscript scripts/R/10-visualize-missingness-and-completeness.R

  run_step "Chapter 11 clinical variable engineering" \
    python scripts/python/11-engineer-clinical-variables.py

  run_step "Chapter 11 variable visualization" \
    Rscript scripts/R/11-visualize-clinical-variables.R

  run_step "Chapter 12 analysis-ready dataset" \
    python scripts/python/12-build-analysis-ready-clinical-dataset.py

  run_step "Chapter 12 analysis-ready visualization" \
    Rscript scripts/R/12-visualize-analysis-ready-clinical-dataset.R

  run_step "Chapter 13 descriptive clinical analysis" \
    python scripts/python/13-run-descriptive-clinical-analysis.py

  run_step "Chapter 13 descriptive visualization" \
    Rscript scripts/R/13-visualize-descriptive-clinical-analysis.R

  run_step "Chapter 14 risk stratification" \
    python scripts/python/14-risk-stratification-and-clinical-models-safe.py

  run_step "Chapter 14 risk visualization" \
    Rscript scripts/R/14-visualize-risk-stratification-safe.R

  run_step "Chapter 15 clinical model evaluation" \
    python scripts/python/15-clinical-model-evaluation-safe.py

  run_step "Chapter 15 model evaluation visualization" \
    Rscript scripts/R/15-visualize-clinical-model-evaluation-safe.R

  run_step "Chapter 16 interpretation and decision support" \
    python scripts/python/16-clinical-interpretation-and-decision-support-safe.py

  run_step "Chapter 16 decision-support visualization" \
    Rscript scripts/R/16-visualize-decision-support-readiness-safe.R

  run_step "Chapter 17 reproducible clinical report" \
    python scripts/python/17-build-reproducible-clinical-report-safe.py

  run_step "Chapter 18 dashboard readiness" \
    python scripts/python/18-build-clinical-dashboard-readiness-safe.py

  run_step "Chapter 18 dashboard visualization" \
    Rscript scripts/R/18-visualize-dashboard-readiness-safe.R

  run_step "Chapter 19 interoperability roadmap" \
    python scripts/python/19-build-fhir-interoperability-roadmap-safe.py

  run_step "Chapter 19 interoperability visualization" \
    Rscript scripts/R/19-visualize-fhir-interoperability-readiness-safe.R

  run_step "Chapter 20 end-to-end case study summary" \
    python scripts/python/20-build-end-to-end-case-study-summary-safe.py

  echo
  echo "Expected Chapter 20 outputs:"
  echo "results/case-study/end-to-end-case-study-file-inventory.tsv"
  echo "results/case-study/end-to-end-case-study-stage-summary.tsv"
  echo "results/case-study/end-to-end-case-study-summary.md"
  echo "results/case-study/end-to-end-case-study-readiness-summary.txt"

  echo
  echo "Completed Chapter 20 end-to-end case study"
} 2>&1 | tee "${LOG_FILE}"
