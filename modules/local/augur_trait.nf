process AUGUR_TRAIT {
    tag "getting taxa traits"
    label 'process_medium'
    label 'error_ignore'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/augur%3A30.0.1--pyhdfd78af_0' :
        'biocontainers/augur:30.0.1--pyhdfd78af_0' }"

    input:
        tuple val(meta) , path(refined_nwk)
        tuple val(meta) , path(metadata_tsv)

    output:
        path "${filename}_traits.json"           , emit: traits_json
        path "versions.yml"                      , emit: versions

    script:      // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    filename = refined_nwk.simpleName

    """
    augur \\
     traits \\
     --tree $refined_nwk \\
     --metadata $metadata_tsv \\
     --output-node-data ${filename}_traits.json \\
     --columns region country genotype \\
     --confidence

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        augur: \$(augur version)
    END_VERSIONS
    """
}
