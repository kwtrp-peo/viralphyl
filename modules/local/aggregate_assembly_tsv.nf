
process AGGREGATE_ASSEMBLY_TSVS {
    tag "aggregate tsvs"
    label 'process_high'
    label 'error_ignore'

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

    input:
    path text_files
     
    output:
    path "assemlby_module_metadata.tsv"                    , emit: tsv

    script:
    """
    aggregate_assembly_tsvs.py \\
        --input  $text_files \\
        --key strain_id \\
        --sort-by coverage_percent \\
        --output assemlby_module_metadata.tsv
    """
}