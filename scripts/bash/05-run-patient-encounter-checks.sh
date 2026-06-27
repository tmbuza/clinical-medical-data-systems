#!/usr/bin/env bash
set -euo pipefail

mkdir -p data/example results logs

python scripts/python/05-create-example-patient-encounter-data.py | tee logs/05-create-example-patient-encounter-data.log
python scripts/python/05-check-patient-encounter-data.py \
  --patients data/example/patient-demographics.csv \
  --encounters data/example/patient-encounters.csv \
  --outdir results | tee logs/05-check-patient-encounter-data.log

echo "Patient and encounter checks completed."
