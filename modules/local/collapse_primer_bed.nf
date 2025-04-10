process COLLAPSE_PRIMER_BED {

     tag "collapsing $filename"
     label 'error_ignore'
     label 'process_single'
    
    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

    input:
    path scheme_bed

    output:
    path "*.collapsed.scheme.bed"                      ,        emit: collapsed_bed

    script:
    // Get the name of the file being processed
    filename = scheme_bed.simpleName

    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    """
    collapse_primer_bed.py \\
        --bed-file $scheme_bed \\
        --output-bed ${filename}.collapsed.scheme.bed \\
        --fix-negatives
    """
}