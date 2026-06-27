#!/usr/bin/env python3
"""
Build EHR/FHIR interoperability roadmap artifacts.

Outputs:
  results/interoperability/fhir-resource-mapping.tsv
  results/interoperability/interoperability-readiness-checklist.tsv
  results/interoperability/example-fhir-patient-bundle.json
  results/interoperability/interoperability-roadmap-summary.txt
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys

import pandas as pd


DATA_DIR = Path("data/example")
RESULTS_DIR = Path("results")
INTEROP_DIR = RESULTS_DIR / "interoperability"

MAPPING_FILE = INTEROP_DIR / "fhir-resource-mapping.tsv"
CHECKLIST_FILE = INTEROP_DIR / "interoperability-readiness-checklist.tsv"
BUNDLE_FILE = INTEROP_DIR / "example-fhir-patient-bundle.json"
SUMMARY_FILE = INTEROP_DIR / "interoperability-roadmap-summary.txt"


EXPECTED_INPUTS = [
    ("patient-demographics.csv", "Patient"),
    ("clinical-encounters.csv", "Encounter"),
    ("diagnoses.csv", "Condition"),
    ("procedures.csv", "Procedure"),
    ("medications.csv", "MedicationRequest or MedicationStatement"),
    ("laboratory-results.csv", "Observation"),
    ("vital-sign-results.csv", "Observation"),
    ("clinical-outcomes.csv", "Observation, Condition, Encounter, or project-specific outcome"),
]


def input_path(filename: str) -> Path:
    return DATA_DIR / filename


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


def build_mapping() -> pd.DataFrame:
    rows = [
        {
            "local_file": "patient-demographics.csv",
            "local_domain": "patient demographics",
            "candidate_fhir_resource": "Patient",
            "key_local_fields": "patient_id; sex; birth_date or age",
            "candidate_fhir_fields": "Patient.identifier; Patient.gender; Patient.birthDate",
            "mapping_status": "conceptual_mapping",
            "readiness_note": "Production mapping should prefer birthDate over age when available.",
        },
        {
            "local_file": "clinical-encounters.csv",
            "local_domain": "encounters",
            "candidate_fhir_resource": "Encounter",
            "key_local_fields": "encounter_id; patient_id; encounter_date; encounter_type",
            "candidate_fhir_fields": "Encounter.identifier; Encounter.subject; Encounter.period.start; Encounter.class/type",
            "mapping_status": "conceptual_mapping",
            "readiness_note": "Encounter type and timestamp semantics should be reviewed.",
        },
        {
            "local_file": "diagnoses.csv",
            "local_domain": "diagnoses",
            "candidate_fhir_resource": "Condition",
            "key_local_fields": "patient_id; diagnosis_code; diagnosis_date",
            "candidate_fhir_fields": "Condition.subject; Condition.code; Condition.recordedDate/onsetDateTime",
            "mapping_status": "conceptual_mapping",
            "readiness_note": "Diagnosis code system must be documented.",
        },
        {
            "local_file": "procedures.csv",
            "local_domain": "procedures",
            "candidate_fhir_resource": "Procedure",
            "key_local_fields": "patient_id; procedure_code; procedure_date",
            "candidate_fhir_fields": "Procedure.subject; Procedure.code; Procedure.performedDateTime",
            "mapping_status": "conceptual_mapping",
            "readiness_note": "Procedure code system and performed date should be validated.",
        },
        {
            "local_file": "medications.csv",
            "local_domain": "medications",
            "candidate_fhir_resource": "MedicationRequest or MedicationStatement",
            "key_local_fields": "patient_id; medication_name; medication_date; medication_status",
            "candidate_fhir_fields": "MedicationRequest.subject; MedicationRequest.medication; MedicationRequest.authoredOn",
            "mapping_status": "requires_semantic_review",
            "readiness_note": "Clarify whether local data represent orders, prescriptions, administrations, or reported use.",
        },
        {
            "local_file": "laboratory-results.csv",
            "local_domain": "laboratory results",
            "candidate_fhir_resource": "Observation",
            "key_local_fields": "patient_id; test_name; result_value; result_unit; result_date; abnormal_flag",
            "candidate_fhir_fields": "Observation.subject; Observation.code; Observation.valueQuantity; Observation.effectiveDateTime; Observation.interpretation",
            "mapping_status": "conceptual_mapping",
            "readiness_note": "Units and test code systems should be standardized before exchange.",
        },
        {
            "local_file": "vital-sign-results.csv",
            "local_domain": "vital signs",
            "candidate_fhir_resource": "Observation",
            "key_local_fields": "patient_id; vital_name; vital_value; vital_unit; vital_date",
            "candidate_fhir_fields": "Observation.subject; Observation.code; Observation.valueQuantity; Observation.effectiveDateTime",
            "mapping_status": "conceptual_mapping",
            "readiness_note": "Vital sign names should be mapped to standard observation concepts where possible.",
        },
        {
            "local_file": "clinical-outcomes.csv",
            "local_domain": "clinical outcomes",
            "candidate_fhir_resource": "Observation, Condition, Encounter, or project-specific outcome",
            "key_local_fields": "patient_id; outcome_status; outcome_date; follow_up_days",
            "candidate_fhir_fields": "Depends on outcome definition and clinical meaning",
            "mapping_status": "requires_clinical_definition",
            "readiness_note": "Outcome representation should be reviewed by clinical and informatics stakeholders.",
        },
    ]

    out = pd.DataFrame(rows)
    out["input_file_exists"] = out["local_file"].apply(lambda filename: input_path(filename).exists())
    return out


def build_checklist(mapping: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for filename, resource in EXPECTED_INPUTS:
        path = input_path(filename)
        df = safe_read_csv(path)

        rows.append(
            {
                "readiness_domain": "input_availability",
                "item": f"{filename} available for {resource} mapping",
                "status": "present" if path.exists() else "missing",
                "evidence": str(path),
                "interoperability_note": "Input availability is required before field-level mapping can be validated.",
            }
        )

        if path.exists():
            rows.append(
                {
                    "readiness_domain": "input_structure",
                    "item": f"{filename} readable as tabular data",
                    "status": "present" if not df.empty else "limited_or_empty",
                    "evidence": f"rows={len(df)}; columns={len(df.columns)}",
                    "interoperability_note": "Readable structure is necessary but not sufficient for interoperability.",
                }
            )

    table_status_counts = mapping["mapping_status"].value_counts(dropna=False).to_dict()
    for status, count in table_status_counts.items():
        rows.append(
            {
                "readiness_domain": "mapping_status",
                "item": f"Mapping rows with status {status}",
                "status": "present" if count > 0 else "missing",
                "evidence": f"count={count}",
                "interoperability_note": "Rows requiring semantic or clinical review should be resolved before production exchange.",
            }
        )

    rows.extend(
        [
            {
                "readiness_domain": "governance",
                "item": "Privacy and minimum necessary data review",
                "status": "required_not_completed_by_script",
                "evidence": "Institutional review required.",
                "interoperability_note": "FHIR mapping does not remove privacy obligations.",
            },
            {
                "readiness_domain": "provenance",
                "item": "Source system and transformation provenance documented",
                "status": "required_not_completed_by_script",
                "evidence": "Project metadata required.",
                "interoperability_note": "Receiving systems need provenance to interpret exchanged data safely.",
            },
            {
                "readiness_domain": "terminology",
                "item": "Terminology and code-system mapping reviewed",
                "status": "required_not_completed_by_script",
                "evidence": "Terminology review required.",
                "interoperability_note": "Local codes should be mapped to documented systems before exchange.",
            },
        ]
    )

    return pd.DataFrame(rows)


def first_value(df: pd.DataFrame, candidates: list[str], default=None):
    for column in candidates:
        if column in df.columns and not df[column].dropna().empty:
            return df[column].dropna().iloc[0]
    return default


def build_example_bundle() -> dict:
    demographics = safe_read_csv(input_path("patient-demographics.csv"))
    encounters = safe_read_csv(input_path("clinical-encounters.csv"))
    labs = safe_read_csv(input_path("laboratory-results.csv"))
    vitals = safe_read_csv(input_path("vital-sign-results.csv"))

    patient_id = first_value(demographics, ["patient_id"], "example-patient-001")
    sex = first_value(demographics, ["sex", "gender"], "unknown")

    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "meta": {
            "profile": ["CDI educational FHIR-like example; not production-valid"],
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
        },
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": str(patient_id),
                    "identifier": [
                        {
                            "system": "https://complexdatainsights.com/example/patient-id",
                            "value": str(patient_id),
                        }
                    ],
                    "gender": str(sex).lower() if str(sex).lower() in {"male", "female", "other", "unknown"} else "unknown",
                }
            }
        ],
    }

    encounter_id = first_value(encounters, ["encounter_id"], None)
    encounter_date = first_value(encounters, ["encounter_date", "date"], None)

    if encounter_id is not None:
        bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "Encounter",
                    "id": str(encounter_id),
                    "identifier": [{"value": str(encounter_id)}],
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "period": {"start": str(encounter_date)} if encounter_date is not None else {},
                }
            }
        )

    lab_name = first_value(labs, ["test_name", "result_name", "lab_name"], None)
    lab_value = first_value(labs, ["result_value", "value"], None)
    lab_unit = first_value(labs, ["result_unit", "unit"], None)

    if lab_name is not None:
        bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "example-lab-observation",
                    "status": "final",
                    "code": {"text": str(lab_name)},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "valueQuantity": {
                        "value": str(lab_value) if lab_value is not None else "",
                        "unit": str(lab_unit) if lab_unit is not None else "",
                    },
                }
            }
        )

    vital_name = first_value(vitals, ["vital_name", "result_name"], None)
    vital_value = first_value(vitals, ["vital_value", "result_value", "value"], None)
    vital_unit = first_value(vitals, ["vital_unit", "result_unit", "unit"], None)

    if vital_name is not None:
        bundle["entry"].append(
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "example-vital-observation",
                    "status": "final",
                    "code": {"text": str(vital_name)},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "valueQuantity": {
                        "value": str(vital_value) if vital_value is not None else "",
                        "unit": str(vital_unit) if vital_unit is not None else "",
                    },
                }
            }
        )

    return bundle


def write_summary(mapping: pd.DataFrame, checklist: pd.DataFrame, bundle: dict) -> None:
    status_counts = mapping["mapping_status"].value_counts(dropna=False).to_dict()
    checklist_counts = checklist["status"].value_counts(dropna=False).to_dict()
    resource_counts = mapping["candidate_fhir_resource"].value_counts(dropna=False).to_dict()

    lines = [
        "EHR, FHIR, and Interoperability Roadmap Summary",
        "================================================",
        "",
        f"Mapping file: {MAPPING_FILE}",
        f"Readiness checklist: {CHECKLIST_FILE}",
        f"Example bundle: {BUNDLE_FILE}",
        "",
        "Mapping status counts:",
    ]

    for status, count in status_counts.items():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "Checklist status counts:"])
    for status, count in checklist_counts.items():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "Candidate FHIR resource counts:"])
    for resource, count in resource_counts.items():
        lines.append(f"- {resource}: {count}")

    lines.extend(
        [
            "",
            f"Example bundle entries: {len(bundle.get('entry', []))}",
            "",
            "Interpretation:",
            "These outputs provide a conceptual interoperability roadmap.",
            "They are not a production FHIR implementation, not a validated interface specification, and not an authorization to exchange clinical data.",
            "Production use requires terminology review, governance approval, privacy review, provenance documentation, and system-specific implementation testing.",
        ]
    )

    SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    try:
        INTEROP_DIR.mkdir(parents=True, exist_ok=True)

        mapping = build_mapping()
        checklist = build_checklist(mapping)
        bundle = build_example_bundle()

        mapping.to_csv(MAPPING_FILE, sep="\t", index=False)
        checklist.to_csv(CHECKLIST_FILE, sep="\t", index=False)
        BUNDLE_FILE.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        write_summary(mapping, checklist, bundle)

        print(f"Wrote: {MAPPING_FILE}")
        print(f"Wrote: {CHECKLIST_FILE}")
        print(f"Wrote: {BUNDLE_FILE}")
        print(f"Wrote: {SUMMARY_FILE}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
