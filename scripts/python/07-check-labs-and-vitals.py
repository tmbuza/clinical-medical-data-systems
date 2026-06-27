#!/usr/bin/env python3
"""Check synthetic laboratory and vital sign result readiness for Chapter 07."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

INPUT_FILE = Path("data/example/clinical-results-combined.csv")
RESULTS_DIR = Path("results")

REQUIRED_COLUMNS = [
    "patient_id",
    "encounter_id",
    "measurement_datetime",
    "result_domain",
    "result_name",
    "result_value",
    "result_unit",
]

EXPECTED_UNITS = {
    "creatinine": {"mg/dL"},
    "hemoglobin": {"g/dL"},
    "glucose": {"mg/dL"},
    "potassium": {"mmol/L"},
    "systolic_bp": {"mmHg"},
    "diastolic_bp": {"mmHg"},
    "heart_rate": {"beats/min"},
    "oxygen_saturation": {"%", "percent"},
}

PLAUSIBILITY_RANGES = {
    "creatinine": (0.1, 20),
    "hemoglobin": (2, 25),
    "glucose": (20, 1000),
    "potassium": (1, 10),
    "systolic_bp": (50, 300),
    "diastolic_bp": (20, 180),
    "heart_rate": (20, 250),
    "oxygen_saturation": (50, 100),
}


def check(condition: bool, check_name: str, details: str) -> dict[str, str]:
    return {
        "check_name": check_name,
        "status": "PASS" if condition else "REVIEW",
        "details": details,
    }


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Run scripts/python/07-create-example-labs-and-vitals.py first."
        )

    df = pd.read_csv(INPUT_FILE)
    checks: list[dict[str, str]] = []

    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(df.columns))
    checks.append(
        check(
            not missing_columns,
            "required_columns_present",
            "Missing columns: " + ", ".join(missing_columns) if missing_columns else "All required columns present.",
        )
    )

    if missing_columns:
        pd.DataFrame(checks).to_csv(RESULTS_DIR / "clinical-result-quality-checks.tsv", sep="\t", index=False)
        raise SystemExit("Required columns are missing; stopping readiness checks.")

    checks.append(
        check(
            df["patient_id"].notna().all() and (df["patient_id"].astype(str).str.len() > 0).all(),
            "patient_ids_populated",
            "Patient identifiers are populated." if df["patient_id"].notna().all() else "Some patient identifiers are missing.",
        )
    )

    checks.append(
        check(
            df["encounter_id"].notna().all() and (df["encounter_id"].astype(str).str.len() > 0).all(),
            "encounter_ids_populated",
            "Encounter identifiers are populated." if df["encounter_id"].notna().all() else "Some encounter identifiers are missing.",
        )
    )

    parsed_datetimes = pd.to_datetime(df["measurement_datetime"], errors="coerce")
    checks.append(
        check(
            parsed_datetimes.notna().all(),
            "measurement_datetimes_parseable",
            f"Parseable datetimes: {int(parsed_datetimes.notna().sum())} of {len(df)}.",
        )
    )

    numeric_values = pd.to_numeric(df["result_value"], errors="coerce")
    checks.append(
        check(
            numeric_values.notna().all(),
            "numeric_result_values",
            f"Numeric result values: {int(numeric_values.notna().sum())} of {len(df)}.",
        )
    )

    checks.append(
        check(
            df["result_unit"].notna().all() and (df["result_unit"].astype(str).str.len() > 0).all(),
            "result_units_populated",
            "Result units are populated." if df["result_unit"].notna().all() else "Some result units are missing.",
        )
    )

    unit_mismatches = []
    plausibility_flags = []

    for row in df.assign(result_value_numeric=numeric_values).itertuples(index=False):
        expected = EXPECTED_UNITS.get(row.result_name)
        if expected and row.result_unit not in expected:
            unit_mismatches.append(f"{row.result_name}: {row.result_unit}")

        bounds = PLAUSIBILITY_RANGES.get(row.result_name)
        if bounds and pd.notna(row.result_value_numeric):
            low, high = bounds
            if row.result_value_numeric < low or row.result_value_numeric > high:
                plausibility_flags.append(
                    f"{row.patient_id}/{row.encounter_id}/{row.result_name}={row.result_value_numeric}"
                )

    checks.append(
        check(
            not unit_mismatches,
            "expected_units",
            "All checked units match expected units."
            if not unit_mismatches
            else "Unexpected units: " + "; ".join(unit_mismatches),
        )
    )

    checks.append(
        check(
            not plausibility_flags,
            "broad_plausibility_ranges",
            "No broad plausibility flags found."
            if not plausibility_flags
            else "Values needing review: " + "; ".join(plausibility_flags),
        )
    )

    domain_summary = (
        df.groupby(["result_domain", "result_name", "result_unit"], dropna=False)
        .size()
        .reset_index(name="row_count")
        .sort_values(["result_domain", "result_name"])
    )

    pd.DataFrame(checks).to_csv(RESULTS_DIR / "clinical-result-quality-checks.tsv", sep="\t", index=False)
    domain_summary.to_csv(RESULTS_DIR / "clinical-result-domain-summary.tsv", sep="\t", index=False)

    passed = sum(item["status"] == "PASS" for item in checks)
    summary = [
        "Clinical result readiness summary",
        "=================================",
        f"Input file: {INPUT_FILE}",
        f"Rows checked: {len(df)}",
        f"Checks passed: {passed} of {len(checks)}",
        "",
        "Review any rows marked REVIEW in results/clinical-result-quality-checks.tsv.",
    ]
    (RESULTS_DIR / "clinical-result-readiness-summary.txt").write_text("\n".join(summary) + "\n")

    print("Clinical result readiness checks complete.")
    print(f"- {RESULTS_DIR / 'clinical-result-quality-checks.tsv'}")
    print(f"- {RESULTS_DIR / 'clinical-result-domain-summary.tsv'}")
    print(f"- {RESULTS_DIR / 'clinical-result-readiness-summary.txt'}")


if __name__ == "__main__":
    main()
