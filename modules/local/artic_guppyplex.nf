process ARTIC_GUPPYPLEX {
     tag "$sample_id"
     errorStrategy 'ignore'

    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.6.2' : 
    'docker.io/samordil/artic-multipurpose:1.6.2'}"

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
        --output /dev/stdout | gzip -c > ${sample_id}.fastq.gz
    """
}