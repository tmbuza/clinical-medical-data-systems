#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
})

input_file <- "results/analysis-ready-clinical-dataset.tsv"
figure_dir <- "results/figures"

dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

if (!file.exists(input_file)) {
  stop(
    "Missing input file: ", input_file,
    "\nRun: bash scripts/bash/12-run-analysis-ready-clinical-dataset.sh",
    call. = FALSE
  )
}

df <- read_tsv(input_file, show_col_types = FALSE)

write_skip_note <- function(path, message_text) {
  writeLines(message_text, con = path)
}

safe_numeric <- function(x) {
  suppressWarnings(as.numeric(as.character(x)))
}

if ("age" %in% names(df)) {
  age_df <- df %>%
    mutate(age_numeric = safe_numeric(age)) %>%
    filter(!is.na(age_numeric))

  if (nrow(age_df) > 0) {
    p_age <- ggplot(age_df, aes(x = age_numeric)) +
      geom_histogram(bins = 20, boundary = 0) +
      labs(
        title = "Age distribution of the clinical cohort",
        subtitle = "Patient-level age distribution in the analysis-ready dataset",
        x = "Age",
        y = "Patient count"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "descriptive-age-distribution.png"),
      plot = p_age,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "descriptive-age-distribution-skipped.txt"),
      "Skipped age distribution plot because age contained no numeric non-missing values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "descriptive-age-distribution-skipped.txt"),
    "Skipped age distribution plot because age column was not found."
  )
}

if ("outcome_status" %in% names(df)) {
  outcome_plot <- df %>%
    mutate(outcome_status = as.character(outcome_status)) %>%
    mutate(outcome_status = if_else(is.na(outcome_status) | outcome_status == "" | outcome_status == "NA", "Missing", outcome_status)) %>%
    count(outcome_status, name = "patient_count") %>%
    filter(patient_count > 0)

  if (nrow(outcome_plot) > 0) {
    outcome_plot <- outcome_plot %>%
      mutate(outcome_status = fct_reorder(outcome_status, patient_count))

    p_outcome <- ggplot(outcome_plot, aes(x = outcome_status, y = patient_count)) +
      geom_col(width = 0.7) +
      coord_flip() +
      labs(
        title = "Clinical outcome distribution",
        subtitle = "Observed outcome categories in the analysis-ready dataset",
        x = "Outcome status",
        y = "Patient count"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "descriptive-outcome-summary.png"),
      plot = p_outcome,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "descriptive-outcome-summary-skipped.txt"),
      "Skipped outcome plot because outcome_status contained no usable values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "descriptive-outcome-summary-skipped.txt"),
    "Skipped outcome plot because outcome_status column was not found."
  )
}

if (all(c("follow_up_days", "outcome_status") %in% names(df))) {
  follow_df <- df %>%
    mutate(
      follow_up_days_numeric = safe_numeric(follow_up_days),
      outcome_status = as.character(outcome_status),
      outcome_status = if_else(is.na(outcome_status) | outcome_status == "" | outcome_status == "NA", "Missing", outcome_status)
    ) %>%
    filter(!is.na(follow_up_days_numeric))

  if (nrow(follow_df) > 0) {
    p_follow <- ggplot(follow_df, aes(x = outcome_status, y = follow_up_days_numeric)) +
      geom_boxplot(outlier.alpha = 0.6) +
      coord_flip() +
      labs(
        title = "Follow-up duration by outcome status",
        subtitle = "Distribution of patient follow-up days across outcome groups",
        x = "Outcome status",
        y = "Follow-up days"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "descriptive-follow-up-by-outcome.png"),
      plot = p_follow,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "descriptive-follow-up-by-outcome-skipped.txt"),
      "Skipped follow-up by outcome plot because follow_up_days contained no numeric non-missing values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "descriptive-follow-up-by-outcome-skipped.txt"),
    "Skipped follow-up by outcome plot because follow_up_days or outcome_status column was not found."
  )
}

message("Wrote figures or skip notes to: ", figure_dir)
