process AUGUR_FILTER {
    tag "subsample $filename gloabal metadata"
    label 'process_medium'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/augur:25.3.0--pyhdfd78af_0' :
        'biocontainers/augur:25.3.0--pyhdfd78af_0' }"

    input:
        path file_tsv
        val seed
        val max_sequence_value
        val subsample_creteria

    output:
        path "${filename}.augur.filtered.tsv"           , emit: subsamples_tsv
        path "versions.yml"                             , emit: versions

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    filename = file_tsv.simpleName

    // Check if seed is -1 then switch to random seed per run
    def seed_value  = seed == -1 ? "" : "--subsample-seed $seed"

    """
    augur \\
        filter \\
            $seed_value \\
            --metadata $file_tsv \\
            --metadata-id-columns accession \\
            --group-by $subsample_creteria  \\
            --subsample-max-sequences $max_sequence_value \\
            --output-metadata ${filename}.augur.filtered.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        augur: \$(augur version)
    END_VERSIONS
    """
}