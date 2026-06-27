#!/usr/bin/env bash

set -euo pipefail

mkdir -p logs results/interoperability results/figures

LOG_FILE="logs/19-ehr-fhir-and-interoperability-roadmap.log"

{
  echo "Starting Chapter 19 EHR, FHIR, and interoperability roadmap workflow"
  echo "Timestamp: $(date)"
  echo

  python scripts/python/19-build-fhir-interoperability-roadmap-safe.py

  echo
  Rscript scripts/R/19-visualize-fhir-interoperability-readiness-safe.R

  echo
  echo "Expected outputs:"
  echo "results/interoperability/fhir-resource-mapping.tsv"
  echo "results/interoperability/interoperability-readiness-checklist.tsv"
  echo "results/interoperability/example-fhir-patient-bundle.json"
  echo "results/interoperability/interoperability-roadmap-summary.txt"
  echo "results/figures/fhir-resource-mapping-summary.png"

  echo
  echo "Completed Chapter 19 workflow"
} 2>&1 | tee "${LOG_FILE}"
