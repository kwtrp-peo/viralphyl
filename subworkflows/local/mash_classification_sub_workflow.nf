/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    PROCESS MASH DATABASE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Subworkflow to provide a valid Mash sketch database:
    - Uses provided .msh file (local or remote)
    - Downloads default Mash RefSeq DB if no input is given

    Input:  Optional Mash sketch path or URL
    Output: Mash sketch file (.msh)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { MASH_SCREEN                   } from '../../modules/nf-core/mash/screen/main'
include { MASH_SKETCH                   } from '../../modules/nf-core/mash/sketch/main'
include { DOWNLOAD_REFERENCE_DATA       } from '../../modules/local/download_reference_data'
include { MASH_REPORT_SUMMARY           } from '../../modules/local/mash_report_summary'


workflow MASH_WORKFLOW {

    take:
        query
        mash_sketch

    main:
        def mash_sketch_str = mash_sketch.toString()

        if (mash_sketch_str.endsWith('.msh')) {
            if (mash_sketch_str.startsWith('http://') ||
                mash_sketch_str.startsWith('https://') ||
                mash_sketch_str.startsWith('ftp://')) {
                
                DOWNLOAD_REFERENCE_DATA(                    // Download existing mash sketch/db
                    channel
                        .value(mash_sketch)
                        .map { [ "Mash database", it ] }
                )
               
               DOWNLOAD_REFERENCE_DATA.out.file
               .map { [ [:], it ] }
               .set { mash_db }

            } else {                                        // Use a provided mash sketch/db
                Channel
                    .fromPath(mash_sketch)
                    .map { [ [:], it ] }
                    .set { mash_db }
            }
        }

        else if (
            (mash_sketch_str.startsWith('http://') || 
             mash_sketch_str.startsWith('https://') || 
             mash_sketch_str.startsWith('ftp://')) &&
            (mash_sketch_str.endsWith('.fna.gz') || 
             mash_sketch_str.endsWith('.fa.gz') || 
             mash_sketch_str.endsWith('.fasta.gz'))
        ) {
            DOWNLOAD_REFERENCE_DATA(                      // Download reference fasta for a custom db
                channel
                    .value(mash_sketch)
                    .map { [ "Genomic data", it ] }
            )

            MASH_SKETCH(                                   // Create a custom mash sketch/db
                DOWNLOAD_REFERENCE_DATA.out.file
                    .map { [ [id: "custom_mash_db"], it ] }
            )

            mash_db = MASH_SKETCH.out.mash
        }

        else {
            error """
            Unsupported Mash reference format: ${mash_sketch_str}
            Supported:
              - Mash sketch (.msh) local or remote
              - Gzipped FASTA (.fna.gz, .fa.gz, .fasta.gz) via URL
            """
        }

        // Now use mash database to classify reads
        MASH_SCREEN (
            query,
            mash_db
        )

        classfication_report   =   MASH_SCREEN.out.screen  
 
        // Summarize the mash screen output for all samples
        MASH_REPORT_SUMMARY (
            MASH_SCREEN.out.screen
            .map {it[1]}.collect()
        )   
        
        final_report =  MASH_REPORT_SUMMARY.out.tsv


    emit:
        db               = mash_db
        report           = classfication_report
        mash_summary     = final_report
}
