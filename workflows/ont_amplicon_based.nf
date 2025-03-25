/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
 include  { GENERATE_SAMPLESHEET                 } from '../modules/local/generate_samplesheet'
  include { ARTIC_GUPPYPLEX                      } from '../modules/local/artic_guppyplex'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow AMPLICON_BASED {

    // Define input channel for an optional tsv metadata file
    if (params.metadata_tsv) { ch_metadata_tsv = file(params.metadata_tsv) } else { ch_metadata_tsv = [] }


    // Define fastq_pass directory channel
    Channel                                                     // Get raw fastq directory
        .fromPath(params.fastq_dir, type: 'dir', maxDepth: 1)
        .set { ch_fastq_data_dir }

    // MODULE: Run bin/viraphly_samplesheet_generator.py to generate samplesheet
    GENERATE_SAMPLESHEET (
        ch_fastq_data_dir,               // raw reads directory channel
        ch_metadata_tsv                  // tsv metadata channel (can be an empty channel)
    )
     GENERATE_SAMPLESHEET.out.samplesheet
        .splitCsv(header:true)
        .map { row-> tuple(row.strain_id, file(row.fastq_dir)) }
        .set { ch_samplesheet }

    // ch_samplesheet.view()

    // MODULE: Run artic guppyplex
    ARTIC_GUPPYPLEX (
        ch_samplesheet
    )

    // ARTIC_GUPPYPLEX.out.fastq_gz.view()       
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
