#!/usr/bin/env python3
"""Process QC TSV files and generate sorted read count visualizations."""

import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
import csv
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

def process_file(file_path):
    """Extract sample metrics from a TSV file."""
    try:
        strain_id = file_path.name.split('.')[0]
        metrics = {'strain_id': strain_id}
        
        with file_path.open() as f:
            for line in f:
                if '\t' in line:
                    key, val = line.strip().split('\t', 1)
                    metrics[key.rstrip(':').replace('-', '_')] = val
        
        metrics['total_reads'] = int(metrics['total_reads'])
        metrics['mapped_reads'] = int(metrics['mapped_reads'])
        return metrics
        
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
        return None

def create_sorted_read_count_plot(data, output_path=None, title=None):
    """Generate a bar plot with samples sorted by total reads (high to low)."""
    if not data:
        print("No data available for plotting", file=sys.stderr)
        return
    
    # Convert to DataFrame and sort by total_reads (descending)
    df = pd.DataFrame(data)
    df = df.sort_values('total_reads', ascending=False)
    
    # Prepare data in long format
    data_long = pd.melt(df,
                      id_vars=['strain_id'],
                      value_vars=['total_reads', 'mapped_reads'],
                      var_name='Read_Type',
                      value_name='Read_Count')
    
    # Set up plot
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Style configuration
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    
    # Plot configuration
    sample_ids = df['strain_id']  # Use the sorted order
    x = np.arange(len(sample_ids))
    width = 0.35
    colors = {"total_reads": "#4E79A7", "mapped_reads": "#D55E00"}
    
    for i, (read_type, color) in enumerate(colors.items()):
        subset = data_long[data_long['Read_Type'] == read_type]
        ax.bar(x + (i * width) - (width/2),
              subset['Read_Count'],
              width,
              color=color,
              label=read_type.replace('_', ' ').title())
    
    # Formatting
    ax.set_title(title or "Read Counts by Sample", pad=20)
    ax.set_xlabel(' ')
    ax.set_ylabel('Read Counts')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_ids, rotation=90, ha='center')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(title='Read Type')
    
    # Output
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Process QC TSV files and generate sorted read count plots')
    parser.add_argument('--tsv-files', nargs='+', required=True, help='Input TSV files')
    parser.add_argument('--output-tsv', help='Output TSV file path')
    parser.add_argument('--output-plot', help='Output plot file path')
    parser.add_argument('--plot-title', help='Title for the plot')
    parser.add_argument('--threads', type=int, default=4, help='Number of processing threads')
    
    args = parser.parse_args()
    
    # Process files
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        results = list(executor.map(process_file, map(Path, args.tsv_files)))
    
    valid_results = [r for r in results if r is not None]
    
    # Write output if requested
    if args.output_tsv and valid_results:
        with open(args.output_tsv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=valid_results[0].keys(), delimiter='\t')
            writer.writeheader()
            writer.writerows(valid_results)
    
    # Generate plot
    if valid_results:
        create_sorted_read_count_plot(
            valid_results,
            output_path=args.output_plot,
            title=args.plot_title
        )
    
    print(f"Processed {len(valid_results)}/{len(args.tsv_files)} files", file=sys.stderr)

if __name__ == '__main__':
    main()