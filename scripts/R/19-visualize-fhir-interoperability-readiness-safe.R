#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(readr)
  library(dplyr)
  library(ggplot2)
  library(forcats)
})

input_file <- "results/interoperability/fhir-resource-mapping.tsv"
figure_dir <- "results/figures"

dir.create(figure_dir, recursive = TRUE, showWarnings = FALSE)

write_skip_note <- function(path, message_text) {
  writeLines(message_text, con = path)
}

if (!file.exists(input_file)) {
  write_skip_note(
    file.path(figure_dir, "fhir-resource-mapping-summary-skipped.txt"),
    paste("Skipped FHIR resource mapping summary because input file was not found:", input_file)
  )
  message("Wrote skip note to: ", figure_dir)
  quit(save = "no", status = 0)
}

df <- read_tsv(input_file, show_col_types = FALSE)

if (!all(c("candidate_fhir_resource", "mapping_status") %in% names(df))) {
  write_skip_note(
    file.path(figure_dir, "fhir-resource-mapping-summary-skipped.txt"),
    "Skipped FHIR resource mapping summary because required columns were not found."
  )
  message("Wrote skip note to: ", figure_dir)
  quit(save = "no", status = 0)
}

plot_df <- df %>%
  mutate(
    candidate_fhir_resource = as.character(candidate_fhir_resource),
    mapping_status = as.character(mapping_status)
  ) %>%
  filter(!is.na(candidate_fhir_resource), candidate_fhir_resource != "") %>%
  count(candidate_fhir_resource, mapping_status, name = "mapping_count")

if (nrow(plot_df) == 0) {
  write_skip_note(
    file.path(figure_dir, "fhir-resource-mapping-summary-skipped.txt"),
    "Skipped FHIR resource mapping summary because no usable mapping rows were available."
  )
  message("Wrote skip note to: ", figure_dir)
  quit(save = "no", status = 0)
}

plot_df <- plot_df %>%
  mutate(candidate_fhir_resource = fct_reorder(candidate_fhir_resource, mapping_count, .fun = sum))

p <- ggplot(plot_df, aes(x = candidate_fhir_resource, y = mapping_count, fill = mapping_status)) +
  geom_col(width = 0.7) +
  coord_flip() +
  labs(
    title = "FHIR resource mapping summary",
    subtitle = "Conceptual mapping coverage from local clinical tables to candidate FHIR resources",
    x = "Candidate FHIR resource",
    y = "Mapping count",
    fill = "Mapping status"
  ) +
  theme_minimal(base_size = 12)

ggsave(
  filename = file.path(figure_dir, "fhir-resource-mapping-summary.png"),
  plot = p,
  width = 9,
  height = 5.5,
  dpi = 300
)

message("Wrote figure to: ", figure_dir)
