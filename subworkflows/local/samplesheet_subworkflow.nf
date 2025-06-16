 /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GENERATE_SAMPLESHEET                 } from '../../modules/local/generate_samplesheet'

 /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    END OF MODULE IMPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow PREPARE_SAMPLESHEET {

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        DEFINE DATA INPUT CHANNELS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    // Define input channel for an optional tsv metadata file
    if (params.metadata_tsv) { ch_metadata_tsv = file(params.metadata_tsv) } else { ch_metadata_tsv = [] }


    // Define fastq_pass directory channel
    Channel                                                     // Get raw fastq directory
        .fromPath(params.fastq_dir, type: 'dir', maxDepth: 1)
        .set { ch_fastq_data_dir }

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    END OF DATA INPUT CHANNEL DEFINATIONS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    // Main workflow for samplesheet generation
    main:
        // MODULE: Run bin/viraphly_samplesheet_generator.py to generate samplesheet
        GENERATE_SAMPLESHEET (
            ch_fastq_data_dir,               // raw reads directory channel
            ch_metadata_tsv                  // tsv metadata channel (can be an empty channel)
        )
        
        raw_csv_file = GENERATE_SAMPLESHEET.out.samplesheet

        GENERATE_SAMPLESHEET.out.samplesheet
            .splitCsv(header:true)
            .map { row-> tuple(row.strain_id, file(row.fastq_dir)) }
            .set { ch_samplesheet }
    
    emit:
        raw_samplesheet_csv            = raw_csv_file 
        samplesheet_ch                 = ch_samplesheet    
}