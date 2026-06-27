#!/usr/bin/env python3
"""
Build a simple clinical risk stratification workflow.

Input:
  results/analysis-ready-clinical-dataset.tsv

Outputs:
  results/clinical-risk-stratification-results.tsv
  results/clinical-risk-model-feature-summary.tsv
  results/clinical-risk-model-summary.txt
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


INPUT_FILE = Path("results/analysis-ready-clinical-dataset.tsv")
RESULTS_DIR = Path("results")

RISK_RESULTS_FILE = RESULTS_DIR / "clinical-risk-stratification-results.tsv"
FEATURE_SUMMARY_FILE = RESULTS_DIR / "clinical-risk-model-feature-summary.tsv"
MODEL_SUMMARY_FILE = RESULTS_DIR / "clinical-risk-model-summary.txt"


CANDIDATE_NUMERIC_FEATURES = [
    "age",
    "encounter_count",
    "diagnosis_count",
    "procedure_count",
    "medication_count",
    "abnormal_lab_count",
    "latest_systolic_bp",
    "latest_diastolic_bp",
    "latest_bmi",
    "follow_up_days",
]

CANDIDATE_BOOLEAN_FEATURES = [
    "has_diabetes_code",
    "has_hypertension_code",
    "has_ckd_code",
]

POSITIVE_OUTCOME_VALUES = {
    "event",
    "adverse_event",
    "adverse event",
    "died",
    "death",
    "dead",
    "readmitted",
    "yes",
    "true",
    "1",
    "positive",
}

NEGATIVE_OUTCOME_VALUES = {
    "no_event",
    "no event",
    "alive",
    "no",
    "false",
    "0",
    "negative",
    "none",
}


def read_dataset(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input file: {path}. "
            "Run Chapter 12 first: bash scripts/bash/12-run-analysis-ready-clinical-dataset.sh"
        )

    return pd.read_csv(path, sep="\t")


def safe_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(False)

    lowered = series.astype("string").str.lower().str.strip()
    return lowered.isin(["true", "1", "yes", "y"])


def make_binary_outcome(series: pd.Series) -> pd.Series:
    lowered = series.astype("string").str.lower().str.strip()

    outcome = pd.Series(pd.NA, index=series.index, dtype="Int64")
    outcome[lowered.isin(POSITIVE_OUTCOME_VALUES)] = 1
    outcome[lowered.isin(NEGATIVE_OUTCOME_VALUES)] = 0

    return outcome


def select_analysis_rows(df: pd.DataFrame) -> pd.DataFrame:
    if "analysis_inclusion_flag" not in df.columns:
        return df.copy()

    flag = safe_bool(df["analysis_inclusion_flag"])
    selected = df.loc[flag].copy()

    if selected.empty:
        return df.copy()

    return selected


def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    feature_frames = []
    feature_rows = []

    for column in CANDIDATE_NUMERIC_FEATURES:
        if column not in df.columns:
            continue

        values = pd.to_numeric(df[column], errors="coerce")
        non_missing = int(values.notna().sum())

        if non_missing == 0:
            continue

        imputed = values.fillna(values.median())
        feature_frames.append(imputed.rename(column))

        feature_rows.append(
            {
                "feature": column,
                "feature_type": "numeric",
                "non_missing_count": non_missing,
                "missing_count": int(values.isna().sum()),
                "mean": round(float(values.mean()), 4) if values.notna().any() else pd.NA,
                "median": round(float(values.median()), 4) if values.notna().any() else pd.NA,
                "used_in_model": True,
            }
        )

    for column in CANDIDATE_BOOLEAN_FEATURES:
        if column not in df.columns:
            continue

        values = safe_bool(df[column]).astype(int)
        feature_frames.append(values.rename(column))

        feature_rows.append(
            {
                "feature": column,
                "feature_type": "boolean",
                "non_missing_count": int(values.notna().sum()),
                "missing_count": 0,
                "mean": round(float(values.mean()), 4) if len(values) else pd.NA,
                "median": round(float(values.median()), 4) if len(values) else pd.NA,
                "used_in_model": True,
            }
        )

    if not feature_frames:
        feature_matrix = pd.DataFrame(index=df.index)
    else:
        feature_matrix = pd.concat(feature_frames, axis=1)

    feature_summary = pd.DataFrame(feature_rows)

    return feature_matrix, feature_summary


def minmax_scale_scores(values: pd.Series) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce").fillna(0)

    min_value = values.min()
    max_value = values.max()

    if max_value == min_value:
        return pd.Series([0.5] * len(values), index=values.index)

    return (values - min_value) / (max_value - min_value)


def assign_risk_groups(scores: pd.Series) -> pd.Series:
    scores = pd.to_numeric(scores, errors="coerce").fillna(0.5)

    if scores.nunique() < 3:
        return pd.cut(
            scores,
            bins=[-0.01, 0.33, 0.66, 1.01],
            labels=["low", "moderate", "high"],
            include_lowest=True,
        ).astype("string").fillna("moderate")

    try:
        return pd.qcut(
            scores,
            q=3,
            labels=["low", "moderate", "high"],
            duplicates="drop",
        ).astype("string").fillna("moderate")
    except Exception:
        return pd.cut(
            scores,
            bins=[-0.01, 0.33, 0.66, 1.01],
            labels=["low", "moderate", "high"],
            include_lowest=True,
        ).astype("string").fillna("moderate")


def logistic_regression_scores(x: pd.DataFrame, y: pd.Series) -> tuple[pd.Series, str]:
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, solver="liblinear"),
        )
        model.fit(x, y.astype(int))
        scores = pd.Series(model.predict_proba(x)[:, 1], index=x.index)
        return scores, "logistic_regression"

    except Exception as exc:
        raw_score = x.sum(axis=1)
        return minmax_scale_scores(raw_score), f"rule_based_fallback_after_model_error: {exc}"


def rule_based_scores(x: pd.DataFrame) -> pd.Series:
    if x.empty:
        return pd.Series([0.5] * len(x), index=x.index)

    scaled_parts = []
    for column in x.columns:
        scaled_parts.append(minmax_scale_scores(x[column]).rename(column))

    scaled = pd.concat(scaled_parts, axis=1)
    return scaled.mean(axis=1)


def build_risk_scores(df: pd.DataFrame, x: pd.DataFrame, y: pd.Series) -> tuple[pd.Series, str]:
    usable = y.notna()
    unique_classes = y.dropna().nunique()

    if x.empty:
        return pd.Series([0.5] * len(df), index=df.index), "insufficient_features_fallback"

    if int(usable.sum()) >= 6 and unique_classes >= 2:
        scores = pd.Series(index=df.index, dtype=float)
        fitted_scores, method = logistic_regression_scores(x.loc[usable], y.loc[usable])
        scores.loc[usable] = fitted_scores

        if (~usable).any():
            scores.loc[~usable] = rule_based_scores(x.loc[~usable])

        return scores.fillna(0.5), method

    return rule_based_scores(x), "rule_based_fallback_insufficient_outcome_classes_or_rows"


def write_summary(
    df: pd.DataFrame,
    x: pd.DataFrame,
    y: pd.Series,
    method: str,
    risk_results: pd.DataFrame,
) -> None:
    outcome_non_missing = int(y.notna().sum())
    outcome_classes = int(y.dropna().nunique())
    risk_counts = risk_results["risk_group"].value_counts(dropna=False).to_dict()

    lines = [
        "Clinical Risk Stratification Model Summary",
        "==========================================",
        "",
        f"Input file: {INPUT_FILE}",
        f"Output file: {RISK_RESULTS_FILE}",
        "",
        f"Patients used for risk scoring: {len(df)}",
        f"Predictor count: {x.shape[1]}",
        f"Outcome non-missing count: {outcome_non_missing}",
        f"Outcome class count: {outcome_classes}",
        f"Scoring method: {method}",
        "",
        "Risk group counts:",
    ]

    for group, count in risk_counts.items():
        lines.append(f"- {group}: {count}")

    lines.extend(
        [
            "",
            "Interpretation:",
            "This workflow is a transparent risk stratification demonstration, not a validated clinical model.",
            "Real deployment requires clinical outcome review, external validation, calibration assessment, fairness review, and governance approval.",
        ]
    )

    MODEL_SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        raw = read_dataset(INPUT_FILE)
        df = select_analysis_rows(raw)

        if "outcome_status" in df.columns:
            y = make_binary_outcome(df["outcome_status"])
        else:
            y = pd.Series(pd.NA, index=df.index, dtype="Int64")

        x, feature_summary = build_feature_matrix(df)
        risk_scores, method = build_risk_scores(df, x, y)

        risk_results = pd.DataFrame(
            {
                "patient_id": df["patient_id"] if "patient_id" in df.columns else df.index.astype(str),
                "outcome_status": df["outcome_status"] if "outcome_status" in df.columns else pd.NA,
                "binary_outcome": y,
                "predicted_risk_score": risk_scores.round(6),
                "risk_group": assign_risk_groups(risk_scores),
                "scoring_method": method,
            }
        )

        if feature_summary.empty:
            feature_summary = pd.DataFrame(
                [
                    {
                        "feature": "none",
                        "feature_type": "not_available",
                        "non_missing_count": 0,
                        "missing_count": len(df),
                        "mean": pd.NA,
                        "median": pd.NA,
                        "used_in_model": False,
                    }
                ]
            )

        risk_results.to_csv(RISK_RESULTS_FILE, sep="\t", index=False)
        feature_summary.to_csv(FEATURE_SUMMARY_FILE, sep="\t", index=False)
        write_summary(df, x, y, method, risk_results)

        print(f"Wrote: {RISK_RESULTS_FILE}")
        print(f"Wrote: {FEATURE_SUMMARY_FILE}")
        print(f"Wrote: {MODEL_SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
