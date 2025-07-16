 /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GENERATE_SAMPLESHEET as GENERATE_SAMPLESHEET_AMP   } from '../../modules/local/generate_samplesheet'
include { GENERATE_SAMPLESHEET as GENERATE_SAMPLESHEET_META  } from '../../modules/local/generate_samplesheet'


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

        if (params.protocol.toLowerCase() == 'amplicon') {
            // MODULE: Run bin/viraphly_samplesheet_generator.py to generate samplesheet
            GENERATE_SAMPLESHEET_AMP (
                ch_fastq_data_dir,               // raw reads directory channel
                ch_metadata_tsv                  // tsv metadata channel (can be an empty channel)
            )
            
            raw_csv_file = GENERATE_SAMPLESHEET_AMP.out.samplesheet

            GENERATE_SAMPLESHEET_AMP.out.samplesheet
                .splitCsv(header:true)
                .map { row-> tuple(row.strain_id, file(row.fastq_dir)) }
                .set { ch_samplesheet }
        } else if (params.protocol.toLowerCase() == 'metagenomics') {
            // MODULE: Run bin/viraphly_samplesheet_generator.py to generate samplesheet
            GENERATE_SAMPLESHEET_META (
                ch_fastq_data_dir,               // raw reads directory channel
                ch_metadata_tsv                  // tsv metadata channel (can be an empty channel)
            )
            
            raw_csv_file = GENERATE_SAMPLESHEET_META.out.samplesheet

            GENERATE_SAMPLESHEET_META.out.samplesheet
                .splitCsv(header:true)
                .map { row-> tuple(row.strain_id, file(row.fastq_dir)) }
                .set { ch_samplesheet }
        } else {
            error "Invalid protocol specified: ${params.protocol}. Must be 'amplicon' or 'metagenomics'"
        }
    
    emit:
        raw_samplesheet_csv            = raw_csv_file 
        samplesheet_ch                 = ch_samplesheet    
}