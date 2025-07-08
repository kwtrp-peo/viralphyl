// Function for displaying help
def showHelp() {
    def version = 'git describe --tags --always'.execute().text.trim()
    
    log.info """
    ==================================================
            kwtrp/viraphyl Pipeline: ${version}
    ==================================================

    test Run (Recommended before actual analysis):
        nextflow run main.nf -profile docker,test
    
    Standard Usage:
        nextflow run main.nf [OPTIONS] -profile <PROFILE_NAME> --fastq_dir  <FASTQ_DIR>

    Help Option:
    ------------
        --help                  Show this message
        --version               Show pipeline version


    Input Options [Files/Directories]: 
    ----------------------------------
        --fastq_dir             (required) Path to the base directory containing sequencing runs.  
                                Must contain subdirectories named 'runXX' (e.g., run1, rsv_run2, hmpv_run03_data),  
                                each with 'barcodeXX' folders inside (e.g., barcode01, barcode02).  
 
                                Example structure:
                                --------------------------------------------
                                /path/to/raw_data/
                                ├── run1/
                                │   ├── barcode01/
                                │   ├── barcode02/
                                ├── hMPV_run2_2025/
                                │   ├── barcode01/ 
                                --------------------------------------------

        --metadata_tsv          (optional) Path to a tab-separated values (TSV) metadata file.  
                                Must include 'sequence_run', 'barcode_num', 'sample_id' and 'collection_date' columns.  
                                If provided, samples missing required metadata will be excluded.  
  
                                Example TSV format:
                                --------------------------------------------
                                sequence_run    barcode_num    sample_id    collection_date
                                run1            barcode01      SMP001       2025-04-20
                                run4            barcode01      SMP049       2025-04-27
                                --------------------------------------------

        --multi_ref_file       (Optional) Path to a FASTA MSA reference file. See the "Artic MinION Parameters" section for details.  
        --sequencing_summary   (Optional) Path to ont sequencing summary file generated after Nanopore run completion.


    Input Options:
    --------------
        --viral_taxon           String: Select from ["hMPV", "hRV", "hRSVA", "hRSVB", "CA", "CB"] (default: "hMPV").
        --viral_host            String: Host (default: human)  
        --protocol                Analysis protocol to use: "amplicon" or "metagenomics" (default: "amplicon").


    Output Options:
    ---------------
        --outdir                Path to the directory where results will be saved.  
                                Default: './Results' within the pipeline run directory.  


    Module options
    --------------
        --skip_assembly         Boolean: Skip the assembly step for the selected protocol (nanopore or metagenomic) (default: false)
        --skip_qc               Boolean: If set, skips the quality check step for the selected protocol (default: false)
        --skip_phylogenetics    Boolean: If set, skips the nanopore phylogenetics module (default: false)
        --skip_classification   Boolean: If set, skips the metagenomic classification module (default: false)
        
    Assembly Step Parameters:
    -------------------------
        Artic Guppyplex Parameters:
        ---------------------------
        --min_read_length       Minimum length for raw reads to be retained (Default: 10).  
        --max_read_length       Maximum length for raw reads (Default: null - no maximum length restriction).  
        --min_read_quality      Minimum read quality threshold (Default: null - no quality restriction).  


        Artic MinION Parameters:
        ------------------------
        --normalise             Number normalise down to moderate coverage to save runtime (default: 100, deactivate with `--normalise 0`)
        --multi_ref_file        A FASTA file with multiple aligned references; the closest match is selected. 
                                The primer scheme reference must be included. If the file is not provided, 
                                only the primer scheme reference sequence is used.
        --genotypes             Enable genotype output for the closest reference match. *Requires --multi_ref_file*. [Default: true]
        --no-indel              Do not report InDels (uses SNP-only mode of nanopolish/medaka)(default: InDels are reported).
        --primer-match-threshold 
                                Allow fuzzy primer matching within this threshold (default: 35)
        --min_mapq              Minimum mapping quality to consider (default: 20)              
        --min_depth             Minimum coverage required for a position to be included in the consensus sequence (default: 20)
        --sequence_threshold    Min coverage cutoff for tree construction (0.0-1.0, default: 0.7)

        Reference FASTA and BED file (Required if --protocol="amplicon"):
        --------------------------------------------------------------- 
        --ref_fasta             Reference FASTA sequence for the scheme (required for amplicon mode).
        --ref_bed               BED file containing primer scheme (required for amplicon mode).
        --clair3_model          Clair3 model to use (if not provided, pipeline uses models available in the container).
        --clair3_model_dir      Path to directory containing Clair3 models (defaults to container model directory).


    Phylogenetics Step Parameters:
    ------------------------------
        GLOBAL DATASET OPTIONS:
        -----------------------
        --global_fasta FILE          FASTA file of global genomes (default: download)
        --global_metadata_tsv FILE   TSV file containing global metadata (default: download)
                                     Must include these columns:
                                     - "strain": Unique sequence identifiers
                                     - "country": Country information
                                     - "region": One of the six global continents (Africa, Asia, Europe, N/S America or Oceania)
        --min_sequence_length INT    Minimum sequence length to keep (-1 = no limit, default: -1)
        --max_sequence_length INT    Maximum sequence length to keep (-1 = no limit, default: -1)

        SUBSAMPLING OPTIONS:
        --------------------
        --subsample_seed INT         Seed for subsampling (-1 = random, default: 123)
        --subsample_max_sequences INT Max sequences in tree (default: 250)
        --subsample_by STR           Criteria: "country", "region", "year", etc. (default: "country year month")

        AUGUR AUSPICE OPTIONS
        ---------------------
        --color_by                  Column name in the TSV file to use for coloring (default: 'region')


    Metagenomics Workflow Parameters:
    ------------------------------
        GLOBAL DATASET OPTIONS:
        -----------------------    
        --human_genome              Path to human genome (MMI index, .fna.gz|.fa.gz file, or URL)
                                    Auto-downloaded from NCBI FTP if not provided.
        --classifier                Read classifier to use: 'mash' or 'kraken2' (Default: mash)
        --mash_db                   Mash sketch DB (.msh). Auto-downloaded if not provided.
        --kraken2_db                Kraken2 DB, a link or a db directory. Auto-downloaded if not provided.
        --show_organisms            Number of top organisms to report per sample from the mash classifier (Default: 3) 
        --target_pathogen           Path to a text file with pathogen(s) (one per line) for genome assembly.
                                    Use a single space between words in multi-word names.
        --min_reads_per_taxon       INT   Minimum reads required per taxon (species/strain) to qualify for assembly.

    Example:
    --------
        nextflow run main.nf -profile docker,local --fastq_dir raw_reads/ --outdir Results/ --metadata_tsv metadata.tsv
    """
    exit(0)
}

// Function for displaying the pipeline version
def showVersion() {
    def version = 'git describe --tags --always'.execute().text.trim()
    log.info "kwtrp/viraphyl Pipeline: ${version}\n"
    exit(0)
}
