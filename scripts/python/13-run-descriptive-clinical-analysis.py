#!/usr/bin/env python3
"""
Run descriptive clinical analysis.

Input:
  results/analysis-ready-clinical-dataset.tsv

Outputs:
  results/descriptive-clinical-cohort-summary.tsv
  results/descriptive-clinical-variable-summary.tsv
  results/descriptive-clinical-outcome-summary.tsv
  results/descriptive-clinical-table-one.tsv
  results/descriptive-clinical-analysis-summary.txt
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


INPUT_FILE = Path("results/analysis-ready-clinical-dataset.tsv")
RESULTS_DIR = Path("results")

COHORT_SUMMARY_FILE = RESULTS_DIR / "descriptive-clinical-cohort-summary.tsv"
VARIABLE_SUMMARY_FILE = RESULTS_DIR / "descriptive-clinical-variable-summary.tsv"
OUTCOME_SUMMARY_FILE = RESULTS_DIR / "descriptive-clinical-outcome-summary.tsv"
TABLE_ONE_FILE = RESULTS_DIR / "descriptive-clinical-table-one.tsv"
TEXT_SUMMARY_FILE = RESULTS_DIR / "descriptive-clinical-analysis-summary.txt"


NUMERIC_TABLE_ONE_VARIABLES = [
    "age",
    "follow_up_days",
    "encounter_count",
    "diagnosis_count",
    "procedure_count",
    "medication_count",
    "abnormal_lab_count",
    "latest_systolic_bp",
    "latest_diastolic_bp",
    "latest_bmi",
]

CATEGORICAL_TABLE_ONE_VARIABLES = [
    "sex",
    "age_group",
    "outcome_status",
    "has_diabetes_code",
    "has_hypertension_code",
    "has_ckd_code",
]


def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input file: {path}. "
            "Run Chapter 12 first: bash scripts/bash/12-run-analysis-ready-clinical-dataset.sh"
        )

    return pd.read_csv(path, sep="\t")


def as_bool_series(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series

    lowered = series.astype("string").str.lower().str.strip()
    return lowered.isin(["true", "1", "yes", "y"])


def summarize_cohort(df: pd.DataFrame) -> pd.DataFrame:
    included = as_bool_series(df["analysis_inclusion_flag"]) if "analysis_inclusion_flag" in df.columns else pd.Series([True] * len(df))

    metrics = [
        ("total_rows", len(df)),
        ("unique_patients", df["patient_id"].nunique(dropna=True) if "patient_id" in df.columns else pd.NA),
        ("duplicate_patient_rows", int(df["patient_id"].duplicated().sum()) if "patient_id" in df.columns else pd.NA),
        ("analysis_included_rows", int(included.sum())),
        ("analysis_excluded_rows", int((~included).sum())),
        ("analysis_included_percent", round(float(included.mean() * 100), 2) if len(df) else 0),
    ]

    for column in ["age", "follow_up_days", "encounter_count"]:
        if column in df.columns:
            values = pd.to_numeric(df[column], errors="coerce")
            metrics.extend(
                [
                    (f"{column}_mean", round(float(values.mean()), 2) if values.notna().any() else pd.NA),
                    (f"{column}_median", round(float(values.median()), 2) if values.notna().any() else pd.NA),
                    (f"{column}_min", round(float(values.min()), 2) if values.notna().any() else pd.NA),
                    (f"{column}_max", round(float(values.max()), 2) if values.notna().any() else pd.NA),
                ]
            )

    return pd.DataFrame(metrics, columns=["metric", "value"])


def summarize_variables(df: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for column in df.columns:
        non_missing = df[column].dropna()
        examples = ", ".join(non_missing.astype(str).unique()[:5]) if not non_missing.empty else ""

        rows.append(
            {
                "variable": column,
                "observed_dtype": str(df[column].dtype),
                "missing_count": int(df[column].isna().sum()),
                "missing_percent": round(float(df[column].isna().mean() * 100), 2),
                "unique_non_missing_values": int(non_missing.nunique()),
                "example_values": examples,
            }
        )

    return pd.DataFrame(rows)


def summarize_outcome(df: pd.DataFrame) -> pd.DataFrame:
    if "outcome_status" not in df.columns:
        return pd.DataFrame(
            [{"outcome_status": "outcome_status column missing", "patient_count": len(df), "patient_percent": 100.0}]
        )

    outcome = (
        df["outcome_status"]
        .fillna("Missing")
        .astype(str)
        .value_counts(dropna=False)
        .reset_index()
    )
    outcome.columns = ["outcome_status", "patient_count"]
    outcome["patient_percent"] = round(outcome["patient_count"] / len(df) * 100, 2) if len(df) else 0
    return outcome


def summarize_numeric_by_group(df: pd.DataFrame, group_column: str, variable: str) -> list[dict]:
    values = df[[group_column, variable]].copy()
    values[variable] = pd.to_numeric(values[variable], errors="coerce")

    rows = []
    for group_value, group_df in values.groupby(group_column, dropna=False):
        x = group_df[variable].dropna()
        rows.append(
            {
                "group_variable": group_column,
                "group_value": str(group_value),
                "variable": variable,
                "variable_type": "numeric",
                "level": "",
                "n_non_missing": int(x.shape[0]),
                "mean": round(float(x.mean()), 2) if not x.empty else pd.NA,
                "median": round(float(x.median()), 2) if not x.empty else pd.NA,
                "min": round(float(x.min()), 2) if not x.empty else pd.NA,
                "max": round(float(x.max()), 2) if not x.empty else pd.NA,
                "count": pd.NA,
                "percent_within_group": pd.NA,
            }
        )
    return rows


def summarize_categorical_by_group(df: pd.DataFrame, group_column: str, variable: str) -> list[dict]:
    rows = []

    grouped = df[[group_column, variable]].copy()
    grouped[variable] = grouped[variable].fillna("Missing").astype(str)

    for group_value, group_df in grouped.groupby(group_column, dropna=False):
        denominator = len(group_df)
        counts = group_df[variable].value_counts(dropna=False)

        for level, count in counts.items():
            rows.append(
                {
                    "group_variable": group_column,
                    "group_value": str(group_value),
                    "variable": variable,
                    "variable_type": "categorical",
                    "level": str(level),
                    "n_non_missing": pd.NA,
                    "mean": pd.NA,
                    "median": pd.NA,
                    "min": pd.NA,
                    "max": pd.NA,
                    "count": int(count),
                    "percent_within_group": round(float(count / denominator * 100), 2) if denominator else 0,
                }
            )

    return rows


def build_table_one(df: pd.DataFrame) -> pd.DataFrame:
    group_column = "analysis_inclusion_flag"

    if group_column not in df.columns:
        df = df.copy()
        df[group_column] = True

    rows = []

    for variable in NUMERIC_TABLE_ONE_VARIABLES:
        if variable in df.columns:
            rows.extend(summarize_numeric_by_group(df, group_column, variable))

    for variable in CATEGORICAL_TABLE_ONE_VARIABLES:
        if variable in df.columns:
            rows.extend(summarize_categorical_by_group(df, group_column, variable))

    return pd.DataFrame(rows)


def write_text_summary(cohort: pd.DataFrame, outcome: pd.DataFrame, table_one: pd.DataFrame) -> None:
    metric_lookup = dict(zip(cohort["metric"], cohort["value"]))

    lines = [
        "Descriptive Clinical Analysis Summary",
        "=====================================",
        "",
        f"Input file: {INPUT_FILE}",
        "",
        f"Total rows: {metric_lookup.get('total_rows', 'not available')}",
        f"Unique patients: {metric_lookup.get('unique_patients', 'not available')}",
        f"Analysis included rows: {metric_lookup.get('analysis_included_rows', 'not available')}",
        f"Analysis excluded rows: {metric_lookup.get('analysis_excluded_rows', 'not available')}",
        "",
        "Outcome distribution:",
    ]

    for _, row in outcome.iterrows():
        lines.append(
            f"- {row['outcome_status']}: {row['patient_count']} patients ({row['patient_percent']}%)"
        )

    lines.extend(
        [
            "",
            f"Table-one rows written: {len(table_one)}",
            "",
            "Interpretation:",
            "These outputs describe the prepared clinical cohort and should be reviewed before modeling.",
            "They do not establish causal effects, prediction performance, or clinical utility.",
        ]
    )

    TEXT_SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        df = read_dataset(INPUT_FILE)

        cohort = summarize_cohort(df)
        variables = summarize_variables(df)
        outcome = summarize_outcome(df)
        table_one = build_table_one(df)

        cohort.to_csv(COHORT_SUMMARY_FILE, sep="\t", index=False)
        variables.to_csv(VARIABLE_SUMMARY_FILE, sep="\t", index=False)
        outcome.to_csv(OUTCOME_SUMMARY_FILE, sep="\t", index=False)
        table_one.to_csv(TABLE_ONE_FILE, sep="\t", index=False)

        write_text_summary(cohort, outcome, table_one)

        print(f"Wrote: {COHORT_SUMMARY_FILE}")
        print(f"Wrote: {VARIABLE_SUMMARY_FILE}")
        print(f"Wrote: {OUTCOME_SUMMARY_FILE}")
        print(f"Wrote: {TABLE_ONE_FILE}")
        print(f"Wrote: {TEXT_SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
