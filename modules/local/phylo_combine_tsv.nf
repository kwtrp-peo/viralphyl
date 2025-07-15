process PHYLO_COMBINE_TSVS {
     tag "Combine phylogenetics metadata"
     label 'error_ignore'
     label 'process_medium'
    
    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

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
