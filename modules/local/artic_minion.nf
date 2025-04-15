
process ARTIC_MINION {
    tag "assembling $filename"
    label 'process_high'
    label 'error_ignore'

    // Fixes compatibility issues on ARM-based machines (e.g., Apple M1, M2, M3)
    beforeScript "export DOCKER_DEFAULT_PLATFORM=linux/amd64"

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/artic-multipurpose:1.2.1' : 
    'docker.io/samordil/artic-multipurpose:1.2.1'}"

    input:
    val model_str
    path model_dir
    path msa_ref_fasta
    path ref_fasta
    path ref_bed
    each path(rawReadsFastq)
     
    output:
    path "${filename}.sorted.bam"                       , emit: bam
    path "${filename}.sorted.bam.bai"                   , emit: bai
    path "${filename}.trimmed.rg.sorted.bam"            , emit: bam_trimmed
    path "${filename}.trimmed.rg.sorted.bam.bai"        , emit: bai_trimmed
    path "${filename}.primertrimmed.rg.sorted.bam"      , emit: bam_primertrimmed
    path "${filename}.primertrimmed.rg.sorted.bam.bai"  , emit: bai_primertrimmed
    path "${filename}.processed.scheme.bed"             , emit: bed
    path "${filename}.consensus.fasta"                  , emit: fasta
    path "${filename}.pass.vcf.gz"                      , emit: vcf
    path "${filename}.pass.vcf.gz.tbi"                  , emit: tbi
    path "${filename}.qc.report.tsv"                    , emit: tsv
    path "${filename}.coverage_mask.txt.depths.png"     , emit: png
    path("*.json"), optional:true                       , emit: json

    script:
    // Check for optional commandline arguments
    def args = task.ext.args ?: ''

    // Check whether MSA file is provided
    def multi_ref_file          = msa_ref_fasta ? "--select-ref-file $msa_ref_fasta" : '' 
    def usr_defined_model       = model_str ? "--model $model_str" : ''
    def usr_defined_model_dir   = model_dir ? "--model-dir $model_dir" : ''

    // Get the name of the file being processed
    filename = rawReadsFastq.simpleName

    """
    artic minion \\
            $usr_defined_model \\
            $usr_defined_model_dir \\
            --threads $task.cpus \\
            --ref $ref_fasta \\
            --bed $ref_bed \\
            $multi_ref_file \\
            --read-file $rawReadsFastq \\
            $filename
    """
}