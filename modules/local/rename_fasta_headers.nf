process RENAME_FASTA_HEADER {
     tag "Cleaning global dataset"
     label 'error_ignore'
     label 'process_medium'
    
    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

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