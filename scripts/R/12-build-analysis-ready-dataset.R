#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
})

dir.create("data/intermediate", recursive = TRUE, showWarnings = FALSE)

patients <- read_tsv("data/example/patients.tsv", show_col_types = FALSE)
encounters <- read_tsv("data/example/encounters.tsv", show_col_types = FALSE)
vitals <- read_tsv("data/example/vitals.tsv", show_col_types = FALSE)
outcomes <- read_tsv("data/example/outcomes.tsv", show_col_types = FALSE)

analysis_ready <- encounters %>%
  left_join(patients, by = "patient_id") %>%
  left_join(vitals, by = c("encounter_id", "patient_id")) %>%
  left_join(outcomes, by = c("encounter_id", "patient_id")) %>%
  mutate(
    age_approx = 2026 - birth_year,
    elevated_systolic_bp = systolic_bp >= 140
  )

write_tsv(analysis_ready, "data/intermediate/analysis-ready-clinical-dataset.tsv")

message("Analysis-ready dataset written to data/intermediate/analysis-ready-clinical-dataset.tsv")
