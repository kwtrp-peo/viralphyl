#!/usr/bin/env python3

import argparse
import json
import csv
import logging
import sys
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert multiple JSON files to a formatted TSV file.")
    parser.add_argument(
        "--input_json",
        nargs="+",
        required=True,
        help="One or more input JSON files"
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output TSV file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging"
    )
    return parser.parse_args()

def read_json_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.warning(f"Skipping invalid JSON in {filepath}: {e}")
    except Exception as e:
        logging.warning(f"Skipping unreadable file {filepath}: {e}")
    return {}

def main():
    args = parse_arguments()

    # Set logging level
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.ERROR,
        format="%(levelname)s: %(message)s"
    )

    column_map = {
        "sample_id": "Sample",
        "taxid": "Taxid",
        "organism": "Organism",
        "total": "Total Reads",
        "mapped": "Mapped Reads",
        "mapped_percent": "Mapped Reads %",
        "ref_id": "Ref Accession",
        "genome_coverage": "Genome Coverage"
    }

    ordered_keys = [
        "sample_id",
        "taxid",
        "organism",
        "total",
        "mapped",
        "mapped_percent",
        "genome_coverage",
        "ref_id"
    ]

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    try:
        with open(args.output, "w", newline="", encoding="utf-8") as tsvfile:
            writer = csv.writer(tsvfile, delimiter="\t")
            writer.writerow([column_map.get(key, key) for key in ordered_keys])

            valid_count = 0
            for filepath in args.input_json:
                data = read_json_file(filepath)
                if data:
                    writer.writerow([data.get(key, "") for key in ordered_keys])
                    valid_count += 1

        if valid_count == 0:
            logging.error("No valid JSON files found. Output file will be empty.")
            sys.exit(2)

        sys.exit(0)

    except Exception as e:
        logging.error(f"Failed to write output TSV: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
