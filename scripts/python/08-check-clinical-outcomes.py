#!/usr/bin/env python3
"""Check synthetic clinical outcome and follow-up data for readiness.

The checks are intentionally simple and transparent so they can be reused as
teaching examples in the Clinical & Medical Data Systems guide.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path.cwd()
INPUT_PATH = PROJECT_ROOT / "data" / "example" / "clinical-outcomes.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

REQUIRED_COLUMNS = [
    "patient_id",
    "outcome_name",
    "outcome_status",
    "outcome_date",
    "index_date",
    "follow_up_end_date",
    "follow_up_days",
    "outcome_source",
    "censoring_reason",
]

VALID_STATUS = {"yes", "no", "unknown", "not_applicable"}


def check_required_columns(df: pd.DataFrame) -> dict[str, object]:
    missing = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    return {
        "check_name": "required_columns_present",
        "status": "pass" if not missing else "fail",
        "issue_count": len(missing),
        "details": ", ".join(missing) if missing else "All required columns present",
    }


def check_missing_patient_ids(df: pd.DataFrame) -> dict[str, object]:
    issue_count = int(df["patient_id"].isna().sum() + (df["patient_id"].astype(str).str.strip() == "").sum())
    return {
        "check_name": "patient_id_not_missing",
        "status": "pass" if issue_count == 0 else "fail",
        "issue_count": issue_count,
        "details": "Missing patient identifiers" if issue_count else "No missing patient identifiers",
    }


def check_status_values(df: pd.DataFrame) -> dict[str, object]:
    observed = set(df["outcome_status"].dropna().astype(str).str.strip().str.lower())
    invalid = sorted(observed - VALID_STATUS)
    return {
        "check_name": "outcome_status_values_valid",
        "status": "pass" if not invalid else "fail",
        "issue_count": len(invalid),
        "details": ", ".join(invalid) if invalid else "All outcome status values are valid",
    }


def check_date_order(df: pd.DataFrame) -> list[dict[str, object]]:
    working = df.copy()
    working["index_date_parsed"] = pd.to_datetime(working["index_date"], errors="coerce")
    working["outcome_date_parsed"] = pd.to_datetime(working["outcome_date"], errors="coerce")
    working["follow_up_end_date_parsed"] = pd.to_datetime(working["follow_up_end_date"], errors="coerce")

    outcome_before_index = int(
        (
            working["outcome_date_parsed"].notna()
            & working["index_date_parsed"].notna()
            & (working["outcome_date_parsed"] < working["index_date_parsed"])
        ).sum()
    )

    followup_before_index = int(
        (
            working["follow_up_end_date_parsed"].notna()
            & working["index_date_parsed"].notna()
            & (working["follow_up_end_date_parsed"] < working["index_date_parsed"])
        ).sum()
    )

    return [
        {
            "check_name": "outcome_date_not_before_index_date",
            "status": "pass" if outcome_before_index == 0 else "fail",
            "issue_count": outcome_before_index,
            "details": "Outcome dates are valid" if outcome_before_index == 0 else "Outcome dates before index date found",
        },
        {
            "check_name": "follow_up_end_not_before_index_date",
            "status": "pass" if followup_before_index == 0 else "fail",
            "issue_count": followup_before_index,
            "details": "Follow-up end dates are valid" if followup_before_index == 0 else "Follow-up end dates before index date found",
        },
    ]


def check_follow_up_days(df: pd.DataFrame) -> dict[str, object]:
    days = pd.to_numeric(df["follow_up_days"], errors="coerce")
    issue_count = int(days.isna().sum() + (days < 0).sum())
    return {
        "check_name": "follow_up_days_non_negative",
        "status": "pass" if issue_count == 0 else "fail",
        "issue_count": issue_count,
        "details": "Follow-up days are non-negative" if issue_count == 0 else "Missing or negative follow-up days found",
    }


def check_event_date_consistency(df: pd.DataFrame) -> dict[str, object]:
    status = df["outcome_status"].astype(str).str.strip().str.lower()
    outcome_date = df["outcome_date"].fillna("").astype(str).str.strip()
    issue_count = int(((status == "yes") & (outcome_date == "")).sum())
    return {
        "check_name": "observed_events_have_outcome_dates",
        "status": "pass" if issue_count == 0 else "fail",
        "issue_count": issue_count,
        "details": "All observed events have outcome dates" if issue_count == 0 else "Observed events without outcome dates found",
    }


def check_duplicate_patient_outcomes(df: pd.DataFrame) -> dict[str, object]:
    issue_count = int(df.duplicated(subset=["patient_id", "outcome_name"]).sum())
    return {
        "check_name": "one_row_per_patient_outcome",
        "status": "pass" if issue_count == 0 else "review",
        "issue_count": issue_count,
        "details": "No duplicate patient-outcome rows" if issue_count == 0 else "Duplicate patient-outcome rows require review",
    }


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.groupby(["outcome_name", "outcome_status"], dropna=False)
        .size()
        .reset_index(name="patient_count")
        .sort_values(["outcome_name", "outcome_status"])
    )
    return summary


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. Run scripts/python/08-create-example-clinical-outcomes.py first."
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_PATH, keep_default_na=False)

    checks: list[dict[str, object]] = [check_required_columns(df)]

    if checks[0]["status"] == "pass":
        checks.extend(
            [
                check_missing_patient_ids(df),
                check_status_values(df),
                check_follow_up_days(df),
                check_event_date_consistency(df),
                check_duplicate_patient_outcomes(df),
            ]
        )
        checks.extend(check_date_order(df))

    checks_df = pd.DataFrame(checks)
    summary_df = build_summary(df) if checks[0]["status"] == "pass" else pd.DataFrame()

    checks_path = RESULTS_DIR / "outcome-quality-checks.tsv"
    summary_path = RESULTS_DIR / "outcome-summary.tsv"
    readiness_path = RESULTS_DIR / "outcome-readiness-summary.txt"

    checks_df.to_csv(checks_path, sep="\t", index=False)
    summary_df.to_csv(summary_path, sep="\t", index=False)

    failed = checks_df[checks_df["status"] == "fail"]
    review = checks_df[checks_df["status"] == "review"]

    with readiness_path.open("w", encoding="utf-8") as handle:
        handle.write("Clinical outcome and follow-up readiness summary\n")
        handle.write("================================================\n\n")
        handle.write(f"Input file: {INPUT_PATH}\n")
        handle.write(f"Rows checked: {len(df)}\n")
        handle.write(f"Checks run: {len(checks_df)}\n")
        handle.write(f"Failed checks: {len(failed)}\n")
        handle.write(f"Review checks: {len(review)}\n\n")
        if len(failed) == 0:
            handle.write("Status: READY FOR BASIC OUTCOME SUMMARY\n")
        else:
            handle.write("Status: NOT READY - resolve failed checks before analysis\n")

    print(f"Wrote {checks_path}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {readiness_path}")


if __name__ == "__main__":
    main()
