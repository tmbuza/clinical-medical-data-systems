#!/usr/bin/env python3
"""Create small example patient demographic and encounter datasets.

This script is intentionally lightweight and local. It creates synthetic,
de-identified teaching data for Chapter 05 of the Clinical & Medical Data
Systems guide.
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "example"
DATA_DIR.mkdir(parents=True, exist_ok=True)

patients = pd.DataFrame(
    [
        {"patient_id": "P001", "birth_date": "1971-04-12", "sex": "Female", "race_ethnicity": "Black", "residence_region": "Region A"},
        {"patient_id": "P002", "birth_date": "1958-11-03", "sex": "Male", "race_ethnicity": "Black", "residence_region": "Region B"},
        {"patient_id": "P003", "birth_date": "1986-07-22", "sex": "Female", "race_ethnicity": "Unknown", "residence_region": "Region A"},
        {"patient_id": "P004", "birth_date": "1949-01-19", "sex": "Male", "race_ethnicity": "Black", "residence_region": "Region C"},
        {"patient_id": "P005", "birth_date": "2001-09-30", "sex": "Female", "race_ethnicity": "Black", "residence_region": "Region B"},
    ]
)

encounters = pd.DataFrame(
    [
        {"encounter_id": "E001", "patient_id": "P001", "encounter_start": "2026-01-04", "encounter_end": "2026-01-08", "encounter_type": "inpatient", "facility_id": "FAC01", "discharge_disposition": "home"},
        {"encounter_id": "E002", "patient_id": "P001", "encounter_start": "2026-02-15", "encounter_end": "2026-02-15", "encounter_type": "outpatient", "facility_id": "FAC01", "discharge_disposition": "not_applicable"},
        {"encounter_id": "E003", "patient_id": "P002", "encounter_start": "2026-01-10", "encounter_end": "2026-01-13", "encounter_type": "inpatient", "facility_id": "FAC02", "discharge_disposition": "transfer"},
        {"encounter_id": "E004", "patient_id": "P003", "encounter_start": "2026-02-01", "encounter_end": "2026-02-01", "encounter_type": "outpatient", "facility_id": "FAC01", "discharge_disposition": "not_applicable"},
        {"encounter_id": "E005", "patient_id": "P004", "encounter_start": "2026-02-03", "encounter_end": "2026-02-12", "encounter_type": "inpatient", "facility_id": "FAC03", "discharge_disposition": "deceased"},
        {"encounter_id": "E006", "patient_id": "P005", "encounter_start": "2026-02-07", "encounter_end": "2026-02-07", "encounter_type": "emergency", "facility_id": "FAC02", "discharge_disposition": "home"},
    ]
)

patients.to_csv(DATA_DIR / "patient-demographics.csv", index=False)
encounters.to_csv(DATA_DIR / "patient-encounters.csv", index=False)

print(f"Wrote {DATA_DIR / 'patient-demographics.csv'}")
print(f"Wrote {DATA_DIR / 'patient-encounters.csv'}")
