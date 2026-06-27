#!/usr/bin/env python3
"""Create small synthetic laboratory and vital sign result datasets for Chapter 07.

The records are artificial and are intended for workflow demonstration only.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/example")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    labs = pd.DataFrame(
        [
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "specimen_datetime": "2026-01-04 08:20:00",
                "result_datetime": "2026-01-04 09:05:00",
                "result_domain": "laboratory",
                "result_name": "creatinine",
                "result_value": 1.1,
                "result_unit": "mg/dL",
                "reference_low": 0.6,
                "reference_high": 1.3,
                "abnormal_flag": "NORMAL",
                "source_system": "example_ehr",
            },
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "specimen_datetime": "2026-01-04 08:20:00",
                "result_datetime": "2026-01-04 09:10:00",
                "result_domain": "laboratory",
                "result_name": "hemoglobin",
                "result_value": 12.4,
                "result_unit": "g/dL",
                "reference_low": 12.0,
                "reference_high": 16.0,
                "abnormal_flag": "NORMAL",
                "source_system": "example_ehr",
            },
            {
                "patient_id": "P002",
                "encounter_id": "E002",
                "specimen_datetime": "2026-01-05 10:00:00",
                "result_datetime": "2026-01-05 11:00:00",
                "result_domain": "laboratory",
                "result_name": "glucose",
                "result_value": 186,
                "result_unit": "mg/dL",
                "reference_low": 70,
                "reference_high": 99,
                "abnormal_flag": "H",
                "source_system": "example_ehr",
            },
            {
                "patient_id": "P003",
                "encounter_id": "E003",
                "specimen_datetime": "2026-01-06 07:45:00",
                "result_datetime": "2026-01-06 08:30:00",
                "result_domain": "laboratory",
                "result_name": "potassium",
                "result_value": 4.2,
                "result_unit": "mmol/L",
                "reference_low": 3.5,
                "reference_high": 5.1,
                "abnormal_flag": "NORMAL",
                "source_system": "example_ehr",
            },
        ]
    )

    vitals = pd.DataFrame(
        [
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "measurement_datetime": "2026-01-04 08:15:00",
                "result_domain": "vital_sign",
                "result_name": "systolic_bp",
                "result_value": 138,
                "result_unit": "mmHg",
                "measurement_position": "sitting",
                "care_setting": "outpatient",
                "source_system": "example_ehr",
            },
            {
                "patient_id": "P001",
                "encounter_id": "E001",
                "measurement_datetime": "2026-01-04 08:15:00",
                "result_domain": "vital_sign",
                "result_name": "diastolic_bp",
                "result_value": 86,
                "result_unit": "mmHg",
                "measurement_position": "sitting",
                "care_setting": "outpatient",
                "source_system": "example_ehr",
            },
            {
                "patient_id": "P002",
                "encounter_id": "E002",
                "measurement_datetime": "2026-01-05 09:55:00",
                "result_domain": "vital_sign",
                "result_name": "heart_rate",
                "result_value": 104,
                "result_unit": "beats/min",
                "measurement_position": "sitting",
                "care_setting": "emergency",
                "source_system": "example_ehr",
            },
            {
                "patient_id": "P003",
                "encounter_id": "E003",
                "measurement_datetime": "2026-01-06 07:40:00",
                "result_domain": "vital_sign",
                "result_name": "oxygen_saturation",
                "result_value": 97,
                "result_unit": "%",
                "measurement_position": "resting",
                "care_setting": "inpatient",
                "source_system": "example_ehr",
            },
        ]
    )

    labs.to_csv(DATA_DIR / "laboratory-results.csv", index=False)
    vitals.to_csv(DATA_DIR / "vital-sign-results.csv", index=False)

    labs_common = labs.assign(measurement_datetime=labs["result_datetime"])[
        [
            "patient_id",
            "encounter_id",
            "measurement_datetime",
            "result_domain",
            "result_name",
            "result_value",
            "result_unit",
            "source_system",
        ]
    ]

    vitals_common = vitals[
        [
            "patient_id",
            "encounter_id",
            "measurement_datetime",
            "result_domain",
            "result_name",
            "result_value",
            "result_unit",
            "source_system",
        ]
    ]

    combined = pd.concat([labs_common, vitals_common], ignore_index=True)
    combined.to_csv(DATA_DIR / "clinical-results-combined.csv", index=False)

    print("Created example clinical result files:")
    print(f"- {DATA_DIR / 'laboratory-results.csv'}")
    print(f"- {DATA_DIR / 'vital-sign-results.csv'}")
    print(f"- {DATA_DIR / 'clinical-results-combined.csv'}")


if __name__ == "__main__":
    main()
