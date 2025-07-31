#!/usr/bin/env python3

# Import standard libraries for system interaction, parallelism, file handling, and subprocess management
import argparse
import json
import logging
import multiprocessing
import os
import shutil
import subprocess
import sys
import tempfile
import re
from concurrent.futures import ThreadPoolExecutor
from Bio import SeqIO  # For reading/writing sequence files in FASTA/FASTQ formats

# Runs a shell command and raises an error if the command fails
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logging.error(f"Command failed: {command}\n{result.stderr}")
        raise RuntimeError(f"Command failed: {command}\n{result.stderr}")
    return result.stdout

# Cleans up and returns a safe string for filenames from a ref sequence description
def safe_id(description):
    first_word = description.split()[0]
    return re.sub(r"[^\w.-]", "_", first_word)

# Runs minimap2 and samtools to align reads and generate a consensus FASTA
def generate_consensus(reads_path, ref_path, output_prefix, threads, min_depth):
    bam_file = f"{output_prefix}.bam"
    consensus_file = f"{output_prefix}.fasta"

    # Align reads to reference and sort into BAM
    cmd_align = f"minimap2 -ax map-ont -t {threads} {ref_path} {reads_path} | samtools sort -@ {threads} -o {bam_file}"
    run_command(cmd_align)
    run_command(f"samtools index {bam_file}")  # Index BAM for downstream tools

    # Generate consensus sequence using a minimum depth threshold
    cmd_cons = f"samtools consensus --min-depth {min_depth} --threads {threads} -aa --format fasta {bam_file}"
    result = run_command(cmd_cons)

    # Write the consensus to file
    with open(consensus_file, "w") as f:
        f.write(result)

    return consensus_file, bam_file

# Calculates genome coverage (percentage of bases that are not 'N')
def parse_consensus_coverage(consensus_fasta):
    record = SeqIO.read(consensus_fasta, "fasta")
    total_len = len(record.seq)
    covered_bases = total_len - record.seq.upper().count("N")
    return round((covered_bases / total_len) * 100, 2)

# Parses JSON stats from `samtools flagstat` output
def parse_bam_stats(bam_file):
    cmd = f"samtools flagstat -O json {bam_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
    stats_json = json.loads(result.stdout)

    try:
        qc_passed = stats_json["QC-passed reads"]
        total_reads = qc_passed["primary"]
        mapped_reads = qc_passed["primary mapped"]
    except KeyError as e:
        raise RuntimeError(f"Expected key missing in samtools output: {e}")

    mapped_percent = (mapped_reads / total_reads * 100) if total_reads > 0 else 0.0

    return {
        "total": total_reads,
        "mapped": mapped_reads,
        "mapped_percent": round(mapped_percent, 2)
    }

# Full processing pipeline for a single reference: align, consensus, coverage, stats
def process_reference(ref_record, reads_path, threads, tempdir, min_depth, sample_id):
    ref_id = safe_id(ref_record.description)  # Sanitize reference header
    ref_fasta = os.path.join(tempdir, f"{ref_id}.fa")
    with open(ref_fasta, "w") as f:
        SeqIO.write(ref_record, f, "fasta")

    prefix = os.path.join(tempdir, f"{sample_id}_{ref_id}_output")

    try:
        consensus_path, bam_path = generate_consensus(reads_path, ref_fasta, prefix, threads, min_depth)
        coverage = parse_consensus_coverage(consensus_path)
        stats = parse_bam_stats(bam_path)
        score = stats["mapped"] * (coverage / 100)  # Score used for best-reference ranking
    except Exception as e:
        logging.warning(f"Failed to process reference {ref_id}: {e}")
        return None

    return {
        "sample_id": sample_id,
        "ref_id": ref_id,
        "coverage": coverage,
        "stats": stats,
        "consensus": consensus_path,
        "bam": bam_path,
        "score": round(score, 2)
    }

# Returns a sorting key function based on chosen priority
def get_priority_key(priority):
    return {
        "mapped": lambda x: (x["stats"]["mapped"], x["coverage"]),
        "coverage": lambda x: (x["coverage"], x["stats"]["mapped"]),
        "score": lambda x: x["score"]
    }[priority]

# Main entry point of the script
def main():
    # Command-line interface definition
    parser = argparse.ArgumentParser(description="Select best reference after consensus")
    parser.add_argument("--reads", required=True, help="Input FASTQ(.gz)")
    parser.add_argument("--msa", required=True, help="Multi-FASTA file of reference genomes")
    parser.add_argument("--output", required=True, help="Output prefix or directory")
    parser.add_argument("--mapping-json", help="Optional: output all reference mapping stats")
    parser.add_argument("--best-json", help="Optional: output best reference mapping stats")
    parser.add_argument("--threads", type=int, default=4, help="Threads per job (default: 4)")
    parser.add_argument("--min_depth", type=int, default=10, help="Minimum depth for consensus generation (default: 10)")
    parser.add_argument("--workers", type=int, default=None, help="Parallel jobs. Defaults to (CPUs - 1)")
    parser.add_argument("--sample_id", required=True, help="Sample ID (e.g., run1_bc01)")
    parser.add_argument("--taxid", required=True, help="NCBI taxon ID")
    parser.add_argument("--pathogen", required=True, help="Pathogen name (e.g., Zaire ebolavirus)")
    parser.add_argument("--keep_all_bams", action="store_true", help="If set, all BAMs and indices are retained")
    parser.add_argument("--priority", choices=["mapped", "coverage", "score"], default="mapped", help="Metric to prioritize for best reference selection (default: mapped)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Determine how many worker threads to run in parallel
    cpu_count = multiprocessing.cpu_count()
    workers = args.workers if args.workers else max(1, cpu_count - 1)
    logging.info(f"Using {workers} parallel workers out of {cpu_count} CPU cores.")

    # Load reference sequences from MSA
    references = list(SeqIO.parse(args.msa, "fasta"))
    if not references:
        logging.error("No references found in MSA.")
        sys.exit(1)

    output_dir = os.path.dirname(args.output)
    bam_dir = None
    if args.keep_all_bams:
        bam_dir = os.path.join(output_dir, f"{args.sample_id}_bams")
        os.makedirs(bam_dir, exist_ok=True)

    # Temporary directory to hold intermediate outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create processing tasks for each reference
        tasks = [(ref, args.reads, args.threads, tmpdir, args.min_depth, args.sample_id) for ref in references]

        # Run all reference mapping tasks in parallel
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda x: process_reference(*x), tasks))

        # Filter out any failed reference mappings
        results = [r for r in results if r]

        if not results:
            logging.error("All references failed during processing.")
            sys.exit(1)

        # If keeping all BAMs, move them to persistent directory
        if args.keep_all_bams:
            for entry in results:
                bam_src = entry["bam"]
                bai_src = bam_src + ".bai"
                bam_dest = os.path.join(bam_dir, os.path.basename(bam_src))
                bai_dest = bam_dest + ".bai"
                shutil.copy(bam_src, bam_dest)
                shutil.copy(bai_src, bai_dest)
                entry["bam"] = bam_dest  # Update path in metadata

        # Write all mapping statistics to file (optional)
        if args.mapping_json:
            with open(args.mapping_json, "w") as f:
                json.dump(results, f, indent=2)

        # Select best reference according to user-defined priority
        best = sorted(results, key=get_priority_key(args.priority), reverse=True)[0]

        # Determine consensus output path
        output_consensus = f"{args.output}.consensus.fasta" if not args.output.endswith(".fasta") else args.output

        # Create FASTA header with sample ID, taxid, organism, and reference accession
        ref_accession = best["ref_id"]
        custom_header = f">{args.sample_id}|taxon_{args.taxid}|{args.pathogen}|ref_{ref_accession}"

        # Load consensus and write with new custom header
        record = SeqIO.read(best["consensus"], "fasta")
        record.id = custom_header[1:]  # Remove '>' for ID
        record.description = ""  # Clear description
        with open(output_consensus, "w") as out_f:
            SeqIO.write(record, out_f, "fasta")

        # Copy best BAM and BAI to output
        best_bam_dest = f"{args.output}.bam"
        best_bai_dest = best_bam_dest + ".bai"
        shutil.copy(best["bam"], best_bam_dest)
        shutil.copy(best["bam"] + ".bai", best_bai_dest)

        # Write summary JSON for best reference
        if args.best_json:
            best_output = {
                "sample_id": args.sample_id,
                "taxid": args.taxid,
                "organism": args.pathogen,
                **best["stats"],
                "genome_coverage": best["coverage"],
                "ref_id": best["ref_id"]
            }
            with open(args.best_json, "w") as f:
                json.dump(best_output, f, indent=2)

        # Delete all non-best BAMs if not requested to keep them
        if not args.keep_all_bams:
            for entry in results:
                if entry["bam"] != best["bam"]:
                    try:
                        os.remove(entry["bam"])
                        os.remove(entry["bam"] + ".bai")
                    except Exception as e:
                        logging.warning(f"Failed to remove temp BAMs for {entry['ref_id']}: {e}")

        # Log summary info
        logging.info(f"Best reference: {best['ref_id']} with {best['stats']['mapped_percent']}% mapped and {best['coverage']}% coverage.")
        logging.info(f"Consensus written to: {output_consensus}")
        logging.info(f"Best BAM file: {best_bam_dest}")

# Entrypoint check
if __name__ == "__main__":
    main()
