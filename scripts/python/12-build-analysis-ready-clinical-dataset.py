#!/usr/bin/env python3
"""
Build an analysis-ready clinical dataset.

Inputs:
  results/patient-level-derived-variables.tsv

Outputs:
  results/analysis-ready-clinical-dataset.tsv
  results/analysis-ready-clinical-dataset-data-dictionary.tsv
  results/analysis-ready-clinical-dataset-readiness-summary.txt
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


INPUT_FILE = Path("results/patient-level-derived-variables.tsv")
RESULTS_DIR = Path("results")

OUTPUT_FILE = RESULTS_DIR / "analysis-ready-clinical-dataset.tsv"
DICTIONARY_FILE = RESULTS_DIR / "analysis-ready-clinical-dataset-data-dictionary.tsv"
SUMMARY_FILE = RESULTS_DIR / "analysis-ready-clinical-dataset-readiness-summary.txt"


REQUIRED_COLUMNS = [
    "patient_id",
    "age",
    "sex",
    "age_group",
    "encounter_count",
    "outcome_status",
    "follow_up_days",
]


OPTIONAL_COLUMNS = [
    "diagnosis_count",
    "procedure_count",
    "medication_count",
    "abnormal_lab_count",
    "latest_systolic_bp",
    "latest_diastolic_bp",
    "latest_bmi",
    "has_diabetes_code",
    "has_hypertension_code",
    "has_ckd_code",
]


def read_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input file: {path}. "
            "Run Chapter 11 first: python scripts/python/11-engineer-clinical-variables.py"
        )

    return pd.read_csv(path, sep="\t")


def ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if column not in out.columns:
            out[column] = pd.NA

    return out


def coerce_analysis_types(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    numeric_columns = [
        "age",
        "encounter_count",
        "follow_up_days",
        "diagnosis_count",
        "procedure_count",
        "medication_count",
        "abnormal_lab_count",
        "latest_systolic_bp",
        "latest_diastolic_bp",
        "latest_bmi",
    ]

    for column in numeric_columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")

    for column in ["patient_id", "sex", "age_group", "outcome_status"]:
        if column in out.columns:
            out[column] = out[column].astype("string").str.strip()

    for column in ["has_diabetes_code", "has_hypertension_code", "has_ckd_code"]:
        if column in out.columns:
            out[column] = out[column].fillna(False).astype(bool)

    return out


def add_readiness_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["valid_patient_id_flag"] = out["patient_id"].notna() & (out["patient_id"].astype(str).str.len() > 0)
    out["valid_age_flag"] = out["age"].notna() & (out["age"] >= 0) & (out["age"] <= 120)
    out["valid_sex_flag"] = out["sex"].notna() & (out["sex"].astype(str).str.len() > 0)
    out["valid_outcome_flag"] = out["outcome_status"].notna() & (out["outcome_status"].astype(str).str.len() > 0)
    out["valid_follow_up_flag"] = out["follow_up_days"].notna() & (out["follow_up_days"] >= 0)

    out["analysis_inclusion_flag"] = (
        out["valid_patient_id_flag"]
        & out["valid_age_flag"]
        & out["valid_sex_flag"]
        & out["valid_outcome_flag"]
        & out["valid_follow_up_flag"]
    )

    return out


def build_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    descriptions = {
        "patient_id": "Stable patient-level identifier.",
        "age": "Patient age at or near index encounter.",
        "sex": "Recorded patient sex.",
        "age_group": "Categorical age band derived from age.",
        "encounter_count": "Number of recorded encounters for the patient.",
        "diagnosis_count": "Number of diagnosis records linked to the patient.",
        "procedure_count": "Number of procedure records linked to the patient.",
        "medication_count": "Number of medication records linked to the patient.",
        "abnormal_lab_count": "Number of abnormal laboratory result indicators.",
        "latest_systolic_bp": "Most recent systolic blood pressure value available in the example data.",
        "latest_diastolic_bp": "Most recent diastolic blood pressure value available in the example data.",
        "latest_bmi": "Most recent body mass index value available in the example data.",
        "has_diabetes_code": "Patient has at least one diabetes-related diagnosis code in the example coded data.",
        "has_hypertension_code": "Patient has at least one hypertension-related diagnosis code in the example coded data.",
        "has_ckd_code": "Patient has at least one chronic kidney disease-related diagnosis code in the example coded data.",
        "outcome_status": "Recorded clinical outcome status.",
        "follow_up_days": "Follow-up duration in days.",
        "valid_patient_id_flag": "Identifier validity flag used for analysis readiness.",
        "valid_age_flag": "Age validity flag used for analysis readiness.",
        "valid_sex_flag": "Sex completeness flag used for analysis readiness.",
        "valid_outcome_flag": "Outcome completeness flag used for analysis readiness.",
        "valid_follow_up_flag": "Follow-up validity flag used for analysis readiness.",
        "analysis_inclusion_flag": "Overall patient-level eligibility flag for downstream example analysis.",
    }

    required = set(REQUIRED_COLUMNS)

    rows = []
    for column in df.columns:
        rows.append(
            {
                "variable": column,
                "description": descriptions.get(column, "Carried forward from the derived patient-level variable table."),
                "required_for_example_analysis": column in required,
                "observed_dtype": str(df[column].dtype),
                "missing_count": int(df[column].isna().sum()),
                "missing_percent": round(float(df[column].isna().mean() * 100), 2),
            }
        )

    return pd.DataFrame(rows)


def write_summary(df: pd.DataFrame, missing_required: list[str]) -> None:
    total_rows = len(df)
    unique_patients = df["patient_id"].nunique(dropna=True) if "patient_id" in df.columns else 0
    duplicate_patient_rows = int(df["patient_id"].duplicated().sum()) if "patient_id" in df.columns else 0
    included = int(df["analysis_inclusion_flag"].sum()) if "analysis_inclusion_flag" in df.columns else 0
    excluded = int(total_rows - included)

    lines = [
        "Analysis-Ready Clinical Dataset Readiness Summary",
        "=================================================",
        "",
        f"Input file: {INPUT_FILE}",
        f"Output file: {OUTPUT_FILE}",
        "",
        f"Rows: {total_rows}",
        f"Unique patients: {unique_patients}",
        f"Duplicate patient rows: {duplicate_patient_rows}",
        f"Analysis included rows: {included}",
        f"Analysis excluded rows: {excluded}",
        "",
        "Required columns:",
    ]

    for column in REQUIRED_COLUMNS:
        status = "present" if column in df.columns and column not in missing_required else "missing"
        missing_count = int(df[column].isna().sum()) if column in df.columns else "not available"
        lines.append(f"- {column}: {status}; missing = {missing_count}")

    if missing_required:
        lines.extend(["", "Missing required columns:", *[f"- {c}" for c in missing_required]])
    else:
        lines.extend(["", "Missing required columns: none"])

    lines.extend(
        [
            "",
            "Interpretation:",
            "This file is structurally prepared for downstream example analysis when the inclusion flag is true.",
            "Clinical validity still depends on the appropriateness of the question, cohort definition, and outcome definition.",
        ]
    )

    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        raw = read_input(INPUT_FILE)
        original_columns = set(raw.columns)

        missing_required = [column for column in REQUIRED_COLUMNS if column not in original_columns]

        df = ensure_columns(raw)
        df = coerce_analysis_types(df)
        df = add_readiness_flags(df)

        preferred_columns = [
            *REQUIRED_COLUMNS,
            *OPTIONAL_COLUMNS,
            "valid_patient_id_flag",
            "valid_age_flag",
            "valid_sex_flag",
            "valid_outcome_flag",
            "valid_follow_up_flag",
            "analysis_inclusion_flag",
        ]

        remaining_columns = [column for column in df.columns if column not in preferred_columns]
        df = df[[column for column in preferred_columns if column in df.columns] + remaining_columns]

        dictionary = build_dictionary(df)

        df.to_csv(OUTPUT_FILE, sep="\t", index=False)
        dictionary.to_csv(DICTIONARY_FILE, sep="\t", index=False)
        write_summary(df, missing_required)

        print(f"Wrote: {OUTPUT_FILE}")
        print(f"Wrote: {DICTIONARY_FILE}")
        print(f"Wrote: {SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
