#!/usr/bin/env python3
"""
Evaluate a clinical risk stratification output.

Input:
  results/clinical-risk-stratification-results.tsv

Outputs:
  results/clinical-model-evaluation-metrics.tsv
  results/clinical-model-threshold-evaluation.tsv
  results/clinical-model-risk-group-evaluation.tsv
  results/clinical-model-calibration-table.tsv
  results/clinical-model-evaluation-summary.txt
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


INPUT_FILE = Path("results/clinical-risk-stratification-results.tsv")
RESULTS_DIR = Path("results")

METRICS_FILE = RESULTS_DIR / "clinical-model-evaluation-metrics.tsv"
THRESHOLD_FILE = RESULTS_DIR / "clinical-model-threshold-evaluation.tsv"
RISK_GROUP_FILE = RESULTS_DIR / "clinical-model-risk-group-evaluation.tsv"
CALIBRATION_FILE = RESULTS_DIR / "clinical-model-calibration-table.tsv"
SUMMARY_FILE = RESULTS_DIR / "clinical-model-evaluation-summary.txt"


THRESHOLDS = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90]


def read_input(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing input file: {path}. "
            "Run Chapter 14 first: bash scripts/bash/14-run-risk-stratification-and-clinical-models.sh"
        )

    return pd.read_csv(path, sep="\t")


def safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def safe_binary_outcome(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.lower().str.strip()

    out = pd.Series(pd.NA, index=series.index, dtype="Int64")
    out[values.isin(["1", "true", "yes", "positive", "event"])] = 1
    out[values.isin(["0", "false", "no", "negative", "no_event", "no event"])] = 0

    numeric = pd.to_numeric(series, errors="coerce")
    out[numeric == 1] = 1
    out[numeric == 0] = 0

    return out


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0 or pd.isna(denominator):
        return np.nan
    return numerator / denominator


def calculate_optional_metrics(y: pd.Series, scores: pd.Series) -> dict:
    metrics = {
        "auroc": np.nan,
        "average_precision": np.nan,
        "brier_score": np.nan,
    }

    valid = y.notna() & scores.notna()
    y_valid = y.loc[valid].astype(int)
    scores_valid = scores.loc[valid].astype(float)

    if len(y_valid) == 0:
        return metrics

    metrics["brier_score"] = float(np.mean((scores_valid - y_valid) ** 2))

    if y_valid.nunique() < 2:
        return metrics

    try:
        from sklearn.metrics import average_precision_score, roc_auc_score

        metrics["auroc"] = float(roc_auc_score(y_valid, scores_valid))
        metrics["average_precision"] = float(average_precision_score(y_valid, scores_valid))
    except Exception:
        pass

    return metrics


def build_metrics(df: pd.DataFrame, y: pd.Series, scores: pd.Series) -> pd.DataFrame:
    valid = y.notna() & scores.notna()
    y_valid = y.loc[valid].astype(int)
    scores_valid = scores.loc[valid].astype(float)

    optional = calculate_optional_metrics(y, scores)

    metric_rows = [
        ("total_rows", len(df)),
        ("known_outcome_rows", int(y.notna().sum())),
        ("usable_evaluation_rows", int(valid.sum())),
        ("positive_outcome_count", int((y_valid == 1).sum()) if len(y_valid) else 0),
        ("negative_outcome_count", int((y_valid == 0).sum()) if len(y_valid) else 0),
        ("observed_event_rate", round(float(y_valid.mean()), 6) if len(y_valid) else np.nan),
        ("mean_predicted_risk", round(float(scores_valid.mean()), 6) if len(scores_valid) else np.nan),
        ("median_predicted_risk", round(float(scores_valid.median()), 6) if len(scores_valid) else np.nan),
        ("auroc", round(optional["auroc"], 6) if not pd.isna(optional["auroc"]) else np.nan),
        ("average_precision", round(optional["average_precision"], 6) if not pd.isna(optional["average_precision"]) else np.nan),
        ("brier_score", round(optional["brier_score"], 6) if not pd.isna(optional["brier_score"]) else np.nan),
    ]

    return pd.DataFrame(metric_rows, columns=["metric", "value"])


def build_threshold_table(y: pd.Series, scores: pd.Series) -> pd.DataFrame:
    valid = y.notna() & scores.notna()
    y_valid = y.loc[valid].astype(int)
    scores_valid = scores.loc[valid].astype(float)

    rows = []
    for threshold in THRESHOLDS:
        predicted_positive = scores_valid >= threshold

        tp = int(((predicted_positive) & (y_valid == 1)).sum())
        fp = int(((predicted_positive) & (y_valid == 0)).sum())
        tn = int(((~predicted_positive) & (y_valid == 0)).sum())
        fn = int(((~predicted_positive) & (y_valid == 1)).sum())

        sensitivity = safe_divide(tp, tp + fn)
        specificity = safe_divide(tn, tn + fp)
        ppv = safe_divide(tp, tp + fp)
        npv = safe_divide(tn, tn + fn)

        rows.append(
            {
                "threshold": threshold,
                "true_positive": tp,
                "false_positive": fp,
                "true_negative": tn,
                "false_negative": fn,
                "sensitivity": round(sensitivity, 6) if not pd.isna(sensitivity) else np.nan,
                "specificity": round(specificity, 6) if not pd.isna(specificity) else np.nan,
                "positive_predictive_value": round(ppv, 6) if not pd.isna(ppv) else np.nan,
                "negative_predictive_value": round(npv, 6) if not pd.isna(npv) else np.nan,
            }
        )

    return pd.DataFrame(rows)


def build_risk_group_table(df: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    if "risk_group" not in df.columns:
        return pd.DataFrame(
            [
                {
                    "risk_group": "missing",
                    "patient_count": len(df),
                    "known_outcome_count": int(y.notna().sum()),
                    "positive_outcome_count": int((y == 1).sum(skipna=True)),
                    "observed_event_rate": np.nan,
                }
            ]
        )

    temp = df.copy()
    temp["binary_outcome_safe"] = y
    temp["risk_group_safe"] = temp["risk_group"].astype("string").fillna("Missing")

    rows = []
    for group, group_df in temp.groupby("risk_group_safe", dropna=False):
        known = group_df["binary_outcome_safe"].dropna().astype(int)
        rows.append(
            {
                "risk_group": str(group),
                "patient_count": len(group_df),
                "known_outcome_count": int(known.shape[0]),
                "positive_outcome_count": int((known == 1).sum()) if len(known) else 0,
                "observed_event_rate": round(float(known.mean()), 6) if len(known) else np.nan,
            }
        )

    return pd.DataFrame(rows)


def build_calibration_table(y: pd.Series, scores: pd.Series) -> pd.DataFrame:
    valid = y.notna() & scores.notna()
    data = pd.DataFrame(
        {
            "binary_outcome": y.loc[valid].astype(int),
            "predicted_risk_score": scores.loc[valid].astype(float),
        }
    )

    if data.empty:
        return pd.DataFrame(
            [
                {
                    "calibration_bin": "not_available",
                    "patient_count": 0,
                    "mean_predicted_risk": np.nan,
                    "observed_event_rate": np.nan,
                }
            ]
        )

    if data["predicted_risk_score"].nunique() >= 4:
        try:
            data["calibration_bin"] = pd.qcut(
                data["predicted_risk_score"],
                q=min(5, data["predicted_risk_score"].nunique()),
                duplicates="drop",
            ).astype(str)
        except Exception:
            data["calibration_bin"] = "single_bin"
    else:
        data["calibration_bin"] = "single_bin"

    out = (
        data.groupby("calibration_bin", dropna=False)
        .agg(
            patient_count=("binary_outcome", "size"),
            mean_predicted_risk=("predicted_risk_score", "mean"),
            observed_event_rate=("binary_outcome", "mean"),
        )
        .reset_index()
    )

    out["mean_predicted_risk"] = out["mean_predicted_risk"].round(6)
    out["observed_event_rate"] = out["observed_event_rate"].round(6)

    return out


def write_summary(metrics: pd.DataFrame, threshold_table: pd.DataFrame, risk_group: pd.DataFrame, calibration: pd.DataFrame) -> None:
    metric_lookup = dict(zip(metrics["metric"], metrics["value"]))

    lines = [
        "Clinical Model Evaluation Summary",
        "=================================",
        "",
        f"Input file: {INPUT_FILE}",
        "",
        f"Total rows: {metric_lookup.get('total_rows', 'not available')}",
        f"Known outcome rows: {metric_lookup.get('known_outcome_rows', 'not available')}",
        f"Usable evaluation rows: {metric_lookup.get('usable_evaluation_rows', 'not available')}",
        f"Positive outcomes: {metric_lookup.get('positive_outcome_count', 'not available')}",
        f"Negative outcomes: {metric_lookup.get('negative_outcome_count', 'not available')}",
        f"Observed event rate: {metric_lookup.get('observed_event_rate', 'not available')}",
        f"Mean predicted risk: {metric_lookup.get('mean_predicted_risk', 'not available')}",
        f"AUROC: {metric_lookup.get('auroc', 'not available')}",
        f"Average precision: {metric_lookup.get('average_precision', 'not available')}",
        f"Brier score: {metric_lookup.get('brier_score', 'not available')}",
        "",
        f"Threshold rows written: {len(threshold_table)}",
        f"Risk group rows written: {len(risk_group)}",
        f"Calibration rows written: {len(calibration)}",
        "",
        "Interpretation:",
        "These outputs evaluate the example risk stratification workflow only.",
        "Small sample size, missing outcomes, or single-class outcomes limit what can be interpreted.",
        "Clinical deployment requires additional validation, calibration review, subgroup assessment, and governance approval.",
    ]

    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        df = read_input(INPUT_FILE)

        if "binary_outcome" in df.columns:
            y = safe_binary_outcome(df["binary_outcome"])
        else:
            y = pd.Series(pd.NA, index=df.index, dtype="Int64")

        if "predicted_risk_score" in df.columns:
            scores = safe_numeric(df["predicted_risk_score"]).clip(lower=0, upper=1)
        else:
            scores = pd.Series(np.nan, index=df.index)

        metrics = build_metrics(df, y, scores)
        threshold_table = build_threshold_table(y, scores)
        risk_group = build_risk_group_table(df, y)
        calibration = build_calibration_table(y, scores)

        metrics.to_csv(METRICS_FILE, sep="\t", index=False)
        threshold_table.to_csv(THRESHOLD_FILE, sep="\t", index=False)
        risk_group.to_csv(RISK_GROUP_FILE, sep="\t", index=False)
        calibration.to_csv(CALIBRATION_FILE, sep="\t", index=False)
        write_summary(metrics, threshold_table, risk_group, calibration)

        print(f"Wrote: {METRICS_FILE}")
        print(f"Wrote: {THRESHOLD_FILE}")
        print(f"Wrote: {RISK_GROUP_FILE}")
        print(f"Wrote: {CALIBRATION_FILE}")
        print(f"Wrote: {SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
