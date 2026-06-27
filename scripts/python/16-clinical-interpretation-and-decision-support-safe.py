#!/usr/bin/env python3
"""
Create clinical interpretation and decision-support readiness outputs.

Inputs:
  results/clinical-risk-stratification-results.tsv
  results/clinical-model-evaluation-metrics.tsv
  results/clinical-model-threshold-evaluation.tsv
  results/clinical-model-risk-group-evaluation.tsv
  results/clinical-model-calibration-table.tsv

Outputs:
  results/clinical-decision-support-readiness.tsv
  results/clinical-risk-interpretation-statements.tsv
  results/clinical-decision-support-action-map.tsv
  results/clinical-interpretation-and-decision-support-summary.txt
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


RESULTS_DIR = Path("results")

RISK_FILE = RESULTS_DIR / "clinical-risk-stratification-results.tsv"
METRICS_FILE = RESULTS_DIR / "clinical-model-evaluation-metrics.tsv"
THRESHOLD_FILE = RESULTS_DIR / "clinical-model-threshold-evaluation.tsv"
RISK_GROUP_FILE = RESULTS_DIR / "clinical-model-risk-group-evaluation.tsv"
CALIBRATION_FILE = RESULTS_DIR / "clinical-model-calibration-table.tsv"

READINESS_FILE = RESULTS_DIR / "clinical-decision-support-readiness.tsv"
STATEMENTS_FILE = RESULTS_DIR / "clinical-risk-interpretation-statements.tsv"
ACTION_MAP_FILE = RESULTS_DIR / "clinical-decision-support-action-map.tsv"
SUMMARY_FILE = RESULTS_DIR / "clinical-interpretation-and-decision-support-summary.txt"


def file_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def safe_read_tsv(path: Path) -> pd.DataFrame:
    if not file_exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path, sep="\t")
    except Exception:
        return pd.DataFrame()


def safe_numeric(value) -> float | None:
    try:
        parsed = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(parsed):
            return None
        return float(parsed)
    except Exception:
        return None


def metric_value(metrics: pd.DataFrame, name: str):
    if metrics.empty or "metric" not in metrics.columns or "value" not in metrics.columns:
        return None

    row = metrics.loc[metrics["metric"].astype(str) == name]
    if row.empty:
        return None

    return row["value"].iloc[0]


def build_readiness(metrics: pd.DataFrame, threshold: pd.DataFrame, risk_group: pd.DataFrame, calibration: pd.DataFrame) -> pd.DataFrame:
    known_outcome_rows = safe_numeric(metric_value(metrics, "known_outcome_rows"))
    usable_rows = safe_numeric(metric_value(metrics, "usable_evaluation_rows"))
    auroc = safe_numeric(metric_value(metrics, "auroc"))
    brier = safe_numeric(metric_value(metrics, "brier_score"))

    rows = [
        {
            "readiness_domain": "cohort_definition",
            "item": "Cohort and analysis-ready dataset documented",
            "status": "requires_project_review",
            "evidence": "Review Chapters 12 and 13 outputs.",
            "decision_support_note": "A decision-support workflow needs a visible denominator and inclusion logic.",
        },
        {
            "readiness_domain": "risk_output",
            "item": "Patient-level risk stratification output available",
            "status": "present" if file_exists(RISK_FILE) else "missing",
            "evidence": str(RISK_FILE),
            "decision_support_note": "Risk output is required before interpretation statements can be generated.",
        },
        {
            "readiness_domain": "evaluation",
            "item": "Model evaluation metrics available",
            "status": "present" if not metrics.empty else "missing",
            "evidence": str(METRICS_FILE),
            "decision_support_note": "Evaluation must be reviewed before any workflow use.",
        },
        {
            "readiness_domain": "evaluation",
            "item": "Known outcome rows available for evaluation",
            "status": "present" if known_outcome_rows is not None and known_outcome_rows > 0 else "limited_or_missing",
            "evidence": f"known_outcome_rows={known_outcome_rows}",
            "decision_support_note": "Decision support should not proceed without outcome-grounded review.",
        },
        {
            "readiness_domain": "thresholds",
            "item": "Threshold behavior table available",
            "status": "present" if not threshold.empty else "missing",
            "evidence": str(THRESHOLD_FILE),
            "decision_support_note": "Threshold behavior is needed before choosing an action cutoff.",
        },
        {
            "readiness_domain": "risk_groups",
            "item": "Observed event rates by risk group available",
            "status": "present" if not risk_group.empty else "missing",
            "evidence": str(RISK_GROUP_FILE),
            "decision_support_note": "Risk groups should show clinically meaningful separation before use.",
        },
        {
            "readiness_domain": "calibration",
            "item": "Calibration table available",
            "status": "present" if not calibration.empty else "missing",
            "evidence": str(CALIBRATION_FILE),
            "decision_support_note": "Calibration matters if predicted risks are interpreted as probabilities.",
        },
        {
            "readiness_domain": "performance",
            "item": "Discrimination metric is interpretable",
            "status": "present" if auroc is not None else "limited_or_missing",
            "evidence": f"auroc={auroc}",
            "decision_support_note": "AUROC may be unavailable when sample size is too small or outcomes have one class.",
        },
        {
            "readiness_domain": "performance",
            "item": "Brier score is available",
            "status": "present" if brier is not None else "limited_or_missing",
            "evidence": f"brier_score={brier}",
            "decision_support_note": "Brier score summarizes probability error but does not establish clinical utility.",
        },
        {
            "readiness_domain": "governance",
            "item": "Clinical governance approval",
            "status": "required_not_completed_by_script",
            "evidence": "Human/institutional review required.",
            "decision_support_note": "Governance review is mandatory before real clinical deployment.",
        },
        {
            "readiness_domain": "workflow",
            "item": "Human review and override process",
            "status": "required_not_completed_by_script",
            "evidence": "Workflow owner must define reviewer and escalation path.",
            "decision_support_note": "Decision support should assist qualified review, not replace it.",
        },
        {
            "readiness_domain": "monitoring",
            "item": "Post-deployment monitoring plan",
            "status": "required_not_completed_by_script",
            "evidence": "Monitoring plan must be defined before deployment.",
            "decision_support_note": "Clinical models can drift and should be monitored over time.",
        },
    ]

    return pd.DataFrame(rows)


def build_action_map() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "risk_group": "low",
                "decision_support_category": "routine_review",
                "example_action_language": "Continue routine review according to existing clinical workflow.",
                "required_safeguard": "Do not use low-risk status to deny clinically indicated care.",
                "deployment_status": "design_scaffold_only",
            },
            {
                "risk_group": "moderate",
                "decision_support_category": "consider_review",
                "example_action_language": "Consider additional review if clinically appropriate and resources allow.",
                "required_safeguard": "Clinical context should guide whether any action is needed.",
                "deployment_status": "design_scaffold_only",
            },
            {
                "risk_group": "high",
                "decision_support_category": "prioritize_review",
                "example_action_language": "Prioritize for qualified clinical review under an approved protocol.",
                "required_safeguard": "High-risk status should trigger review, not automatic treatment.",
                "deployment_status": "design_scaffold_only",
            },
            {
                "risk_group": "missing",
                "decision_support_category": "insufficient_information",
                "example_action_language": "Risk group is missing or not interpretable; review data completeness.",
                "required_safeguard": "Do not make risk-based decisions from missing or invalid model output.",
                "deployment_status": "design_scaffold_only",
            },
        ]
    )


def normalize_risk_group(value) -> str:
    if pd.isna(value):
        return "missing"
    text = str(value).strip().lower()
    if text in {"low", "moderate", "high"}:
        return text
    return "missing"


def build_interpretation_statements(risk: pd.DataFrame, action_map: pd.DataFrame) -> pd.DataFrame:
    if risk.empty:
        return pd.DataFrame(
            [
                {
                    "patient_id": "not_available",
                    "risk_group": "missing",
                    "predicted_risk_score": pd.NA,
                    "scoring_method": "not_available",
                    "interpretation_statement": "Risk interpretation statements could not be generated because the risk stratification file was not available.",
                    "decision_support_category": "insufficient_information",
                    "review_note": "Run Chapter 14 before generating interpretation statements.",
                }
            ]
        )

    action_lookup = action_map.set_index("risk_group").to_dict(orient="index")
    rows = []

    for _, row in risk.iterrows():
        patient_id = row.get("patient_id", "unknown_patient")
        risk_group = normalize_risk_group(row.get("risk_group", "missing"))
        score = safe_numeric(row.get("predicted_risk_score", None))
        method = row.get("scoring_method", "not_available")

        if score is None:
            score_text = "not available"
        else:
            score_text = f"{score:.2f}"

        action = action_lookup.get(risk_group, action_lookup["missing"])

        statement = (
            f"Patient {patient_id} is assigned to the {risk_group} risk group "
            f"with a predicted risk score of {score_text}. "
            "This is an example clinical risk stratification output and should not be used "
            "for clinical action without clinical validation, workflow approval, and governance review."
        )

        rows.append(
            {
                "patient_id": patient_id,
                "risk_group": risk_group,
                "predicted_risk_score": score_text,
                "scoring_method": method,
                "interpretation_statement": statement,
                "decision_support_category": action["decision_support_category"],
                "example_action_language": action["example_action_language"],
                "review_note": "Qualified clinical review is required before any real-world action.",
            }
        )

    return pd.DataFrame(rows)


def write_summary(readiness: pd.DataFrame, statements: pd.DataFrame, action_map: pd.DataFrame) -> None:
    readiness_counts = readiness["status"].value_counts(dropna=False).to_dict()
    risk_counts = statements["risk_group"].value_counts(dropna=False).to_dict() if "risk_group" in statements.columns else {}

    lines = [
        "Clinical Interpretation and Decision Support Summary",
        "====================================================",
        "",
        f"Readiness output: {READINESS_FILE}",
        f"Interpretation statements: {STATEMENTS_FILE}",
        f"Action map: {ACTION_MAP_FILE}",
        "",
        "Readiness status counts:",
    ]

    for status, count in readiness_counts.items():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "Risk group counts in interpretation statements:"])
    for group, count in risk_counts.items():
        lines.append(f"- {group}: {count}")

    lines.extend(
        [
            "",
            f"Action map rows: {len(action_map)}",
            f"Interpretation statement rows: {len(statements)}",
            "",
            "Interpretation:",
            "These outputs are decision-support design artifacts only.",
            "They do not constitute clinical recommendations, treatment instructions, or deployment approval.",
            "Real-world use requires clinical validation, governance review, workflow design, monitoring, and accountability.",
        ]
    )

    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        risk = safe_read_tsv(RISK_FILE)
        metrics = safe_read_tsv(METRICS_FILE)
        threshold = safe_read_tsv(THRESHOLD_FILE)
        risk_group = safe_read_tsv(RISK_GROUP_FILE)
        calibration = safe_read_tsv(CALIBRATION_FILE)

        readiness = build_readiness(metrics, threshold, risk_group, calibration)
        action_map = build_action_map()
        statements = build_interpretation_statements(risk, action_map)

        readiness.to_csv(READINESS_FILE, sep="\t", index=False)
        statements.to_csv(STATEMENTS_FILE, sep="\t", index=False)
        action_map.to_csv(ACTION_MAP_FILE, sep="\t", index=False)
        write_summary(readiness, statements, action_map)

        print(f"Wrote: {READINESS_FILE}")
        print(f"Wrote: {STATEMENTS_FILE}")
        print(f"Wrote: {ACTION_MAP_FILE}")
        print(f"Wrote: {SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
