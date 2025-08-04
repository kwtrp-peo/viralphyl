process FETCH_FEFERENCE_FASTA {
    tag "Download ref for $taxid"
    label 'process_medium'
    label 'error_ignore'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    'https://depot.galaxyproject.org/singularity/entrez-direct:22.4--he881be0_0':
    'biocontainers/entrez-direct:22.4--he881be0_0' }"

    input:
    val(taxid)          
    path(seqid2taxid_map)

    output:
    tuple val(taxid), path("${taxid}.fasta"),       emit: fasta

    script:
    """
    # Extract all accessions for the given taxid from the seqid2taxid map
    accessions=\$(awk -v TAXID=${taxid} -F'\t' '\$2 == TAXID { n = split(\$1, a, "|"); print a[n] }' ${seqid2taxid_map} | paste -sd "," -)

    # Download the reference sequences in FASTA format
    epost -db nuccore -id "\$accessions" | efetch -format fasta > "${taxid}.fasta"

    """
}
