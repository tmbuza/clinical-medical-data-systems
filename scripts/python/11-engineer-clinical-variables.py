#!/usr/bin/env python3
"""Engineer patient-level clinical variables from example clinical input files.

Run from the project root:
    python scripts/python/11-engineer-clinical-variables.py

Inputs are expected in data/example/.
Outputs are written to results/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd


PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data" / "example"
RESULTS_DIR = PROJECT_ROOT / "results"

INPUT_FILES = {
    "demographics": "patient-demographics.csv",
    "encounters": "clinical-encounters.csv",
    "diagnoses": "diagnoses.csv",
    "procedures": "procedures.csv",
    "medications": "medications.csv",
    "labs": "laboratory-results.csv",
    "vitals": "vital-sign-results.csv",
    "outcomes": "clinical-outcomes.csv",
}

DATE_CANDIDATES = {
    "demographics": ["date_of_birth", "birth_date", "dob"],
    "encounters": ["encounter_date", "admission_date", "visit_date", "start_date"],
    "diagnoses": ["diagnosis_date", "event_date", "recorded_date"],
    "procedures": ["procedure_date", "event_date", "recorded_date"],
    "medications": ["medication_start_date", "start_date", "order_date", "event_date"],
    "labs": ["result_date", "collection_date", "lab_date", "event_date"],
    "vitals": ["result_date", "measurement_date", "vital_date", "event_date"],
    "outcomes": ["outcome_date", "event_date", "follow_up_date"],
}

PATIENT_ID_CANDIDATES = ["patient_id", "person_id", "subject_id", "mrn"]


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def read_table(name: str, filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def find_column(columns: Iterable[str], candidates: list[str]) -> str | None:
    lookup = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate in lookup:
            return lookup[candidate]
    return None


def patient_id_column(frame: pd.DataFrame) -> str | None:
    return find_column(frame.columns, PATIENT_ID_CANDIDATES)


def date_column(frame: pd.DataFrame, domain: str) -> str | None:
    return find_column(frame.columns, DATE_CANDIDATES.get(domain, []))


def parse_date_column(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None or frame.empty:
        return pd.Series(pd.NaT, index=frame.index)
    return pd.to_datetime(frame[column], errors="coerce")


def coerce_datetime_series(series: pd.Series | object, index: pd.Index | None = None) -> pd.Series:
    """Return a datetime Series even when input contains blanks, floats, or mixed objects."""
    if isinstance(series, pd.Series):
        return pd.to_datetime(series, errors="coerce")
    return pd.Series(pd.to_datetime(series, errors="coerce"), index=index)


def coerce_datetime_value(value: object) -> pd.Timestamp | pd.NaT:
    """Safely coerce one scalar value to a pandas Timestamp or NaT.

    This is intentionally scalar-level because some clinical example files can
    produce object columns containing both pandas Timestamps and float missing
    values after groupby/merge operations. Vectorized subtraction may then try
    to evaluate Timestamp - float before dtype coercion fully settles.
    """
    if pd.isna(value):
        return pd.NaT
    return pd.to_datetime(value, errors="coerce")


def days_between(later: pd.Series, earlier: pd.Series) -> pd.Series:
    """Safely calculate day differences without ever subtracting raw mixed objects."""
    later_values = later.tolist() if isinstance(later, pd.Series) else list(later)
    earlier_values = earlier.tolist() if isinstance(earlier, pd.Series) else list(earlier)
    index = later.index if isinstance(later, pd.Series) else None

    differences: list[float | pd.NA] = []
    for later_value, earlier_value in zip(later_values, earlier_values):
        later_dt = coerce_datetime_value(later_value)
        earlier_dt = coerce_datetime_value(earlier_value)
        if pd.isna(later_dt) or pd.isna(earlier_dt):
            differences.append(pd.NA)
        else:
            differences.append((later_dt - earlier_dt).days)

    return pd.Series(differences, index=index, dtype="Float64")


def first_non_null(series: pd.Series) -> object:
    clean = series.dropna()
    return clean.iloc[0] if len(clean) else pd.NA


def build_patient_spine(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    patient_ids: set[str] = set()
    for frame in tables.values():
        if frame.empty:
            continue
        pid_col = patient_id_column(frame)
        if pid_col is not None:
            patient_ids.update(frame[pid_col].dropna().astype(str).tolist())

    return pd.DataFrame({"patient_id": sorted(patient_ids)})


def derive_demographics(demographics: pd.DataFrame) -> pd.DataFrame:
    columns = ["patient_id", "date_of_birth", "gender", "race_ethnicity", "insurance_type"]
    if demographics.empty:
        return pd.DataFrame(columns=columns)

    pid_col = patient_id_column(demographics)
    if pid_col is None:
        return pd.DataFrame(columns=columns)

    dob_col = find_column(demographics.columns, DATE_CANDIDATES["demographics"])
    gender_col = find_column(demographics.columns, ["gender", "sex"])
    race_col = find_column(demographics.columns, ["race_ethnicity", "race", "ethnicity"])
    insurance_col = find_column(demographics.columns, ["insurance_type", "insurance", "payer"])

    output = pd.DataFrame({"patient_id": demographics[pid_col].astype(str)})
    output["date_of_birth"] = parse_date_column(demographics, dob_col)
    output["gender"] = demographics[gender_col] if gender_col else pd.NA
    output["race_ethnicity"] = demographics[race_col] if race_col else pd.NA
    output["insurance_type"] = demographics[insurance_col] if insurance_col else pd.NA

    return output.groupby("patient_id", as_index=False).agg(first_non_null)


def derive_encounters(encounters: pd.DataFrame) -> pd.DataFrame:
    if encounters.empty:
        return pd.DataFrame(
            columns=[
                "patient_id",
                "index_encounter_date",
                "last_encounter_date",
                "encounter_count",
                "inpatient_encounter_count",
                "outpatient_encounter_count",
                "emergency_encounter_count",
                "follow_up_days",
            ]
        )

    pid_col = patient_id_column(encounters)
    enc_date_col = date_column(encounters, "encounters")
    if pid_col is None or enc_date_col is None:
        return pd.DataFrame(columns=["patient_id"])

    temp = encounters.copy()
    temp["patient_id"] = temp[pid_col].astype(str)
    temp["encounter_date_parsed"] = parse_date_column(temp, enc_date_col)

    type_col = find_column(temp.columns, ["encounter_type", "visit_type", "care_setting"])
    if type_col is None:
        temp["encounter_type_normalized"] = "unknown"
    else:
        temp["encounter_type_normalized"] = temp[type_col].astype(str).str.lower()

    summary = (
        temp.groupby("patient_id", as_index=False)
        .agg(
            index_encounter_date=("encounter_date_parsed", "min"),
            last_encounter_date=("encounter_date_parsed", "max"),
            encounter_count=("encounter_date_parsed", "count"),
        )
    )

    for setting, label in [
        ("inpatient", "inpatient_encounter_count"),
        ("outpatient", "outpatient_encounter_count"),
        ("emergency", "emergency_encounter_count"),
    ]:
        setting_counts = (
            temp.loc[temp["encounter_type_normalized"].str.contains(setting, na=False)]
            .groupby("patient_id")
            .size()
            .rename(label)
            .reset_index()
        )
        summary = summary.merge(setting_counts, on="patient_id", how="left")

    count_cols = [
        "inpatient_encounter_count",
        "outpatient_encounter_count",
        "emergency_encounter_count",
    ]
    for column in count_cols:
        if column not in summary.columns:
            summary[column] = 0
        summary[column] = summary[column].fillna(0).astype(int)

    summary["last_encounter_date"] = coerce_datetime_series(summary["last_encounter_date"])
    summary["index_encounter_date"] = coerce_datetime_series(summary["index_encounter_date"])
    summary["follow_up_days"] = days_between(
        summary["last_encounter_date"], summary["index_encounter_date"]
    ).fillna(0).astype(int)

    return summary


def derive_age(demographic_summary: pd.DataFrame, encounter_summary: pd.DataFrame) -> pd.DataFrame:
    if demographic_summary.empty:
        return demographic_summary
    output = demographic_summary.merge(
        encounter_summary[["patient_id", "index_encounter_date"]]
        if "index_encounter_date" in encounter_summary.columns
        else pd.DataFrame(columns=["patient_id", "index_encounter_date"]),
        on="patient_id",
        how="left",
    )
    output["date_of_birth"] = coerce_datetime_series(output["date_of_birth"])
    output["index_encounter_date"] = coerce_datetime_series(output["index_encounter_date"])
    output["age_at_index"] = (
        days_between(output["index_encounter_date"], output["date_of_birth"]) / 365.25
    ).round(1)

    output.loc[(output["age_at_index"] < 0) | (output["age_at_index"] > 120), "age_at_index"] = pd.NA
    output["age_group"] = pd.cut(
        output["age_at_index"],
        bins=[0, 17, 39, 64, 120],
        labels=["0-17", "18-39", "40-64", "65+"],
        include_lowest=True,
    ).astype("string")
    return output.drop(columns=["index_encounter_date"])


def derive_diagnosis_indicators(diagnoses: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "patient_id",
        "diagnosis_record_count",
        "has_diabetes",
        "has_hypertension",
        "has_chronic_kidney_disease",
        "condition_indicator_count",
    ]
    if diagnoses.empty:
        return pd.DataFrame(columns=columns)

    pid_col = patient_id_column(diagnoses)
    if pid_col is None:
        return pd.DataFrame(columns=columns)

    temp = diagnoses.copy()
    temp["patient_id"] = temp[pid_col].astype(str)
    text_columns = [
        col
        for col in temp.columns
        if any(key in col.lower() for key in ["code", "diagnosis", "condition", "description", "name"])
    ]
    if text_columns:
        temp["diagnosis_text"] = temp[text_columns].astype(str).agg(" ".join, axis=1).str.lower()
    else:
        temp["diagnosis_text"] = ""

    temp["has_diabetes_row"] = temp["diagnosis_text"].str.contains("diabetes|e11|e10", regex=True, na=False)
    temp["has_hypertension_row"] = temp["diagnosis_text"].str.contains("hypertension|high blood pressure|i10", regex=True, na=False)
    temp["has_ckd_row"] = temp["diagnosis_text"].str.contains("chronic kidney|ckd|n18", regex=True, na=False)

    summary = (
        temp.groupby("patient_id", as_index=False)
        .agg(
            diagnosis_record_count=("diagnosis_text", "count"),
            has_diabetes=("has_diabetes_row", "max"),
            has_hypertension=("has_hypertension_row", "max"),
            has_chronic_kidney_disease=("has_ckd_row", "max"),
        )
    )
    boolean_cols = ["has_diabetes", "has_hypertension", "has_chronic_kidney_disease"]
    for column in boolean_cols:
        summary[column] = summary[column].astype(bool).astype(int)
    summary["condition_indicator_count"] = summary[boolean_cols].sum(axis=1)
    return summary


def derive_medication_summary(medications: pd.DataFrame) -> pd.DataFrame:
    columns = ["patient_id", "medication_record_count", "medication_class_count"]
    if medications.empty:
        return pd.DataFrame(columns=columns)

    pid_col = patient_id_column(medications)
    if pid_col is None:
        return pd.DataFrame(columns=columns)

    class_col = find_column(medications.columns, ["medication_class", "drug_class", "therapeutic_class"])
    temp = medications.copy()
    temp["patient_id"] = temp[pid_col].astype(str)
    if class_col is None:
        temp["medication_class_engineered"] = pd.NA
    else:
        temp["medication_class_engineered"] = temp[class_col]

    return (
        temp.groupby("patient_id", as_index=False)
        .agg(
            medication_record_count=("patient_id", "size"),
            medication_class_count=("medication_class_engineered", pd.Series.nunique),
        )
    )


def derive_baseline_results(results: pd.DataFrame, domain: str, index_dates: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame(columns=["patient_id"])

    pid_col = patient_id_column(results)
    result_date_col = date_column(results, domain)
    value_col = find_column(results.columns, ["result_value", "value", "numeric_value", "measurement_value"])
    name_col = find_column(results.columns, ["test_name", "result_name", "measurement_name", "vital_sign", "loinc_name"])

    if pid_col is None or value_col is None or name_col is None:
        return pd.DataFrame(columns=["patient_id"])

    temp = results.copy()
    temp["patient_id"] = temp[pid_col].astype(str)
    temp["result_date_parsed"] = parse_date_column(temp, result_date_col)
    temp["result_value_numeric"] = pd.to_numeric(temp[value_col], errors="coerce")
    temp["result_name_normalized"] = temp[name_col].astype(str).str.lower()
    temp = temp.merge(index_dates, on="patient_id", how="left")

    if "index_encounter_date" in temp.columns:
        temp["index_encounter_date"] = coerce_datetime_series(temp["index_encounter_date"])
        temp = temp.loc[
            temp["index_encounter_date"].isna()
            | temp["result_date_parsed"].isna()
            | (temp["result_date_parsed"] <= temp["index_encounter_date"])
        ].copy()

    mappings = {
        "labs": {
            "baseline_creatinine": "creatinine",
            "baseline_glucose": "glucose",
            "baseline_hemoglobin": "hemoglobin",
        },
        "vitals": {
            "baseline_systolic_bp": "systolic",
            "baseline_diastolic_bp": "diastolic",
            "baseline_bmi": "bmi|body mass index",
        },
    }

    output = pd.DataFrame({"patient_id": sorted(temp["patient_id"].dropna().unique())})
    for variable, pattern in mappings.get(domain, {}).items():
        selected = temp.loc[temp["result_name_normalized"].str.contains(pattern, regex=True, na=False)].copy()
        if selected.empty:
            output[variable] = pd.NA
            continue
        selected = selected.sort_values(["patient_id", "result_date_parsed"])
        latest = selected.groupby("patient_id", as_index=False).tail(1)[["patient_id", "result_value_numeric"]]
        latest = latest.rename(columns={"result_value_numeric": variable})
        output = output.merge(latest, on="patient_id", how="left")

    count_name = "baseline_lab_result_count" if domain == "labs" else "baseline_vital_result_count"
    counts = temp.groupby("patient_id").size().rename(count_name).reset_index()
    output = output.merge(counts, on="patient_id", how="left")
    return output


def derive_outcomes(outcomes: pd.DataFrame, index_dates: pd.DataFrame) -> pd.DataFrame:
    columns = ["patient_id", "outcome_observed", "outcome_type", "outcome_date", "days_to_outcome"]
    if outcomes.empty:
        return pd.DataFrame(columns=columns)

    pid_col = patient_id_column(outcomes)
    outcome_date_col = date_column(outcomes, "outcomes")
    type_col = find_column(outcomes.columns, ["outcome_type", "outcome", "event_type"])
    observed_col = find_column(outcomes.columns, ["outcome_observed", "observed", "event_observed"])
    if pid_col is None:
        return pd.DataFrame(columns=columns)

    temp = outcomes.copy()
    temp["patient_id"] = temp[pid_col].astype(str)
    temp["outcome_date"] = parse_date_column(temp, outcome_date_col)
    temp["outcome_type"] = temp[type_col] if type_col else pd.NA
    if observed_col:
        temp["outcome_observed"] = temp[observed_col].fillna(0).astype(int)
    else:
        temp["outcome_observed"] = temp["outcome_date"].notna().astype(int)

    temp = temp.merge(index_dates, on="patient_id", how="left")
    if "index_encounter_date" not in temp.columns:
        temp["index_encounter_date"] = pd.NaT
    temp["index_encounter_date"] = coerce_datetime_series(temp["index_encounter_date"])
    temp["outcome_date"] = coerce_datetime_series(temp["outcome_date"])
    temp["days_to_outcome"] = days_between(temp["outcome_date"], temp["index_encounter_date"])

    return (
        temp.sort_values(["patient_id", "outcome_date"])
        .groupby("patient_id", as_index=False)
        .agg(
            outcome_observed=("outcome_observed", "max"),
            outcome_type=("outcome_type", first_non_null),
            outcome_date=("outcome_date", first_non_null),
            days_to_outcome=("days_to_outcome", first_non_null),
        )
    )


def build_variable_dictionary() -> pd.DataFrame:
    rows = [
        ("patient_id", "Patient identifier", "all_domains", "Retained linkage identifier", "Unique patient key used to join clinical domains", "identifier"),
        ("index_encounter_date", "Index encounter date", "encounters", "Earliest observed encounter date", "Baseline time point for derived variables", "cohort_context"),
        ("age_at_index", "Age at index", "demographics + encounters", "Difference between index encounter date and date of birth", "Patient age at baseline", "predictor"),
        ("age_group", "Age group", "demographics + encounters", "Grouped age_at_index into 0-17, 18-39, 40-64, and 65+", "Age category for stratified summaries", "stratification_variable"),
        ("gender", "Gender", "demographics", "First non-missing demographic value", "Recorded gender or sex field depending on source", "predictor"),
        ("race_ethnicity", "Race or ethnicity", "demographics", "First non-missing demographic value", "Socially constructed demographic context; interpret carefully", "predictor"),
        ("insurance_type", "Insurance type", "demographics", "First non-missing payer or insurance value", "Healthcare access and payer context", "predictor"),
        ("encounter_count", "Encounter count", "encounters", "Number of dated encounter records", "Care contact intensity", "predictor"),
        ("follow_up_days", "Follow-up days", "encounters", "Days between first and last observed encounter", "Observed care-system follow-up duration", "quality_check_variable"),
        ("has_diabetes", "Diabetes indicator", "diagnoses", "Diagnosis text or code contains diabetes, E10, or E11", "Diagnosis-code evidence of diabetes", "predictor"),
        ("has_hypertension", "Hypertension indicator", "diagnoses", "Diagnosis text or code contains hypertension, high blood pressure, or I10", "Diagnosis-code evidence of hypertension", "predictor"),
        ("has_chronic_kidney_disease", "Chronic kidney disease indicator", "diagnoses", "Diagnosis text or code contains chronic kidney, CKD, or N18", "Diagnosis-code evidence of chronic kidney disease", "predictor"),
        ("condition_indicator_count", "Condition indicator count", "diagnoses", "Sum of engineered condition indicators", "Simple comorbidity signal from available diagnosis indicators", "predictor"),
        ("medication_record_count", "Medication record count", "medications", "Number of medication records", "Medication documentation intensity", "predictor"),
        ("medication_class_count", "Medication class count", "medications", "Number of unique medication classes", "Therapeutic exposure diversity", "predictor"),
        ("baseline_creatinine", "Baseline creatinine", "laboratory_results", "Latest creatinine value on or before index date", "Kidney function marker at baseline", "predictor"),
        ("baseline_glucose", "Baseline glucose", "laboratory_results", "Latest glucose value on or before index date", "Glycemic state marker at baseline", "predictor"),
        ("baseline_hemoglobin", "Baseline hemoglobin", "laboratory_results", "Latest hemoglobin value on or before index date", "Anemia or blood status marker at baseline", "predictor"),
        ("baseline_systolic_bp", "Baseline systolic blood pressure", "vital_signs", "Latest systolic blood pressure on or before index date", "Blood pressure status at baseline", "predictor"),
        ("baseline_diastolic_bp", "Baseline diastolic blood pressure", "vital_signs", "Latest diastolic blood pressure on or before index date", "Blood pressure status at baseline", "predictor"),
        ("baseline_bmi", "Baseline BMI", "vital_signs", "Latest BMI on or before index date", "Body size marker at baseline", "predictor"),
        ("outcome_observed", "Outcome observed", "outcomes", "Any observed outcome record for the patient", "Primary outcome availability flag", "outcome"),
        ("outcome_type", "Outcome type", "outcomes", "First non-missing outcome type", "Clinical outcome category", "outcome"),
        ("days_to_outcome", "Days to outcome", "outcomes + encounters", "Outcome date minus index encounter date", "Time from baseline to outcome", "outcome"),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "variable_name",
            "variable_label",
            "source_domain",
            "derivation_rule",
            "clinical_interpretation",
            "analysis_role",
        ],
    )


def write_summary(dataset: pd.DataFrame, dictionary: pd.DataFrame, loaded_tables: dict[str, pd.DataFrame]) -> None:
    missing_by_variable = dataset.isna().mean().sort_values(ascending=False).head(10)
    with (RESULTS_DIR / "clinical-variable-engineering-summary.txt").open("w", encoding="utf-8") as handle:
        handle.write("Clinical variable engineering summary\n")
        handle.write("=====================================\n\n")
        handle.write(f"Input domains checked: {len(INPUT_FILES)}\n")
        handle.write(f"Input domains available: {sum(not frame.empty for frame in loaded_tables.values())}\n")
        handle.write(f"Patients in engineered dataset: {len(dataset)}\n")
        handle.write(f"Engineered variables: {dataset.shape[1]}\n")
        handle.write(f"Dictionary rows: {len(dictionary)}\n\n")
        handle.write("Highest missingness among engineered variables:\n")
        for variable, fraction in missing_by_variable.items():
            handle.write(f"- {variable}: {round(float(fraction) * 100, 2)}% missing\n")
        handle.write("\nInterpretation note:\n")
        handle.write("Engineered variables are example definitions for teaching. Review and adapt definitions before using them in a real clinical study.\n")


def main() -> None:
    ensure_dirs()
    tables = {name: read_table(name, filename) for name, filename in INPUT_FILES.items()}

    patient_spine = build_patient_spine(tables)
    if patient_spine.empty:
        raise SystemExit(
            "No patient identifiers found. Run the Part II example data scripts before this workflow."
        )

    encounters = derive_encounters(tables["encounters"])
    index_dates = encounters[["patient_id", "index_encounter_date"]].copy() if "index_encounter_date" in encounters.columns else pd.DataFrame(columns=["patient_id", "index_encounter_date"])
    if "index_encounter_date" in index_dates.columns:
        index_dates["index_encounter_date"] = coerce_datetime_series(index_dates["index_encounter_date"])

    demographics = derive_demographics(tables["demographics"])
    demographics = derive_age(demographics, encounters)
    diagnoses = derive_diagnosis_indicators(tables["diagnoses"])
    medications = derive_medication_summary(tables["medications"])
    labs = derive_baseline_results(tables["labs"], "labs", index_dates)
    vitals = derive_baseline_results(tables["vitals"], "vitals", index_dates)
    outcomes = derive_outcomes(tables["outcomes"], index_dates)

    derived = patient_spine.copy()
    for frame in [demographics, encounters, diagnoses, medications, labs, vitals, outcomes]:
        if not frame.empty and "patient_id" in frame.columns:
            derived = derived.merge(frame, on="patient_id", how="left")

    fill_zero_columns = [
        "encounter_count",
        "inpatient_encounter_count",
        "outpatient_encounter_count",
        "emergency_encounter_count",
        "diagnosis_record_count",
        "has_diabetes",
        "has_hypertension",
        "has_chronic_kidney_disease",
        "condition_indicator_count",
        "medication_record_count",
        "medication_class_count",
        "baseline_lab_result_count",
        "baseline_vital_result_count",
        "outcome_observed",
    ]
    for column in fill_zero_columns:
        if column in derived.columns:
            derived[column] = derived[column].fillna(0).astype(int)

    dictionary = build_variable_dictionary()

    derived.to_csv(RESULTS_DIR / "patient-level-derived-variables.tsv", sep="\t", index=False)
    dictionary.to_csv(RESULTS_DIR / "clinical-variable-dictionary.tsv", sep="\t", index=False)
    write_summary(derived, dictionary, tables)

    print("Wrote results/patient-level-derived-variables.tsv")
    print("Wrote results/clinical-variable-dictionary.tsv")
    print("Wrote results/clinical-variable-engineering-summary.txt")


if __name__ == "__main__":
    main()
