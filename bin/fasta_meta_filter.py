#!/usr/bin/env python3
"""
fasta_meta_filter.py - Process FASTA files with metadata merging, coverage filtering, and optional visualization
"""

import argparse
from pathlib import Path
import pandas as pd
from Bio import SeqIO
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

def stream_records(fasta_paths):
    """Stream FASTA records one at a time with error handling"""
    for fasta_path in fasta_paths:
        try:
            with fasta_path.open("r") as handle:
                for record in SeqIO.parse(handle, "fasta"):
                    yield record
        except Exception as e:
            print(f"Error processing {fasta_path}: {str(e)}", file=sys.stderr)
            continue

def validate_metadata(metadata_df, merge_on):
    """Validate metadata dataframe structure"""
    if merge_on not in metadata_df.columns:
        print(f"Error: Merge column '{merge_on}' missing from metadata", file=sys.stderr)
        sys.exit(1)
    
    metadata_df[merge_on] = metadata_df[merge_on].astype(str)
    if metadata_df[merge_on].isnull().any():
        print("Error: Merge column contains empty values", file=sys.stderr)
        sys.exit(1)
    
    return metadata_df

def parse_coverage(coverage_str):
    """Parse coverage percentage from string"""
    try:
        if pd.isna(coverage_str):
            return 0.0
        return float(str(coverage_str).replace('%', '').strip())
    except ValueError:
        return 0.0

def generate_coverage_plot(coverage_data, threshold, output_file):
    """Generate coverage plot only if requested"""
    if not coverage_data:
        print("Warning: No coverage data available for plotting", file=sys.stderr)
        return
    
    plt.figure(figsize=(14, 7))
    colors = {'Pass': '#4E79A7', 'Fail': '#E15759'}
    
    plot_df = pd.DataFrame(coverage_data)
    plot_df.sort_values('coverage_percent', ascending=False, inplace=True)
    
    bars = plt.bar(
        plot_df['strain_id'], 
        plot_df['coverage_percent'],
        color=[colors[status] for status in plot_df['Status']]
    )
    
    plt.axhline(y=threshold, color='black', linestyle=':', linewidth=1)
    plt.title('Genome Coverage (%) Per Sample', pad=20)
    plt.xlabel('')
    plt.ylabel('Coverage Percent (%)')
    plt.ylim(0, 100)
    plt.yticks(range(0, 101, 10))
    plt.xticks(rotation=90)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    
    legend_elements = [
        Patch(facecolor=colors['Pass'], label=f'Pass (≥{threshold}%)'),
        Patch(facecolor=colors['Fail'], label=f'Fail (<{threshold}%)')
    ]
    plt.legend(handles=legend_elements, loc='upper right')
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description="Process FASTA files with metadata merging and coverage filtering",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('-i', '--input-fasta', nargs='+', required=True,
                      help='Input FASTA file(s) (supports wildcards)')
    
    # Output options
    parser.add_argument('--tsv-output', type=Path,
                      help='Output TSV file (without sequences)')
    parser.add_argument('--fasta-output', type=Path,
                      help='Output concatenated FASTA file')
    parser.add_argument('--filtered-tsv', type=Path,
                      help='Output filtered TSV file (coverage >= threshold)')
    parser.add_argument('--filtered-fasta', type=Path,
                      help='Output filtered FASTA file (coverage >= threshold)')
    parser.add_argument('--coverage-plot', type=Path,
                      help='Optional output coverage visualization plot (PNG format)')
    
    # Processing options
    parser.add_argument('--merge-tsv', type=Path,
                      help='Optional metadata TSV to merge')
    parser.add_argument('--merge-on', default='strain_id',
                      help='Column to merge on (default: strain_id)')
    parser.add_argument('--coverage-col', default='coverage_percent',
                      help='Column name for coverage percentage (default: coverage_percent)')
    parser.add_argument('--threshold', type=float, default=0.7,
                      help='Coverage threshold for filtering (0.0-1.0, default: 0.7)\n'
                           'Note: This represents a fraction (0.7 = 70%)')
    
    args = parser.parse_args()

    # Validate at least one output was requested
    if not any([args.tsv_output, args.fasta_output, args.filtered_tsv, args.filtered_fasta, args.coverage_plot]):
        print("Error: At least one output file must be specified", file=sys.stderr)
        sys.exit(1)

    # Convert threshold to percentage
    threshold_percent = args.threshold * 100
    required_fields = {'genotype', 'collection_date'}

    # Resolve and deduplicate input files
    fasta_paths = list({p.resolve() for pattern in args.input_fasta 
                       for p in Path().glob(pattern)})
    if not fasta_paths:
        print("Error: No FASTA files found", file=sys.stderr)
        sys.exit(1)

    # Pre-process metadata if provided
    metadata_map = {}
    metadata_cols = []
    coverage_available = False
    
    if args.merge_tsv:
        try:
            metadata_df = validate_metadata(
                pd.read_csv(args.merge_tsv, sep='\t', dtype=str),
                args.merge_on
            )
            metadata_cols = [col for col in metadata_df.columns if col != args.merge_on]
            coverage_available = args.coverage_col in metadata_df.columns
            
            metadata_map = metadata_df.set_index(args.merge_on).to_dict('index')
        except Exception as e:
            print(f"Metadata error: {str(e)}", file=sys.stderr)
            sys.exit(1)

    # Prepare output files
    file_handles = {}
    coverage_data = [] if args.coverage_plot else None
    
    try:
        if args.tsv_output:
            tsv_out = open(args.tsv_output, 'w')
            file_handles['tsv_out'] = tsv_out
            tsv_out.write("\t".join(["sequence_id", "strain_id"] + metadata_cols) + "\n")
        
        if args.fasta_output:
            file_handles['fasta_out'] = open(args.fasta_output, 'w')
        
        if args.filtered_tsv:
            filtered_tsv_out = open(args.filtered_tsv, 'w')
            file_handles['filtered_tsv_out'] = filtered_tsv_out
            filtered_tsv_out.write("\t".join(["sequence_id", "strain_id"] + metadata_cols) + "\n")
        
        if args.filtered_fasta:
            file_handles['filtered_fasta_out'] = open(args.filtered_fasta, 'w')

        # Process records
        for record in stream_records(fasta_paths):
            parts = record.description.split('/')
            strain_id = parts[0].strip()
            sequence_id_parts = [strain_id]
            meta_data = {col: '' for col in metadata_cols}
            meets_coverage = False
            coverage_value = 0.0
            
            if metadata_map and strain_id in metadata_map:
                meta_row = metadata_map[strain_id]
                
                for field in required_fields:
                    if field in meta_row and meta_row[field]:
                        sequence_id_parts.append(str(meta_row[field]))
                
                for col in metadata_cols:
                    if col in meta_row:
                        meta_data[col] = str(meta_row[col])
                
                if coverage_available:
                    coverage_value = parse_coverage(meta_row.get(args.coverage_col))
                    meets_coverage = (coverage_value >= threshold_percent)
                    if args.coverage_plot:
                        coverage_data.append({
                            'strain_id': strain_id,
                            'coverage_percent': coverage_value,
                            'Status': 'Pass' if meets_coverage else 'Fail'
                        })
            
            sequence_id = "|".join(sequence_id_parts)
            row_line = "\t".join([sequence_id, strain_id] + [meta_data[col] for col in metadata_cols]) + "\n"
            
            if args.fasta_output:
                file_handles['fasta_out'].write(f">{sequence_id}\n{str(record.seq)}\n")
            if args.tsv_output:
                file_handles['tsv_out'].write(row_line)
            
            if (not coverage_available) or meets_coverage:
                if args.filtered_fasta:
                    file_handles['filtered_fasta_out'].write(f">{sequence_id}\n{str(record.seq)}\n")
                if args.filtered_tsv:
                    file_handles['filtered_tsv_out'].write(row_line)

        # Generate coverage plot if requested
        if args.coverage_plot:
            if coverage_available and coverage_data:
                generate_coverage_plot(coverage_data, threshold_percent, args.coverage_plot)
            else:
                print("Warning: Cannot generate coverage plot - no coverage data available", file=sys.stderr)

    finally:
        for handle in file_handles.values():
            handle.close()

    # Print summary
    print(f"\nProcessed {len(fasta_paths)} input files")
    generated_files = {
        'Full FASTA': args.fasta_output,
        'Full metadata': args.tsv_output,
        f'Filtered FASTA (≥{threshold_percent}%)': args.filtered_fasta,
        f'Filtered metadata (≥{threshold_percent}%)': args.filtered_tsv,
        'Coverage plot': args.coverage_plot
    }
    for desc, path in generated_files.items():
        if path:
            print(f"{desc}: {path}")

if __name__ == "__main__":
    main()