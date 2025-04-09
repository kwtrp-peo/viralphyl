process ARTIC_GUPPYPLEX {
     tag "$sample_id"
     label 'error_ignore'
     label 'process_medium'
    
    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.0' : 
    'docker.io/samordil/artic-multipurpose:1.2.0'}"

    input:
    tuple val(sample_id), path(fastq_dir)

    output:
    path "${sample_id}.fastq.gz"                      , emit: fastq_gz

    script:
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    artic guppyplex  \
        --directory $fastq_dir  \\
         $args \\
        --output /dev/stdout | pigz -p $task.cpus > ${sample_id}.fastq.gz
    """
}