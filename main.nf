#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    kwtrp-peo/viralphyl
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Github : https://github.com/kwtrp-peo/viralphyl
    Website: https://github.com/kwtrp-peo/
----------------------------------------------------------------------------------------
*/

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT FUNCTIONS / MODULES / SUBWORKFLOWS / WORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { AMPLICON_BASED  } from './workflows/ont_amplicon_based'
include { METAGENOMICS    } from './workflows/ont_metagenomics'
include { showHelp        } from './modules/local/help.nf'
include { showVersion     } from './modules/local/help.nf'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW - ENTRY INTO THE WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow  {

    // Display help then exit
    if (params.help) {
        showHelp()
        exit(0)
    } else if (params.version) {
        showVersion()
        exit(0)
    }

    // Start the pipeline by checking the --method parameter
    switch (params.method.toLowerCase()) {
        case 'metagenomics':    // Run the metagenomics pipeline
            METAGENOMICS()
            break               // Prevents fall-through to other cases
        case 'amplicon':        // Run the amplicon-based pipeline
            AMPLICON_BASED()
            break 
        default:                // Handle invalid --method values
            log.error "ERROR: Invalid --method '${params.method}'. Choose either 'amplicon' or 'metagenomics'."
            exit(1)  // Exit with error code 1 to indicate failure
    }

}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
