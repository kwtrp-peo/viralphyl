process AUSPICE_CONFIG {
    tag "Generating auspice configurations"
    label 'process_medium'

    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

    input:
        tuple val(meta) , path(metadata_tsv)

    output:
        path "auspice_config.json"                      , emit: json
        path "colors.tsv"                               , emit: tsv
        path "versions.yml"                             , emit: versions

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    generate_auspice_config.py \\
        $args \\
        --input $metadata_tsv \\
        --json auspice_config.json \\
        --colors colors.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python version)
    END_VERSIONS
    """
}