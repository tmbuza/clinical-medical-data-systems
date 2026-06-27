#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
})

input_file <- "results/clinical-risk-stratification-results.tsv"
figure_dir <- "results/figures"

dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

if (!file.exists(input_file)) {
  stop(
    "Missing input file: ", input_file,
    "\nRun: python scripts/python/14-risk-stratification-and-clinical-models-safe.py",
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

if ("predicted_risk_score" %in% names(df)) {
  risk_df <- df %>%
    mutate(predicted_risk_score_numeric = safe_numeric(predicted_risk_score)) %>%
    filter(!is.na(predicted_risk_score_numeric))

  if (nrow(risk_df) > 0) {
    p_score <- ggplot(risk_df, aes(x = predicted_risk_score_numeric)) +
      geom_histogram(bins = 20, boundary = 0) +
      labs(
        title = "Predicted clinical risk score distribution",
        subtitle = "Patient-level risk scores from the Chapter 14 stratification workflow",
        x = "Predicted risk score",
        y = "Patient count"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "risk-score-distribution.png"),
      plot = p_score,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "risk-score-distribution-skipped.txt"),
      "Skipped risk score plot because predicted_risk_score contained no numeric non-missing values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "risk-score-distribution-skipped.txt"),
    "Skipped risk score plot because predicted_risk_score column was not found."
  )
}

if ("risk_group" %in% names(df)) {
  group_df <- df %>%
    mutate(risk_group = as.character(risk_group)) %>%
    mutate(risk_group = if_else(is.na(risk_group) | risk_group == "" | risk_group == "NA", "Missing", risk_group)) %>%
    count(risk_group, name = "patient_count") %>%
    filter(patient_count > 0)

  if (nrow(group_df) > 0) {
    group_df <- group_df %>%
      mutate(risk_group = fct_reorder(risk_group, patient_count))

    p_group <- ggplot(group_df, aes(x = risk_group, y = patient_count)) +
      geom_col(width = 0.7) +
      coord_flip() +
      labs(
        title = "Clinical risk group summary",
        subtitle = "Patient counts by assigned risk group",
        x = "Risk group",
        y = "Patient count"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "risk-group-summary.png"),
      plot = p_group,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "risk-group-summary-skipped.txt"),
      "Skipped risk group plot because risk_group contained no usable values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "risk-group-summary-skipped.txt"),
    "Skipped risk group plot because risk_group column was not found."
  )
}

message("Wrote figures or skip notes to: ", figure_dir)
