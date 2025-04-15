#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
from functools import reduce

def read_and_clean_file(file_path):
    """Read and clean a single file, dropping fastq_dir and standardizing NA values."""
    try:
        df = pd.read_csv(file_path, sep=None, engine='python', na_values=['', 'NA', 'N/A'])
        return df.drop(columns=['fastq_dir'], errors='ignore').replace(r'^\s*$', pd.NA, regex=True)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def combine_files(input_files, output_file, key_field='strain_id', sort_by='coverage_percent'):
    """
    Combine TSV/CSV files with optimized processing:
    - Efficient file reading and cleaning
    - Memory-efficient merging
    - Optional sorting with column validation
    - Proper NA handling
    """
    # Read and clean all files in one go using list comprehension
    dfs = [df for df in (read_and_clean_file(f) for f in input_files) if df is not None]
    
    if not dfs:
        print("No valid files to process!")
        return

    try:
        # Proper merging of multiple dataframes
        combined = reduce(lambda left, right: pd.merge(
            left, 
            right, 
            on=key_field, 
            how='outer'
        ), dfs)

        # Remove completely empty columns more efficiently
        combined = combined.dropna(axis=1, how='all')

        # Optimized sorting with column validation
        if sort_by and sort_by in combined.columns:
            combined = combined.sort_values(
                by=sort_by,
                ascending=False,
                kind='mergesort'  # Stable sort
            )
            print(f"Sorted rows by '{sort_by}' in descending order")
        elif sort_by:
            print(f"Note: '{sort_by}' column not found - skipping sort")

        # Efficient NA handling
        combined = combined.fillna('NA')

        # Optimized file writing
        combined.to_csv(output_file, sep='\t', index=False, na_rep='NA')
        print(f"Created: {output_file} with {len(combined)} records from {len(dfs)} files")

    except KeyError:
        print(f"Error: Key column '{key_field}' missing")
        print("Available columns in first file:", list(dfs[0].columns))
        exit(1)
    except Exception as e:
        print(f"Merge error: {e}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Optimized TSV/CSV file merger with smart empty handling',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', nargs='+', required=True,
                       help='Input files (TSV/CSV)')
    parser.add_argument('-o', '--output', required=True,
                       help='Output TSV file')
    parser.add_argument('-k', '--key', default='strain_id',
                       help='Merge key column')
    parser.add_argument('-s', '--sort-by', default='coverage_percent',
                       help='Column to sort by (set to empty string to disable)')
    
    args = parser.parse_args()

    # Validate input files efficiently
    missing_files = [f for f in args.input if not Path(f).exists()]
    if missing_files:
        print(f"Error: Missing files: {missing_files}")
        exit(1)
    
    combine_files(args.input, args.output, args.key, args.sort_by)

if __name__ == "__main__":
    main()