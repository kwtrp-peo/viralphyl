process FASTA_META_FILTER {

     tag "cleaning genomes"
     //label 'error_ignore'
     label 'process_single'
    
    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

    input:
    path fasta_seqs
    path tsv_file

    output:
    path "all_sequences.tsv"                 , emit: all_tsv
    path "all_sequences.fasta"               , emit: all_fasta
    path "coverage.png"                      , emit: all_png
    path "high_coverage.fasta"               , emit: high_coverage_fasta
    path "high_coverage.tsv"                 , emit: high_coverage_tsv
   
    script:
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    fasta_meta_filter.py \\
        --input-fasta $fasta_seqs \\
        --tsv-output all_sequences.tsv \\
        --fasta-output all_sequences.fasta \\
        --filtered-tsv high_coverage.tsv \\
        --filtered-fasta high_coverage.fasta \\
        --merge-tsv $tsv_file \\
        --coverage-plot coverage.png \\
        $args
    """
}