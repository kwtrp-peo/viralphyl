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
__version__ = "1.2.4"
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
        print(f"WARNING: Could not parse date '{date_str}', setting to 'NA'.")
        return "NA"


def normalize_barcode(barcode: str) -> str:
    """Normalize barcode to 'barcodeXX' format."""
    barcode = barcode.lower().replace("barcode", "").strip()
    if barcode.isdigit():
        barcode = barcode.zfill(2)
    return f"barcode{barcode}"


def find_barcode_dirs(base_dir: Union[str, Path]) -> list[str]:
    """Find barcode directories with optimized pathlib usage."""
    base_path = Path(base_dir).resolve()
    if not base_path.is_dir():
        print(f"WARNING: {base_dir} is not a directory or does not exist")
        return []
    
    barcode_dirs = []
    base_str = str(base_path)
    run_regex = re.compile(r'run\d+', re.IGNORECASE)
    
    # Helper: Check single directory
    def is_valid_barcode_dir(dir_path: Path, is_base: bool = False) -> bool:
        """Check if directory meets all criteria."""
        # Fast name check
        name = dir_path.name.lower()
        if not (name.startswith("barcode") and len(name) == 9 and name[7:].isdigit()):
            return False
        
        # Skip if not base and same as base
        if not is_base and str(dir_path) == base_str:
            return False
        
        # Skip fastq_fail
        if "fastq_fail" in dir_path.parts:
            return False
        
        # Check for run in path
        if not run_regex.search(str(dir_path)):
            return False
        
        # Check for FASTQ files (most expensive)
        for pattern in ["*.fastq.gz", "*.fq.gz", "*.fastq", "*.fq"]:
            if next(dir_path.glob(pattern), None):
                return True
        return False
    
    # Check base directory
    if is_valid_barcode_dir(base_path, is_base=True):
        barcode_dirs.append(base_str)
    
    # Search subdirectories with filesystem filtering
    for candidate in base_path.rglob("barcode[0-9][0-9]"):
        if candidate.is_dir() and is_valid_barcode_dir(candidate, is_base=False):
            barcode_dirs.append(str(candidate.resolve()))
    
    return barcode_dirs


def extract_run_name(path: Union[str, Path]) -> Optional[str]:
    """Extract sequencing run name from directory path."""
    match = re.search(r'run\d+', str(path), re.IGNORECASE)
    return match.group(0).lower() if match else None


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
    
    # FIRST: Collect ALL optional columns from ALL metadata entries
    optional_columns: set[str] = set()
    if metadata is not None:
        for barcode_path in barcode_dirs:
            barcode_path = Path(barcode_path)
            run_name = extract_run_name(barcode_path)
            barcode = normalize_barcode(barcode_path.name)
            
            if (barcode, run_name) in metadata.index:
                row = metadata.loc[(barcode, run_name)]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
                # Add all columns except the required ones
                optional_columns.update(
                    col for col in metadata.columns 
                    if col not in {"sample_id", "collection_date"}
                )
    
    # Convert to sorted list for consistent ordering
    optional_columns_sorted = sorted(optional_columns)
    
    # SECOND: Process each barcode directory
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

            # Create ordered optional metadata using the sorted columns
            optional_metadata = [
                str(row.get(col, missing_value)).strip()
                for col in optional_columns_sorted
            ]

            if missing_value in {sample_id_value, collection_date_value}:
                missing_metadata_entries.append(
                    [run_name if run_name else "unknown", barcode, sample_id_value, collection_date_value]
                    + optional_metadata
                )
                continue

            strain_id = f"{sample_id_value}"
            samplesheet_data.append(
                [sample_name, strain_id, str(barcode_path), sample_id_value, collection_date_value]
                + optional_metadata
            )
        elif metadata is not None:
            # All missing metadata entries get the same number of optional columns
            missing_metadata_entries.append(
                [run_name if run_name else "unknown", barcode, missing_value, missing_value]
                + [missing_value] * len(optional_columns_sorted)
            )
        else:
            # No metadata provided
            samplesheet_data.append(
                [sample_name, strain_id, str(barcode_path), missing_value, missing_value]
                + [missing_value] * len(optional_columns_sorted)
            )

    if metadata is not None and missing_metadata_entries:
        missing_df = pd.DataFrame(
            missing_metadata_entries,
            columns=["sequence_run", "barcode_num", "sample_id", "collection_date"] + optional_columns_sorted
        )
        missing_df.to_csv("sample_without_metadata.csv", index=False)
        print("\nWARNING: Some samples had missing required metadata and were excluded. Logged in 'sample_without_metadata.csv'.")

    if not samplesheet_data:
        print("\u274c ERROR: No valid sample entries found. Check metadata and directory structure!")
        sys.exit(1)

    columns = ["sample", "strain_id", "fastq_dir", "sample_id", "collection_date"] + optional_columns_sorted
    samplesheet_df = pd.DataFrame(samplesheet_data, columns=columns)

    output_path = Path(output_file)
    if output_format == "tsv":
        samplesheet_df.to_csv(output_path, index=False, sep="\t")
    else:
        samplesheet_df.to_csv(output_path, index=False)

    print(f"\n SUCCESS: Samplesheet generated: {output_path}")
    print(f"   - Total samples: {len(samplesheet_data)}")
    if metadata is not None and missing_metadata_entries:
        print(f"   - Samples excluded (missing metadata): {len(missing_metadata_entries)}")


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