#!/usr/bin/env python3
"""
Build a reproducible clinical report from saved workflow outputs.

This safe version avoids pandas.to_markdown(), so it does not require tabulate.

Outputs:
  results/reports/reproducible-clinical-report.md
  results/reports/reproducible-clinical-report-summary.tsv
  results/reports/reproducible-clinical-report-file-inventory.tsv
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd


RESULTS_DIR = Path("results")
REPORT_DIR = RESULTS_DIR / "reports"

REPORT_FILE = REPORT_DIR / "reproducible-clinical-report.md"
SUMMARY_FILE = REPORT_DIR / "reproducible-clinical-report-summary.tsv"
INVENTORY_FILE = REPORT_DIR / "reproducible-clinical-report-file-inventory.tsv"


EXPECTED_FILES = [
    {
        "path": "results/analysis-ready-clinical-dataset-readiness-summary.txt",
        "role": "Analysis-ready dataset readiness narrative",
    },
    {
        "path": "results/descriptive-clinical-analysis-summary.txt",
        "role": "Descriptive clinical analysis narrative",
    },
    {
        "path": "results/clinical-risk-model-summary.txt",
        "role": "Risk stratification model narrative",
    },
    {
        "path": "results/clinical-model-evaluation-summary.txt",
        "role": "Clinical model evaluation narrative",
    },
    {
        "path": "results/clinical-interpretation-and-decision-support-summary.txt",
        "role": "Clinical interpretation and decision-support narrative",
    },
    {
        "path": "results/descriptive-clinical-cohort-summary.tsv",
        "role": "Cohort summary metrics",
    },
    {
        "path": "results/clinical-model-evaluation-metrics.tsv",
        "role": "Model evaluation metrics",
    },
    {
        "path": "results/clinical-decision-support-readiness.tsv",
        "role": "Decision-support readiness checklist",
    },
]


def escape_markdown_cell(value) -> str:
    if pd.isna(value):
        text = ""
    else:
        text = str(value)

    text = text.replace("\n", " ").replace("\r", " ")
    text = text.replace("|", "\\|")
    return text


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Render a small DataFrame as a Markdown table without tabulate."""
    if df.empty:
        return "_No rows available._"

    if max_rows is not None:
        df = df.head(max_rows)

    columns = [str(column) for column in df.columns]
    header = "| " + " | ".join(escape_markdown_cell(column) for column in columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"

    rows = []
    for _, row in df.iterrows():
        rows.append("| " + " | ".join(escape_markdown_cell(row[column]) for column in df.columns) + " |")

    return "\n".join([header, separator, *rows])


def file_inventory() -> pd.DataFrame:
    rows = []

    for item in EXPECTED_FILES:
        path = Path(item["path"])
        exists = path.exists()

        rows.append(
            {
                "file_path": str(path),
                "role": item["role"],
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if exists else "",
            }
        )

    return pd.DataFrame(rows)


def read_text_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return f"Missing file: `{path}`"

    text = p.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return f"File exists but is empty: `{path}`"

    return text


def read_metric_tsv(path: str, max_rows: int = 20) -> str:
    p = Path(path)
    if not p.exists():
        return f"Missing file: `{path}`"

    try:
        df = pd.read_csv(p, sep="\t")
    except Exception as exc:
        return f"Could not read `{path}`: {exc}"

    if df.empty:
        return f"File exists but contains no rows: `{path}`"

    return dataframe_to_markdown(df, max_rows=max_rows)


def summarize_inventory(inventory: pd.DataFrame) -> pd.DataFrame:
    total = len(inventory)
    present = int(inventory["exists"].sum())
    missing = total - present

    return pd.DataFrame(
        [
            {"metric": "expected_files", "value": total},
            {"metric": "present_files", "value": present},
            {"metric": "missing_files", "value": missing},
            {"metric": "report_file", "value": str(REPORT_FILE)},
            {"metric": "created_at", "value": datetime.now().isoformat(timespec="seconds")},
        ]
    )


def build_report(inventory: pd.DataFrame, summary: pd.DataFrame) -> str:
    created_at = datetime.now().isoformat(timespec="seconds")

    missing_files = inventory.loc[~inventory["exists"], "file_path"].tolist()

    lines = [
        "# Reproducible Clinical Report",
        "",
        f"Generated: `{created_at}`",
        "",
        "## Report Purpose",
        "",
        "This report assembles saved outputs from the Clinical & Medical Data Systems workflow into a single reviewable artifact.",
        "",
        "It is intended for clinical data review, not direct clinical deployment.",
        "",
        "## File Inventory Summary",
        "",
        dataframe_to_markdown(summary),
        "",
        "## Evidence File Inventory",
        "",
        dataframe_to_markdown(inventory),
        "",
    ]

    if missing_files:
        lines.extend(
            [
                "## Missing Evidence Files",
                "",
                "The following expected files were not found:",
                "",
            ]
        )
        lines.extend([f"- `{path}`" for path in missing_files])
        lines.append("")

    sections = [
        (
            "Analysis-Ready Dataset Readiness",
            "results/analysis-ready-clinical-dataset-readiness-summary.txt",
            "text",
        ),
        (
            "Descriptive Clinical Analysis",
            "results/descriptive-clinical-analysis-summary.txt",
            "text",
        ),
        (
            "Risk Stratification Model Summary",
            "results/clinical-risk-model-summary.txt",
            "text",
        ),
        (
            "Clinical Model Evaluation Summary",
            "results/clinical-model-evaluation-summary.txt",
            "text",
        ),
        (
            "Clinical Interpretation and Decision-Support Summary",
            "results/clinical-interpretation-and-decision-support-summary.txt",
            "text",
        ),
        (
            "Cohort Summary Metrics",
            "results/descriptive-clinical-cohort-summary.tsv",
            "table",
        ),
        (
            "Model Evaluation Metrics",
            "results/clinical-model-evaluation-metrics.tsv",
            "table",
        ),
        (
            "Decision-Support Readiness Checklist",
            "results/clinical-decision-support-readiness.tsv",
            "table",
        ),
    ]

    for title, path, section_type in sections:
        lines.extend([f"## {title}", ""])

        if section_type == "text":
            lines.extend(["```text", read_text_file(path), "```", ""])
        else:
            lines.extend([read_metric_tsv(path), ""])

    lines.extend(
        [
            "## Interpretation Boundaries",
            "",
            "This report can support review of cohort structure, descriptive summaries, model outputs, and decision-support readiness.",
            "",
            "It does not establish causal effects, clinical utility, patient safety, regulatory compliance, or deployment approval.",
            "",
            "## Recommended Next Review Steps",
            "",
            "1. Confirm the cohort definition and denominator.",
            "2. Review missingness and variable completeness.",
            "3. Confirm the clinical outcome definition.",
            "4. Review model evaluation limitations.",
            "5. Review risk group action language.",
            "6. Complete clinical governance review before any real-world use.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    try:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        inventory = file_inventory()
        summary = summarize_inventory(inventory)
        report = build_report(inventory, summary)

        inventory.to_csv(INVENTORY_FILE, sep="\t", index=False)
        summary.to_csv(SUMMARY_FILE, sep="\t", index=False)
        REPORT_FILE.write_text(report, encoding="utf-8")

        print(f"Wrote: {REPORT_FILE}")
        print(f"Wrote: {SUMMARY_FILE}")
        print(f"Wrote: {INVENTORY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
