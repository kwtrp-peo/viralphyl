process PHYLO_COMBINE_TSVS {
     tag "Combine phylogenetics metadata"
     label 'error_ignore'
     label 'process_medium'
    
    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

    input:
    path tsv_files    // [tsv1 tsv2 tsv3 ]

    output:
    path "phylogenetics_metadata.tsv"         , emit: tsv

    script:
    """
     phylo_combine_tsv.py \\
        --tsv $tsv_files \\
        --output phylogenetics_metadata.tsv
    """
}
