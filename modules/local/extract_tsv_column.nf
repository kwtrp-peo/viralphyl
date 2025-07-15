process EXTRACT_ACCESSIONS {
    tag "extract $virus_name metadata"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"
    
    input:
    path file_tsv

    output:
    path "${virus_name}.global.accession.tsv"           , emit: acc_tsv
    path "versions.yml"                                 , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script: // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    def args = task.ext.args ?: ''
    virus_name = file_tsv.SimpleName

    """
    extract_tsv_column.py \\
        $args \\
        --input $file_tsv \\
        --column accession \\
        --output ${virus_name}.global.accession.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version)
    END_VERSIONS
    """
}