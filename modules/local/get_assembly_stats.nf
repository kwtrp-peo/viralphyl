process GET_ASSEMBLY_STATS {
     tag "getting assembly stats"
     label 'error_ignore'
     label 'process_medium'
    
    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

    input:
    path tsv_files

    output:
    path "assembly_stats.tsv"                   , emit: tsv
    path "genome_coverage.png"                  , emit: png

    script:
    """
    get_assembly_stats.py \\
        --tsv-files  $tsv_files\\
        --threads $task.cpus \\
        --output-tsv assembly_stats.tsv \\
        --output-plot genome_coverage.png
    """
}