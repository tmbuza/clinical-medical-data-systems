#!/usr/bin/env python3
"""
Build an end-to-end clinical data systems case-study summary.

Outputs:
  results/case-study/end-to-end-case-study-file-inventory.tsv
  results/case-study/end-to-end-case-study-stage-summary.tsv
  results/case-study/end-to-end-case-study-summary.md
  results/case-study/end-to-end-case-study-readiness-summary.txt
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd


RESULTS_DIR = Path("results")
CASE_STUDY_DIR = RESULTS_DIR / "case-study"

INVENTORY_FILE = CASE_STUDY_DIR / "end-to-end-case-study-file-inventory.tsv"
STAGE_SUMMARY_FILE = CASE_STUDY_DIR / "end-to-end-case-study-stage-summary.tsv"
SUMMARY_MD_FILE = CASE_STUDY_DIR / "end-to-end-case-study-summary.md"
READINESS_SUMMARY_FILE = CASE_STUDY_DIR / "end-to-end-case-study-readiness-summary.txt"


EXPECTED_STAGE_FILES = {
    "input_generation": [
        "data/example/patient-demographics.csv",
        "data/example/clinical-encounters.csv",
        "data/example/diagnoses.csv",
        "data/example/procedures.csv",
        "data/example/medications.csv",
        "data/example/laboratory-results.csv",
        "data/example/vital-sign-results.csv",
        "data/example/clinical-outcomes.csv",
    ],
    "input_validation": [
        "results/clinical-data-quality-file-summary.tsv",
        "results/clinical-data-quality-column-checks.tsv",
        "results/clinical-data-quality-missingness.tsv",
        "results/clinical-data-quality-linkage-checks.tsv",
        "results/clinical-data-quality-temporal-checks.tsv",
        "results/clinical-data-quality-readiness-summary.txt",
    ],
    "missingness_and_readiness": [
        "results/missingness-file-summary.tsv",
        "results/missingness-variable-summary.tsv",
        "results/missingness-domain-summary.tsv",
        "results/missingness-patient-summary.tsv",
        "results/missingness-completeness-readiness-summary.txt",
    ],
    "variable_engineering": [
        "results/patient-level-derived-variables.tsv",
        "results/clinical-variable-dictionary.tsv",
        "results/clinical-variable-engineering-summary.txt",
    ],
    "analysis_ready_dataset": [
        "results/analysis-ready-clinical-dataset.tsv",
        "results/analysis-ready-clinical-dataset-data-dictionary.tsv",
        "results/analysis-ready-clinical-dataset-readiness-summary.txt",
    ],
    "descriptive_analysis": [
        "results/descriptive-clinical-cohort-summary.tsv",
        "results/descriptive-clinical-variable-summary.tsv",
        "results/descriptive-clinical-outcome-summary.tsv",
        "results/descriptive-clinical-table-one.tsv",
        "results/descriptive-clinical-analysis-summary.txt",
    ],
    "risk_stratification": [
        "results/clinical-risk-stratification-results.tsv",
        "results/clinical-risk-model-feature-summary.tsv",
        "results/clinical-risk-model-summary.txt",
    ],
    "model_evaluation": [
        "results/clinical-model-evaluation-metrics.tsv",
        "results/clinical-model-threshold-evaluation.tsv",
        "results/clinical-model-risk-group-evaluation.tsv",
        "results/clinical-model-calibration-table.tsv",
        "results/clinical-model-evaluation-summary.txt",
    ],
    "clinical_interpretation": [
        "results/clinical-decision-support-readiness.tsv",
        "results/clinical-risk-interpretation-statements.tsv",
        "results/clinical-decision-support-action-map.tsv",
        "results/clinical-interpretation-and-decision-support-summary.txt",
    ],
    "reporting": [
        "results/reports/reproducible-clinical-report.md",
        "results/reports/reproducible-clinical-report-summary.tsv",
        "results/reports/reproducible-clinical-report-file-inventory.tsv",
    ],
    "dashboard_readiness": [
        "results/dashboard/dashboard-metric-catalog.tsv",
        "results/dashboard/dashboard-kpi-summary.tsv",
        "results/dashboard/dashboard-risk-group-summary.tsv",
        "results/dashboard/dashboard-readiness-issues.tsv",
        "results/dashboard/clinical-dashboard-prototype.html",
    ],
    "interoperability": [
        "results/interoperability/fhir-resource-mapping.tsv",
        "results/interoperability/interoperability-readiness-checklist.tsv",
        "results/interoperability/example-fhir-patient-bundle.json",
        "results/interoperability/interoperability-roadmap-summary.txt",
    ],
}


def escape_markdown_cell(value) -> str:
    if pd.isna(value):
        text = ""
    else:
        text = str(value)
    return text.replace("\n", " ").replace("\r", " ").replace("|", "\\|")


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df.empty:
        return "_No rows available._"

    if max_rows is not None:
        df = df.head(max_rows)

    columns = list(df.columns)
    header = "| " + " | ".join(escape_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(escape_markdown_cell(row[column]) for column in columns) + " |")

    return "\n".join([header, separator, *rows])


def build_inventory() -> pd.DataFrame:
    rows = []

    for stage, files in EXPECTED_STAGE_FILES.items():
        for file_path in files:
            path = Path(file_path)
            exists = path.exists()

            rows.append(
                {
                    "stage": stage,
                    "file_path": file_path,
                    "exists": exists,
                    "size_bytes": path.stat().st_size if exists else 0,
                    "modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if exists else "",
                }
            )

    return pd.DataFrame(rows)


def build_stage_summary(inventory: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for stage, group in inventory.groupby("stage", sort=False):
        expected = len(group)
        present = int(group["exists"].sum())
        missing = expected - present
        completion_percent = round(float(present / expected * 100), 2) if expected else 0

        if missing == 0:
            status = "complete"
        elif present > 0:
            status = "partial"
        else:
            status = "missing"

        rows.append(
            {
                "stage": stage,
                "expected_files": expected,
                "present_files": present,
                "missing_files": missing,
                "completion_percent": completion_percent,
                "status": status,
            }
        )

    return pd.DataFrame(rows)


def read_small_text(path: str, max_chars: int = 1200) -> str:
    p = Path(path)
    if not p.exists():
        return f"Missing file: `{path}`"

    text = p.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return f"File exists but is empty: `{path}`"

    if len(text) > max_chars:
        return text[:max_chars].rstrip() + "\n\n[truncated in case-study summary]"

    return text


def build_markdown_summary(inventory: pd.DataFrame, stage_summary: pd.DataFrame) -> str:
    created_at = datetime.now().isoformat(timespec="seconds")
    total_expected = len(inventory)
    total_present = int(inventory["exists"].sum())
    total_missing = total_expected - total_present
    complete_stages = int((stage_summary["status"] == "complete").sum())
    partial_stages = int((stage_summary["status"] == "partial").sum())
    missing_stages = int((stage_summary["status"] == "missing").sum())

    lines = [
        "# End-to-End Clinical Data Systems Case Study Summary",
        "",
        f"Generated: `{created_at}`",
        "",
        "## Purpose",
        "",
        "This case-study summary checks whether the Clinical & Medical Data Systems workflow produced the expected outputs across input generation, readiness, analysis, interpretation, reporting, dashboard readiness, and interoperability planning.",
        "",
        "This is an educational reproducibility artifact, not a clinical validation report.",
        "",
        "## Overall Completion",
        "",
        f"- Expected files: `{total_expected}`",
        f"- Present files: `{total_present}`",
        f"- Missing files: `{total_missing}`",
        f"- Complete stages: `{complete_stages}`",
        f"- Partial stages: `{partial_stages}`",
        f"- Missing stages: `{missing_stages}`",
        "",
        "## Stage Summary",
        "",
        dataframe_to_markdown(stage_summary),
        "",
        "## Key Narrative Outputs",
        "",
        "### Analysis-Ready Dataset",
        "",
        "```text",
        read_small_text("results/analysis-ready-clinical-dataset-readiness-summary.txt"),
        "```",
        "",
        "### Descriptive Clinical Analysis",
        "",
        "```text",
        read_small_text("results/descriptive-clinical-analysis-summary.txt"),
        "```",
        "",
        "### Risk Stratification",
        "",
        "```text",
        read_small_text("results/clinical-risk-model-summary.txt"),
        "```",
        "",
        "### Model Evaluation",
        "",
        "```text",
        read_small_text("results/clinical-model-evaluation-summary.txt"),
        "```",
        "",
        "### Clinical Interpretation and Decision Support",
        "",
        "```text",
        read_small_text("results/clinical-interpretation-and-decision-support-summary.txt"),
        "```",
        "",
        "### Interoperability Roadmap",
        "",
        "```text",
        read_small_text("results/interoperability/interoperability-roadmap-summary.txt"),
        "```",
        "",
        "## Missing Files",
        "",
    ]

    missing = inventory.loc[~inventory["exists"]]
    if missing.empty:
        lines.append("No expected files are missing.")
    else:
        lines.append(dataframe_to_markdown(missing[["stage", "file_path"]], max_rows=100))

    lines.extend(
        [
            "",
            "## Interpretation Boundaries",
            "",
            "A complete case-study run means the workflow generated the expected educational artifacts.",
            "",
            "It does not mean the model is clinically validated, the dashboard is production-ready, or the interoperability outputs are implementation-ready.",
            "",
            "## Recommended Final Review",
            "",
            "1. Review missing or partial stages.",
            "2. Inspect key summary text files.",
            "3. Open the reproducible Markdown report.",
            "4. Open the dashboard prototype.",
            "5. Review the interoperability roadmap.",
            "6. Confirm that all claims remain cautious and evidence-bound.",
            "",
        ]
    )

    return "\n".join(lines)


def build_readiness_text(stage_summary: pd.DataFrame) -> str:
    total_stages = len(stage_summary)
    complete = int((stage_summary["status"] == "complete").sum())
    partial = int((stage_summary["status"] == "partial").sum())
    missing = int((stage_summary["status"] == "missing").sum())

    if missing == 0 and partial == 0:
        overall = "complete"
    elif complete > 0:
        overall = "partial"
    else:
        overall = "missing"

    lines = [
        "End-to-End Case Study Readiness Summary",
        "=======================================",
        "",
        f"Overall status: {overall}",
        f"Total stages: {total_stages}",
        f"Complete stages: {complete}",
        f"Partial stages: {partial}",
        f"Missing stages: {missing}",
        "",
        "Stage statuses:",
    ]

    for _, row in stage_summary.iterrows():
        lines.append(
            f"- {row['stage']}: {row['status']} "
            f"({row['present_files']}/{row['expected_files']} files present)"
        )

    lines.extend(
        [
            "",
            "Interpretation:",
            "This readiness summary reflects workflow artifact availability only.",
            "Clinical validity, dashboard deployment, and interoperability implementation require additional review.",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> int:
    try:
        CASE_STUDY_DIR.mkdir(parents=True, exist_ok=True)

        inventory = build_inventory()
        stage_summary = build_stage_summary(inventory)
        markdown = build_markdown_summary(inventory, stage_summary)
        readiness_text = build_readiness_text(stage_summary)

        inventory.to_csv(INVENTORY_FILE, sep="\t", index=False)
        stage_summary.to_csv(STAGE_SUMMARY_FILE, sep="\t", index=False)
        SUMMARY_MD_FILE.write_text(markdown, encoding="utf-8")
        READINESS_SUMMARY_FILE.write_text(readiness_text, encoding="utf-8")

        print(f"Wrote: {INVENTORY_FILE}")
        print(f"Wrote: {STAGE_SUMMARY_FILE}")
        print(f"Wrote: {SUMMARY_MD_FILE}")
        print(f"Wrote: {READINESS_SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
