process GET_ASSEMBLY_STATS {
     tag "getting assembly stats"
     label 'error_ignore'
     label 'process_medium'
    
    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

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