#!/usr/bin/env Rscript

# Visualize missingness and completeness outputs.
# Run from the project root:
#   Rscript scripts/R/10-visualize-missingness-and-completeness.R

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
  library(stringr)
})

results_dir <- "results"
figures_dir <- file.path(results_dir, "figures")
dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)

domain_path <- file.path(results_dir, "missingness-domain-summary.tsv")
variable_path <- file.path(results_dir, "missingness-variable-summary.tsv")

if (!file.exists(domain_path)) {
  stop("Missing domain summary file: ", domain_path, call. = FALSE)
}

if (!file.exists(variable_path)) {
  stop("Missing variable summary file: ", variable_path, call. = FALSE)
}

domain_summary <- read_tsv(domain_path, show_col_types = FALSE)
variable_summary <- read_tsv(variable_path, show_col_types = FALSE)

if (nrow(domain_summary) > 0) {
  domain_plot <- domain_summary %>%
    mutate(domain = str_replace_all(domain, "_", " ")) %>%
    mutate(domain = fct_reorder(domain, average_completeness_percent)) %>%
    ggplot(aes(x = domain, y = average_completeness_percent)) +
    geom_col(width = 0.7) +
    coord_flip() +
    labs(
      title = "Clinical data completeness by domain",
      subtitle = "Average completeness across variables in each clinical data domain",
      x = NULL,
      y = "Average completeness (%)"
    ) +
    ylim(0, 100) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title.position = "plot",
      panel.grid.major.y = element_blank()
    )

  ggsave(
    filename = file.path(figures_dir, "missingness-domain-completeness.png"),
    plot = domain_plot,
    width = 9,
    height = 5.5,
    dpi = 300
  )
}

if (nrow(variable_summary) > 0) {
  top_missing <- variable_summary %>%
    arrange(desc(missing_percent)) %>%
    slice_head(n = 20) %>%
    mutate(variable_label = paste(dataset, variable, sep = " :: ")) %>%
    mutate(variable_label = fct_reorder(variable_label, missing_percent))

  variable_plot <- top_missing %>%
    ggplot(aes(x = variable_label, y = missing_percent)) +
    geom_col(width = 0.7) +
    coord_flip() +
    labs(
      title = "Variables with the highest missingness",
      subtitle = "Top 20 variables by missing percentage across available clinical input files",
      x = NULL,
      y = "Missing (%)"
    ) +
    ylim(0, 100) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title.position = "plot",
      panel.grid.major.y = element_blank()
    )

  ggsave(
    filename = file.path(figures_dir, "missingness-variable-top20.png"),
    plot = variable_plot,
    width = 10,
    height = 7,
    dpi = 300
  )
}

message("Missingness visualizations written to ", figures_dir)
