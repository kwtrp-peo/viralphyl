process GENERATE_SAMPLESHEET {
    tag "samplesheet generation"
    label 'process_single'

    container "${workflow.containerEngine == 'singularity' || workflow.containerEngine == 'apptainer' ? 
    'docker://samordil/python-pandas-dateutil:1.0.0' : 
    'docker.io/samordil/python-pandas-dateutil:1.0.0'}"

    input:
        path fastq_dir
        path metadata_tsv

    output:
        path "samplesheet.csv"                          , emit: samplesheet
        path "*without*.csv"    , optional: true      , emit: csv


    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    def metadata  = metadata_tsv ? "--metadata $metadata_tsv" : ""

    """
   samplesheet_generator.py \\
        --directory $fastq_dir \\
        $metadata \\
        --output samplesheet.csv
    """
}