process DEPLETE_HUMAN_READS {
    tag "$meta.id"
    label 'process_high'

    // Note: the versions here need to match the versions used in the mulled container below and minimap2/index
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/minimap2_samtools_pigz:6d454bf355c27623' :
        'community.wave.seqera.io/library/minimap2_samtools_pigz:e4ab85aa71b479df' }"

    input:
    // tuple val(meta), path(reads)
    // tuple val(meta2), path(reference)

    tuple val(meta), path(reads), path(reference)

    output:
    tuple val(meta), path("*.non_human_reads.fastq.gz")      , emit: fast_gz
    path "versions.yml"                                      , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    """
    minimap2 \\
        -t $task.cpus \\
        -ax map-ont ${reference} ${reads} | \
        samtools view -b -f 4 | \
        samtools sort | samtools fastq | pigz -p $task.cpus > ${meta.id}.non_human_reads.fastq.gz


    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        minimap2: \$(minimap2 --version 2>&1)
        samtools: \$(echo \$(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*\$//')
    END_VERSIONS

    """
}
