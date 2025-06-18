process MASH_REPORT_SUMMARY {
    errorStrategy 'ignore'
    tag "Summarised mash report"
    label 'process_single'
    
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_pandas_python-dateutil:d6988e7e56918bdb' :
        'community.wave.seqera.io/library/pip_pandas_python-dateutil:62541a5d0213d960' }"
    
    input:
        path tsv_file

    output:
        path "mash_summary.tsv"   ,      emit: tsv

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/

    """
   mash_summary.py \\
        --input $tsv_file \\
        --output mash_summary.tsv
    """
}