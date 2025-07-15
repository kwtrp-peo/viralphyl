process GET_GENOTYPES {
     tag "Getting genotypes"
     label 'error_ignore'
     label 'process_medium'
    
    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

    input:
    path fasta_files

    output:
    path "genotypes.tsv"                   , emit: tsv

    script:
    """
    get_genotypes.sh $fasta_files > genotypes.tsv

    """
}