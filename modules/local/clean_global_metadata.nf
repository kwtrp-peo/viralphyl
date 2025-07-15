process CLEAN_GLOBAL_METADATA {
    tag "extract $virus_name metadata"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"
    
    input:
    path file_tsv
    val min
    val max

    output:
    path "${virus_name}.cleaned.metadata.tsv"       , emit: meta_tsv
    path "versions.yml"                             , optional:true,  emit: versions

    when:
    task.ext.when == null || task.ext.when

    script: // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    virus_name = file_tsv.SimpleName

    // Check if max is null and assign a default value
    def min_value   = min == -1 ? "" : "--min_length $min"
    def max_value   = max == -1 ? "" : "--max_length $max"

    """
    clean_global_metadata.py \\
        --input_tsv $file_tsv \\
        $min_value \\
        $max_value \\
        --output_file ${virus_name}.cleaned.metadata.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version)
    END_VERSIONS
    """
}