process GET_GENOTYPES {
     tag "Getting genotypes"
     label 'error_ignore'
     label 'process_medium'
    
    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

    input:
    path fasta_files

    output:
    path "genotypes.tsv"                   , emit: tsv

    script:
    """
    get_genotypes.sh $fasta_files > genotypes.tsv

    """
}