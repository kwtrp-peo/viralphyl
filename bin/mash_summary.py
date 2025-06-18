#!/usr/bin/env python3

"""
summarize_mash.py

Description:
------------
Parse and summarize MASH result files. For each input file, the script:
- Sorts the lines numerically by the first column (descending), equivalent to `sort -gr`
- Extracts the top N hits
- Outputs a combined summary TSV file with sample name, identity, coverage, and organism info.

Usage:
------
$ python summarize_mash.py -i sample1.txt sample2.txt -o summary.tsv -n 5

Arguments:
----------
-i / --input       One or more MASH result files to process
-o / --output      Output TSV file to write the summary
-n / --num_lines   Number of top hits to extract from each file (default: 3)
"""

import argparse
import pandas as pd
from pathlib import Path
import logging
import sys

def setup_logging():
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Summarize MASH results across multiple files.")
    parser.add_argument(
        "-i", "--input", nargs="+", required=True,
        help="List of MASH result files to process"
    )
    parser.add_argument(
        "-o", "--output", required=True,
        help="Output TSV file to write the summary"
    )
    parser.add_argument(
        "-n", "--num_lines", type=int, default=3,
        help="Number of top lines to extract per file (default: 3)"
    )
    return parser.parse_args()

def process_file(file_path, num_lines):
    """
    Process a single MASH result file.

    Parameters:
    -----------
    file_path : str or Path
        Path to the input MASH result file
    num_lines : int
        Number of top hits to extract

    Returns:
    --------
    list of list
        Extracted rows as lists of [sample, identity, coverage, organism]
    """
    rows = []
    try:
        sample_name = Path(file_path).stem.split('.')[0]

        with open(file_path, "r") as f:
            lines = [line.strip().split("\t") for line in f if line.strip()]

        valid_lines = [line for line in lines if len(line) >= 6]

        if not valid_lines:
            logging.warning(f"No valid data in file: {file_path}")
            return rows

        # Sort like `sort -gr` — numerically by first column, descending
        sorted_lines = sorted(valid_lines, key=lambda x: float(x[0]), reverse=True)

        top_lines = sorted_lines[:num_lines]

        for i, line in enumerate(top_lines):
            organism_info = " ".join(line[5:]).strip()
            rows.append([
                sample_name if i == 0 else "",
                line[0],  # identity
                line[1],  # coverage
                organism_info
            ])

        rows.append(["", "", "", ""])  # Separator

    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
    
    return rows

def write_output(summary_data, output_path):
    """
    Write the summary data to a TSV file.

    Parameters:
    -----------
    summary_data : list of list
        The collected rows to write
    output_path : str
        Path to the output TSV file
    """
    try:
        df = pd.DataFrame(summary_data, columns=["Sample", "Identity", "Coverage", "Organism Found"])
        df.to_csv(output_path, sep="\t", index=False)
        logging.info(f"Summary written to {output_path}")
    except Exception as e:
        logging.error(f"Failed to write output file {output_path}: {e}")
        sys.exit(1)

def main():
    setup_logging()
    args = parse_arguments()

    summary_data = []
    for file_path in args.input:
        if not Path(file_path).exists():
            logging.warning(f"Skipping missing file: {file_path}")
            continue

        rows = process_file(file_path, args.num_lines)
        summary_data.extend(rows)

    if not summary_data:
        logging.error("No valid data to write. Exiting.")
        sys.exit(1)

    write_output(summary_data, args.output)

if __name__ == "__main__":
    main()
