process RENAME_FASTA_HEADER {
     tag "Cleaning global dataset"
     label 'error_ignore'
     label 'process_medium'
    
    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

    input:
    path fasta_file
    path tsv_file

    output:
    path "${filename}_header_cleaned.fasta"               , emit: fasta
    path "${filename}_header_cleaned_metadata.tsv"        , emit: tsv

    script:
    filename = fasta_file.simpleName
 
    """
    rename_fasta_headers.py \\
        --fasta $fasta_file \\
        --tsv $tsv_file \\
        --tsv-output ${filename}_header_cleaned_metadata.tsv \\
        --fasta-output ${filename}_header_cleaned.fasta
    """
}