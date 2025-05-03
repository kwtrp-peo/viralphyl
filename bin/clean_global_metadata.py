#!/usr/bin/env python3

import pandas as pd
import argparse
import re
from datetime import datetime

def main():
    # Define command-line arguments
    parser = argparse.ArgumentParser(description='Clean metadata TSV file')
    parser.add_argument('-i', '--input_tsv', required=True,
                        help='Path to the input TSV file [required]')
    parser.add_argument('-o', '--output_file', default='cleaned_meta.tsv',
                        help='Path to the output cleaned TSV file (default: cleaned_meta.tsv)')
    parser.add_argument('-l', '--min_length', type=int, default=None,
                        help='Minimum length filter [optional]')
    parser.add_argument('-u', '--max_length', type=int, default=None,
                        help='Maximum length filter [optional]')

    args = parser.parse_args()

    # Load the input TSV file
    try:
        data = pd.read_csv(args.input_tsv, sep='\t')
    except FileNotFoundError:
        print(f"Error: Input file {args.input_tsv} not found.")
        exit(1)

    # Clean column names - modified to handle specific column names
    data.columns = data.columns.str.lower().str.replace(' ', '_')
    
    # Now the columns should be:
    # accession, geographic_location, geographic_region, isolate_collection_date, length

    # Drop rows where "isolate_collection_date" is NA
    data = data.dropna(subset=['isolate_collection_date'])

    # Apply length filtering
    if args.min_length is not None:
        data = data[data['length'] >= args.min_length]
    if args.max_length is not None:
        data = data[data['length'] <= args.max_length]

    # Create the "country" column
    data['country'] = data['geographic_location'].apply(
        lambda x: x.split(':')[0] if ':' in str(x) else x
    ).str.replace(' ', '_')

    # Rename the column geographic_region to region
    data = data.rename(columns={'geographic_region': 'region'})

    # Create a new "date" column in the format YYYY-MM-DD
    def parse_date(date_str):
        if pd.isna(date_str):
            return pd.NaT
        date_str = str(date_str)
        try:
            if re.match(r'^\d{4}$', date_str):
                return datetime.strptime(date_str + '-01-01', '%Y-%m-%d').date()
            elif re.match(r'^\d{4}-\d{2}$', date_str):
                return datetime.strptime(date_str + '-01', '%Y-%m-%d').date()
            else:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return pd.NaT

    data['date'] = data['isolate_collection_date'].apply(parse_date)
    
    # Create the "strain" column in format "accession|country|date"
    # data['strain'] = data.apply(
    #     lambda row: f"{row['accession']}|{row['country']}|{row['date']}",
    #     axis=1
    # )

    # Write the cleaned data to the output TSV file
    data.to_csv(args.output_file, sep='\t', index=False)

    # Inform the user that the script has completed
    print(f"Data cleaning complete. Output saved to: {args.output_file}")

if __name__ == '__main__':
    main()