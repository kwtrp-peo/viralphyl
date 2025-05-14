#!/usr/bin/env python3

import json
import csv
import argparse
from pathlib import Path
from collections import defaultdict

COLOR_PALETTE = [
    "#440154", "#482878", "#3e4989", "#31688e", "#26828e",
    "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725",
    "#e377c2", "#8c564b", "#9467bd", "#d62728", "#ff7f0e",
    "#2ca02c", "#17becf", "#bcbd22", "#7f7f7f", "#1f77b4"
]

class MetadataProcessor:
    def __init__(self, tsv_path):
        self.tsv_path = tsv_path
        self.fieldnames = None
        self.original_fieldnames = None  # Store original case fieldnames
        self.categorical_cols = set()
        self.column_values = defaultdict(set)
        
    def _load_fieldnames(self):
        """Initialize fieldnames from the TSV file, preserving original case"""
        with open(self.tsv_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            self.original_fieldnames = reader.fieldnames
            self.fieldnames = [name.lower() for name in reader.fieldnames]
        
    def _get_original_case_name(self, col_lower):
        """Get the original case column name from lowercase version"""
        if not self.original_fieldnames:
            self._load_fieldnames()
        for name in self.original_fieldnames:
            if name.lower() == col_lower:
                return name
        return col_lower  # fallback
    
    def analyze(self, protected_columns, threshold=30, sample_size=1000):
        """Identify categorical columns in the metadata"""
        if not self.fieldnames:
            self._load_fieldnames()
            
        with open(self.tsv_path, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, row in enumerate(reader):
                if i >= sample_size:
                    break
                    
                for col in self.original_fieldnames:
                    if value := row.get(col, '').strip():
                        self.column_values[col.lower()].add(value)
        
        protected_set = {col.lower() for col in protected_columns}
        for col in self.fieldnames:
            values = self.column_values[col]
            if (col in protected_set) or (len(values) < threshold):
                self.categorical_cols.add(col)
    
    def generate_json(self, output_path, title, exclude_columns=None):
        """Generate the JSON configuration file"""
        exclude = {col.lower() for col in (exclude_columns or [])} | {'strain', 'date'}
        config = {
            "title": f"Phylogenetic Analysis Output for {title}",
            "maintainers": [{"name": "Samuel Odoyo", "url": "https://github.com/samordil/"}],
            "build_url": "https://github.com/kwtrp-peo/viralphyl",
            "colorings": [
                {
                    "key": col,
                    "title": self._get_original_case_name(col).capitalize(),
                    "type": "categorical"
                }
                for col in self.categorical_cols 
                if col not in exclude
            ],
            "panels": ["tree", "map", "entropy"],
            "filters": [col for col in self.categorical_cols if col not in exclude]
        }
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        return output_path
    
    def generate_colors(self, output_path, target_variable=None, existing_colors=None, protected_columns=None):
        """Generate the colors TSV file with proper case handling"""
        if not self.fieldnames:
            self._load_fieldnames()
            
        existing = existing_colors or defaultdict(dict)
        protected_set = {col.lower() for col in (protected_columns or [])}
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f, delimiter='\t')
            # writer.writerow(['variable', 'value', 'color'])
            
            # When variable is specified
            if target_variable:
                target_var_lower = target_variable.lower()
                if target_var_lower not in self.fieldnames:
                    raise ValueError(f"Column '{target_variable}' not found in TSV")
                
                # Get original case column name
                original_col = self._get_original_case_name(target_var_lower)
                
                # Check if column is protected or categorical
                if (target_var_lower in protected_set) or (target_var_lower in self.categorical_cols):
                    values = set()
                    with open(self.tsv_path, 'r') as tsv:
                        reader = csv.DictReader(tsv, delimiter='\t')
                        for row in reader:
                            if val := row.get(original_col, '').strip():
                                values.add(val)
                    
                    # Write color mappings with original case column name
                    for idx, val in enumerate(sorted(values)):
                        color = existing.get(target_var_lower, {}).get(val.lower(), 
                                       COLOR_PALETTE[idx % len(COLOR_PALETTE)])
                        writer.writerow([original_col, val, color])
                else:
                    print(f"Skipping non-categorical column: {original_col}")
            else:
                # Process all categorical columns
                for col_lower in self.categorical_cols:
                    original_col = self._get_original_case_name(col_lower)
                    
                    values = set()
                    with open(self.tsv_path, 'r') as tsv:
                        reader = csv.DictReader(tsv, delimiter='\t')
                        for row in reader:
                            if val := row.get(original_col, '').strip():
                                values.add(val)
                    
                    for idx, val in enumerate(sorted(values)):
                        color = existing.get(col_lower, {}).get(val.lower(), 
                                       COLOR_PALETTE[idx % len(COLOR_PALETTE)])
                        writer.writerow([original_col, val, color])
        return output_path

def main():
    parser = argparse.ArgumentParser(
        description='Generate metadata visualization configuration files',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Input
    parser.add_argument('-i', '--input', required=True, help='Input TSV file path')
    
    # Output options
    parser.add_argument('-j', '--json', help='Output JSON config path')
    parser.add_argument('-c', '--colors', help='Output colors TSV path')
    
    # Processing parameters
    parser.add_argument('-t', '--title', default="Dataset", help='Dataset title for JSON')
    parser.add_argument('-v', '--variable', help='Specific column to process (colors TSV only)')
    parser.add_argument('-p', '--protected', nargs='*', default=['country', 'genotype', 'region'],
                      help='Columns always treated as categorical (case-insensitive)')
    parser.add_argument('-n', '--threshold', type=int, default=30,
                      help='Max unique values for non-protected columns')
    parser.add_argument('-e', '--existing-colors', help='Existing colors TSV file')
    parser.add_argument('-x', '--exclude', nargs='*', default=['strain', 'date'],
                      help='Columns to exclude from JSON output')
    
    args = parser.parse_args()
    
    if not (args.json or args.colors):
        parser.error("At least one output (--json or --colors) must be specified")
    
    if args.variable and not args.colors:
        parser.error("--variable requires --colors output to be specified")

    try:
        processor = MetadataProcessor(args.input)
        
        # Always analyze for JSON generation
        if args.json:
            processor.analyze(
                protected_columns=args.protected,
                threshold=args.threshold
            )
        
        # Generate requested outputs
        results = []
        if args.json:
            json_path = processor.generate_json(args.json, args.title, args.exclude)
            results.append(f"JSON config: {json_path}")
        
        if args.colors:
            # For colors, ensure the variable is processed if specified
            if args.variable:
                var_lower = args.variable.lower()
                if var_lower not in processor.categorical_cols:
                    # If variable isn't categorical, check if it's protected
                    protected_set = {col.lower() for col in args.protected}
                    if var_lower in protected_set:
                        # Add to categorical_cols if protected
                        processor.categorical_cols.add(var_lower)
            
            colors_path = processor.generate_colors(
                args.colors,
                target_variable=args.variable,
                existing_colors=None if not args.existing_colors else defaultdict(dict),
                protected_columns=args.protected
            )
            results.append(f"Colors TSV: {colors_path}")
        
        print("Successfully generated:")
        print(" • " + "\n • ".join(results))
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()