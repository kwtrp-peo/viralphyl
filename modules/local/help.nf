// Function for displaying help
def showHelp() {
    def version = 'git describe --tags --always'.execute().text.trim()
    
    log.info """
    ========================================
            kwtrp/viraphyl Pipeline: ${version}
    ========================================
    
    Usage:
        nextflow run main.nf -profile <profile_name> --fastq_dir  <directory>

    Help Option:
        --help                  Show this message
        --version               Show pipeline version

    Input Options [Files/Directories]:
        --fastq_dir             Path to the directory containing the FASTQ reads (required)
        --multiref_fasta        Path to the file containing multi-aligned sequences (optional)
        --metadata_tsv          Path to the file containing metadata (optional)

    Input Parameters:
        --pathogen              String: one of ["hMPV", "hRV", "hRSVA", "hRSVB", "CA", "CB"] (default: 'hMPV')
        --method                String: one of ["amplicon", "metagenomics"] (default: 'amplicon')

    Output Options:
        --outdir                Path to the directory where results will be saved (default: './Results' in the pipeline run directory)

    Module options
        --skip_assembly         Boolean: If set, skips the genome assembly step (default: false)
        --skip_qc               Boolean: If set, skips the quality check step for FASTQ files (default: true)

    Assembly Step Parameters:
        --normalize             Number to reduce computational burden (default: 1000)
        --min_read_length       Number to filter out raw sequences (default: 50)
        --max_read_length       Number to filter out raw sequences (default: null, meaning no maximum length restriction)

    Primer Scheme Parameters (Required if --method = 'amplicon'):
        --scheme_directory      Path to the directory containing the primer scheme (required for 'amplicon')
        --scheme_name           String name for the scheme (required for 'amplicon')
        --scheme_version        String specifying the scheme version (required for 'amplicon')
        --medaka_model          String for Medaka model (default: 'r1041_e82_400bps_hac_v4.3.0', required for 'amplicon')

    Example:
        nextflow run main.nf --fastq_dir reads/ --outdir Results/
    """
    exit(0)
}

// Function for displaying the pipeline version
def showVersion() {
    def version = 'git describe --tags --always'.execute().text.trim()
    log.info "kwtrp/viraphyl Pipeline: ${version}\n"
    exit(0)
}

