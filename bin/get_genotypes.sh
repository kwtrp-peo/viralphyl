#!/bin/bash

# get_genotypes.sh - FASTA header parser for sample, accession, and genotype extraction
#
# Usage:
#   ./get_genotypes.sh input1.fasta [input2.fasta ...] > output.tsv

# Input Format Expected:
#   >run1_bc02/OL794440.1_B1/ARTIC/clair3
#
# Output Format (TSV):
#   sample      ref_accession  genotype
#   run1_bc02   OL794440.1     B1


# Print TSV header
echo -e "strain_id\tref_accession\tgenotype"

# Process each input file
for fasta_file in "$@"; do
    # Skip if file doesn't exist
    [[ ! -f "$fasta_file" ]] && continue
    
    # Extract headers (prefer seqkit, fallback to grep)
    if command -v seqkit &>/dev/null; then
        headers=$(seqkit seq -n -i "$fasta_file" 2>/dev/null)
    else
        headers=$(grep '^>' "$fasta_file" | sed 's/^>//')
    fi

    # Parse with version preservation
    while IFS= read -r header; do
        [[ -z "$header" ]] && continue    # Skip empty l
        
        # Match patterns like: run1_bc02/OL794440.1_B1/...
        # Extract components using regex groups:
        # Group 1: sample (run1_bc02)
        # Group 2: ref_accession (OL794440.1)
        # Group 3: genotype (B1)
        if [[ "$header" =~ ^([^/]+)/([^_]+)_([^/]+) ]]; then
            printf "%s\t%s\t%s\n" \
                "${BASH_REMATCH[1]}" \
                "${BASH_REMATCH[2]}" \
                "${BASH_REMATCH[3]}"
        fi
    done <<< "$headers"
done