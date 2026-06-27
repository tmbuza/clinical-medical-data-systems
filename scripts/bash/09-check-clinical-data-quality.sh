#!/usr/bin/env bash
###############################################################################
# Basic clinical data quality checks
###############################################################################

set -euo pipefail

DATA_DIR="${1:-data/example}"
REPORT_DIR="reports"

mkdir -p "${REPORT_DIR}"

REPORT="${REPORT_DIR}/clinical-data-quality-summary.tsv"

echo -e "table\trows\tcolumns" > "${REPORT}"

for file in "${DATA_DIR}"/*.tsv; do
  table_name="$(basename "${file}")"
  rows="$(tail -n +2 "${file}" | wc -l | tr -d ' ')"
  columns="$(head -n 1 "${file}" | awk -F '\t' '{print NF}')"
  echo -e "${table_name}\t${rows}\t${columns}" >> "${REPORT}"
done

echo "Clinical data quality summary written to ${REPORT}"
