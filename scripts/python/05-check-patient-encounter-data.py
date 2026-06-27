#!/usr/bin/env python3
"""Check patient demographic and encounter data readiness.

The script reads patient and encounter CSV files, performs basic structural
checks, and writes modern, tidy TSV summaries for downstream review.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate patient and encounter inputs.")
    parser.add_argument("--patients", default="data/example/patient-demographics.csv", help="Patient demographics CSV path")
    parser.add_argument("--encounters", default="data/example/patient-encounters.csv", help="Patient encounters CSV path")
    parser.add_argument("--outdir", default="results", help="Output directory")
    return parser.parse_args()


def summarize_missing(df: pd.DataFrame, table_name: str) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "table": table_name,
            "column": df.columns,
            "missing_count": [int(df[col].isna().sum()) for col in df.columns],
            "missing_percent": [round(float(df[col].isna().mean() * 100), 2) for col in df.columns],
        }
    )


def main() -> None:
    args = parse_args()
    patients_path = Path(args.patients)
    encounters_path = Path(args.encounters)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    patients = pd.read_csv(patients_path)
    encounters = pd.read_csv(encounters_path)

    required_patient_cols = {"patient_id", "birth_date", "sex"}
    required_encounter_cols = {"encounter_id", "patient_id", "encounter_start", "encounter_end", "encounter_type"}

    missing_patient_cols = sorted(required_patient_cols - set(patients.columns))
    missing_encounter_cols = sorted(required_encounter_cols - set(encounters.columns))

    patients["birth_date"] = pd.to_datetime(patients.get("birth_date"), errors="coerce")
    encounters["encounter_start"] = pd.to_datetime(encounters.get("encounter_start"), errors="coerce")
    encounters["encounter_end"] = pd.to_datetime(encounters.get("encounter_end"), errors="coerce")

    duplicate_patients = int(patients["patient_id"].duplicated().sum()) if "patient_id" in patients else None
    duplicate_encounters = int(encounters["encounter_id"].duplicated().sum()) if "encounter_id" in encounters else None

    orphan_encounters = 0
    if "patient_id" in patients and "patient_id" in encounters:
        orphan_encounters = int((~encounters["patient_id"].isin(patients["patient_id"])).sum())

    invalid_date_order = int((encounters["encounter_end"] < encounters["encounter_start"]).sum())

    demographics_summary = pd.DataFrame(
        [
            {"metric": "patient_rows", "value": len(patients)},
            {"metric": "unique_patients", "value": patients["patient_id"].nunique() if "patient_id" in patients else None},
            {"metric": "duplicate_patient_ids", "value": duplicate_patients},
            {"metric": "missing_required_patient_columns", "value": ",".join(missing_patient_cols) if missing_patient_cols else "none"},
        ]
    )

    encounters_summary = pd.DataFrame(
        [
            {"metric": "encounter_rows", "value": len(encounters)},
            {"metric": "unique_encounters", "value": encounters["encounter_id"].nunique() if "encounter_id" in encounters else None},
            {"metric": "duplicate_encounter_ids", "value": duplicate_encounters},
            {"metric": "orphan_encounters_without_patient", "value": orphan_encounters},
            {"metric": "encounters_with_end_before_start", "value": invalid_date_order},
            {"metric": "missing_required_encounter_columns", "value": ",".join(missing_encounter_cols) if missing_encounter_cols else "none"},
        ]
    )

    quality_report = pd.concat(
        [
            summarize_missing(patients, "patients"),
            summarize_missing(encounters, "encounters"),
        ],
        ignore_index=True,
    )

    demographics_summary.to_csv(outdir / "demographics-summary.tsv", sep="\t", index=False)
    encounters_summary.to_csv(outdir / "encounters-summary.tsv", sep="\t", index=False)
    quality_report.to_csv(outdir / "patient-encounter-quality-report.tsv", sep="\t", index=False)

    print(f"Wrote {outdir / 'demographics-summary.tsv'}")
    print(f"Wrote {outdir / 'encounters-summary.tsv'}")
    print(f"Wrote {outdir / 'patient-encounter-quality-report.tsv'}")


if __name__ == "__main__":
    main()
