#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# fetch_ref.sh (hardened + help)
#
# Download or assemble reference sequences in FASTA format for a given NCBI TaxID
# using:
#   - an official seqid2taxid map
#   - optionally a user-provided TSV
#   - optionally a directory of local FASTA files (accession.{fasta,fa,fna}[.gz])
#
# If a local directory is provided, sequences are taken from there (offline mode).
# Otherwise, sequences are fetched from NCBI (online mode).
#
# USAGE:
#   ./fetch_ref.sh TAXID SEQID2TAXID_MAP [USER_TSV] [LOCAL_REFS_DIR] [CHUNK_SIZE]
#
# DEFAULTS:
#   CHUNK_SIZE = 500
# -----------------------------------------------------------------------------

show_help() {
    cat << EOF
Usage: $0 TAXID SEQID2TAXID_MAP [USER_TSV] [LOCAL_REFS_DIR] [CHUNK_SIZE]

Download or assemble reference sequences in FASTA format for a given NCBI TaxID.

Arguments:
  TAXID             NCBI Taxonomy ID (e.g. 2697049 for SARS-CoV-2)
  SEQID2TAXID_MAP   Path to the official seqid2taxid.map file (from Kraken DB)
  USER_TSV          (Optional) User-provided TSV file, same format as seqid2taxid.map
  LOCAL_REFS_DIR    (Optional) Directory containing local reference FASTAs
                    named as accession.{fasta,fa,fna}[.gz]
  CHUNK_SIZE        (Optional) Number of IDs per NCBI request [default: 500]

Options:
  -h, --help        Show this help message and exit

Examples:
  # Online mode: fetch from NCBI
  $0 2697049 seqid2taxid.map

  # Online mode with user TSV
  $0 2697049 seqid2taxid.map user_extra.tsv

  # Offline mode using local FASTA directory
  $0 2697049 seqid2taxid.map "" my_refs/

  # Increase chunk size for large sets
  $0 2697049 seqid2taxid.map "" "" 1000
EOF
}

# --- check for help flag ---
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    show_help
    exit 0
fi

# --- args ---
if [[ $# -lt 2 ]]; then
    show_help >&2
    exit 1
fi

TAXID="$1"
SEQID2TAXID_MAP="$2"
USER_TSV="${3:-}"
LOCAL_REFS_DIR="${4:-}"
CHUNK_SIZE="${5:-500}"

# --- validation ---
if ! [[ "$TAXID" =~ ^[0-9]+$ ]]; then
    echo "ERROR: TAXID must be numeric. Got: '$TAXID'" >&2
    exit 4
fi

if ! [[ -r "$SEQID2TAXID_MAP" && -f "$SEQID2TAXID_MAP" ]]; then
    echo "ERROR: seqid2taxid map not found or not readable: $SEQID2TAXID_MAP" >&2
    exit 5
fi

if [[ -n "$USER_TSV" && ! ( -r "$USER_TSV" && -f "$USER_TSV" ) ]]; then
    echo "ERROR: user TSV provided but not found or not readable: $USER_TSV" >&2
    exit 6
fi

if [[ -n "$LOCAL_REFS_DIR" && ! -d "$LOCAL_REFS_DIR" ]]; then
    echo "ERROR: local refs directory provided but not a directory: $LOCAL_REFS_DIR" >&2
    exit 7
fi

if ! [[ "$CHUNK_SIZE" =~ ^[0-9]+$ && "$CHUNK_SIZE" -ge 1 ]]; then
    echo "ERROR: CHUNK_SIZE must be a positive integer. Got: '$CHUNK_SIZE'" >&2
    exit 8
fi

# --- safe cleanup handler ---
tmp_out=""
cleanup() {
    if [[ -n "$tmp_out" && -f "$tmp_out" ]]; then rm -f "$tmp_out"; fi
}
trap cleanup EXIT

# --- Step 1. Collect accessions ---
extract_accessions() {
    if [[ -n "$USER_TSV" ]]; then
        awk -v TAXID="$TAXID" -F'\t' '
        {
            n = split($1, a, "|")
            if (a[2] == TAXID) print a[n]
        }' <(cat "$SEQID2TAXID_MAP" <(awk '{gsub(/^[ \t]+|[ \t]+$/, "", $1); gsub(/^[ \t]+|[ \t]+$/, "", $2); gsub(/[ \t]+/, "\t"); print}' "$USER_TSV"))
    else
        awk -v TAXID="$TAXID" -F'\t' '
        {
            n = split($1, a, "|")
            if (a[2] == TAXID) print a[n]
        }' "$SEQID2TAXID_MAP"
    fi
}

mapfile -t raw_accessions < <(extract_accessions | sed '/^[[:space:]]*$/d' | sort -u)

if [[ ${#raw_accessions[@]} -eq 0 ]]; then
    echo "No accessions found for TAXID=$TAXID" >&2
    exit 2
fi

# sanitize
accessions=()
bad_acc=()
for a in "${raw_accessions[@]}"; do
    if [[ "$a" =~ ^[A-Za-z0-9_.-]+$ ]]; then
        accessions+=("$a")
    else
        bad_acc+=("$a")
    fi
done

if [[ ${#accessions[@]} -eq 0 ]]; then
    echo "ERROR: After sanitization, no valid accessions remain for TAXID=$TAXID" >&2
    printf 'Rejected accession: %s\n' "${bad_acc[@]}" >&2
    exit 9
fi

if [[ ${#bad_acc[@]} -gt 0 ]]; then
    echo "Warning: ${#bad_acc[@]} accessions skipped due to invalid characters:" >&2
    printf '%s\n' "${bad_acc[@]}" >&2
fi

# --- Step 2. Offline mode ---
if [[ -n "$LOCAL_REFS_DIR" ]]; then
    echo "Using local refs directory: $LOCAL_REFS_DIR" >&2
    declare -A fasta_index
    shopt -s nullglob
    for f in "$LOCAL_REFS_DIR"/*.fasta "$LOCAL_REFS_DIR"/*.fa "$LOCAL_REFS_DIR"/*.fna \
             "$LOCAL_REFS_DIR"/*.fasta.gz "$LOCAL_REFS_DIR"/*.fa.gz "$LOCAL_REFS_DIR"/*.fna.gz; do
        [[ -e "$f" ]] || continue
        fname=$(basename -- "$f")
        acc="$fname"

        # Strip only known extensions, preserve version numbers
        acc="${acc%.fasta}"
        acc="${acc%.fa}"
        acc="${acc%.fna}"
        acc="${acc%.fasta.gz}"
        acc="${acc%.fa.gz}"
        acc="${acc%.fna.gz}"

        if [[ "$acc" =~ ^[A-Za-z0-9_.-]+$ ]]; then
            fasta_index["$acc"]="$f"
        fi
    done
    shopt -u nullglob

    tmp_out="$(mktemp)"
    found=0
    missing=()
    for acc in "${accessions[@]}"; do
        if [[ -n "${fasta_index[$acc]:-}" ]]; then
            fpath="${fasta_index[$acc]}"
            if [[ "$fpath" == *.gz ]]; then
                zcat -- "$fpath" >> "$tmp_out"
            else
                cat -- "$fpath" >> "$tmp_out"
            fi
            printf '\n' >> "$tmp_out"
            found=$((found+1))
        else
            missing+=("$acc")
        fi
    done

    if [[ $found -eq 0 ]]; then
        rm -f "$tmp_out"
        echo "ERROR: No matching FASTA files found in '$LOCAL_REFS_DIR' for TAXID=$TAXID" >&2
        exit 3
    fi

    mv "$tmp_out" "${TAXID}.fasta"
    tmp_out=""
    echo "Assembled ${TAXID}.fasta from $found local fasta file(s)." >&2
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Warning: ${#missing[@]} accessions not found in local dir:" >&2
        printf '%s\n' "${missing[@]}" >&2
    fi
    trap - EXIT
    exit 0
fi

# --- Step 3. Online mode ---
echo "Fetching from NCBI for TAXID=$TAXID in chunks of $CHUNK_SIZE" >&2
tmp_out="$(mktemp)"
total=${#accessions[@]}
i=0
while (( i < total )); do
    chunk_ids=()
    for ((j=0; j<CHUNK_SIZE && i<total; j++, i++)); do
        chunk_ids+=("${accessions[i]}")
    done
    ids=$(printf "%s," "${chunk_ids[@]}")
    ids="${ids%,}"
    echo "Fetching chunk with ${#chunk_ids[@]} id(s)..." >&2
    if ! epost -db nuccore -id "$ids" | efetch -format fasta >> "$tmp_out"; then
        echo "ERROR: NCBI fetch failed for chunk." >&2
        rm -f "$tmp_out"
        exit 11
    fi
done

mv "$tmp_out" "${TAXID}.fasta"
tmp_out=""
echo "Fetched and assembled ${TAXID}.fasta from NCBI (${total} accession(s))." >&2
trap - EXIT
exit 0
