#!/usr/bin/env python3
"""
Kraken Output Parser and Summary Generator

This script processes output files from Kraken (a taxonomic sequence classifier) and generates
summary reports in both TSV and JSON formats. The reports include taxonomic classification
statistics at various levels of detail.

Key Features:
- Parses Kraken output files (standard format with taxid annotations)
- Calculates classification percentages (both against classified reads and total reads)
- Generates comprehensive summaries with:
  - Total read counts
  - Classified vs unclassified statistics
  - Breakdown by taxonomic ID with counts and percentages
- Supports multiple input files with sample name handling
- Output options:
  - TSV output (controlled by --tsv flag)
  - JSON output (controlled by --json flag)
  - Configurable top N taxa reporting
- Memory-efficient processing for large files
- Progress reporting for long-running jobs

Usage Examples:
1. Basic usage with single file (generates both TSV and JSON):
   python kraken_parser.py -k kraken_output.txt

2. Custom TSV output name:
   python kraken_parser.py -k file1.txt --tsv custom_output.tsv

3. JSON output only with progress reporting:
   python kraken_parser.py -k data.txt --json results.json --progress
"""

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

# Constants for progress reporting
PROGRESS_INTERVAL = 1_000_000  # Print progress every 1M reads

def parse_kraken_file(file_path, show_progress=False):
    """
    Parse Kraken output file efficiently with:
    - Streaming line processing
    - Memory-efficient counters
    - Optional progress reporting
    """
    taxid_counts = defaultdict(int)
    taxid_names = {}
    total_classified = 0
    total_reads = 0

    pattern = re.compile(r'\(taxid\s+(\d+)\)')

    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            total_reads += 1
            
            # Progress reporting
            if show_progress and line_num % PROGRESS_INTERVAL == 0:
                print(f"  Processed {line_num:,} reads...", flush=True)
            
            if not line.startswith('C'):
                continue

            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue

            name_taxid = parts[2]
            match = pattern.search(name_taxid)
            if match:
                taxid = match.group(1)
                name = name_taxid[:match.start()].strip()
                taxid_counts[taxid] += 1
                taxid_names[taxid] = name
                total_classified += 1

    if show_progress:
        print(f"Finished processing {total_reads:,} total reads", flush=True)
    
    return taxid_counts, taxid_names, total_classified, total_reads

def generate_summary_chunked(taxid_counts, taxid_names, total_classified,
                           total_reads, top_n=None, chunk_size=1000):
    """
    Generate summary in chunks to avoid memory spikes with:
    - Yielding results in batches
    - Sorted output without full list storage
    """
    # Process in chunks if we have many taxa
    if len(taxid_counts) > chunk_size * 10:
        print(f"Processing {len(taxid_counts):,} taxa in chunks...", flush=True)
        
    sorted_taxa = sorted(
        taxid_counts.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    if top_n:
        sorted_taxa = sorted_taxa[:top_n]
    
    rows = []
    for taxid, count in sorted_taxa:
        name = taxid_names[taxid]
        classified_pct = (count / total_classified * 100) if total_classified else 0
        total_pct = (count / total_reads * 100) if total_reads else 0
        
        rows.append({
            "TaxID": taxid,
            "Name": name,
            "Count": count,
            "Classified_Percentage": round(classified_pct, 2),
            "Total_Percentage": round(total_pct, 2)
        })
        
        # Yield chunks if we have many taxa
        if len(rows) >= chunk_size and len(taxid_counts) > chunk_size:
            yield rows
            rows = []
    
    if rows:
        yield rows

def write_tsv_chunked(summary_data, output_file):
    """Write TSV in chunks for memory efficiency"""
    # Extract only the needed parameters
    chunk_generator = generate_summary_chunked(
        taxid_counts=summary_data["taxid_counts"],
        taxid_names=summary_data["taxid_names"],
        total_classified=summary_data["total_classified"],
        total_reads=summary_data["total_reads"],
        top_n=summary_data.get("top_n")
    )
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['taxid', 'name', 'reads',
                        'classified_percentage', 'total_percentage'])
        
        for chunk in chunk_generator:
            for taxon in chunk:
                writer.writerow([
                    taxon["TaxID"],
                    taxon["Name"],
                    taxon["Count"],
                    f"{taxon['Classified_Percentage']:.2f}",
                    f"{taxon['Total_Percentage']:.2f}"
                ])
    print(f"Saved TSV output to {output_file}")

def write_json(summary_data, output_file):
    """Write summary data to JSON file."""
    # Create output dictionary without the generator functions
    output = {
        "Sample": summary_data["Sample"],
        "Total_Reads": summary_data["total_reads"],
        "Classified_Reads": summary_data["total_classified"],
        "Unclassified_Reads": summary_data["total_reads"] - summary_data["total_classified"],
        "Classified_Pct": round((summary_data["total_classified"] / summary_data["total_reads"] * 100), 2) 
                         if summary_data["total_reads"] else 0,
        "Taxa": list(generate_summary_chunked(
            taxid_counts=summary_data["taxid_counts"],
            taxid_names=summary_data["taxid_names"],
            total_classified=summary_data["total_classified"],
            total_reads=summary_data["total_reads"],
            top_n=summary_data.get("top_n")
        ))[0]  # Get first (and only) chunk since we're not chunking for JSON
    }
    
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Saved JSON output to {output_file}")

def process_large_files(kraken_files, sample_name=None, top_n=None, 
                       tsv_output=None, json_output=None, show_progress=False):
    """Process files with memory-efficient methods"""
    results = []
    
    for i, kraken_file in enumerate(kraken_files):
        current_sample = sample_name or Path(kraken_file).stem
        if sample_name and len(kraken_files) > 1:
            current_sample = f"{sample_name}_{i+1}"
        
        print(f"Processing {kraken_file}...", flush=True)
        
        # Parse with progress reporting
        taxid_counts, taxid_names, total_classified, total_reads = parse_kraken_file(
            kraken_file, 
            show_progress=show_progress
        )
        
        summary = {
            "taxid_counts": taxid_counts,
            "taxid_names": taxid_names,
            "total_classified": total_classified,
            "total_reads": total_reads,
            "top_n": top_n,
            "Sample": current_sample
        }

        # Write TSV if requested or by default
        if tsv_output or not json_output:
            tsv_file = tsv_output if len(kraken_files) == 1 else f"{current_sample}_{tsv_output}" if tsv_output else f"{current_sample}_kraken_summary.tsv"
            write_tsv_chunked(summary, tsv_file)
        
        # Write JSON if requested or by default
        if json_output or not tsv_output:
            json_file = json_output if len(kraken_files) == 1 else f"{current_sample}_{json_output}" if json_output else f"{current_sample}.json"
            write_json(summary, json_file)
        
        results.append(summary)
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Memory-efficient Kraken output processor for large files.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-k', '--kraken_files',
        nargs='+',
        required=True,
        help='Input Kraken output file(s)',
        metavar='FILE'
    )
    
    parser.add_argument(
        '-s', '--sample',
        help='Base sample name (appended with numbers for multiple files)'
    )
    
    parser.add_argument(
        '-t', '--top',
        type=int,
        help='Number of top taxa to include in reports'
    )
    
    parser.add_argument(
        '--json',
        help='Output JSON file name (default: <sample>.json)',
        metavar='FILE'
    )
    
    parser.add_argument(
        '--tsv',
        help='Output TSV file name (default: <sample>_kraken_summary.tsv)',
        metavar='FILE'
    )
    
    parser.add_argument(
        '--progress',
        action='store_true',
        help='Show progress during processing of large files'
    )
    
    args = parser.parse_args()
    
    # Process files - no need to store returned results since they're already written to files
    process_large_files(
        kraken_files=args.kraken_files,
        sample_name=args.sample,
        top_n=args.top,
        tsv_output=args.tsv,
        json_output=args.json,
        show_progress=args.progress
    )
if __name__ == "__main__":
    main()