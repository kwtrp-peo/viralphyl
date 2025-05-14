#!/usr/bin/env python3
import argparse
import sys
import glob
import os
from csv import reader, writer

def safe_glob(patterns):
    """Expand file patterns safely (skip bad patterns)"""
    files = []
    for pattern in patterns:
        try:
            files.extend(glob.glob(pattern))
        except:
            continue
    return sorted(files)  # Deterministic order

def get_column_indices(header, required_cols):
    """Case-insensitive column index mapping with fallback"""
    header_lower = [h.lower() for h in header]
    return {
        col: header_lower.index(col.lower()) if col.lower() in header_lower else None
        for col in required_cols
    }

def process_file(input_path, output_handle, required_cols, write_header=True):
    """Process a TSV file line-by-line with rigorous validation"""
    with open(input_path, 'r', newline='') as f:
        csv_reader = reader(f, delimiter='\t')
        try:
            header = next(csv_reader)
        except StopIteration:
            return  # Skip empty files

        col_indices = get_column_indices(header, required_cols)
        csv_writer = writer(output_handle, delimiter='\t')

        if write_header:
            csv_writer.writerow(required_cols)

        for row in csv_reader:
            try:
                output_row = [
                    row[col_indices[col]] if col_indices[col] is not None and col_indices[col] < len(row) else 'Unspecified'
                    for col in required_cols
                ]
                csv_writer.writerow(output_row)
            except Exception as e:
                sys.stderr.write(f"WARNING: Skipping malformed row in {input_path}: {str(e)}\n")
                continue

def main():
    REQUIRED_COLS = ['strain', 'country', 'region', 'date', 'genotype']

    parser = argparse.ArgumentParser(description='Pipeline-safe TSV combiner')
    parser.add_argument('--tsv', nargs='+', required=True, help='Input files/patterns')
    parser.add_argument('-o', '--output', required=True, help='Output file')
    args = parser.parse_args()

    # Safely handle input files
    input_files = safe_glob(args.tsv)
    if not input_files:
        sys.stderr.write("ERROR: No valid input files found\n")
        sys.exit(1)

    # Atomic write to output (safer for pipelines)
    tmp_output = f"{args.output}.tmp"
    try:
        with open(tmp_output, 'w', newline='') as out_file:
            for i, input_file in enumerate(input_files):
                process_file(
                    input_file,
                    out_file,
                    REQUIRED_COLS,
                    write_header=(i == 0)  # Header only once
                )
        os.replace(tmp_output, args.output)  # Atomic operation
    except Exception as e:
        sys.stderr.write(f"CRITICAL: {str(e)}\n")
        if os.path.exists(tmp_output):
            os.unlink(tmp_output)
        sys.exit(1)

if __name__ == "__main__":
    main()