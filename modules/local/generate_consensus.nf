process GENERATE_CONSENSUS {
    tag "${sample_id}_taxon_${taxid}"
    label 'process_high'

    // Note: the versions here need to match the versions used in the mulled container below and minimap2/index
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/minimap2_samtools_pigz:6d454bf355c27623' :
        'community.wave.seqera.io/library/minimap2_samtools_pigz:e4ab85aa71b479df' }"

    input:
    tuple val(taxid), val(sample_id), path(ref), path(fastq_gz)

    output:
    tuple val("${sample_id}_taxon_${taxid}"), path("${sample_id}_taxon_${taxid}.fasta")      , emit: fasta
    path "versions.yml"                                                                     , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    minimap2 \\
	    -ax map-ont -t $task.cpus $ref $fastq_gz | samtools view --bam -F 4 | samtools sort -o ${sample_id}_taxon_${taxid}.bam

    # Call the consensus
    samtools consensus \\
        $args \\
        --threads $task.cpus ${sample_id}_taxon_${taxid}.bam \\
        -aa \\
        --format fasta | sed "s/^>/>${sample_id}_taxon_${taxid}|/" > ${sample_id}_taxon_${taxid}.fasta

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        minimap2: \$(minimap2 --version 2>&1)
        samtools: \$(echo \$(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*\$//')
    END_VERSIONS

    """
}
