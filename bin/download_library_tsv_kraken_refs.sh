#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# download_kraken2_refs.sh
#
# Downloads FASTA files from a Kraken2 library_report.tsv using URLs.
# Supports parallel downloads, retries, resume, throttling, and live progress.
# Fully portable (macOS/Linux, Bash 3.x/4.x), no flock or temp files.
# -----------------------------------------------------------------------------

if [[ $# -lt 2 || "$1" == "-h" || "$1" == "--help" ]]; then
    cat << EOF
Usage: $0 LIB_REPORT OUTDIR [PARALLEL] [RESUME] [RETRIES] [THROTTLE]

ARGUMENTS:
  LIB_REPORT   Kraken2 library_report.tsv
  OUTDIR       Directory to store FASTA files
  PARALLEL     Optional: number of parallel downloads (default = CPU cores)
  RESUME       Optional: "resume" or "noresume" (default = resume)
  RETRIES      Optional: number of retries (default = 3)
  THROTTLE     Optional: delay between downloads in seconds (default = 0.5)
EOF
    exit 0
fi

LIB_REPORT="$1"
OUTDIR="$2"
PARALLEL="${3:-$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)}"
RESUME="${4:-resume}"
RETRIES="${5:-3}"
THROTTLE="${6:-0.5}"

mkdir -p "$OUTDIR"
LOG_FILE="$OUTDIR/download.log"
FAILED_FILE="$OUTDIR/failed_downloads.tsv"

: > "$LOG_FILE"
: > "$FAILED_FILE"

# --- Total records and progress ---
TOTAL=$(tail -n +2 "$LIB_REPORT" | wc -l)
DONE=0

update_progress() {
    local percent=$((DONE*100/TOTAL))
    local filled=$((percent/2))
    local empty=$((50-filled))
    local bar=$(printf "%0.s#" $(seq 1 $filled))
    local spaces=$(printf "%0.s-" $(seq 1 $empty))
    echo -ne "Progress: [$bar$spaces] $percent% ($DONE/$TOTAL)\r"
}

# --- Determine download command ---
if command -v curl >/dev/null 2>&1; then
    if [[ "$RESUME" == "resume" ]]; then
        DL_CMD="curl -sS -L --retry 3 -C -"
    else
        DL_CMD="curl -sS -L --retry 3"
    fi
elif command -v wget >/dev/null 2>&1; then
    if [[ "$RESUME" == "resume" ]]; then
        DL_CMD="wget -qO- -c"
    else
        DL_CMD="wget -qO-"
    fi
else
    echo "Error: Neither curl nor wget is available." >&2
    exit 1
fi

# --- Download function ---
download_file() {
    local seqname="$1"
    local url="$2"
    local acc
    acc=$(echo "$seqname" | cut -d' ' -f1 | tr -cd '[:alnum:]_.')
    local out="$OUTDIR/$acc.fasta"

    if [[ -f "$out" ]]; then
        echo "$(date '+%F %T') [SKIP] $acc already exists" >> "$LOG_FILE"
        return 0
    fi

    local attempt=0
    local success=0
    while (( attempt < RETRIES )); do
        ((attempt++))
        echo "$(date '+%F %T') [START] $acc from $url (attempt $attempt)" >> "$LOG_FILE"

        if $DL_CMD "$url" 2>/dev/null | gunzip -t >/dev/null 2>&1; then
            if $DL_CMD "$url" | gunzip > "$out"; then
                echo "$(date '+%F %T') [OK] $acc downloaded (gzipped)" >> "$LOG_FILE"
                success=1
                break
            fi
        else
            if $DL_CMD "$url" > "$out"; then
                echo "$(date '+%F %T') [OK] $acc downloaded (plain)" >> "$LOG_FILE"
                success=1
                break
            fi
        fi

        echo "$(date '+%F %T') [FAIL] $acc attempt $attempt failed" >> "$LOG_FILE"
        sleep $((2**(attempt-1)))
    done

    if (( success == 0 )); then
        echo -e "$seqname\t$url" >> "$FAILED_FILE"
    fi

    sleep "$THROTTLE"
    return 0
}

# --- Main loop with portable parallel queue ---
pids=()
while IFS=$'\t' read -r _ seqname url; do
    download_file "$seqname" "$url" &
    pids+=($!)

    while (( ${#pids[@]} >= PARALLEL )); do
        for i in "${!pids[@]}"; do
            if ! kill -0 "${pids[i]}" 2>/dev/null; then
                ((DONE++))
                update_progress
                unset 'pids[i]'
            fi
        done
        # Reindex array safely
        if (( ${#pids[@]} )); then
            pids=("${pids[@]}")
        else
            pids=()
        fi
        sleep 0.1
    done
done < <(tail -n +2 "$LIB_REPORT")

# Wait for remaining jobs
for pid in "${pids[@]}"; do
    wait "$pid"
    ((DONE++))
    update_progress
done

echo -e "\nDownload complete."
echo "Log file: $LOG_FILE"
echo "Failed downloads (if any): $FAILED_FILE"
