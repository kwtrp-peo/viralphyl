#!/usr/bin/env python3
"""
Process QC TSV files and generate sorted read count visualizations.
Supports multiple plot types:
- grouped-bar
- stacked-bar
- mapping-rate-bar
- scatter
- histogram
"""

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

def plot_grouped_bar(data, output_path=None, title=None):
    """Grouped bar plot of total and mapped reads."""
    if not data:
        print("No data available for plotting", file=sys.stderr)
        return
    
    df = pd.DataFrame(data)
    if len(df) > 30:
        print("Warning: too many samples for grouped bar plot, may be unreadable!", file=sys.stderr)
    
    df = df.sort_values('total_reads', ascending=False)
    
    data_long = pd.melt(
        df,
        id_vars=['strain_id'],
        value_vars=['total_reads', 'mapped_reads'],
        var_name='Read_Type',
        value_name='Read_Count'
    )
    
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')
    ax.grid(True, axis='y', linestyle='--', alpha=0.7)
    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)
    
    sample_ids = df['strain_id']
    x = np.arange(len(sample_ids))
    width = 0.35
    colors = {"total_reads": "#0072B2", "mapped_reads": "#E69F00"}
    
    for i, (read_type, color) in enumerate(colors.items()):
        subset = data_long[data_long['Read_Type'] == read_type]
        ax.bar(
            x + (i * width) - (width/2),
            subset['Read_Count'],
            width,
            color=color,
            label=read_type.replace('_', ' ').title()
        )
    
    ax.set_title(title or "Read Counts by Sample", pad=20)
    ax.set_xlabel('Sample')
    ax.set_ylabel('Read Counts')
    ax.set_xticks(x)
    ax.set_xticklabels(sample_ids, rotation=90, ha='center')
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(title='Read Type')
    
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def plot_stacked_bar(data, output_path=None, title=None):
    """Stacked bar plot of mapped and unmapped reads."""
    if not data:
        print("No data available for plotting", file=sys.stderr)
        return
    
    df = pd.DataFrame(data)
    if len(df) > 30:
        print("Warning: too many samples for stacked bar plot, may be unreadable!", file=sys.stderr)
    
    df['unmapped_reads'] = df['total_reads'] - df['mapped_reads']
    df = df.sort_values('total_reads', ascending=False)
    
    sample_ids = df['strain_id']
    x = np.arange(len(sample_ids))
    
    plt.figure(figsize=(14, 7))
    plt.bar(x, df['mapped_reads'], label='Mapped Reads', color='#4E79A7')
    plt.bar(x, df['unmapped_reads'], bottom=df['mapped_reads'], label='Unmapped Reads', color='#D55E00')
    
    plt.title(title or 'Stacked Barplot of Reads by Sample')
    plt.xlabel('Sample')
    plt.ylabel('Read Counts')
    plt.xticks(x, sample_ids, rotation=90, ha='center')
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def plot_mapping_rate_bar(data, output_path=None, title=None):
    """Bar plot of mapping rate per sample."""
    if not data:
        print("No data available for plotting", file=sys.stderr)
        return
    
    df = pd.DataFrame(data)
    df['mapping_rate'] = df['mapped_reads'] / df['total_reads']
    df = df.sort_values('mapping_rate', ascending=False)
    
    plt.figure(figsize=(14, 6))
    plt.bar(df['strain_id'], df['mapping_rate'], color='#4E79A7')
    plt.ylabel('Mapping Rate')
    plt.title(title or 'Mapping Rate by Sample')
    plt.xticks(rotation=90, ha='center')
    plt.ylim(0, 1.05)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def plot_scatter_total_vs_mapping_rate(data, output_path=None, title=None):
    """Scatter plot of total reads vs. mapping rate."""
    if not data:
        print("No data available for plotting", file=sys.stderr)
        return
    
    df = pd.DataFrame(data)
    df['mapping_rate'] = df['mapped_reads'] / df['total_reads']
    
    plt.figure(figsize=(8, 6))
    plt.scatter(df['total_reads'], df['mapping_rate'], alpha=0.7, color='#4E79A7')
    plt.xlabel('Total Reads')
    plt.ylabel('Mapping Rate')
    plt.title(title or 'Mapping Rate vs. Total Reads')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def plot_mapping_rate_histogram(data, output_path=None, title=None):
    """Histogram of mapping rates across samples."""
    if not data:
        print("No data available for plotting", file=sys.stderr)
        return
    
    df = pd.DataFrame(data)
    df['mapping_rate'] = df['mapped_reads'] / df['total_reads']
    
    plt.figure(figsize=(8, 6))
    plt.hist(df['mapping_rate'], bins=30, color='#4E79A7', alpha=0.8)
    plt.xlabel('Mapping Rate')
    plt.ylabel('Number of Samples')
    plt.title(title or 'Distribution of Mapping Rates')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
    else:
        plt.show()
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Process QC TSV files and generate read count plots.')
    parser.add_argument('--tsv-files', nargs='+', required=True, help='Input TSV files')
    parser.add_argument('--output-tsv', help='Output TSV file path')
    parser.add_argument('--output-plot', help='Output plot file path')
    parser.add_argument('--plot-title', help='Title for the plot')
    parser.add_argument(
        '--plot-type',
        choices=['grouped-bar', 'stacked-bar', 'mapping-rate-bar', 'scatter', 'histogram'],
        default='stacked-bar',
        help='Type of plot to generate'
    )
    parser.add_argument('--threads', type=int, default=4, help='Number of processing threads')
    args = parser.parse_args()
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        results = list(executor.map(process_file, map(Path, args.tsv_files)))
    valid_results = [r for r in results if r is not None]
    
    if args.output_tsv and valid_results:
        with open(args.output_tsv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=valid_results[0].keys(), delimiter='\t')
            writer.writeheader()
            writer.writerows(valid_results)
    
    if valid_results:
        plot_type = args.plot_type
        
        if plot_type == 'grouped-bar':
            plot_grouped_bar(valid_results, output_path=args.output_plot, title=args.plot_title)
        
        elif plot_type == 'stacked-bar':
            plot_stacked_bar(valid_results, output_path=args.output_plot, title=args.plot_title)
        
        elif plot_type == 'mapping-rate-bar':
            plot_mapping_rate_bar(valid_results, output_path=args.output_plot, title=args.plot_title)
        
        elif plot_type == 'scatter':
            plot_scatter_total_vs_mapping_rate(valid_results, output_path=args.output_plot, title=args.plot_title)
        
        elif plot_type == 'histogram':
            plot_mapping_rate_histogram(valid_results, output_path=args.output_plot, title=args.plot_title)
    
    print(f"Processed {len(valid_results)}/{len(args.tsv_files)} files", file=sys.stderr)

if __name__ == '__main__':
    main()
