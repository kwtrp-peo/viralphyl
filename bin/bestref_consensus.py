#!/usr/bin/env python3
"""
Select Best Reference - Consensus & Mapping Tool
Version: 1.2.0
"""

__version__ = "1.2.0"

import argparse
import json
import logging
import shutil
import subprocess
import sys
import tempfile
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from Bio import SeqIO

# ==========================
# Safe Command Execution
# ==========================
def run_command(command):
    """Run a command safely without shell=True."""
    logging.info(f"Running: {' '.join(command)}")
    result = subprocess.run(
        command,
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
# Coverage Analysis
# ==========================
def get_coverage_data(bam_file, threads=1):
    """Get coverage depth at each position."""
    cmd = ["samtools", "depth", "-aa", "--threads", str(threads), str(bam_file)]
    depth_output = run_command(cmd)
    
    positions = []
    depths = []
    
    for line in depth_output.strip().split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 3:
                positions.append(int(parts[1]))
                depths.append(int(parts[2]))
    
    return positions, depths

def create_coverage_plot(bam_file, ref_id, sample_id, output_path, pathogen, threads=1, min_depth=10):
    """Generate coverage plot for the best reference genome."""
    try:
        positions, depths = get_coverage_data(bam_file, threads)
        
        if not positions:
            logging.warning(f"No coverage data for {ref_id}")
            return None
        
        ref_length = len(positions)
        
        plt.figure(figsize=(15, 6))
        plt.fill_between(positions, depths, alpha=0.4, color='#2E86AB', linewidth=0)
        plt.plot(positions, depths, color='#2E86AB', alpha=0.9, linewidth=1.2)
        plt.xlabel('Genomic Position', fontsize=12)
        plt.ylabel('Coverage Depth', fontsize=12)
        plt.title(f'Coverage Plot: {sample_id} | Pathogen: {pathogen} | Ref: {ref_id}', fontsize=14, pad=20)
        plt.grid(True, alpha=0.3)
        plt.yscale('log')
        
        # Set y-axis ticks
        if depths:
            max_depth = max(depths)
            y_ticks = [1, 5, 10, 20, 50, 100, 500, 1000, 5000, 10000, 50000]
            y_ticks = [t for t in y_ticks if t <= max_depth * 2]
            plt.yticks(y_ticks, [str(t) for t in y_ticks])
        
        # Add statistics
        if depths:
            mean_depth = np.mean(depths)
            median_depth = np.median(depths)
            coverage_above_min = sum(1 for d in depths if d >= min_depth) / len(depths) * 100
            max_depth_val = max(depths)
            
            stats_text = f"Mean depth: {mean_depth:.1f}x\nMedian depth: {median_depth:.1f}x\n{min_depth}x coverage: {coverage_above_min:.1f}%\nMax depth: {max_depth_val}x"
            plt.annotate(stats_text, xy=(0.02, 0.98), xycoords='axes fraction', 
                        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                        fontsize=10)
        
        plt.axhline(y=min_depth, color='red', linestyle='--', alpha=0.8, linewidth=1.2, 
                   label=f'Consensus threshold ({min_depth}x) | Ref: {ref_length:,} bp')
        plt.legend(loc='upper right')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        logging.info(f"Coverage plot generated: {output_path}")
        return output_path
        
    except Exception as e:
        logging.warning(f"Failed to generate coverage plot: {e}")
        return None

def get_coverage_statistics(bam_file, threads=1, min_depth=10):
    """Calculate comprehensive coverage statistics."""
    positions, depths = get_coverage_data(bam_file, threads)
    
    if not depths:
        return {
            "mean_depth": 0,
            "median_depth": 0,
            "max_depth": 0,
            f"coverage_above_{min_depth}x": 0,
            "genome_length": 0,
            "covered_positions": 0
        }
    
    total_positions = len(depths)
    depths_array = np.array(depths)
    
    return {
        "mean_depth": float(np.mean(depths_array)),
        "median_depth": float(np.median(depths_array)),
        "max_depth": int(np.max(depths_array)),
        f"coverage_above_{min_depth}x": float(np.sum(depths_array >= min_depth) / total_positions * 100),
        "genome_length": total_positions,
        "covered_positions": int(np.sum(depths_array > 0))
    }

# ==========================
# Core Alignment Functions
# ==========================
def generate_consensus(reads_path, ref_path, output_prefix, threads, min_depth):
    """Align reads and generate consensus sequence."""
    bam_file = f"{output_prefix}.bam"
    consensus_file = f"{output_prefix}.fasta"

    logging.info(f"Generating BAM and consensus for {ref_path}")
    
    # Align reads and sort BAM
    with subprocess.Popen(
        ["minimap2", "-ax", "map-ont", "-t", str(threads), str(ref_path), str(reads_path)],
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
    result = run_command([
        "samtools", "consensus",
        "--min-depth", str(min_depth),
        "--threads", str(threads),
        "-aa", "--format", "fasta",
        bam_file
    ])

    with open(consensus_file, "w") as f:
        f.write(result)

    return consensus_file, bam_file

def parse_consensus_coverage(consensus_fasta):
    """Calculate % of bases not N."""
    record = SeqIO.read(consensus_fasta, "fasta")
    total_len = len(record.seq)
    covered_bases = total_len - record.seq.upper().count("N")
    return round((covered_bases / total_len) * 100, 2)

def parse_bam_stats(bam_file):
    """Parse stats from samtools flagstat."""
    result = run_command(["samtools", "flagstat", "-O", "json", str(bam_file)])
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

# ==========================
# Reference Processing
# ==========================
def process_reference(ref_record, reads_path, threads, tempdir, min_depth, sample_id):
    """Process one reference: generate consensus and BAM."""
    ref_id = safe_id(ref_record.description)
    ref_fasta = Path(tempdir) / f"{ref_id}.fa"
    SeqIO.write(ref_record, ref_fasta, "fasta")

    prefix = Path(tempdir) / f"{sample_id}_{ref_id}_output"

    try:
        consensus_path, bam_path = generate_consensus(reads_path, str(ref_fasta), str(prefix), threads, min_depth)
        coverage = parse_consensus_coverage(consensus_path)
        stats = parse_bam_stats(bam_path)
        coverage_stats = get_coverage_statistics(bam_path, threads)
        score = stats["mapped"] * (coverage / 100)
    except Exception as e:
        logging.warning(f"Failed to process reference {ref_id}: {e}")
        return None

    return {
        "sample_id": sample_id,
        "ref_id": ref_id,
        "coverage": coverage,
        "stats": stats,
        "coverage_stats": coverage_stats,
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
# Main Function
# ==========================
def main():
    parser = argparse.ArgumentParser(description="Select best reference after consensus")
    parser.add_argument("--reads", required=True, help="Input FASTQ(.gz)")
    parser.add_argument("--msa", required=True, help="Multi-FASTA file of reference genomes")
    parser.add_argument("--output", required=True, help="Output prefix or directory")
    parser.add_argument("--mapping-json", help="Optional: output all reference mapping stats")
    parser.add_argument("--best-json", help="Optional: output best reference mapping stats")
    parser.add_argument("--threads", type=int, default=4, help="Threads per job (default: 4)")
    parser.add_argument("--min_depth", type=int, default=10, help="Minimum depth for consensus generation (default: 10)")
    parser.add_argument("--workers", type=int, default=None, help="Parallel jobs. Defaults to --threads if not specified")
    parser.add_argument("--sample_id", required=True, help="Sample ID (e.g., run1_bc01)")
    parser.add_argument("--taxid", required=True, help="NCBI taxon ID")
    parser.add_argument("--pathogen", required=True, help="Pathogen name (e.g., Zaire ebolavirus)")
    parser.add_argument("--keep_all_bams", action="store_true", help="If set, all BAMs and indices are retained")
    parser.add_argument("--coverage_plot", action="store_true", help="Generate coverage plot for best reference")
    parser.add_argument("--priority", choices=["mapped", "coverage", "score"], default="mapped", 
                       help="Metric to prioritize for best reference selection (default: mapped)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Safe worker allocation - no CPU detection
    workers = args.workers if args.workers is not None else args.threads
    logging.info(f"Using {workers} parallel workers")

    # Load reference sequences
    references = list(SeqIO.parse(args.msa, "fasta"))
    if not references:
        logging.error("No references found in MSA.")
        sys.exit(1)

    output_path = Path(args.output)
    output_dir = output_path.parent if output_path.parent != Path(".") else Path(".")

    # Create BAM directory if requested
    bam_dir = None
    if args.keep_all_bams:
        bam_dir = output_dir / f"{args.sample_id}_bams"
        bam_dir.mkdir(exist_ok=True)

    # Process all references
    with tempfile.TemporaryDirectory() as tmpdir:
        tasks = [(ref, args.reads, args.threads, tmpdir, args.min_depth, args.sample_id) 
                for ref in references]

        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(lambda x: process_reference(*x), tasks))

        results = [r for r in results if r]

        if not results:
            logging.error("All references failed during processing.")
            sys.exit(1)

        # Keep all BAMs if requested
        if args.keep_all_bams:
            for entry in results:
                bam_src = Path(entry["bam"])
                bai_src = Path(entry["bam"] + ".bai")
                bam_dest = bam_dir / bam_src.name
                bai_dest = bam_dir / bai_src.name
                shutil.copy(bam_src, bam_dest)
                shutil.copy(bai_src, bai_dest)
                entry["bam"] = str(bam_dest)

        # Save mapping stats for all references
        if args.mapping_json:
            with open(args.mapping_json, "w") as f:
                json.dump(results, f, indent=2)

        # Select best reference
        best = sorted(results, key=get_priority_key(args.priority), reverse=True)[0]

        # Generate coverage plot if requested
        coverage_plot_path = None
        if args.coverage_plot:
            plot_filename = f"{args.sample_id}_{args.taxid}_coverage.png"
            coverage_plot_path = str(output_dir / plot_filename)
            best_coverage_stats = get_coverage_statistics(best["bam"], args.threads, args.min_depth)
            create_coverage_plot(best["bam"], best["ref_id"], args.sample_id, coverage_plot_path, 
                               args.pathogen, args.threads, args.min_depth)
            best["coverage_stats"] = best_coverage_stats
            logging.info(f"Generated coverage plot: {coverage_plot_path}")

        # Write consensus
        if not args.output.endswith(".fasta"):
            output_consensus = f"{args.output}.consensus.fasta"
        else:
            output_consensus = args.output

        ref_accession = best["ref_id"]
        custom_header = f">{args.sample_id}|taxon_{args.taxid}|{args.pathogen}|ref_{ref_accession}"

        record = SeqIO.read(best["consensus"], "fasta")
        record.id = custom_header[1:]
        record.description = ""
        with open(output_consensus, "w") as out_f:
            SeqIO.write(record, out_f, "fasta")

        # Copy best BAM
        best_bam_dest = f"{args.output}.bam"
        best_bai_dest = best_bam_dest + ".bai"
        shutil.copy(best["bam"], best_bam_dest)
        shutil.copy(best["bam"] + ".bai", best_bai_dest)

        # Save best reference stats
        if args.best_json:
            best_output = {
                "sample_id": args.sample_id,
                "taxid": args.taxid,
                "organism": args.pathogen,
                **best["stats"],
                "genome_coverage": best["coverage"],
                "coverage_statistics": best.get("coverage_stats", {}),
                "ref_id": best["ref_id"],
                "coverage_plot": coverage_plot_path
            }
            with open(args.best_json, "w") as f:
                json.dump(best_output, f, indent=2)

        # Clean up temporary BAMs if not keeping all
        if not args.keep_all_bams:
            for entry in results:
                if entry["bam"] != best["bam"]:
                    try:
                        Path(entry["bam"]).unlink(missing_ok=True)
                        Path(entry["bam"] + ".bai").unlink(missing_ok=True)
                    except Exception as e:
                        logging.warning(f"Failed to remove temp BAMs for {entry['ref_id']}: {e}")

        # Final logging
        logging.info(f"Best reference: {best['ref_id']} with {best['stats']['mapped_percent']}% mapped and {best['coverage']}% coverage.")
        if args.coverage_plot and best.get("coverage_stats"):
            stats = best["coverage_stats"]
            logging.info(f"Coverage statistics - Mean: {stats['mean_depth']:.1f}x")
        logging.info(f"Consensus written to: {output_consensus}")
        logging.info(f"Best BAM file: {best_bam_dest}")

if __name__ == "__main__":
    main()
