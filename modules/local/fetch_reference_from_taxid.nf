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
    path user_tsv 
    path local_dir_refs

    output:
    tuple val(taxid), path("${taxid}.fasta"),       emit: fasta

    script:
    // Check whether an optional tsv file has been provided
    def user_tsv_file        = user_tsv ? "$user_tsv" : ''

    // Check whether an optional local directory with references fasta has been provided
    def offline_ref_dir      = local_dir_refs ? "$local_dir_refs" : ''

    """
    fetch_ref_1.1.0.sh ${taxid} ${seqid2taxid_map} ${user_tsv_file} ${offline_ref_dir}
    """
}
