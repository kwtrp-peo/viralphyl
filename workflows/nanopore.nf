/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// include { GENERATE_SAMPLESHEET                 } from '../modules/local/generate_samplesheet'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow AMPLICON_BASED {

    // Define metadata_tsv channel
    def ch_metadata_tsv = params.metadata_tsv ? 
        Channel.fromPath(params.metadata_tsv) : 
        Channel.empty()
        ch_metadata_tsv.view()

    // Define fastq_pass directory channel
    Channel                                                     // Get raw fastq directory
        .fromPath(params.fastq_dir, type: 'dir', maxDepth: 1)
        //.set { ch_fastq_data_dir }
        .view()

    // MODULE: Run bin/viraphly_samplesheet_generator.py 
    //
    // GENERATE_SAMPLESHEET (
    //     ch_fastq_data_dir,
    //     ch_metadata_tsv
    // )
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
