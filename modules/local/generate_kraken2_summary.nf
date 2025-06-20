process GENERATE_KRAKEN2_SUMMARY {
    tag "summarise ${meta.id}"
    label 'process_single'
    label 'error_ignore'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_pandas_python-dateutil:d6988e7e56918bdb' :
        'community.wave.seqera.io/library/pip_pandas_python-dateutil:62541a5d0213d960' }"

    input:
        tuple val(meta), path(kraken_output)

    output:
        path "${meta.id}.json"           , emit: json
        path "${meta.id}.tsv"            , emit: tsv


    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/

    """
    kraken_summary.py \\
        --kraken_files $kraken_output \\
        --sample ${meta.id} \\
        --json ${meta.id}.json \\
        --tsv ${meta.id}.tsv
    """
}