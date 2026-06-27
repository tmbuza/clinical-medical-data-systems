#!/usr/bin/env python3
"""Profile missingness and completeness across example clinical data files.

Run from the project root:
    python scripts/python/10-profile-missingness-and-completeness.py

Outputs are written to results/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data" / "example"
RESULTS_DIR = PROJECT_ROOT / "results"

EXPECTED_FILES = {
    "demographics": "patient-demographics.csv",
    "encounters": "clinical-encounters.csv",
    "diagnoses": "diagnoses.csv",
    "procedures": "procedures.csv",
    "medications": "medications.csv",
    "laboratory_results": "laboratory-results.csv",
    "vital_signs": "vital-sign-results.csv",
    "outcomes": "clinical-outcomes.csv",
}

DOMAIN_GROUPS = {
    "demographics": "patient_identity_and_context",
    "encounters": "care_contacts",
    "diagnoses": "coded_clinical_events",
    "procedures": "coded_clinical_events",
    "medications": "coded_clinical_events",
    "laboratory_results": "clinical_results",
    "vital_signs": "clinical_results",
    "outcomes": "outcomes_and_follow_up",
}

PATIENT_ID_CANDIDATES = ["patient_id", "person_id", "subject_id", "mrn"]


@dataclass(frozen=True)
class LoadedTable:
    dataset: str
    domain: str
    path: Path
    exists: bool
    data: pd.DataFrame | None


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_if_exists(dataset: str, filename: str) -> LoadedTable:
    path = DATA_DIR / filename
    domain = DOMAIN_GROUPS.get(dataset, "other")
    if not path.exists():
        return LoadedTable(dataset=dataset, domain=domain, path=path, exists=False, data=None)
    data = pd.read_csv(path)
    return LoadedTable(dataset=dataset, domain=domain, path=path, exists=True, data=data)


def completeness_percent(frame: pd.DataFrame) -> float:
    if frame.empty or frame.shape[1] == 0:
        return 0.0
    total_cells = frame.shape[0] * frame.shape[1]
    missing_cells = int(frame.isna().sum().sum())
    return round(100 * (1 - missing_cells / total_cells), 2)


def find_patient_id_column(columns: Iterable[str]) -> str | None:
    normalized = {column.lower(): column for column in columns}
    for candidate in PATIENT_ID_CANDIDATES:
        if candidate in normalized:
            return normalized[candidate]
    return None


def build_file_summary(tables: list[LoadedTable]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for table in tables:
        if table.data is None:
            rows.append(
                {
                    "dataset": table.dataset,
                    "domain": table.domain,
                    "file_path": str(table.path),
                    "exists": False,
                    "rows": 0,
                    "columns": 0,
                    "missing_cells": None,
                    "total_cells": None,
                    "completeness_percent": None,
                }
            )
            continue

        total_cells = table.data.shape[0] * table.data.shape[1]
        missing_cells = int(table.data.isna().sum().sum())
        rows.append(
            {
                "dataset": table.dataset,
                "domain": table.domain,
                "file_path": str(table.path),
                "exists": True,
                "rows": int(table.data.shape[0]),
                "columns": int(table.data.shape[1]),
                "missing_cells": missing_cells,
                "total_cells": total_cells,
                "completeness_percent": completeness_percent(table.data),
            }
        )
    return pd.DataFrame(rows)


def build_variable_summary(tables: list[LoadedTable]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for table in tables:
        if table.data is None:
            continue
        row_count = len(table.data)
        for column in table.data.columns:
            missing_count = int(table.data[column].isna().sum())
            non_missing_count = int(row_count - missing_count)
            rows.append(
                {
                    "dataset": table.dataset,
                    "domain": table.domain,
                    "variable": column,
                    "rows": row_count,
                    "missing_count": missing_count,
                    "non_missing_count": non_missing_count,
                    "missing_percent": round(100 * missing_count / row_count, 2) if row_count else 0.0,
                    "completeness_percent": round(100 * non_missing_count / row_count, 2) if row_count else 0.0,
                }
            )
    return pd.DataFrame(rows)


def build_domain_summary(variable_summary: pd.DataFrame) -> pd.DataFrame:
    if variable_summary.empty:
        return pd.DataFrame(
            columns=[
                "domain",
                "datasets",
                "variables",
                "average_completeness_percent",
                "minimum_completeness_percent",
                "maximum_missing_percent",
            ]
        )

    return (
        variable_summary.groupby("domain", as_index=False)
        .agg(
            datasets=("dataset", "nunique"),
            variables=("variable", "count"),
            average_completeness_percent=("completeness_percent", "mean"),
            minimum_completeness_percent=("completeness_percent", "min"),
            maximum_missing_percent=("missing_percent", "max"),
        )
        .round(2)
        .sort_values("average_completeness_percent")
    )


def build_patient_summary(tables: list[LoadedTable]) -> pd.DataFrame:
    patient_rows: list[pd.DataFrame] = []

    for table in tables:
        if table.data is None:
            continue
        patient_column = find_patient_id_column(table.data.columns)
        if patient_column is None:
            continue
        temp = table.data.copy()
        temp["_present_rows"] = 1
        patient_dataset_summary = (
            temp.groupby(patient_column, dropna=False)
            .agg(records=("_present_rows", "sum"))
            .reset_index()
            .rename(columns={patient_column: "patient_id"})
        )
        patient_dataset_summary["dataset"] = table.dataset
        patient_dataset_summary["domain"] = table.domain
        patient_rows.append(patient_dataset_summary)

    if not patient_rows:
        return pd.DataFrame(columns=["patient_id", "datasets_present", "domains_present", "total_records"])

    combined = pd.concat(patient_rows, ignore_index=True)
    return (
        combined.groupby("patient_id", as_index=False)
        .agg(
            datasets_present=("dataset", "nunique"),
            domains_present=("domain", "nunique"),
            total_records=("records", "sum"),
        )
        .sort_values(["domains_present", "datasets_present", "total_records"], ascending=[True, True, True])
    )


def write_readiness_summary(
    file_summary: pd.DataFrame,
    variable_summary: pd.DataFrame,
    domain_summary: pd.DataFrame,
    patient_summary: pd.DataFrame,
) -> None:
    available_files = int(file_summary["exists"].sum()) if not file_summary.empty else 0
    expected_files = len(EXPECTED_FILES)
    low_completeness_variables = (
        variable_summary.loc[variable_summary["completeness_percent"] < 80]
        if not variable_summary.empty
        else pd.DataFrame()
    )

    lines = [
        "Clinical Missingness and Completeness Readiness Summary",
        "======================================================",
        "",
        f"Expected files: {expected_files}",
        f"Available files: {available_files}",
        f"Missing expected files: {expected_files - available_files}",
        "",
        f"Variables below 80% completeness: {len(low_completeness_variables)}",
        f"Patients represented in patient-level summary: {len(patient_summary)}",
        "",
        "Domain completeness ranking:",
    ]

    if domain_summary.empty:
        lines.append("- No domain summary available.")
    else:
        for row in domain_summary.itertuples(index=False):
            lines.append(
                f"- {row.domain}: average completeness {row.average_completeness_percent}% "
                f"across {row.variables} variables"
            )

    lines.extend(
        [
            "",
            "Suggested next steps:",
            "- Review variables below the completeness threshold before engineering analysis variables.",
            "- Check whether missingness is concentrated in specific domains or patient groups.",
            "- Document whether missingness reflects clinical workflow, extraction limits, or true absence.",
        ]
    )

    (RESULTS_DIR / "missingness-completeness-readiness-summary.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    ensure_dirs()
    tables = [read_csv_if_exists(dataset, filename) for dataset, filename in EXPECTED_FILES.items()]

    file_summary = build_file_summary(tables)
    variable_summary = build_variable_summary(tables)
    domain_summary = build_domain_summary(variable_summary)
    patient_summary = build_patient_summary(tables)

    file_summary.to_csv(RESULTS_DIR / "missingness-file-summary.tsv", sep="\t", index=False)
    variable_summary.to_csv(RESULTS_DIR / "missingness-variable-summary.tsv", sep="\t", index=False)
    domain_summary.to_csv(RESULTS_DIR / "missingness-domain-summary.tsv", sep="\t", index=False)
    patient_summary.to_csv(RESULTS_DIR / "missingness-patient-summary.tsv", sep="\t", index=False)

    write_readiness_summary(file_summary, variable_summary, domain_summary, patient_summary)

    print("Missingness and completeness profiling complete.")
    print(f"Results written to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
