process AUSPICE_CONFIG {
    tag "Generating auspice configurations"
    label 'process_medium'

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

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