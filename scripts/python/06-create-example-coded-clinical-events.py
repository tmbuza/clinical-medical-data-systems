#!/usr/bin/env python3
"""
Create synthetic diagnosis, procedure, medication, and combined coded event data
for Chapter 06 of the Clinical & Medical Data Systems guide.

Run from the project root:
    python scripts/python/06-create-example-coded-clinical-events.py
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path("data/example")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    diagnoses = pd.DataFrame(
        [
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "code_system": "ICD-10-CM",
                "code": "E11.9",
                "code_description": "Type 2 diabetes mellitus without complications",
                "event_date": "2026-01-05",
                "diagnosis_position": "primary",
            },
            {
                "patient_id": "P002",
                "encounter_id": "E002",
                "code_system": "ICD-10-CM",
                "code": "I10",
                "code_description": "Essential hypertension",
                "event_date": "2026-01-09",
                "diagnosis_position": "secondary",
            },
            {
                "patient_id": "P003",
                "encounter_id": "E003",
                "code_system": "ICD-10-CM",
                "code": "J18.9",
                "code_description": "Pneumonia, unspecified organism",
                "event_date": "2026-01-14",
                "diagnosis_position": "primary",
            },
            {
                "patient_id": "P004",
                "encounter_id": "E004",
                "code_system": "ICD-10-CM",
                "code": "N39.0",
                "code_description": "Urinary tract infection, site not specified",
                "event_date": "2026-02-03",
                "diagnosis_position": "primary",
            },
        ]
    )

    procedures = pd.DataFrame(
        [
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "code_system": "CPT",
                "code": "83036",
                "code_description": "Hemoglobin A1c test",
                "event_date": "2026-01-05",
                "procedure_location": "outpatient clinic",
            },
            {
                "patient_id": "P002",
                "encounter_id": "E002",
                "code_system": "CPT",
                "code": "93000",
                "code_description": "Electrocardiogram",
                "event_date": "2026-01-09",
                "procedure_location": "outpatient clinic",
            },
            {
                "patient_id": "P003",
                "encounter_id": "E003",
                "code_system": "CPT",
                "code": "71046",
                "code_description": "Chest X-ray, two views",
                "event_date": "2026-01-14",
                "procedure_location": "emergency department",
            },
        ]
    )

    medications = pd.DataFrame(
        [
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "code_system": "RxNorm",
                "code": "860975",
                "code_description": "Metformin hydrochloride 500 MG oral tablet",
                "event_date": "2026-01-05",
                "medication_source": "order",
            },
            {
                "patient_id": "P003",
                "encounter_id": "E003",
                "code_system": "RxNorm",
                "code": "308182",
                "code_description": "Amoxicillin 500 MG oral capsule",
                "event_date": "2026-01-14",
                "medication_source": "administration",
            },
            {
                "patient_id": "P004",
                "encounter_id": "E004",
                "code_system": "RxNorm",
                "code": "197361",
                "code_description": "Ciprofloxacin 500 MG oral tablet",
                "event_date": "2026-02-03",
                "medication_source": "prescription",
            },
        ]
    )

    diagnoses.to_csv(DATA_DIR / "diagnoses.csv", index=False)
    procedures.to_csv(DATA_DIR / "procedures.csv", index=False)
    medications.to_csv(DATA_DIR / "medications.csv", index=False)

    common_cols = [
        "patient_id",
        "encounter_id",
        "code_system",
        "code",
        "code_description",
        "event_date",
    ]

    combined = pd.concat(
        [
            diagnoses[common_cols].assign(event_domain="diagnosis", source_table="diagnoses"),
            procedures[common_cols].assign(event_domain="procedure", source_table="procedures"),
            medications[common_cols].assign(event_domain="medication", source_table="medications"),
        ],
        ignore_index=True,
    )

    combined = combined[
        [
            "patient_id",
            "encounter_id",
            "event_domain",
            "code_system",
            "code",
            "code_description",
            "event_date",
            "source_table",
        ]
    ]

    combined.to_csv(DATA_DIR / "coded-clinical-events.csv", index=False)

    print("Created synthetic coded clinical event files:")
    print(f"- {DATA_DIR / 'diagnoses.csv'}")
    print(f"- {DATA_DIR / 'procedures.csv'}")
    print(f"- {DATA_DIR / 'medications.csv'}")
    print(f"- {DATA_DIR / 'coded-clinical-events.csv'}")


if __name__ == "__main__":
    main()
