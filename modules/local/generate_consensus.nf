process GENERATE_CONSENSUS {
    tag "${sample_id}_taxon_${taxid}"
    label 'process_high'

    // Note: the versions here need to match the versions used in the mulled container below and minimap2/index
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/minimap2_samtools_pip_biopython:bbb619d04ed4d583' :
        'community.wave.seqera.io/library/minimap2_samtools_pip_biopython:74cbfe42612aa285' }"

    input:
    tuple val(taxid), val(sample_id), path(ref), path(fastq_gz), val(pathogen)

    output:
    path "${sample_id}_${taxid}.consensus.fasta"            , emit: fasta
    path "${sample_id}_${taxid}.bam.bai"                    , emit: bai
    path "${sample_id}_${taxid}.bam"                        , emit: bam
    path "${sample_id}_${taxid}_beststat.json"              , emit: beststat_json
    path "${sample_id}_${taxid}_allstats.json"              , emit: allstats_json
    path "${sample_id}_bams",             optional:true     , emit: all_bams
    path "versions.yml"                                     , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    bestref_consensus.py \\
    $args \\
    --threads $task.cpus \\
    --reads $fastq_gz \\
    --msa $ref \\
    --output ${sample_id}_${taxid} \\
    --sample_id ${sample_id} \\
    --taxid ${taxid} \\
    --pathogen "${pathogen}" \\
    --mapping-json ${sample_id}_${taxid}_allstats.json \\
    --best-json ${sample_id}_${taxid}_beststat.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        minimap2: \$(minimap2 --version 2>&1)
        samtools: \$(echo \$(samtools --version 2>&1) | sed 's/^.*samtools //; s/Using.*\$//')
    END_VERSIONS

    """
}
