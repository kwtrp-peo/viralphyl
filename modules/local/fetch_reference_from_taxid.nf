process FETCH_FEFERENCE_FASTA {
    tag "Download ref for $taxid"
    label 'process_medium'
    label 'error_retry'

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
    # Get accession from kraken db
    accession=\$(awk -v TAXID=$taxid '\$2 == TAXID { split(\$1, a, "|"); print a[3]; exit }' ${seqid2taxid_map})
    
    # download the reference
    epost -db nuccore -id \$accession | efetch -format fasta > ${taxid}.fasta
    """
}
