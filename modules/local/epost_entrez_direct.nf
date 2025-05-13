process EPOST_ENTREZ_DIRECT {
    tag "download $filename global seqeunces"
    label 'process_medium'
    label 'error_retry'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    'https://depot.galaxyproject.org/singularity/entrez-direct:22.4--he881be0_0':
    'biocontainers/entrez-direct:22.4--he881be0_0' }"

    input:
        path accession_file

    output:
        path "${filename}_global.fasta"           , emit: fasta
        path "versions.yml"                        , emit: versions

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    filename = accession_file.simpleName

    """
    epost \\
        -db nuccore \\
        -input $accession_file \\
        -format acc | efetch -format fasta > ${filename}_global.fasta

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        entrez-direct epost: \$(epost -version)
    END_VERSIONS
    """
}