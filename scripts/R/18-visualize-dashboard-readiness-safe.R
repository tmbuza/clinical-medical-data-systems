#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
})

input_file <- "results/dashboard/dashboard-kpi-summary.tsv"
figure_dir <- "results/figures"

dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

write_skip_note <- function(path, message_text) {
  writeLines(message_text, con = path)
}

if (!file.exists(input_file)) {
  write_skip_note(
    file.path(figure_dir, "dashboard-kpi-readiness-summary-skipped.txt"),
    paste("Skipped dashboard KPI readiness figure because input file was not found:", input_file)
  )
  message("Wrote skip note to: ", figure_dir)
  quit(save = "no", status = 0)
}

df <- read_tsv(input_file, show_col_types = FALSE)

if (!all(c("display_label", "status") %in% names(df))) {
  write_skip_note(
    file.path(figure_dir, "dashboard-kpi-readiness-summary-skipped.txt"),
    "Skipped dashboard KPI readiness figure because display_label or status column was not found."
  )
  message("Wrote skip note to: ", figure_dir)
  quit(save = "no", status = 0)
}

plot_df <- df %>%
  mutate(
    display_label = as.character(display_label),
    status = as.character(status)
  ) %>%
  filter(!is.na(display_label), display_label != "", !is.na(status), status != "") %>%
  count(status, name = "metric_count")

if (nrow(plot_df) == 0) {
  write_skip_note(
    file.path(figure_dir, "dashboard-kpi-readiness-summary-skipped.txt"),
    "Skipped dashboard KPI readiness figure because no usable KPI status values were available."
  )
  message("Wrote skip note to: ", figure_dir)
  quit(save = "no", status = 0)
}

plot_df <- plot_df %>%
  mutate(status = fct_reorder(status, metric_count))

p <- ggplot(plot_df, aes(x = status, y = metric_count)) +
  geom_col(width = 0.7) +
  coord_flip() +
  labs(
    title = "Dashboard KPI readiness summary",
    subtitle = "Availability status of dashboard-ready clinical KPI metrics",
    x = "KPI status",
    y = "Metric count"
  ) +
  theme_minimal(base_size = 12)

ggsave(
  filename = file.path(figure_dir, "dashboard-kpi-readiness-summary.png"),
  plot = p,
  width = 8,
  height = 5,
  dpi = 300
)

message("Wrote figure to: ", figure_dir)
