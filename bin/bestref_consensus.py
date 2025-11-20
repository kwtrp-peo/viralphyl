#!/usr/bin/env python3

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
from concurrent.futures import ProcessPoolExecutor, as_completed
from Bio import SeqIO

# ==========================
# Utility Functions
# ==========================
def run_command(command, input_data=None):
    """Run a command safely (no shell=True) and return stdout."""
    logging.info(f"Running: {' '.join(command)}")
    result = subprocess.run(
        command,
        input=input_data,
        capture_output=True,
        text=True,
        check=False
    )
    if result.returncode != 0:
        logging.error(f"Command failed: {' '.join(command)}\n{result.stderr}")
        raise RuntimeError(f"Command failed: {' '.join(command)}\n{result.stderr}")
    return result.stdout


def safe_id(description):
    """Convert reference description to safe filename."""
    first_word = description.split()[0]
    return re.sub(r"[^\w.-]", "_", first_word)


# ==========================
# Core Functions
# ==========================
def generate_consensus(reads_path, ref_path, output_prefix, threads, min_depth):
    """Align reads and generate consensus sequence."""
    bam_file = f"{output_prefix}.bam"
    consensus_file = f"{output_prefix}.fasta"

    logging.info(f"Generating BAM and consensus for {ref_path} -> {bam_file}")

    # Align reads and sort BAM
    with subprocess.Popen(
        ["minimap2", "-ax", "map-ont", "-t", str(threads), ref_path, reads_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    ) as minimap2_proc:
        with subprocess.Popen(
            ["samtools", "sort", "-@", str(threads), "-o", bam_file],
            stdin=minimap2_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ) as samtools_proc:
            minimap2_proc.stdout.close()
            _, samtools_err = samtools_proc.communicate()

        minimap2_stdout, minimap2_err = minimap2_proc.communicate()
        if minimap2_proc.returncode != 0:
            raise RuntimeError(f"minimap2 failed:\n{minimap2_err.decode()}")
        if samtools_proc.returncode != 0:
            raise RuntimeError(f"samtools sort failed:\n{samtools_err.decode()}")

    # Index BAM
    run_command(["samtools", "index", bam_file])

    # Generate consensus
    consensus_result = run_command([
        "samtools", "consensus",
        "--min-depth", str(min_depth),
        "--threads", str(threads),
        "-aa", "--format", "fasta",
        bam_file
    ])

    with open(consensus_file, "w") as f:
        f.write(consensus_result)

    return consensus_file, bam_file


def parse_consensus_coverage(consensus_fasta):
    """Calculate % of bases not N."""
    record = SeqIO.read(consensus_fasta, "fasta")
    total_len = len(record.seq)
    covered_bases = total_len - record.seq.upper().count("N")
    return round((covered_bases / total_len) * 100, 2)


def parse_bam_stats(bam_file):
    """Parse stats from samtools flagstat."""
    result = run_command(["samtools", "flagstat", "-O", "json", bam_file])
    stats_json = json.loads(result)

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


def process_reference(ref_record, reads_path, threads, tempdir, min_depth, sample_id):
    """Process one reference: generate consensus and BAM."""
    ref_id = safe_id(ref_record.description)
    ref_fasta = os.path.join(tempdir, f"{ref_id}.fa")
    SeqIO.write(ref_record, ref_fasta, "fasta")

    prefix = os.path.join(tempdir, f"{sample_id}_{ref_id}_output")

    try:
        consensus_path, bam_path = generate_consensus(reads_path, ref_fasta, prefix, threads, min_depth)
        coverage = parse_consensus_coverage(consensus_path)
        stats = parse_bam_stats(bam_path)
        score = stats["mapped"] * (coverage / 100)
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


def get_priority_key(priority):
    return {
        "mapped": lambda x: (x["stats"]["mapped"], x["coverage"]),
        "coverage": lambda x: (x["coverage"], x["stats"]["mapped"]),
        "score": lambda x: x["score"]
    }[priority]


# ==========================
# Main Script
# ==========================
def main():
    parser = argparse.ArgumentParser(description="Select best reference after consensus")
    parser.add_argument("--reads", required=True)
    parser.add_argument("--msa", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mapping-json")
    parser.add_argument("--best-json")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--min_depth", type=int, default=10)
    parser.add_argument("--workers", type=int, default=None)
    parser.add_argument("--sample_id", required=True)
    parser.add_argument("--taxid", required=True)
    parser.add_argument("--pathogen", required=True)
    parser.add_argument("--keep_all_bams", action="store_true")
    parser.add_argument("--priority", choices=["mapped", "coverage", "score"], default="mapped")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    cpu_count = multiprocessing.cpu_count()
    workers = args.workers or max(1, cpu_count - 1)
    logging.info(f"Using {workers} parallel workers out of {cpu_count} CPU cores.")

    references = list(SeqIO.parse(args.msa, "fasta"))
    if not references:
        logging.error("No references found in MSA.")
        sys.exit(1)

    output_dir = os.path.dirname(args.output)
    bam_dir = None
    if args.keep_all_bams:
        bam_dir = os.path.join(output_dir, f"{args.sample_id}_bams")
        os.makedirs(bam_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        futures = []
        results = []

        with ProcessPoolExecutor(max_workers=workers) as executor:
            for ref in references:
                futures.append(
                    executor.submit(process_reference, ref, args.reads, args.threads, tmpdir, args.min_depth, args.sample_id)
                )
            for future in as_completed(futures):
                res = future.result()
                if res:
                    results.append(res)

        if not results:
            logging.error("All references failed during processing.")
            sys.exit(1)

        # Keep all BAMs if requested
        if args.keep_all_bams:
            for entry in results:
                bam_src = entry["bam"]
                bai_src = bam_src + ".bai"
                bam_dest = os.path.join(bam_dir, os.path.basename(bam_src))
                bai_dest = bam_dest + ".bai"
                shutil.copy(bam_src, bam_dest)
                shutil.copy(bai_src, bai_dest)
                entry["bam"] = bam_dest

        # Save mapping stats for all references
        if args.mapping_json:
            with open(args.mapping_json, "w") as f:
                json.dump(results, f, indent=2)

        # Select best reference
        best = sorted(results, key=get_priority_key(args.priority), reverse=True)[0]

        output_consensus = f"{args.output}.consensus.fasta" if not args.output.endswith(".fasta") else args.output
        ref_accession = best["ref_id"]
        custom_header = f">{args.sample_id}|taxon_{args.taxid}|{args.pathogen}|ref_{ref_accession}"

        record = SeqIO.read(best["consensus"], "fasta")
        record.id = custom_header[1:]
        record.description = ""
        with open(output_consensus, "w") as out_f:
            SeqIO.write(record, out_f, "fasta")

        best_bam_dest = f"{args.output}.bam"
        best_bai_dest = best_bam_dest + ".bai"
        shutil.copy(best["bam"], best_bam_dest)
        shutil.copy(best["bam"] + ".bai", best_bai_dest)

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

        # Clean up temporary BAMs if not keeping all
        if not args.keep_all_bams:
            for entry in results:
                if entry["bam"] != best["bam"]:
                    try:
                        os.remove(entry["bam"])
                        os.remove(entry["bam"] + ".bai")
                    except Exception as e:
                        logging.warning(f"Failed to remove temp BAMs for {entry['ref_id']}: {e}")

        logging.info(f"Best reference: {best['ref_id']} with {best['stats']['mapped_percent']}% mapped and {best['coverage']}% coverage.")
        logging.info(f"Consensus written to: {output_consensus}")
        logging.info(f"Best BAM file: {best_bam_dest}")


if __name__ == "__main__":
    main()
