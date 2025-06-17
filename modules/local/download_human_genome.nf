process DOWNLOAD_HUMAN_GENOME {

    tag "Downloading Human Genome"
    label 'process_low'
    label 'error_retry'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    'oras://community.wave.seqera.io/library/wget:1.21.4--1b359e4e806cc792' :
    'community.wave.seqera.io/library/wget:1.21.4--8b0fcde81c17be5e' }" 

    input:
    val url

    output:
    path "GRCh38.fa.gz"             , emit: gz            

    script:
    """
    wget -q --continue --tries=5 -O GRCh38.fa.gz $url
    """
}
