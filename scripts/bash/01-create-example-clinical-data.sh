#!/usr/bin/env bash
###############################################################################
# Create privacy-safe synthetic clinical example tables
###############################################################################

set -euo pipefail

mkdir -p data/example

cat > data/example/patients.tsv <<'DATA'
patient_id	sex	birth_year
P001	Female	1965
P002	Male	1972
P003	Female	1958
P004	Male	1980
P005	Female	1991
DATA

cat > data/example/encounters.tsv <<'DATA'
encounter_id	patient_id	encounter_date	encounter_type
E001	P001	2026-01-10	outpatient
E002	P002	2026-01-12	emergency
E003	P003	2026-01-14	inpatient
E004	P004	2026-01-15	outpatient
E005	P005	2026-01-18	outpatient
DATA

cat > data/example/diagnoses.tsv <<'DATA'
encounter_id	patient_id	diagnosis_code	diagnosis_label
E001	P001	I10	Hypertension
E002	P002	E11	Type 2 diabetes mellitus
E003	P003	J18	Pneumonia
E004	P004	I10	Hypertension
E005	P005	Z00	General examination
DATA

cat > data/example/medications.tsv <<'DATA'
encounter_id	patient_id	medication_name	medication_class
E001	P001	Amlodipine	Antihypertensive
E002	P002	Metformin	Antidiabetic
E003	P003	Amoxicillin	Antibiotic
E004	P004	Losartan	Antihypertensive
E005	P005	None	None
DATA

cat > data/example/labs.tsv <<'DATA'
encounter_id	patient_id	lab_name	lab_value	lab_unit
E001	P001	hemoglobin	13.1	g/dL
E002	P002	glucose	188	mg/dL
E003	P003	wbc	14.2	10^9/L
E004	P004	creatinine	1.1	mg/dL
E005	P005	hemoglobin	12.5	g/dL
DATA

cat > data/example/vitals.tsv <<'DATA'
encounter_id	patient_id	systolic_bp	diastolic_bp	heart_rate	temperature_c
E001	P001	142	88	78	36.8
E002	P002	150	92	86	37.0
E003	P003	128	82	104	38.4
E004	P004	138	85	74	36.7
E005	P005	118	76	68	36.6
DATA

cat > data/example/outcomes.tsv <<'DATA'
encounter_id	patient_id	followup_days	outcome_status
E001	P001	30	stable
E002	P002	30	review_needed
E003	P003	30	improved
E004	P004	30	stable
E005	P005	30	stable
DATA

echo "Example clinical data created in data/example/"
