#!/usr/bin/env Rscript

################################################
## LOAD LIBRARIES                             ##
################################################

library(optparse)
library(ComplexHeatmap)
library(viridis)
library(tidyverse)

################################################
## VALIDATE COMMAND-LINE PARAMETERS           ##
################################################

option_list <- list(
  make_option(c("-i", "--input_files"), type = "character", default = NULL,
              help = "Comma-separated list of mosdepth regions output file (typically end in *.regions.bed.gz)",
              metavar = "input_files"),
  make_option(c("-s", "--input_suffix"), type = "character", default = '.regions.bed.gz',
              help = "Portion of filename after sample name to trim for plot title e.g. '.regions.bed.gz' if 'SAMPLE1.regions.bed.gz'",
              metavar = "input_suffix"),
  make_option(c("-o", "--output_dir"), type = "character", default = './',
              help = "Output directory", metavar = "path"),
  make_option(c("-p", "--output_suffix"), type = "character", default = 'regions',
              help = "Output suffix", metavar = "output_suffix"),
  make_option(c("-r", "--regions_prefix"), type = "character", default = NULL,
              help = "Replace this prefix from region names before plotting",
              metavar = "regions_prefix")
)

opt_parser <- OptionParser(option_list = option_list)
opt <- parse_args(opt_parser)

## Check input files
INPUT_FILES <- unique(unlist(strsplit(opt$input_files, ",")))
if (length(INPUT_FILES) == 0) {
  print_help(opt_parser)
  stop("At least one input file must be supplied", call. = FALSE)
}
if (!all(file.exists(INPUT_FILES))) {
  stop(paste("The following input files don't exist:", 
             paste(INPUT_FILES[!file.exists(INPUT_FILES)], collapse = ' ')), 
       call. = FALSE)
}

## Check the output directory has a trailing slash, if not add one
OUTDIR <- opt$output_dir
if (tail(strsplit(OUTDIR, "")[[1]], 1) != "/") {
  OUTDIR <- paste(OUTDIR, "/", sep = '')
}
## Create the directory if it doesn't already exist
if (!file.exists(OUTDIR)) {
  dir.create(OUTDIR, recursive = TRUE)
}

OUTSUFFIX <- trimws(opt$output_suffix, "both", whitespace = "\\.")

################################################
## READ IN DATA                               ##
################################################

## Read in data
dat <- NULL
for (input_file in INPUT_FILES) {
  sample <- gsub(opt$input_suffix, '', basename(input_file))
  dat <- rbind(dat, cbind(read.delim(input_file, header = FALSE, sep = '\t', 
                           stringsAsFactors = FALSE, check.names = FALSE)[, -6], 
                     sample, stringsAsFactors = FALSE))
}

## Reformat table
if (ncol(dat) == 6) {
  colnames(dat) <- c('chrom', 'start', 'end', 'region', 'coverage', 'sample')
  if (!is.null(opt$regions_prefix)) {
    dat$region <- as.character(gsub(opt$regions_prefix, '', dat$region))
  }
  dat$region <- factor(dat$region, levels = unique(dat$region[order(dat$start)]))
} else {
  stop("Input files must have region information (6 columns) for heatmap generation", 
       call. = FALSE)
}
dat$sample <- factor(dat$sample, levels = sort(unique(dat$sample)))

################################################
## REGION-BASED HEATMAP ACROSS ALL SAMPLES    ##
################################################

mat <- spread(dat[, c("sample", "region", "coverage")], sample, coverage, 
              fill = NA, convert = FALSE)
rownames(mat) <- mat[, 1]
mat <- t(as.matrix(log10(mat[, -1] + 1)))

# Adjust heatmap parameters based on number of samples
if (nrow(mat) > 1) {
  cluster_rows <- TRUE
  row_names_side <- "right"
} else {
  cluster_rows <- FALSE
  row_names_side <- "left"
}

heatmap <- Heatmap(
  mat,
  column_title = "Amplicon Median Coverage Heatmap",
  name = "read depth",
  cluster_rows = cluster_rows,
  cluster_columns = FALSE,
  show_row_names = TRUE,
  show_column_names = TRUE,
  column_title_side = "top",
  column_names_side = "bottom",
  row_names_side = row_names_side,
  rect_gp = gpar(col = "white", lwd = 1),
  show_heatmap_legend = TRUE,
  heatmap_legend_param = list(
    title_gp = gpar(fontsize = 12, fontface = "bold"),
    labels_gp = gpar(fontsize = 10),
    direction = "horizontal",
    at = c(0, 1, 2, 3),
    labels = c("0", "10", "100", "1000")
  ),
  column_title_gp = gpar(fontsize = 14, fontface = "bold"),
  row_names_gp = gpar(fontsize = 10, fontface = "bold"),
  column_names_gp = gpar(fontsize = 10, fontface = "bold"),
  height = unit(5, "mm") * nrow(mat),
  width = unit(5, "mm") * ncol(mat),
  col = viridisLite::cividis(50)
)

## Size of heatmaps scaled based on matrix dimensions
height <- 0.1969 * nrow(mat) + (2 * 1.5)
width <- 0.1969 * ncol(mat) + (2 * 1.5)
outfile <- paste(OUTDIR, "all_samples.", OUTSUFFIX, ".heatmap.pdf", sep = '')
pdf(file = outfile, height = height, width = width)
draw(heatmap, heatmap_legend_side = "bottom")
dev.off()

## Write heatmap to file
if (nrow(mat) > 1) {
  mat <- mat[row_order(heatmap), ]
}
outfile <- paste(OUTDIR, "all_samples.", OUTSUFFIX, ".heatmap.tsv", sep = '')
write.table(cbind(sample = rownames(mat), mat), 
            file = outfile, 
            row.names = FALSE, 
            col.names = TRUE, 
            sep = "\t", 
            quote = FALSE)