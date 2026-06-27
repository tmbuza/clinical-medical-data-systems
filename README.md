# Clinical & Medical Data Systems

**Clinical & Medical Data Systems** is a Complex Data Insights (CDI) guide and reproducible project for moving from structured healthcare data inputs to analysis-ready datasets, clinical interpretation, reporting, dashboard readiness, and interoperability planning.

This repository demonstrates a full educational clinical data workflow using synthetic example data.

It is not a clinical deployment system and does not use real patient data.

---

## Purpose

Clinical and medical data often come from many sources:

- demographics
- encounters
- diagnoses
- procedures
- medications
- laboratory results
- vital signs
- outcomes
- follow-up records

This project shows how those inputs can be organized, validated, transformed, analyzed, interpreted, reported, and prepared for dashboard and interoperability review.

The guide emphasizes reproducible workflows, clear denominators, clinical data quality checks, missingness and completeness, patient-level variable engineering, analysis-ready clinical datasets, descriptive clinical analysis, risk stratification, model evaluation, cautious clinical interpretation, decision-support readiness, reproducible reports, dashboard prototypes, and EHR/FHIR interoperability planning.

---

## Repository

```text
https://github.com/tmbuza/clinical-medical-data-systems
```

---

## Guide Structure

```text
index.qmd
00-preface-and-overview.qmd

Part I: Clinical Data Foundations
01-clinical-data-systems-overview.qmd
02-healthcare-data-types.qmd
03-clinical-questions-and-cohorts.qmd
04-data-governance-privacy-and-ethics.qmd

Part II: Clinical Data Inputs
05-patient-demographics-and-encounters.qmd
06-diagnoses-procedures-and-medications.qmd
07-laboratory-and-vital-sign-results.qmd
08-clinical-outcomes-and-follow-up.qmd

Part III: Cleaning, Validation, and Readiness
09-clinical-data-quality-checks.qmd
10-missingness-and-data-completeness.qmd
11-clinical-variable-engineering.qmd
12-analysis-ready-clinical-datasets.qmd

Part IV: Clinical Analysis and Interpretation
13-descriptive-clinical-analysis.qmd
14-risk-stratification-and-clinical-models.qmd
15-clinical-model-evaluation.qmd
16-clinical-interpretation-and-decision-support.qmd

Part V: Reporting and Real-World Systems
17-reproducible-clinical-reports.qmd
18-clinical-dashboard-readiness.qmd
19-ehr-fhir-and-interoperability-roadmap.qmd
20-end-to-end-case-study.qmd

Appendices
999-appendix.qmd
999-references.qmd
```

---

## Project Layout

```text
clinical-medical-data-systems/
├── data/
│   └── example/
├── logs/
├── results/
│   ├── case-study/
│   ├── dashboard/
│   ├── figures/
│   ├── interoperability/
│   └── reports/
├── scripts/
│   ├── bash/
│   ├── python/
│   └── R/
├── *.qmd
└── README.md
```

---

## Requirements

This project uses a lightweight modern stack.

Recommended:

```text
Python 3.10+
R 4.3+
Quarto
pandas
ggplot2
dplyr
readr
forcats
scikit-learn
```

The workflow is designed to avoid unnecessary heavy dependencies.

Several scripts use safe fallbacks for small example datasets.

---

## Quick Start

From the project root:

```bash
bash scripts/bash/20-run-end-to-end-case-study.sh
```

This runs the full educational workflow from example clinical inputs to final case-study outputs.

---

## Main End-to-End Outputs

```text
results/case-study/end-to-end-case-study-file-inventory.tsv
results/case-study/end-to-end-case-study-stage-summary.tsv
results/case-study/end-to-end-case-study-summary.md
results/case-study/end-to-end-case-study-readiness-summary.txt
logs/20-end-to-end-case-study.log
```

---

## Useful Review Commands

```bash
cat results/case-study/end-to-end-case-study-readiness-summary.txt
head -20 results/case-study/end-to-end-case-study-stage-summary.tsv
open results/reports/reproducible-clinical-report.md
open results/dashboard/clinical-dashboard-prototype.html
```

---

## Run Individual Workflow Layers

### Clinical data inputs

```bash
python scripts/python/05-create-example-patient-encounter-data.py
python scripts/python/06-create-example-coded-clinical-events.py
python scripts/python/07-create-example-labs-and-vitals.py
python scripts/python/08-create-example-clinical-outcomes.py
```

### Data quality and readiness

```bash
python scripts/python/09-run-clinical-data-quality-checks.py
python scripts/python/10-profile-missingness-and-completeness.py
Rscript scripts/R/10-visualize-missingness-and-completeness.R
```

### Variable engineering and analysis-ready dataset

```bash
python scripts/python/11-engineer-clinical-variables.py
Rscript scripts/R/11-visualize-clinical-variables.R
python scripts/python/12-build-analysis-ready-clinical-dataset.py
Rscript scripts/R/12-visualize-analysis-ready-clinical-dataset.R
```

### Clinical analysis and modeling

```bash
python scripts/python/13-run-descriptive-clinical-analysis.py
Rscript scripts/R/13-visualize-descriptive-clinical-analysis.R
python scripts/python/14-risk-stratification-and-clinical-models-safe.py
Rscript scripts/R/14-visualize-risk-stratification-safe.R
python scripts/python/15-clinical-model-evaluation-safe.py
Rscript scripts/R/15-visualize-clinical-model-evaluation-safe.R
```

### Interpretation, reporting, dashboards, and interoperability

```bash
python scripts/python/16-clinical-interpretation-and-decision-support-safe.py
Rscript scripts/R/16-visualize-decision-support-readiness-safe.R
python scripts/python/17-build-reproducible-clinical-report-safe.py
python scripts/python/18-build-clinical-dashboard-readiness-safe.py
Rscript scripts/R/18-visualize-dashboard-readiness-safe.R
python scripts/python/19-build-fhir-interoperability-roadmap-safe.py
Rscript scripts/R/19-visualize-fhir-interoperability-readiness-safe.R
```

---

## Render the Quarto Guide

```bash
quarto render
```

---

## Important Safety Note

This repository is for education, reproducible workflow design, and clinical data systems training.

It does not provide medical advice.

It does not create validated clinical decision support.

It does not authorize clinical deployment.

Any real-world clinical use would require governance review, privacy review, clinical validation, workflow review, monitoring, and approval from the responsible institution.

---

## CDI Principle

A clinical data system is not a single model, table, report, or dashboard.

It is a chain of defensible transformations from clinical questions and governed data inputs to transparent, reproducible, and responsibly interpreted outputs.

---

## Author

Teresia Mrema Buza  
Complex Data Insights
# cdi-system-guides
