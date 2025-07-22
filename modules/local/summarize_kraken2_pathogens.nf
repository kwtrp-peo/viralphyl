process SUMMARIZE_KRAKEN2_PATHOGENS {
    tag "Summarizing Kraken2 pathogens"
    label 'process_single'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_pandas_python-dateutil:d6988e7e56918bdb' :
        'community.wave.seqera.io/library/pip_pandas_python-dateutil:62541a5d0213d960' }"
        
    input:
        path files

    output:
        path "combined_kraken_summary.tsv",             emit: summary

    script:
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    summarize_detected_pathogens.py \\
        $args \\
        --input-file $files \\
        --output combined_kraken_summary.tsv
    """
}