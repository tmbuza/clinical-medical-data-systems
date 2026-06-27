#!/usr/bin/env Rscript

# Visualize engineered clinical variables.
# Run from the project root:
#   Rscript scripts/R/11-visualize-clinical-variables.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(tidyr)
  library(ggplot2)
  library(forcats)
  library(stringr)
})

results_dir <- "results"
figures_dir <- file.path(results_dir, "figures")
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

derived_path <- file.path(results_dir, "patient-level-derived-variables.tsv")

if (!file.exists(derived_path)) {
  stop("Missing engineered variable file: ", derived_path, call. = FALSE)
}

derived <- read_tsv(derived_path, show_col_types = FALSE)

if ("age_group" %in% names(derived)) {
  age_plot_data <- derived %>%
    mutate(age_group = if_else(is.na(age_group), "Missing", as.character(age_group))) %>%
    count(age_group, name = "patients") %>%
    mutate(age_group = fct_reorder(age_group, patients))

  age_plot <- age_plot_data %>%
    ggplot(aes(x = age_group, y = patients)) +
    geom_col(width = 0.7) +
    coord_flip() +
    labs(
      title = "Age group distribution in engineered clinical dataset",
      subtitle = "Patient counts after deriving age at index encounter",
      x = NULL,
      y = "Patients"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title.position = "plot",
      panel.grid.major.y = element_blank()
    )

  ggsave(
    filename = file.path(figures_dir, "age-group-distribution.png"),
    plot = age_plot,
    width = 8,
    height = 5,
    dpi = 300
  )
}

completeness_data <- derived %>%
  summarise(across(everything(), ~ mean(!is.na(.x)) * 100)) %>%
  pivot_longer(everything(), names_to = "variable", values_to = "completeness_percent") %>%
  filter(variable != "patient_id") %>%
  arrange(completeness_percent) %>%
  slice_head(n = 25) %>%
  mutate(variable = str_replace_all(variable, "_", " ")) %>%
  mutate(variable = fct_reorder(variable, completeness_percent))

if (nrow(completeness_data) > 0) {
  completeness_plot <- completeness_data %>%
    ggplot(aes(x = variable, y = completeness_percent)) +
    geom_col(width = 0.7) +
    coord_flip() +
    labs(
      title = "Completeness of engineered clinical variables",
      subtitle = "Lowest-completeness engineered variables shown first",
      x = NULL,
      y = "Completeness (%)"
    ) +
    ylim(0, 100) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title.position = "plot",
      panel.grid.major.y = element_blank()
    )

  ggsave(
    filename = file.path(figures_dir, "clinical-variable-completeness.png"),
    plot = completeness_plot,
    width = 9,
    height = 7,
    dpi = 300
  )
}

message("Clinical variable visualizations written to ", figures_dir)
