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

def get_column_indices(header, required_cols, aliases=None):
    """
    Case-insensitive column index mapping with optional aliases.
    For each required column, look for itself and any aliases.
    """
    if aliases is None:
        aliases = {}

    header_lower = [h.lower() for h in header]
    mapping = {}

    for col in required_cols:
        candidates = [col.lower()] + [alias.lower() for alias in aliases.get(col, [])]
        found_index = None
        for candidate in candidates:
            if candidate in header_lower:
                found_index = header_lower.index(candidate)
                break
        mapping[col] = found_index

    return mapping

def process_file(input_path, output_handle, required_cols, output_cols, aliases=None, write_header=True):
    """Process a TSV file line-by-line with rigorous validation"""
    with open(input_path, 'r', newline='') as f:
        csv_reader = reader(f, delimiter='\t')
        try:
            header = next(csv_reader)
        except StopIteration:
            return  # Skip empty files

        col_indices = get_column_indices(header, required_cols, aliases=aliases)

        csv_writer = writer(output_handle, delimiter='\t')

        if write_header:
            csv_writer.writerow(output_cols)

        for row in csv_reader:
            try:
                # Get values in order of REQUIRED_COLS
                output_row_raw = [
                    row[col_indices[col]] if col_indices[col] is not None and col_indices[col] < len(row) else 'Unspecified'
                    for col in required_cols
                ]

                # Map country → location in output
                output_row = []
                for out_col in output_cols:
                    if out_col == "location":
                        # pull from country position
                        country_idx = required_cols.index("country")
                        output_row.append(output_row_raw[country_idx])
                    else:
                        # same name in required_cols
                        idx = required_cols.index(out_col)
                        output_row.append(output_row_raw[idx])

                csv_writer.writerow(output_row)
            except Exception as e:
                sys.stderr.write(f"WARNING: Skipping malformed row in {input_path}: {str(e)}\n")
                continue

def main():
    REQUIRED_COLS = ['strain', 'country', 'region', 'date', 'genotype']
    OUTPUT_COLS = ['strain', 'location', 'region', 'date', 'genotype']

    # Define fallback/alias mappings here:
    ALIASES = {
        'date': ['collection_date'],
        'country': ['location']
    }

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
                    output_cols=OUTPUT_COLS,
                    aliases=ALIASES,
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
