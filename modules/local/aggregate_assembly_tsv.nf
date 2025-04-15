
process AGGREGATE_ASSEMBLY_TSVS {
    tag "aggregate tsvs"
    label 'process_high'
    // label 'error_ignore'

    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

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