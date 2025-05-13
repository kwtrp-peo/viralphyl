process AUGUR_EXPORT {
    tag "generating auspice report"
    label 'process_medium'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/augur%3A30.0.1--pyhdfd78af_0' :
        'biocontainers/augur:30.0.1--pyhdfd78af_0' }"

    input:
        tuple val(meta) , path(refined_nwk)
        tuple val(meta) , path(metadata_tsv)
        tuple val(meta) , path(branch_len_json)
        tuple val(meta) , path(traits_json)
        tuple val(meta) , path(auspice_config_json)
        tuple val(meta) , path(color_config_tsv)

    output:
        path "global_auspice_tree.json"          ,   emit: auspice_json
        path "versions.yml"                      ,   emit: versions

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    """
    augur \\
        export v2 \\
        --tree $refined_nwk \\
        --metadata $metadata_tsv \\
        --node-data $branch_len_json $traits_json \\
        --auspice-config $auspice_config_json \\
        --colors $color_config_tsv \\
        --output global_auspice_tree.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        augur: \$(augur version)
    END_VERSIONS

    """
}
