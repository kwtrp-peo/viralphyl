process COLLAPSE_PRIMER_BED {

     tag "collapsing $filename"
     label 'error_ignore'
     label 'process_single'
    
    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/fieldbio-multiref:1.0.0' : 
    'docker.io/samordil/fieldbio-multiref:1.0.0'}"

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