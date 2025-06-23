process FILTER_PRIORITY_PATHOGENS {
    tag "Filtering pathogens from ${sample_id}"
    label 'process_single'
    label 'error_ignore'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_pandas_python-dateutil:d6988e7e56918bdb' :
        'community.wave.seqera.io/library/pip_pandas_python-dateutil:62541a5d0213d960' }"

    input:
        tuple val(sample_id), path(kraken_summary_tsv)
        each path(taxonki_name2taxid_tsv)

    output:
        tuple val(sample_id), path("${sample_id}.priority.tsv")         , emit: tsv


    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/

    """
    filter_priority_pathogen.py \\
        --kraken $kraken_summary_tsv \\
        --taxonkit $taxonki_name2taxid_tsv \\
        --output  ${sample_id}.priority.tsv
    """
}