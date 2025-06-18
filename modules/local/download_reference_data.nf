process DOWNLOAD_REFERENCE_DATA {

    tag "${meta}"
    label 'process_low'
    label 'error_retry'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    'oras://community.wave.seqera.io/library/wget:1.21.4--1b359e4e806cc792' :
    'community.wave.seqera.io/library/wget:1.21.4--8b0fcde81c17be5e' }" 

    input:
    tuple val(meta) , val(url)

    output:
    path "$filename"             , emit: file            

    script:

    // Set filename in Groovy
    filename = url.tokenize('/')[-1]

    """
    wget -q --continue --tries=5 -O $filename $url
    """
}
