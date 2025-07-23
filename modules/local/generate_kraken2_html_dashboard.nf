process GENERATE_KRAKEN2_HTML_DASHBOARD {
    tag "Generating html file"
    label 'process_single'
    label 'error_ignore'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_pandas_python-dateutil:d6988e7e56918bdb' :
        'community.wave.seqera.io/library/pip_pandas_python-dateutil:62541a5d0213d960' }"

    input:
        path files

    output:
        path "metagenomic_dashboard.html"     , emit: html

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    """
    generate_dashboard.py \\
        --json $files \\
        --title "Classification Results Dashboard" \\
        --output metagenomic_dashboard.html
    """
}