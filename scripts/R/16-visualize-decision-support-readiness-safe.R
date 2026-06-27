#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
})

action_file <- "results/clinical-decision-support-action-map.tsv"
statement_file <- "results/clinical-risk-interpretation-statements.tsv"
figure_dir <- "results/figures"

dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

write_skip_note <- function(path, message_text) {
  writeLines(message_text, con = path)
}

if (file.exists(statement_file)) {
  statements <- read_tsv(statement_file, show_col_types = FALSE)

  if ("risk_group" %in% names(statements)) {
    plot_df <- statements %>%
      mutate(risk_group = as.character(risk_group)) %>%
      mutate(risk_group = if_else(is.na(risk_group) | risk_group == "" | risk_group == "NA", "missing", risk_group)) %>%
      count(risk_group, name = "patient_count") %>%
      filter(patient_count > 0)

    if (nrow(plot_df) > 0) {
      plot_df <- plot_df %>%
        mutate(risk_group = fct_reorder(risk_group, patient_count))

      p <- ggplot(plot_df, aes(x = risk_group, y = patient_count)) +
        geom_col(width = 0.7) +
        coord_flip() +
        labs(
          title = "Decision-support risk group action map",
          subtitle = "Patient counts by risk group for interpretation and review planning",
          x = "Risk group",
          y = "Patient count"
        ) +
        theme_minimal(base_size = 12)

      ggsave(
        filename = file.path(figure_dir, "decision-support-risk-group-action-map.png"),
        plot = p,
        width = 8,
        height = 5,
        dpi = 300
      )
    } else {
      write_skip_note(
        file.path(figure_dir, "decision-support-risk-group-action-map-skipped.txt"),
        "Skipped decision-support risk group plot because no usable risk groups were available."
      )
    }
  } else {
    write_skip_note(
      file.path(figure_dir, "decision-support-risk-group-action-map-skipped.txt"),
      "Skipped decision-support risk group plot because risk_group column was not found."
    )
  }
} else {
  write_skip_note(
    file.path(figure_dir, "decision-support-risk-group-action-map-skipped.txt"),
    paste("Skipped decision-support risk group plot because input file was not found:", statement_file)
  )
}

message("Wrote figures or skip notes to: ", figure_dir)
