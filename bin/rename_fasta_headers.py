#!/usr/bin/env python
import csv
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import argparse
import sys
from collections import defaultdict

def fasta_generator(fasta_file):
    """Yield accession-sequence pairs one at a time."""
    for record in SeqIO.parse(fasta_file, "fasta"):
        yield {'accession': record.id, 'sequence': str(record.seq)}

def tsv_generator(tsv_file):
    """Yield TSV records one at a time."""
    with open(tsv_file, 'r') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            yield row

def process_records(fasta_file, tsv_file):
    """Merge records and generate outputs."""
    tsv_index = defaultdict(list)
    for tsv_record in tsv_generator(tsv_file):
        tsv_index[tsv_record['accession']].append(tsv_record)
    
    for fasta_record in fasta_generator(fasta_file):
        acc = fasta_record['accession']
        if acc in tsv_index:
            for tsv_record in tsv_index[acc]:
                country = tsv_record.get('country', 'unknown')
                date = tsv_record.get('date', 'unknown')
                region = tsv_record.get('region', 'unknown')
                strain_id = f"{acc}|{country}|{date}"
                
                # TSV output record (now 4 columns)
                tsv_output = {
                    'strain': strain_id,
                    'country': country,
                    'region': region,
                    'date': date
                }
                
                # FASTA record
                fasta_record = SeqRecord(
                    Seq(fasta_record['sequence']),
                    id=strain_id,
                    description=""
                )
                
                yield tsv_output, fasta_record

def main():
    parser = argparse.ArgumentParser(
        description='Merge FASTA/TSV and output TSV + FASTA',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-f', '--fasta', required=True, help='Input FASTA file')
    parser.add_argument('-t', '--tsv', required=True, help='Input TSV file')
    parser.add_argument('--tsv-output', required=True, help='Output TSV file')
    parser.add_argument('--fasta-output', required=True, help='Output FASTA file')
    args = parser.parse_args()

    try:
        tsv_writer = None
        processed_count = 0
        output_columns = ['strain', 'country', 'region', 'date']
        
        with open(args.tsv_output, 'w') as tsv_file, open(args.fasta_output, 'w') as fasta_file:
            for tsv_record, fasta_record in process_records(args.fasta, args.tsv):
                if tsv_writer is None:
                    tsv_writer = csv.DictWriter(tsv_file, fieldnames=output_columns, delimiter='\t')
                    tsv_writer.writeheader()
                
                tsv_writer.writerow(tsv_record)
                SeqIO.write(fasta_record, fasta_file, 'fasta')
                processed_count += 1

        if processed_count == 0:
            print("Error: No matching accessions found between files", file=sys.stderr)
            sys.exit(1)

        print(f"Successfully processed {processed_count} records", file=sys.stderr)

    except FileNotFoundError as e:
        print(f"Error: {e.filename} not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()