#!/usr/bin/env python3
"""Create synthetic clinical outcome and follow-up data for Chapter 08.

This script writes a small example outcome table that can be used to test
clinical outcome readiness checks. The data are synthetic and intended only
for teaching and workflow demonstration.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path.cwd()
EXAMPLE_DIR = PROJECT_ROOT / "data" / "example"


def build_outcomes() -> pd.DataFrame:
    """Return a small synthetic clinical outcomes table."""
    rows = [
        {
            "patient_id": "P001",
            "outcome_name": "30_day_readmission",
            "outcome_status": "yes",
            "outcome_date": "2026-02-02",
            "index_date": "2026-01-10",
            "follow_up_end_date": "2026-02-09",
            "follow_up_days": 30,
            "outcome_source": "encounter_data",
            "censoring_reason": "event_observed",
        },
        {
            "patient_id": "P002",
            "outcome_name": "30_day_readmission",
            "outcome_status": "no",
            "outcome_date": "",
            "index_date": "2026-01-12",
            "follow_up_end_date": "2026-02-11",
            "follow_up_days": 30,
            "outcome_source": "encounter_data",
            "censoring_reason": "window_complete",
        },
        {
            "patient_id": "P003",
            "outcome_name": "30_day_readmission",
            "outcome_status": "unknown",
            "outcome_date": "",
            "index_date": "2026-01-18",
            "follow_up_end_date": "2026-01-25",
            "follow_up_days": 7,
            "outcome_source": "encounter_data",
            "censoring_reason": "lost_to_follow_up",
        },
        {
            "patient_id": "P004",
            "outcome_name": "30_day_mortality",
            "outcome_status": "yes",
            "outcome_date": "2026-02-05",
            "index_date": "2026-01-20",
            "follow_up_end_date": "2026-02-05",
            "follow_up_days": 16,
            "outcome_source": "mortality_registry",
            "censoring_reason": "event_observed",
        },
        {
            "patient_id": "P005",
            "outcome_name": "30_day_mortality",
            "outcome_status": "no",
            "outcome_date": "",
            "index_date": "2026-01-22",
            "follow_up_end_date": "2026-02-21",
            "follow_up_days": 30,
            "outcome_source": "mortality_registry",
            "censoring_reason": "window_complete",
        },
        {
            "patient_id": "P006",
            "outcome_name": "aki_during_admission",
            "outcome_status": "no",
            "outcome_date": "",
            "index_date": "2026-01-24",
            "follow_up_end_date": "2026-01-29",
            "follow_up_days": 5,
            "outcome_source": "laboratory_results",
            "censoring_reason": "discharged",
        },
    ]
    return pd.DataFrame(rows)


def main() -> None:
    EXAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EXAMPLE_DIR / "clinical-outcomes.csv"

    outcomes = build_outcomes()
    outcomes.to_csv(output_path, index=False)

    print(f"Wrote {len(outcomes)} rows to {output_path}")


if __name__ == "__main__":
    main()
