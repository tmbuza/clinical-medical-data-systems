# Reproducible Clinical Report

Generated: `2026-06-27T12:46:18`

## Report Purpose

This report assembles saved outputs from the Clinical & Medical Data Systems workflow into a single reviewable artifact.

It is intended for clinical data review, not direct clinical deployment.

## File Inventory Summary

| metric | value |
| --- | --- |
| expected_files | 8 |
| present_files | 8 |
| missing_files | 0 |
| report_file | results/reports/reproducible-clinical-report.md |
| created_at | 2026-06-27T12:46:18 |

## Evidence File Inventory

| file_path | role | exists | size_bytes | modified_time |
| --- | --- | --- | --- | --- |
| results/analysis-ready-clinical-dataset-readiness-summary.txt | Analysis-ready dataset readiness narrative | True | 905 | 2026-06-27T12:46:14 |
| results/descriptive-clinical-analysis-summary.txt | Descriptive clinical analysis narrative | True | 493 | 2026-06-27T12:46:14 |
| results/clinical-risk-model-summary.txt | Risk stratification model narrative | True | 670 | 2026-06-27T12:46:15 |
| results/clinical-model-evaluation-summary.txt | Clinical model evaluation narrative | True | 726 | 2026-06-27T12:46:16 |
| results/clinical-interpretation-and-decision-support-summary.txt | Clinical interpretation and decision-support narrative | True | 844 | 2026-06-27T12:46:17 |
| results/descriptive-clinical-cohort-summary.tsv | Cohort summary metrics | True | 361 | 2026-06-27T12:46:14 |
| results/clinical-model-evaluation-metrics.tsv | Model evaluation metrics | True | 236 | 2026-06-27T12:46:16 |
| results/clinical-decision-support-readiness.tsv | Decision-support readiness checklist | True | 2166 | 2026-06-27T12:46:17 |

## Analysis-Ready Dataset Readiness

```text
Analysis-Ready Clinical Dataset Readiness Summary
=================================================

Input file: results/patient-level-derived-variables.tsv
Output file: results/analysis-ready-clinical-dataset.tsv

Rows: 6
Unique patients: 6
Duplicate patient rows: 0
Analysis included rows: 0
Analysis excluded rows: 6

Required columns:
- patient_id: present; missing = 0
- age: missing; missing = 6
- sex: missing; missing = 6
- age_group: present; missing = 6
- encounter_count: missing; missing = 6
- outcome_status: missing; missing = 6
- follow_up_days: missing; missing = 6

Missing required columns:
- age
- sex
- encounter_count
- outcome_status
- follow_up_days

Interpretation:
This file is structurally prepared for downstream example analysis when the inclusion flag is true.
Clinical validity still depends on the appropriateness of the question, cohort definition, and outcome definition.
```

## Descriptive Clinical Analysis

```text
Descriptive Clinical Analysis Summary
=====================================

Input file: results/analysis-ready-clinical-dataset.tsv

Total rows: 6
Unique patients: 6
Analysis included rows: 0
Analysis excluded rows: 6

Outcome distribution:
- Missing: 6 patients (100.0%)

Table-one rows written: 16

Interpretation:
These outputs describe the prepared clinical cohort and should be reviewed before modeling.
They do not establish causal effects, prediction performance, or clinical utility.
```

## Risk Stratification Model Summary

```text
Clinical Risk Stratification Model Summary
==========================================

Input file: results/analysis-ready-clinical-dataset.tsv
Output file: results/clinical-risk-stratification-results.tsv

Patients used for risk scoring: 6
Predictor count: 3
Outcome non-missing count: 0
Outcome class count: 0
Scoring method: rule_based_fallback_insufficient_outcome_classes_or_rows

Risk group counts:
- moderate: 6

Interpretation:
This workflow is a transparent risk stratification demonstration, not a validated clinical model.
Real deployment requires clinical outcome review, external validation, calibration assessment, fairness review, and governance approval.
```

## Clinical Model Evaluation Summary

```text
Clinical Model Evaluation Summary
=================================

Input file: results/clinical-risk-stratification-results.tsv

Total rows: 6.0
Known outcome rows: 0.0
Usable evaluation rows: 0.0
Positive outcomes: 0.0
Negative outcomes: 0.0
Observed event rate: nan
Mean predicted risk: nan
AUROC: nan
Average precision: nan
Brier score: nan

Threshold rows written: 9
Risk group rows written: 1
Calibration rows written: 1

Interpretation:
These outputs evaluate the example risk stratification workflow only.
Small sample size, missing outcomes, or single-class outcomes limit what can be interpreted.
Clinical deployment requires additional validation, calibration review, subgroup assessment, and governance approval.
```

## Clinical Interpretation and Decision-Support Summary

```text
Clinical Interpretation and Decision Support Summary
====================================================

Readiness output: results/clinical-decision-support-readiness.tsv
Interpretation statements: results/clinical-risk-interpretation-statements.tsv
Action map: results/clinical-decision-support-action-map.tsv

Readiness status counts:
- present: 5
- limited_or_missing: 3
- required_not_completed_by_script: 3
- requires_project_review: 1

Risk group counts in interpretation statements:
- moderate: 6

Action map rows: 4
Interpretation statement rows: 6

Interpretation:
These outputs are decision-support design artifacts only.
They do not constitute clinical recommendations, treatment instructions, or deployment approval.
Real-world use requires clinical validation, governance review, workflow design, monitoring, and accountability.
```

## Cohort Summary Metrics

| metric | value |
| --- | --- |
| total_rows | 6.0 |
| unique_patients | 6.0 |
| duplicate_patient_rows | 0.0 |
| analysis_included_rows | 0.0 |
| analysis_excluded_rows | 6.0 |
| analysis_included_percent | 0.0 |
| age_mean |  |
| age_median |  |
| age_min |  |
| age_max |  |
| follow_up_days_mean |  |
| follow_up_days_median |  |
| follow_up_days_min |  |
| follow_up_days_max |  |
| encounter_count_mean |  |
| encounter_count_median |  |
| encounter_count_min |  |
| encounter_count_max |  |

## Model Evaluation Metrics

| metric | value |
| --- | --- |
| total_rows | 6.0 |
| known_outcome_rows | 0.0 |
| usable_evaluation_rows | 0.0 |
| positive_outcome_count | 0.0 |
| negative_outcome_count | 0.0 |
| observed_event_rate |  |
| mean_predicted_risk |  |
| median_predicted_risk |  |
| auroc |  |
| average_precision |  |
| brier_score |  |

## Decision-Support Readiness Checklist

| readiness_domain | item | status | evidence | decision_support_note |
| --- | --- | --- | --- | --- |
| cohort_definition | Cohort and analysis-ready dataset documented | requires_project_review | Review Chapters 12 and 13 outputs. | A decision-support workflow needs a visible denominator and inclusion logic. |
| risk_output | Patient-level risk stratification output available | present | results/clinical-risk-stratification-results.tsv | Risk output is required before interpretation statements can be generated. |
| evaluation | Model evaluation metrics available | present | results/clinical-model-evaluation-metrics.tsv | Evaluation must be reviewed before any workflow use. |
| evaluation | Known outcome rows available for evaluation | limited_or_missing | known_outcome_rows=0.0 | Decision support should not proceed without outcome-grounded review. |
| thresholds | Threshold behavior table available | present | results/clinical-model-threshold-evaluation.tsv | Threshold behavior is needed before choosing an action cutoff. |
| risk_groups | Observed event rates by risk group available | present | results/clinical-model-risk-group-evaluation.tsv | Risk groups should show clinically meaningful separation before use. |
| calibration | Calibration table available | present | results/clinical-model-calibration-table.tsv | Calibration matters if predicted risks are interpreted as probabilities. |
| performance | Discrimination metric is interpretable | limited_or_missing | auroc=None | AUROC may be unavailable when sample size is too small or outcomes have one class. |
| performance | Brier score is available | limited_or_missing | brier_score=None | Brier score summarizes probability error but does not establish clinical utility. |
| governance | Clinical governance approval | required_not_completed_by_script | Human/institutional review required. | Governance review is mandatory before real clinical deployment. |
| workflow | Human review and override process | required_not_completed_by_script | Workflow owner must define reviewer and escalation path. | Decision support should assist qualified review, not replace it. |
| monitoring | Post-deployment monitoring plan | required_not_completed_by_script | Monitoring plan must be defined before deployment. | Clinical models can drift and should be monitored over time. |

## Interpretation Boundaries

This report can support review of cohort structure, descriptive summaries, model outputs, and decision-support readiness.

It does not establish causal effects, clinical utility, patient safety, regulatory compliance, or deployment approval.

## Recommended Next Review Steps

1. Confirm the cohort definition and denominator.
2. Review missingness and variable completeness.
3. Confirm the clinical outcome definition.
4. Review model evaluation limitations.
5. Review risk group action language.
6. Complete clinical governance review before any real-world use.
