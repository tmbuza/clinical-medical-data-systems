#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
})

dir.create("results/tables", recursive = TRUE, showWarnings = FALSE)

df <- read_tsv("data/intermediate/analysis-ready-clinical-dataset.tsv", show_col_types = FALSE)

summary_table <- df %>%
  summarise(
    patients = n_distinct(patient_id),
    encounters = n_distinct(encounter_id),
    mean_age_approx = mean(age_approx, na.rm = TRUE),
    mean_systolic_bp = mean(systolic_bp, na.rm = TRUE),
    elevated_systolic_bp_count = sum(elevated_systolic_bp, na.rm = TRUE)
  )

write_tsv(summary_table, "results/tables/descriptive-clinical-summary.tsv")

message("Descriptive clinical summary written to results/tables/descriptive-clinical-summary.tsv")
