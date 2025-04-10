#!/usr/bin/env python
import os
import sys
import re
import errno
import argparse


def parse_args(args=None):
    Description = "Collapse LEFT/RIGHT primers in primer BED to single intervals with coordinate validation."
    Epilog = """Example usage: 
    python collapse_primer_bed.py --bed-file input.bed --output-bed output.bed
    python collapse_primer_bed.py -b input.bed -o output.bed -lp _L -rp _R
    """

    parser = argparse.ArgumentParser(description=Description, epilog=Epilog)
    # Required arguments
    parser.add_argument(
        "-b", "--bed-file",
        dest="BED_FILE",
        required=True,
        help="Input BED file containing primer intervals."
    )
    parser.add_argument(
        "-o", "--output-bed",
        dest="OUTPUT_BED",
        required=True,
        help="Output BED file where collapsed intervals will be written."
    )
    # Optional arguments
    parser.add_argument(
        "-lp", "--left-primer-suffix",
        dest="LEFT_PRIMER_SUFFIX",
        default="_LEFT",
        help="Suffix for left primer in name column (default: '_LEFT')."
    )
    parser.add_argument(
        "-rp", "--right-primer-suffix",
        dest="RIGHT_PRIMER_SUFFIX",
        default="_RIGHT",
        help="Suffix for right primer in name column (default: '_RIGHT')."
    )
    parser.add_argument(
        "--fix-negatives",
        dest="FIX_NEGATIVES",
        action="store_true",
        help="Convert negative coordinates to zero before processing."
    )
    return parser.parse_args(args)


def make_dir(path):
    if not len(path) == 0:
        try:
            os.makedirs(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise


def uniqify(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def process_coordinates(fields, fix_negatives=False):
    """Process BED fields and optionally fix negative coordinates."""
    chrom, start, end = fields[0], int(fields[1]), int(fields[2])
    
    if fix_negatives:
        start = max(0, start)
        end = max(0, end)
    
    return (chrom, start, end) + tuple(fields[3:])


def collapse_primer_bed(bed_file, output_bed, left_suffix, right_suffix, fix_negatives=False):
    start_pos_list = []
    interval_dict = {}
    neg_count = 0
    
    with open(bed_file, "r") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            
            fields = line.split("\t")
            if len(fields) < 3:
                continue
                
            # Process coordinates (optionally fixing negatives)
            processed = process_coordinates(fields[:6], fix_negatives)
            chrom, start, end, name, score, strand = processed
            
            # Count corrected negatives
            if fix_negatives:
                if int(fields[1]) < 0 or int(fields[2]) < 0:
                    neg_count += 1
            
            # Remove primer suffixes
            primer = re.sub(rf"(?:{left_suffix}|{right_suffix}).*", "", name)
            if primer not in interval_dict:
                interval_dict[primer] = []
            interval_dict[primer].append((chrom, start, end, score))
            start_pos_list.append((start, primer))
    
    if fix_negatives and neg_count > 0:
        print(f"Fixed {neg_count} negative coordinate(s)", file=sys.stderr)
    
    with open(output_bed, "w") as fout:
        for primer in uniqify([x[1] for x in sorted(start_pos_list)]):
            pos_list = [item for elem in interval_dict[primer] for item in elem[1:3]]
            chrom = interval_dict[primer][0][0]
            start = min(pos_list)
            end = max(pos_list)
            strand = "+"
            score = interval_dict[primer][0][3]
            fout.write(f"{chrom}\t{start}\t{end}\t{primer}\t{score}\t{strand}\n")


def main(args=None):
    args = parse_args(args)
    collapse_primer_bed(
        args.BED_FILE,
        args.OUTPUT_BED,
        args.LEFT_PRIMER_SUFFIX,
        args.RIGHT_PRIMER_SUFFIX,
        args.FIX_NEGATIVES
    )


if __name__ == "__main__":
    sys.exit(main())