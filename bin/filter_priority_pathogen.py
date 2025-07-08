#!/usr/bin/env python3
"""
Standard taxid-based Kraken report filter

Follows bioinformatics conventions:
1. Single-pass streaming for memory efficiency
2. Minimal validation (assumes proper inputs)
3. TSV handling with csv module
4. Clear exit codes and stderr messaging
"""

import argparse
import csv
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="Filter Kraken report by taxids",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Example:
  %(prog)s -k kraken.tsv -t taxids.tsv -o filtered.tsv
"""
    )
    
    parser.add_argument('-k', '--kraken', required=True,
                      help='Kraken report (TSV with taxid column)')
    parser.add_argument('-t', '--taxonkit', required=True,
                      help='TaxonKit output (TSV with name<tab>taxid)')
    parser.add_argument('-o', '--output', required=True,
                      help='Filtered output TSV')
    
    args = parser.parse_args()

    # Validate inputs
    if not Path(args.kraken).is_file():
        sys.exit(f"ERROR: File not found: {args.kraken}")
    if not Path(args.taxonkit).is_file():
        sys.exit(f"ERROR: File not found: {args.taxonkit}")

    try:
        # Load taxids (simple and efficient)
        with open(args.taxonkit) as f:
            taxids = {row[1] for row in csv.reader(f, delimiter='\t') if len(row) > 1}

        # Process Kraken report
        with open(args.kraken) as infile, open(args.output, 'w') as outfile:
            reader = csv.reader(infile, delimiter='\t')
            writer = csv.writer(outfile, delimiter='\t')
            
            try:
                header = next(reader)
                taxid_col = header.index('taxid')
                writer.writerow(header)
                
                kept = 0
                for row in reader:
                    if len(row) > taxid_col and row[taxid_col] in taxids:
                        writer.writerow(row)
                        kept += 1
                        
                print(f"Kept {kept} records", file=sys.stderr)
                
            except ValueError:
                sys.exit("ERROR: Missing 'taxid' column in Kraken report")
                
    except Exception as e:
        sys.exit(f"ERROR: {str(e)}")

if __name__ == "__main__":
    main()