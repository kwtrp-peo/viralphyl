#!/usr/bin/env python3

import json
import argparse
import os
import sys
import csv

def parse_args():
    parser = argparse.ArgumentParser(description="Convert JSON classification files to a filtered TSV report.")
    parser.add_argument("-i", "--input-file", nargs='+', required=True, help="Input JSON file(s)")
    parser.add_argument("--min_reads", type=int, default=500, help="Minimum read count threshold (default: 500)")
    parser.add_argument("--output", type=str, default=None, help="Output TSV file (default: stdout)")
    return parser.parse_args()

def yield_rows(file_path, min_reads):
    with open(file_path) as f:
        data = json.load(f)

    sample_name = data.get("Sample", os.path.splitext(os.path.basename(file_path))[0])
    total_reads = data.get("Total_Reads", "")
    classified_reads = data.get("Classified_Reads", "")

    for taxon in data.get("Taxa", []):
        if taxon["Count"] >= min_reads:
            yield {
                "Sample ID": sample_name,
                "Taxid": taxon["TaxID"],
                "Pathogen Name": taxon["Name"],
                "Pathogen Reads": taxon["Count"],
                "Rel_Abundance % ( classfied)": taxon["Classified_Percentage"],
                "Abs_Abundance % (Total Reads)": taxon["Total_Percentage"],
                "Classified Reads": classified_reads,
                "Total Reads": total_reads
            }

def main():
    args = parse_args()
    fieldnames = [
        "Sample ID", "Taxid", "Pathogen Name", "Total Reads",
         "Classified Reads", "Pathogen Reads",
        "Rel_Abundance % ( classfied)", "Abs_Abundance % (Total Reads)"
        
    ]

    output_stream = open(args.output, 'w', newline='') if args.output else sys.stdout
    writer = csv.DictWriter(output_stream, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()

    for json_file in args.input_file:
        for row in yield_rows(json_file, args.min_reads):
            writer.writerow(row)

    if args.output:
        output_stream.close()

if __name__ == "__main__":
    main()
