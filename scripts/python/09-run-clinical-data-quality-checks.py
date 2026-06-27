#!/usr/bin/env python3
"""Run cross-domain quality checks for example clinical data inputs.

This script is intentionally lightweight and portable. It checks the example
clinical data domains created in Part II of the Clinical & Medical Data Systems
guide and writes machine-readable TSV outputs plus a human-readable readiness
summary.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data" / "example"
RESULTS_DIR = PROJECT_ROOT / "results"


@dataclass(frozen=True)
class ClinicalFileSpec:
    domain: str
    path: Path
    required_columns: tuple[str, ...]
    key_columns: tuple[str, ...]
    date_columns: tuple[str, ...] = ()


FILE_SPECS: tuple[ClinicalFileSpec, ...] = (
    ClinicalFileSpec(
        domain="patients",
        path=DATA_DIR / "patient-demographics.csv",
        required_columns=("patient_id", "birth_date", "sex", "race_ethnicity"),
        key_columns=("patient_id", "birth_date", "sex"),
        date_columns=("birth_date",),
    ),
    ClinicalFileSpec(
        domain="encounters",
        path=DATA_DIR / "clinical-encounters.csv",
        required_columns=("encounter_id", "patient_id", "encounter_date", "encounter_type"),
        key_columns=("encounter_id", "patient_id", "encounter_date"),
        date_columns=("encounter_date",),
    ),
    ClinicalFileSpec(
        domain="diagnoses",
        path=DATA_DIR / "diagnoses.csv",
        required_columns=("patient_id", "encounter_id", "diagnosis_date", "diagnosis_code", "code_system"),
        key_columns=("patient_id", "diagnosis_date", "diagnosis_code"),
        date_columns=("diagnosis_date",),
    ),
    ClinicalFileSpec(
        domain="procedures",
        path=DATA_DIR / "procedures.csv",
        required_columns=("patient_id", "encounter_id", "procedure_date", "procedure_code", "code_system"),
        key_columns=("patient_id", "procedure_date", "procedure_code"),
        date_columns=("procedure_date",),
    ),
    ClinicalFileSpec(
        domain="medications",
        path=DATA_DIR / "medications.csv",
        required_columns=("patient_id", "encounter_id", "medication_start_date", "medication_name", "dose"),
        key_columns=("patient_id", "medication_start_date", "medication_name"),
        date_columns=("medication_start_date",),
    ),
    ClinicalFileSpec(
        domain="laboratory_results",
        path=DATA_DIR / "laboratory-results.csv",
        required_columns=("patient_id", "encounter_id", "result_date", "test_name", "result_value", "result_unit"),
        key_columns=("patient_id", "result_date", "test_name", "result_value"),
        date_columns=("result_date",),
    ),
    ClinicalFileSpec(
        domain="vital_sign_results",
        path=DATA_DIR / "vital-sign-results.csv",
        required_columns=("patient_id", "encounter_id", "result_date", "vital_name", "result_value", "result_unit"),
        key_columns=("patient_id", "result_date", "vital_name", "result_value"),
        date_columns=("result_date",),
    ),
    ClinicalFileSpec(
        domain="outcomes",
        path=DATA_DIR / "clinical-outcomes.csv",
        required_columns=("patient_id", "index_date", "follow_up_end_date", "outcome_status"),
        key_columns=("patient_id", "index_date", "follow_up_end_date", "outcome_status"),
        date_columns=("index_date", "follow_up_end_date"),
    ),
)


def read_csv_if_exists(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])


def write_tsv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, sep="\t", index=False)


def missingness_for_columns(df: pd.DataFrame, domain: str, columns: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    row_count = len(df)
    for column in columns:
        if column not in df.columns:
            rows.append(
                {
                    "domain": domain,
                    "column": column,
                    "column_present": False,
                    "row_count": row_count,
                    "missing_count": None,
                    "missing_percent": None,
                }
            )
            continue
        missing_count = int(df[column].isna().sum() + (df[column].astype(str).str.strip() == "").sum())
        missing_percent = round((missing_count / row_count) * 100, 2) if row_count else 0.0
        rows.append(
            {
                "domain": domain,
                "column": column,
                "column_present": True,
                "row_count": row_count,
                "missing_count": missing_count,
                "missing_percent": missing_percent,
            }
        )
    return rows


def parse_dates(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    parsed = df.copy()
    for column in columns:
        if column in parsed.columns:
            parsed[column] = pd.to_datetime(parsed[column], errors="coerce")
    return parsed


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    loaded: dict[str, pd.DataFrame] = {}
    file_rows: list[dict[str, object]] = []
    column_rows: list[dict[str, object]] = []
    missingness_rows: list[dict[str, object]] = []

    for spec in FILE_SPECS:
        df = read_csv_if_exists(spec.path)
        found = df is not None
        if found and df is not None:
            loaded[spec.domain] = df

        file_rows.append(
            {
                "domain": spec.domain,
                "file_path": str(spec.path.relative_to(PROJECT_ROOT)),
                "file_found": found,
                "row_count": 0 if df is None else len(df),
                "column_count": 0 if df is None else len(df.columns),
                "duplicate_row_count": None if df is None else int(df.duplicated().sum()),
            }
        )

        if df is None:
            for column in spec.required_columns:
                column_rows.append(
                    {
                        "domain": spec.domain,
                        "column": column,
                        "required": True,
                        "present": False,
                    }
                )
            continue

        for column in spec.required_columns:
            column_rows.append(
                {
                    "domain": spec.domain,
                    "column": column,
                    "required": True,
                    "present": column in df.columns,
                }
            )

        missingness_rows.extend(missingness_for_columns(df, spec.domain, spec.key_columns))

    patients = loaded.get("patients")
    known_patient_ids = set(patients["patient_id"].dropna().astype(str)) if patients is not None and "patient_id" in patients.columns else set()

    linkage_rows: list[dict[str, object]] = []
    for domain, df in loaded.items():
        if domain == "patients" or "patient_id" not in df.columns:
            continue
        patient_ids = df["patient_id"].dropna().astype(str)
        unknown_mask = ~patient_ids.isin(known_patient_ids)
        linkage_rows.append(
            {
                "domain": domain,
                "records_checked": len(df),
                "unique_patients_in_domain": int(patient_ids.nunique()),
                "unknown_patient_record_count": int(unknown_mask.sum()),
                "unknown_patient_percent": round((int(unknown_mask.sum()) / len(df)) * 100, 2) if len(df) else 0.0,
            }
        )

    temporal_rows: list[dict[str, object]] = []

    if "outcomes" in loaded:
        outcomes = parse_dates(loaded["outcomes"], ["index_date", "follow_up_end_date", "outcome_date"])
        if {"index_date", "follow_up_end_date"}.issubset(outcomes.columns):
            invalid = outcomes["follow_up_end_date"] < outcomes["index_date"]
            temporal_rows.append(
                {
                    "domain": "outcomes",
                    "rule": "follow_up_end_date should be on or after index_date",
                    "records_checked": len(outcomes),
                    "issue_count": int(invalid.sum()),
                }
            )
        if {"index_date", "outcome_date"}.issubset(outcomes.columns):
            has_outcome_date = outcomes["outcome_date"].notna()
            invalid = has_outcome_date & (outcomes["outcome_date"] < outcomes["index_date"])
            temporal_rows.append(
                {
                    "domain": "outcomes",
                    "rule": "outcome_date should be on or after index_date when present",
                    "records_checked": int(has_outcome_date.sum()),
                    "issue_count": int(invalid.sum()),
                }
            )

    if "medications" in loaded:
        medications = parse_dates(loaded["medications"], ["medication_start_date", "medication_stop_date"])
        if {"medication_start_date", "medication_stop_date"}.issubset(medications.columns):
            has_stop = medications["medication_stop_date"].notna()
            invalid = has_stop & (medications["medication_stop_date"] < medications["medication_start_date"])
            temporal_rows.append(
                {
                    "domain": "medications",
                    "rule": "medication_stop_date should be on or after medication_start_date when present",
                    "records_checked": int(has_stop.sum()),
                    "issue_count": int(invalid.sum()),
                }
            )

    file_summary = pd.DataFrame(file_rows)
    column_checks = pd.DataFrame(column_rows)
    missingness = pd.DataFrame(missingness_rows)
    linkage = pd.DataFrame(linkage_rows)
    temporal = pd.DataFrame(temporal_rows)

    write_tsv(file_summary, RESULTS_DIR / "clinical-data-quality-file-summary.tsv")
    write_tsv(column_checks, RESULTS_DIR / "clinical-data-quality-column-checks.tsv")
    write_tsv(missingness, RESULTS_DIR / "clinical-data-quality-missingness.tsv")
    write_tsv(linkage, RESULTS_DIR / "clinical-data-quality-linkage-checks.tsv")
    write_tsv(temporal, RESULTS_DIR / "clinical-data-quality-temporal-checks.tsv")

    missing_files = int((~file_summary["file_found"]).sum())
    missing_required_columns = int((~column_checks["present"]).sum()) if not column_checks.empty else 0
    linkage_issues = int(linkage["unknown_patient_record_count"].sum()) if not linkage.empty else 0
    temporal_issues = int(temporal["issue_count"].sum()) if not temporal.empty else 0
    high_missingness = 0
    if not missingness.empty and "missing_percent" in missingness.columns:
        high_missingness = int(pd.to_numeric(missingness["missing_percent"], errors="coerce").fillna(0).gt(20).sum())

    if missing_files or missing_required_columns:
        status = "NOT READY"
    elif linkage_issues or temporal_issues or high_missingness:
        status = "REVIEW NEEDED"
    else:
        status = "READY FOR NEXT CHECKS"

    summary_lines = [
        "Clinical Data Quality Readiness Summary",
        "",
        f"Overall status: {status}",
        "",
        "Major checks:",
        f"- Required files missing: {missing_files}",
        f"- Required columns missing: {missing_required_columns}",
        f"- Unknown patient-linked records: {linkage_issues}",
        f"- Temporal issue count: {temporal_issues}",
        f"- Key fields with >20% missingness: {high_missingness}",
        "",
        "Recommended next step:",
    ]

    if status == "READY FOR NEXT CHECKS":
        summary_lines.append("Proceed to missingness and data completeness analysis.")
    elif status == "REVIEW NEEDED":
        summary_lines.append("Review linkage, temporal, and missingness flags before creating analysis-ready datasets.")
    else:
        summary_lines.append("Resolve missing files or required columns before continuing.")

    (RESULTS_DIR / "clinical-data-quality-readiness-summary.txt").write_text("\n".join(summary_lines) + "\n")

    print("Clinical data quality checks complete.")
    print(f"Overall status: {status}")
    print(f"Results written to: {RESULTS_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
