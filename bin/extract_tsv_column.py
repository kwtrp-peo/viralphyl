#!/usr/bin/env python3

import pandas as pd
import argparse
import sys

def main():
    # Set up command-line argument parser
    parser = argparse.ArgumentParser(description='Extract columns from a TSV file')
    parser.add_argument('-i', '--input', required=True,
                        help='Path to the input TSV file [required]')
    parser.add_argument('-c', '--column', required=True,
                        help='Comma-separated list of columns to extract [required]')
    parser.add_argument('-o', '--output', default='output_file.txt',
                        help='Path to the output file (default: output_file.txt)')
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Load the input TSV file
        data = pd.read_csv(args.input, sep='\t')
        
        # Split the column names by comma and strip whitespace
        columns = [col.strip() for col in args.column.split(',')]
        
        # Check if the specified columns exist in the data
        missing_columns = set(columns) - set(data.columns)
        if missing_columns:
            sys.exit(f"Error: The following columns are missing in the input file: {', '.join(missing_columns)}")
        
        # Extract the specified columns
        extracted_data = data[columns]
        
        # Write the extracted data to the output file (without header)
        extracted_data.to_csv(args.output, sep='\t', index=False, header=False)
        
        print(f"Column extraction complete. Output saved to: {args.output}")
        
    except Exception as e:
        sys.exit(f"Error: {str(e)}")

if __name__ == "__main__":
    main()