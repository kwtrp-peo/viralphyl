#!/usr/bin/env python3
# DOC ADDED: Module description
"""
TSV Processor - Transforms multiple QC metric files into unified format

Key Behaviors:
1. Extracts sample names from input filenames (text before first '.')
   Example: 'sample01.qc.tsv' → sample='sample01'
2. Converts each file's key:value pairs to output columns
   Example input TSV line: 'total-reads: 1000' 
   → Output column: 'total_reads' with value 1000
"""

import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import sys
import csv

def process_file(file_path):
    # DOC ADDED: Function description
    """
    Processes individual TSV files into structured data.
    
    Transformations Applied:
    - Filename prefix → sample name
    - Input TSV keys → output columns (with '-' → '_')
    - Values converted to appropriate types (int/float)
    """
    try:
        strain_id = file_path.name.split('.')[0]
        metrics = {'strain_id': strain_id}
        
        with file_path.open() as f:
            for line in f:
                if '\t' in line:
                    key, val = line.strip().split('\t', 1)
                    # CODE CHANGE (requested): Only this line modified
                    metrics[key.rstrip(':').replace('-', '_')] = val
        
        # Original type conversions (now with underscores)
        metrics['total_reads'] = int(metrics['total_reads'])
        metrics['mapped_reads'] = int(metrics['mapped_reads'])
        metrics['mapped_percent'] = float(metrics['mapped_percent'])
        metrics['coverage_percent'] = float(metrics['coverage_percent'])
        
        return metrics
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}", file=sys.stderr)
        return None

def main():
    # DOC ADDED: Main function description
    """
    Coordinates parallel processing and output generation.
    
    Workflow:
    1. Parse command-line arguments
    2. Process files concurrently using ThreadPool
    3. Write validated results to output TSV
    """

    parser = argparse.ArgumentParser(description='Fast TSV processor (no pandas)')
    parser.add_argument('--tsv-files', nargs='+', required=True, help='Input TSV files')
    parser.add_argument('--output', required=True, help='Output TSV file')
    parser.add_argument('--threads', type=int, default=4, help='Parallel threads')
    
    args = parser.parse_args()
    
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        results = list(executor.map(process_file, map(Path, args.tsv_files)))
    
    valid_results = [r for r in results if r is not None]
    
    with open(args.output, 'w', newline='') as f:
        if not valid_results:
            sys.exit(1)
            
        writer = csv.DictWriter(f, fieldnames=valid_results[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(valid_results)
    
    print(f"Processed {len(valid_results)}/{len(args.tsv_files)} files", file=sys.stderr)

if __name__ == '__main__':
    main()