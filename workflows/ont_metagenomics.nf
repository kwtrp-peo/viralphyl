/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { PREPARE_SAMPLESHEET            } from '../subworkflows/local/samplesheet_subworkflow'
include { QUALITY_CHECK                  } from '../subworkflows/local/qc_subworkflow'
include { HUMAN_GENOME_PROCESSING        } from '../subworkflows/local/process_human_genome'
include { DEPLETE_HUMAN_READS            } from '../modules/local/deplete_human_reads'
include { MASH_WORKFLOW                  } from '../subworkflows/local/mash_classification_sub_workflow'


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NF-CORE MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { PORECHOP_ABI                         } from '../modules/nf-core/porechop/abi/main' 


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
workflow METAGENOMICS {
    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    SAMPLESHEET GENERATION SUBWORKFLOW
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    PREPARE_SAMPLESHEET()
    
     /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    QUALITY CHECK SUBWORKFLOW
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    if (!params.skip_qc) { 
        QUALITY_CHECK (
            PREPARE_SAMPLESHEET.out.samplesheet_ch    // [sample_id, path_to_fastq_dir]
        )
    }
 
    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    START OF RAW READS CLASSIFICATION WORKFLOW
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    // Module adopter trimming
    if (!params.skip_classification) {

        // Trim sequencing adapters
        PORECHOP_ABI (
            PREPARE_SAMPLESHEET.out.samplesheet_ch
            .map { sample_id, dir_path ->
                [ [id:sample_id], dir_path ]
            },
            []
        ) 

        // Process human genome
        HUMAN_GENOME_PROCESSING (
            params.human_genome
        )

        // Deplete human reads
        DEPLETE_HUMAN_READS (
            PORECHOP_ABI.out.reads,                  
            HUMAN_GENOME_PROCESSING.out.indexed_HG   
        )

        // Raw read classification
        switch (params.classifier.toLowerCase()) {
            case 'kraken2':
                KRAKEN2_WORKFLOW(
                    DEPLETE_HUMAN_READS.out.fast_gz
                )
                break
            case 'mash':
                MASH_WORKFLOW (
                    DEPLETE_HUMAN_READS.out.fast_gz,
                    params.mash_db
                )
                break
            default:
                log.error "ERROR: Invalid --classifier '${params.classifier}'. Choose either 'mash' or 'kraken2'."
                exit(1)
        }
    }

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        END OF RAW READS CLASSIFICATION WORKFLOW
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    

}
    
