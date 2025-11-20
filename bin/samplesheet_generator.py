#!/usr/bin/env python

from pathlib import Path
import re
import argparse
import pandas as pd
import sys
from typing import Optional, Union
from dateutil import parser as date_parser  # Renamed to avoid conflicts

__author__ = "Samuel Odoyo"
__email__ = "samordil@gmail.com"
__version__ = "1.2.3"
__license__ = "MIT"


def standardize_date(date_str: str) -> str:
    """Convert various date formats to YYYY-MM-DD, assuming DD/MM/YYYY when ambiguous."""
    if not date_str or date_str in ["NA", "nan", "None"]:
        return "NA"

    date_str = date_str.strip()

    try:
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"

        for sep in ["/", "-"]:
            parts = date_str.split(sep)
            if len(parts) == 2 and parts[0].isdigit() and len(parts[0]) == 4:
                return f"{parts[0]}-{parts[1].zfill(2)}-01"

        if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
            day, month, year = date_str.split("/")
            return f"{year}-{month}-{day}"

        return date_parser.parse(date_str, dayfirst=True).strftime("%Y-%m-%d")

    except (ValueError, TypeError):
        print(f"⚠ WARNING: Could not parse date '{date_str}', setting to 'NA'.")
        return "NA"


def normalize_barcode(barcode: str) -> str:
    """Normalize barcode to 'barcodeXX' format."""
    barcode = barcode.lower().replace("barcode", "").strip()
    if barcode.isdigit():
        barcode = barcode.zfill(2)
    return f"barcode{barcode}"


def find_barcode_dirs(base_dir: Union[str, Path]) -> list[str]:
    """Recursively find all barcode directories with format 'barcodeXX'."""
    base_path = Path(base_dir).resolve()
    barcode_dirs: list[str] = []

    barcode_pattern = re.compile(r"^barcode\d{2}$", re.IGNORECASE)
    run_pattern = re.compile(r"(?i)(?:[\w.\-]*[-_]*)?(run\d+)(?:[-_][\w.\-]*)?")

    for barcode_dir in base_path.rglob("barcode*"):
        if not barcode_dir.is_dir():
            continue
        if "fastq_fail" in barcode_dir.parts:
            continue

        # Allow directories where any parent matches the run pattern
        if not any(run_pattern.match(p) for p in barcode_dir.parts):
            continue

        if barcode_pattern.match(barcode_dir.name):
            barcode_dirs.append(str(barcode_dir.resolve()))

    return barcode_dirs


def extract_run_name(path: Union[str, Path]) -> Optional[str]:
    """Extract sequencing run name from directory path."""
    match = re.search(r"(?i)(?:\w*[-_]*)?(run\d+)(?:[-_]\w*)?", str(path))
    return match.group(1).lower() if match else None


def load_metadata(metadata_file: Union[str, Path]) -> pd.DataFrame:
    """Load metadata, ensure required columns exist."""
    metadata_path = Path(metadata_file)

    if not metadata_path.exists():
        print(f"ERROR: Metadata file '{metadata_file}' does not exist!")
        sys.exit(1)

    if metadata_path.stat().st_size == 0:
        print(f"ERROR: Metadata file '{metadata_file}' is empty!")
        sys.exit(1)

    try:
        metadata = pd.read_csv(metadata_path, sep="\t", dtype=str).fillna("NA")
    except (pd.errors.EmptyDataError, pd.errors.ParserError):
        print(f"ERROR: Metadata file '{metadata_file}' is not a valid TSV file!")
        sys.exit(1)

    required_cols = {"sequence_run", "barcode_num", "sample_id"}
    missing_cols = required_cols - set(metadata.columns)
    if missing_cols:
        print(f"ERROR: Metadata file is missing required columns: {', '.join(missing_cols)}")
        sys.exit(1)

    metadata["barcode_num"] = metadata["barcode_num"].apply(normalize_barcode)
    metadata.set_index(["barcode_num", "sequence_run"], inplace=True)
    metadata = metadata.sort_index()
    return metadata


def generate_samplesheet(
    base_dir: Union[str, Path],
    metadata_file: Optional[Union[str, Path]],
    output_file: Union[str, Path],
    output_format: str,
    missing_value: str
) -> None:
    """Generate samplesheet with metadata validation and barcode normalization."""
    metadata: Optional[pd.DataFrame] = None
    if metadata_file:
        metadata = load_metadata(metadata_file)

    barcode_dirs = find_barcode_dirs(base_dir)

    if not barcode_dirs:
        print(f"\u274c ERROR: No valid 'barcodeXX' directories found in {base_dir}.")
        sys.exit(1)

    samplesheet_data: list[list[str]] = []
    missing_metadata_entries: list[list[str]] = []
    optional_columns: set[str] = set()

    for barcode_path in barcode_dirs:
        barcode_path = Path(barcode_path)
        run_name = extract_run_name(barcode_path)
        barcode = normalize_barcode(barcode_path.name)
        sample_name = f"{run_name}_{barcode}" if run_name else barcode
        strain_id = sample_name.replace("barcode", "bc")

        if metadata is not None and (barcode, run_name) in metadata.index:
            row = metadata.loc[(barcode, run_name)]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]

            sample_id_value = str(row.get("sample_id", missing_value)).strip()
            collection_date_value = standardize_date(str(row.get("collection_date", missing_value)).strip())

            optional_metadata = {
                col: str(row.get(col, missing_value)).strip()
                for col in metadata.columns if col not in {"sample_id", "collection_date"}
            }
            optional_columns.update(optional_metadata.keys())

            if missing_value in {sample_id_value, collection_date_value}:
                missing_metadata_entries.append(
                    [run_name if run_name else "unknown", barcode, sample_id_value, collection_date_value]
                    + list(optional_metadata.values())
                )
                continue

            strain_id = f"{sample_id_value}"
            samplesheet_data.append(
                [sample_name, strain_id, str(barcode_path), sample_id_value, collection_date_value]
                + list(optional_metadata.values())
            )
        elif metadata is not None:
            missing_metadata_entries.append(
                [run_name if run_name else "unknown", barcode, missing_value, missing_value]
                + [missing_value] * len(optional_columns)
            )
        else:
            samplesheet_data.append(
                [sample_name, strain_id, str(barcode_path), missing_value, missing_value]
                + [missing_value] * len(optional_columns)
            )

    if metadata is not None and missing_metadata_entries:
        missing_df = pd.DataFrame(
            missing_metadata_entries,
            columns=["sequence_run", "barcode_num", "sample_id", "collection_date"] + list(optional_columns)
        )
        missing_df.to_csv("sample_without_metadata.csv", index=False)
        print("\n⚠ WARNING: Some samples had missing required metadata and were excluded. Logged in 'sample_without_metadata.csv'.")

    if not samplesheet_data:
        print("\u274c ERROR: No valid sample entries found. Check metadata and directory structure!")
        sys.exit(1)

    columns = ["sample", "strain_id", "fastq_dir", "sample_id", "collection_date"] + list(optional_columns)
    samplesheet_df = pd.DataFrame(samplesheet_data, columns=columns)

    output_path = Path(output_file)
    if output_format == "tsv":
        samplesheet_df.to_csv(output_path, index=False, sep="\t")
    else:
        samplesheet_df.to_csv(output_path, index=False)

    print(f"\n SUCCESS: Samplesheet generated: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a samplesheet for sequencing runs.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("-d", "--directory", required=True, help="Base directory containing sequencing runs.")
    parser.add_argument("-m", "--metadata", required=False, help="Metadata TSV file (optional).")
    parser.add_argument("-o", "--output", required=False, default="samplesheet.csv", help="Output samplesheet file (default: samplesheet.csv).")
    parser.add_argument("--format", choices=["csv", "tsv"], default="csv", help="Output format (default: csv).")
    parser.add_argument("--missing-value", default="NA", help="Placeholder for missing metadata values (default: NA).")

    args = parser.parse_args()
    generate_samplesheet(args.directory, args.metadata, args.output, args.format, args.missing_value)