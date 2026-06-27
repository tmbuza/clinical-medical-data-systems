#!/usr/bin/env python3
"""
Run structural quality checks for coded clinical event data.

Run from the project root:
    python scripts/python/06-check-coded-clinical-events.py
"""

from pathlib import Path
import pandas as pd

INPUT_FILE = Path("data/example/coded-clinical-events.csv")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED_COLUMNS = [
    "patient_id",
    "encounter_id",
    "event_domain",
    "code_system",
    "code",
    "code_description",
    "event_date",
    "source_table",
]

EXPECTED_DOMAINS = {"diagnosis", "procedure", "medication"}


def check_pass(name: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "check": name,
        "status": "PASS" if passed else "REVIEW",
        "detail": detail,
    }


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file: {INPUT_FILE}. Run 06-create-example-coded-clinical-events.py first."
        )

    df = pd.read_csv(INPUT_FILE, dtype=str)

    checks: list[dict[str, str]] = []

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    checks.append(
        check_pass(
            "required_columns_present",
            not missing_columns,
            "All required columns present" if not missing_columns else f"Missing: {missing_columns}",
        )
    )

    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            missing_count = int(df[col].isna().sum() + (df[col].astype(str).str.strip() == "").sum())
            checks.append(
                check_pass(
                    f"missing_{col}",
                    missing_count == 0,
                    f"Missing or blank values: {missing_count}",
                )
            )

    if "event_domain" in df.columns:
        observed_domains = set(df["event_domain"].dropna().unique())
        unexpected_domains = sorted(observed_domains - EXPECTED_DOMAINS)
        missing_domains = sorted(EXPECTED_DOMAINS - observed_domains)
        checks.append(
            check_pass(
                "expected_event_domains",
                not unexpected_domains and not missing_domains,
                f"Observed: {sorted(observed_domains)}; unexpected: {unexpected_domains}; missing: {missing_domains}",
            )
        )

    if "event_date" in df.columns:
        parsed_dates = pd.to_datetime(df["event_date"], errors="coerce")
        invalid_dates = int(parsed_dates.isna().sum())
        checks.append(
            check_pass(
                "valid_event_dates",
                invalid_dates == 0,
                f"Invalid dates: {invalid_dates}",
            )
        )

    duplicate_cols = ["patient_id", "encounter_id", "event_domain", "code_system", "code", "event_date"]
    if all(col in df.columns for col in duplicate_cols):
        duplicate_count = int(df.duplicated(subset=duplicate_cols).sum())
        checks.append(
            check_pass(
                "duplicate_patient_event_code_dates",
                duplicate_count == 0,
                f"Duplicate rows by patient/encounter/domain/code/date: {duplicate_count}",
            )
        )

    checks_df = pd.DataFrame(checks)
    checks_df.to_csv(RESULTS_DIR / "coded-event-quality-checks.tsv", sep="\t", index=False)

    domain_summary = (
        df.groupby(["event_domain", "code_system"], dropna=False)
        .agg(
            event_count=("code", "size"),
            patient_count=("patient_id", "nunique"),
            encounter_count=("encounter_id", "nunique"),
        )
        .reset_index()
        .sort_values(["event_domain", "code_system"])
    )
    domain_summary.to_csv(RESULTS_DIR / "coded-event-domain-summary.tsv", sep="\t", index=False)

    review_count = int((checks_df["status"] == "REVIEW").sum())
    readiness = "READY_FOR_REVIEW" if review_count == 0 else "NEEDS_ATTENTION"

    summary_text = [
        "Coded Clinical Event Readiness Summary",
        "======================================",
        f"Input file: {INPUT_FILE}",
        f"Rows: {len(df)}",
        f"Columns: {len(df.columns)}",
        f"Quality checks requiring review: {review_count}",
        f"Readiness status: {readiness}",
        "",
        "Generated outputs:",
        "- results/coded-event-quality-checks.tsv",
        "- results/coded-event-domain-summary.tsv",
        "- results/coded-event-readiness-summary.txt",
    ]

    (RESULTS_DIR / "coded-event-readiness-summary.txt").write_text("\n".join(summary_text) + "\n")

    print("Coded clinical event checks complete.")
    print(f"Readiness status: {readiness}")
    print("Outputs written to results/.")


if __name__ == "__main__":
    main()
