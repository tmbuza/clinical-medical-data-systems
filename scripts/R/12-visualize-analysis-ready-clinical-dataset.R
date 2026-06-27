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
    "\nRun: python scripts/python/12-build-analysis-ready-clinical-dataset.py",
    call. = FALSE
  )
}

df <- read_tsv(input_file, show_col_types = FALSE)

write_skip_note <- function(path, message_text) {
  writeLines(message_text, con = path)
}

if ("age_group" %in% names(df)) {
  age_plot <- df %>%
    mutate(age_group = as.character(age_group)) %>%
    filter(!is.na(age_group), age_group != "", age_group != "NA") %>%
    count(age_group, name = "patient_count")

  if (nrow(age_plot) > 0) {
    age_plot <- age_plot %>%
      mutate(age_group = fct_reorder(age_group, patient_count))

    p_age <- ggplot(age_plot, aes(x = age_group, y = patient_count)) +
      geom_col(width = 0.7) +
      coord_flip() +
      labs(
        title = "Analysis-ready patients by age group",
        subtitle = "Distribution of patient-level age groups in the assembled dataset",
        x = "Age group",
        y = "Patient count"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "analysis-ready-age-group-distribution.png"),
      plot = p_age,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "analysis-ready-age-group-distribution-skipped.txt"),
      "Skipped age-group plot because age_group contained no non-missing values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "analysis-ready-age-group-distribution-skipped.txt"),
    "Skipped age-group plot because age_group column was not found."
  )
}

if ("follow_up_days" %in% names(df)) {
  follow_plot <- df %>%
    mutate(follow_up_days = suppressWarnings(as.numeric(follow_up_days))) %>%
    filter(!is.na(follow_up_days))

  if (nrow(follow_plot) > 0) {
    p_follow <- ggplot(follow_plot, aes(x = follow_up_days)) +
      geom_histogram(bins = 20, boundary = 0) +
      labs(
        title = "Follow-up duration distribution",
        subtitle = "Patient-level follow-up days after analysis-ready assembly",
        x = "Follow-up days",
        y = "Patient count"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "analysis-ready-follow-up-distribution.png"),
      plot = p_follow,
      width = 8,
      height = 5,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "analysis-ready-follow-up-distribution-skipped.txt"),
      "Skipped follow-up plot because follow_up_days contained no numeric non-missing values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "analysis-ready-follow-up-distribution-skipped.txt"),
    "Skipped follow-up plot because follow_up_days column was not found."
  )
}

message("Wrote figures or skip notes to: ", figure_dir)
