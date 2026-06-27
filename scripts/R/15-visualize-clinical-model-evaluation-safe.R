#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
})

risk_input <- "results/clinical-risk-stratification-results.tsv"
calibration_input <- "results/clinical-model-calibration-table.tsv"
threshold_input <- "results/clinical-model-threshold-evaluation.tsv"
figure_dir <- "results/figures"

dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

write_skip_note <- function(path, message_text) {
  writeLines(message_text, con = path)
}

safe_numeric <- function(x) {
  suppressWarnings(as.numeric(as.character(x)))
}

if (file.exists(risk_input)) {
  risk_df <- read_tsv(risk_input, show_col_types = FALSE)

  if (all(c("predicted_risk_score", "binary_outcome") %in% names(risk_df))) {
    plot_df <- risk_df %>%
      mutate(
        predicted_risk_score_numeric = safe_numeric(predicted_risk_score),
        binary_outcome_label = case_when(
          as.character(binary_outcome) %in% c("1", "TRUE", "true") ~ "Outcome present",
          as.character(binary_outcome) %in% c("0", "FALSE", "false") ~ "Outcome absent",
          TRUE ~ "Outcome missing"
        )
      ) %>%
      filter(!is.na(predicted_risk_score_numeric))

    if (nrow(plot_df) > 0) {
      p_risk <- ggplot(plot_df, aes(x = binary_outcome_label, y = predicted_risk_score_numeric)) +
        geom_boxplot(outlier.alpha = 0.6) +
        coord_flip() +
        labs(
          title = "Predicted risk score by observed outcome",
          subtitle = "Distribution of risk scores across observed outcome groups",
          x = "Observed outcome",
          y = "Predicted risk score"
        ) +
        theme_minimal(base_size = 12)

      ggsave(
        filename = file.path(figure_dir, "model-risk-by-outcome.png"),
        plot = p_risk,
        width = 8,
        height = 5,
        dpi = 300
      )
    } else {
      write_skip_note(
        file.path(figure_dir, "model-risk-by-outcome-skipped.txt"),
        "Skipped risk by outcome plot because predicted risk scores contained no numeric values."
      )
    }
  } else {
    write_skip_note(
      file.path(figure_dir, "model-risk-by-outcome-skipped.txt"),
      "Skipped risk by outcome plot because required columns were not found."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "model-risk-by-outcome-skipped.txt"),
    paste("Skipped risk by outcome plot because input file was not found:", risk_input)
  )
}

if (file.exists(calibration_input)) {
  calibration_df <- read_tsv(calibration_input, show_col_types = FALSE) %>%
    mutate(
      mean_predicted_risk_numeric = safe_numeric(mean_predicted_risk),
      observed_event_rate_numeric = safe_numeric(observed_event_rate)
    ) %>%
    filter(!is.na(mean_predicted_risk_numeric), !is.na(observed_event_rate_numeric))

  if (nrow(calibration_df) > 0) {
    p_cal <- ggplot(calibration_df, aes(x = mean_predicted_risk_numeric, y = observed_event_rate_numeric)) +
      geom_point(size = 2.5) +
      geom_abline(slope = 1, intercept = 0, linetype = "dashed") +
      coord_equal(xlim = c(0, 1), ylim = c(0, 1)) +
      labs(
        title = "Model calibration summary",
        subtitle = "Observed event rate compared with mean predicted risk",
        x = "Mean predicted risk",
        y = "Observed event rate"
      ) +
      theme_minimal(base_size = 12)

    ggsave(
      filename = file.path(figure_dir, "model-calibration-plot.png"),
      plot = p_cal,
      width = 6,
      height = 6,
      dpi = 300
    )
  } else {
    write_skip_note(
      file.path(figure_dir, "model-calibration-plot-skipped.txt"),
      "Skipped calibration plot because calibration table contained no usable numeric values."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "model-calibration-plot-skipped.txt"),
    paste("Skipped calibration plot because input file was not found:", calibration_input)
  )
}

if (file.exists(threshold_input)) {
  threshold_df <- read_tsv(threshold_input, show_col_types = FALSE) %>%
    mutate(
      threshold_numeric = safe_numeric(threshold),
      sensitivity_numeric = safe_numeric(sensitivity),
      specificity_numeric = safe_numeric(specificity)
    ) %>%
    filter(!is.na(threshold_numeric))

  if (nrow(threshold_df) > 0) {
    long_df <- bind_rows(
      threshold_df %>%
        transmute(threshold = threshold_numeric, metric = "Sensitivity", value = sensitivity_numeric),
      threshold_df %>%
        transmute(threshold = threshold_numeric, metric = "Specificity", value = specificity_numeric)
    ) %>%
      filter(!is.na(value))

    if (nrow(long_df) > 0) {
      p_threshold <- ggplot(long_df, aes(x = threshold, y = value, linetype = metric)) +
        geom_line(linewidth = 1) +
        geom_point(size = 1.8) +
        scale_y_continuous(limits = c(0, 1)) +
        labs(
          title = "Sensitivity and specificity across thresholds",
          subtitle = "Clinical threshold tradeoffs from the example evaluation workflow",
          x = "Risk threshold",
          y = "Metric value",
          linetype = "Metric"
        ) +
        theme_minimal(base_size = 12)

      ggsave(
        filename = file.path(figure_dir, "model-threshold-sensitivity-specificity.png"),
        plot = p_threshold,
        width = 8,
        height = 5,
        dpi = 300
      )
    } else {
      write_skip_note(
        file.path(figure_dir, "model-threshold-sensitivity-specificity-skipped.txt"),
        "Skipped threshold plot because sensitivity and specificity contained no usable values."
      )
    }
  } else {
    write_skip_note(
      file.path(figure_dir, "model-threshold-sensitivity-specificity-skipped.txt"),
      "Skipped threshold plot because threshold values were not usable."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "model-threshold-sensitivity-specificity-skipped.txt"),
    paste("Skipped threshold plot because input file was not found:", threshold_input)
  )
}

message("Wrote figures or skip notes to: ", figure_dir)
