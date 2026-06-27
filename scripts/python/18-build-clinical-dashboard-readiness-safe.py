#!/usr/bin/env python3
"""
Build clinical dashboard readiness outputs.

Inputs:
  results/analysis-ready-clinical-dataset.tsv
  results/descriptive-clinical-cohort-summary.tsv
  results/descriptive-clinical-outcome-summary.tsv
  results/clinical-model-evaluation-metrics.tsv
  results/clinical-model-risk-group-evaluation.tsv
  results/clinical-decision-support-readiness.tsv

Outputs:
  results/dashboard/dashboard-metric-catalog.tsv
  results/dashboard/dashboard-kpi-summary.tsv
  results/dashboard/dashboard-risk-group-summary.tsv
  results/dashboard/dashboard-readiness-issues.tsv
  results/dashboard/clinical-dashboard-prototype.html
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import sys

import pandas as pd


RESULTS_DIR = Path("results")
DASHBOARD_DIR = RESULTS_DIR / "dashboard"

ANALYSIS_DATASET = RESULTS_DIR / "analysis-ready-clinical-dataset.tsv"
COHORT_SUMMARY = RESULTS_DIR / "descriptive-clinical-cohort-summary.tsv"
OUTCOME_SUMMARY = RESULTS_DIR / "descriptive-clinical-outcome-summary.tsv"
MODEL_METRICS = RESULTS_DIR / "clinical-model-evaluation-metrics.tsv"
RISK_GROUP_EVALUATION = RESULTS_DIR / "clinical-model-risk-group-evaluation.tsv"
DS_READINESS = RESULTS_DIR / "clinical-decision-support-readiness.tsv"

METRIC_CATALOG_FILE = DASHBOARD_DIR / "dashboard-metric-catalog.tsv"
KPI_SUMMARY_FILE = DASHBOARD_DIR / "dashboard-kpi-summary.tsv"
RISK_GROUP_SUMMARY_FILE = DASHBOARD_DIR / "dashboard-risk-group-summary.tsv"
READINESS_ISSUES_FILE = DASHBOARD_DIR / "dashboard-readiness-issues.tsv"
HTML_DASHBOARD_FILE = DASHBOARD_DIR / "clinical-dashboard-prototype.html"


def safe_read_tsv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(path, sep="\t")
    except Exception:
        return pd.DataFrame()


def safe_numeric(value):
    try:
        parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(parsed):
            return None
        return float(parsed)
    except Exception:
        return None


def metric_lookup(df: pd.DataFrame, metric_name: str):
    if df.empty or "metric" not in df.columns or "value" not in df.columns:
        return None

    row = df.loc[df["metric"].astype(str) == metric_name]
    if row.empty:
        return None

    return row["value"].iloc[0]


def build_metric_catalog() -> pd.DataFrame:
    rows = [
        {
            "metric_name": "total_patients",
            "display_label": "Total patients",
            "source_file": str(COHORT_SUMMARY),
            "numerator_definition": "All patient-level rows in prepared cohort.",
            "denominator_definition": "Not applicable.",
            "refresh_expectation": "Refresh after analysis-ready dataset is rebuilt.",
            "interpretation_note": "Represents prepared cohort size, not necessarily analysis-eligible population.",
        },
        {
            "metric_name": "analysis_included_patients",
            "display_label": "Analysis-included patients",
            "source_file": str(COHORT_SUMMARY),
            "numerator_definition": "Patients with analysis_inclusion_flag equal to true.",
            "denominator_definition": "Prepared patient-level cohort.",
            "refresh_expectation": "Refresh after Chapter 12 and Chapter 13 workflows.",
            "interpretation_note": "Patients meeting example analysis readiness rules.",
        },
        {
            "metric_name": "observed_event_rate",
            "display_label": "Observed event rate",
            "source_file": str(MODEL_METRICS),
            "numerator_definition": "Patients with positive binary outcome.",
            "denominator_definition": "Patients with known outcome and usable evaluation rows.",
            "refresh_expectation": "Refresh after model evaluation.",
            "interpretation_note": "Interpret only when outcome definition and sample size are appropriate.",
        },
        {
            "metric_name": "mean_predicted_risk",
            "display_label": "Mean predicted risk",
            "source_file": str(MODEL_METRICS),
            "numerator_definition": "Mean predicted risk score.",
            "denominator_definition": "Patients with risk scores.",
            "refresh_expectation": "Refresh after risk stratification.",
            "interpretation_note": "Prediction summary only; not a clinical recommendation.",
        },
        {
            "metric_name": "high_risk_patients",
            "display_label": "High-risk patients",
            "source_file": str(RISK_GROUP_EVALUATION),
            "numerator_definition": "Patients assigned to high risk group.",
            "denominator_definition": "Patients with assigned risk group.",
            "refresh_expectation": "Refresh after risk stratification.",
            "interpretation_note": "High-risk group requires clinical validation before action.",
        },
        {
            "metric_name": "decision_support_present_items",
            "display_label": "Decision-support readiness items present",
            "source_file": str(DS_READINESS),
            "numerator_definition": "Readiness checklist rows marked present.",
            "denominator_definition": "All decision-support readiness checklist rows.",
            "refresh_expectation": "Refresh after Chapter 16.",
            "interpretation_note": "Present items do not replace governance approval.",
        },
        {
            "metric_name": "decision_support_review_required_items",
            "display_label": "Decision-support items requiring review",
            "source_file": str(DS_READINESS),
            "numerator_definition": "Readiness checklist rows requiring project, governance, or workflow review.",
            "denominator_definition": "All decision-support readiness checklist rows.",
            "refresh_expectation": "Refresh after Chapter 16.",
            "interpretation_note": "Review-required items should be resolved before deployment.",
        },
    ]

    return pd.DataFrame(rows)


def build_issues(*, cohort: pd.DataFrame, model_metrics: pd.DataFrame, risk_group: pd.DataFrame, readiness: pd.DataFrame) -> pd.DataFrame:
    rows = []

    expected_files = [
        ANALYSIS_DATASET,
        COHORT_SUMMARY,
        OUTCOME_SUMMARY,
        MODEL_METRICS,
        RISK_GROUP_EVALUATION,
        DS_READINESS,
    ]

    for path in expected_files:
        if not path.exists():
            rows.append(
                {
                    "issue_level": "warning",
                    "issue": "missing_input_file",
                    "file_path": str(path),
                    "dashboard_impact": "Some dashboard metrics may be unavailable.",
                }
            )

    if cohort.empty:
        rows.append(
            {
                "issue_level": "warning",
                "issue": "cohort_summary_unavailable",
                "file_path": str(COHORT_SUMMARY),
                "dashboard_impact": "Core denominator KPIs may be missing.",
            }
        )

    if model_metrics.empty:
        rows.append(
            {
                "issue_level": "warning",
                "issue": "model_metrics_unavailable",
                "file_path": str(MODEL_METRICS),
                "dashboard_impact": "Model evaluation KPIs may be missing.",
            }
        )

    if risk_group.empty:
        rows.append(
            {
                "issue_level": "warning",
                "issue": "risk_group_summary_unavailable",
                "file_path": str(RISK_GROUP_EVALUATION),
                "dashboard_impact": "Risk group dashboard cards may be unavailable.",
            }
        )

    if readiness.empty:
        rows.append(
            {
                "issue_level": "warning",
                "issue": "decision_support_readiness_unavailable",
                "file_path": str(DS_READINESS),
                "dashboard_impact": "Governance and readiness section may be incomplete.",
            }
        )
    elif "status" in readiness.columns:
        unresolved = readiness["status"].astype(str).str.contains("required|review|missing|limited", case=False, na=False).sum()
        if unresolved > 0:
            rows.append(
                {
                    "issue_level": "review_required",
                    "issue": "decision_support_items_unresolved",
                    "file_path": str(DS_READINESS),
                    "dashboard_impact": f"{int(unresolved)} readiness items require review before deployment.",
                }
            )

    rows.append(
        {
            "issue_level": "note",
            "issue": "prototype_only",
            "file_path": str(HTML_DASHBOARD_FILE),
            "dashboard_impact": "The HTML dashboard is a prototype for review, not a production clinical dashboard.",
        }
    )

    return pd.DataFrame(rows)


def build_kpi_summary(cohort: pd.DataFrame, model_metrics: pd.DataFrame, risk_group: pd.DataFrame, readiness: pd.DataFrame) -> pd.DataFrame:
    total_patients = metric_lookup(cohort, "total_rows")
    analysis_included = metric_lookup(cohort, "analysis_included_rows")
    observed_event_rate = metric_lookup(model_metrics, "observed_event_rate")
    mean_predicted_risk = metric_lookup(model_metrics, "mean_predicted_risk")

    high_risk_count = None
    if not risk_group.empty and "risk_group" in risk_group.columns and "patient_count" in risk_group.columns:
        high_rows = risk_group.loc[risk_group["risk_group"].astype(str).str.lower() == "high"]
        if not high_rows.empty:
            high_risk_count = high_rows["patient_count"].iloc[0]

    present_items = None
    review_required_items = None
    if not readiness.empty and "status" in readiness.columns:
        status = readiness["status"].astype(str)
        present_items = int((status == "present").sum())
        review_required_items = int(status.str.contains("required|review|missing|limited", case=False, na=False).sum())

    rows = [
        {
            "metric_name": "total_patients",
            "display_label": "Total patients",
            "value": total_patients if total_patients is not None else "not_available",
            "status": "available" if total_patients is not None else "missing",
            "interpretation_note": "Prepared patient-level cohort size.",
        },
        {
            "metric_name": "analysis_included_patients",
            "display_label": "Analysis-included patients",
            "value": analysis_included if analysis_included is not None else "not_available",
            "status": "available" if analysis_included is not None else "missing",
            "interpretation_note": "Patients meeting example analysis readiness rules.",
        },
        {
            "metric_name": "observed_event_rate",
            "display_label": "Observed event rate",
            "value": observed_event_rate if observed_event_rate is not None else "not_available",
            "status": "available" if observed_event_rate is not None else "missing",
            "interpretation_note": "Requires known outcomes and reviewed outcome definition.",
        },
        {
            "metric_name": "mean_predicted_risk",
            "display_label": "Mean predicted risk",
            "value": mean_predicted_risk if mean_predicted_risk is not None else "not_available",
            "status": "available" if mean_predicted_risk is not None else "missing",
            "interpretation_note": "Prediction summary only; not an action recommendation.",
        },
        {
            "metric_name": "high_risk_patients",
            "display_label": "High-risk patients",
            "value": high_risk_count if high_risk_count is not None else "not_available",
            "status": "available" if high_risk_count is not None else "missing",
            "interpretation_note": "High-risk group requires governance before workflow use.",
        },
        {
            "metric_name": "decision_support_present_items",
            "display_label": "Decision-support readiness items present",
            "value": present_items if present_items is not None else "not_available",
            "status": "available" if present_items is not None else "missing",
            "interpretation_note": "Present items are technical evidence, not deployment approval.",
        },
        {
            "metric_name": "decision_support_review_required_items",
            "display_label": "Decision-support items requiring review",
            "value": review_required_items if review_required_items is not None else "not_available",
            "status": "available" if review_required_items is not None else "missing",
            "interpretation_note": "Review-required items must be resolved before deployment.",
        },
    ]

    return pd.DataFrame(rows)


def build_risk_group_dashboard_table(risk_group: pd.DataFrame) -> pd.DataFrame:
    if risk_group.empty:
        return pd.DataFrame(
            [
                {
                    "risk_group": "not_available",
                    "patient_count": 0,
                    "known_outcome_count": 0,
                    "positive_outcome_count": 0,
                    "observed_event_rate": "not_available",
                    "dashboard_note": "Risk group evaluation file was unavailable.",
                }
            ]
        )

    out = risk_group.copy()
    for column in ["risk_group", "patient_count", "known_outcome_count", "positive_outcome_count", "observed_event_rate"]:
        if column not in out.columns:
            out[column] = "not_available"

    out = out[["risk_group", "patient_count", "known_outcome_count", "positive_outcome_count", "observed_event_rate"]].copy()
    out["dashboard_note"] = "Risk group summaries are review artifacts and require validation before clinical action."

    return out


def html_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p>No rows available.</p>"

    header = "".join(f"<th>{escape(str(col))}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(f"<td>{escape(str(row[col]))}</td>" for col in df.columns)
        rows.append(f"<tr>{cells}</tr>")

    return f"<table><thead><tr>{header}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def build_html_dashboard(kpi: pd.DataFrame, risk_group: pd.DataFrame, issues: pd.DataFrame) -> str:
    created_at = datetime.now().isoformat(timespec="seconds")

    kpi_cards = []
    for _, row in kpi.iterrows():
        kpi_cards.append(
            f"""
            <section class="card">
              <h3>{escape(str(row['display_label']))}</h3>
              <p class="value">{escape(str(row['value']))}</p>
              <p class="note">{escape(str(row['interpretation_note']))}</p>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Clinical Dashboard Readiness Prototype</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 2rem;
      line-height: 1.5;
      background: #f8fafc;
      color: #0f172a;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin: 1.5rem 0;
    }}
    .card {{
      background: white;
      border: 1px solid #e2e8f0;
      border-radius: 14px;
      padding: 1rem;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
    }}
    .value {{
      font-size: 1.8rem;
      font-weight: 700;
      margin: 0.5rem 0;
    }}
    .note {{
      color: #475569;
      font-size: 0.9rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      margin: 1rem 0 2rem;
    }}
    th, td {{
      border: 1px solid #e2e8f0;
      padding: 0.6rem;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #e2e8f0;
    }}
    .warning {{
      background: #fff7ed;
      border-left: 5px solid #f97316;
      padding: 1rem;
      margin: 1rem 0;
    }}
  </style>
</head>
<body>
  <h1>Clinical Dashboard Readiness Prototype</h1>
  <p>Generated: <code>{escape(created_at)}</code></p>

  <div class="warning">
    <strong>Prototype only.</strong>
    This dashboard is a review artifact. It is not approved clinical decision support.
  </div>

  <h2>KPI Summary</h2>
  <div class="grid">
    {''.join(kpi_cards)}
  </div>

  <h2>Risk Group Summary</h2>
  {html_table(risk_group)}

  <h2>Dashboard Readiness Issues</h2>
  {html_table(issues)}

</body>
</html>
"""


def main() -> int:
    try:
        DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

        cohort = safe_read_tsv(COHORT_SUMMARY)
        model_metrics = safe_read_tsv(MODEL_METRICS)
        risk_group = safe_read_tsv(RISK_GROUP_EVALUATION)
        readiness = safe_read_tsv(DS_READINESS)

        catalog = build_metric_catalog()
        kpi = build_kpi_summary(cohort, model_metrics, risk_group, readiness)
        risk_group_dashboard = build_risk_group_dashboard_table(risk_group)
        issues = build_issues(cohort=cohort, model_metrics=model_metrics, risk_group=risk_group, readiness=readiness)
        html = build_html_dashboard(kpi, risk_group_dashboard, issues)

        catalog.to_csv(METRIC_CATALOG_FILE, sep="\t", index=False)
        kpi.to_csv(KPI_SUMMARY_FILE, sep="\t", index=False)
        risk_group_dashboard.to_csv(RISK_GROUP_SUMMARY_FILE, sep="\t", index=False)
        issues.to_csv(READINESS_ISSUES_FILE, sep="\t", index=False)
        HTML_DASHBOARD_FILE.write_text(html, encoding="utf-8")

        print(f"Wrote: {METRIC_CATALOG_FILE}")
        print(f"Wrote: {KPI_SUMMARY_FILE}")
        print(f"Wrote: {RISK_GROUP_SUMMARY_FILE}")
        print(f"Wrote: {READINESS_ISSUES_FILE}")
        print(f"Wrote: {HTML_DASHBOARD_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
