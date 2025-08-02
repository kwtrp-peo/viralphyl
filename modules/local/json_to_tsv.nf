process METAGENOMICS_ASSEMBLY_STATS {
    tag "Meta assemlby stats"
    label 'process_single'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_pandas_python-dateutil:d6988e7e56918bdb' :
        'community.wave.seqera.io/library/pip_pandas_python-dateutil:62541a5d0213d960' }"
        
    input:
        path files

    output:
        path "metagenomics_assembly_stats.tsv",           emit: stats

    script:
    """
    json_to_tsv.py \\
        --input_json $files \\
        --output metagenomics_assembly_stats.tsv
    """
}