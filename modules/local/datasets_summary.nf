process DATASETS_SUMMARY {
    tag "download $taxon_name global metadata"

    conda "conda-forge::ncbi-datasets-cli"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/ncbi-datasets-pylib:16.6.1--pyhdfd78af_0' :
        'docker.io/biocontainers/ncbi-datasets-cli:16.22.1_cv1' }"

    input:
    val taxon_name
    val host_name

    output:
    path "${taxon_name}.metadata.tsv"                   , emit: tsv
    path "versions.yml"                 , optional:true , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script: // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    def args  = task.ext.args ?: ''
    def args2 = task.ext.args2 ?: ''

    """
    datasets summary virus genome taxon $taxon_name \\
        $args \\
        --host $host_name \\
        --complete-only \\
        --annotated \\
        --as-json-lines | \\
    dataformat tsv virus-genome \\
        $args2 \\
        --fields accession,geo-location,geo-region,isolate-collection-date,length > ${taxon_name}.metadata.tsv

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        datasets download: \$(datasets download --version)
    END_VERSIONS
    """
}
