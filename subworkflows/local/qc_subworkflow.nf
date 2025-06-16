  /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT  MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PREPARE_SAMPLESHEET                  } from './samplesheet_subworkflow'
include { NANOPLOT                             } from '../../modules/nf-core/nanoplot/main' 
include { MULTIQC                              } from '../../modules/nf-core/multiqc/main'

 /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    END OF MODULE IMPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                START OF SEQUENCING QC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow QUALITY_CHECK {

    take:
        ch_samplesheet

    main:
        if (params.sequencing_summary) {
            // Define reference fasta channel
            Channel
                .fromPath(params.sequencing_summary)
                .set { ch_sequencing_summary }

            // MODULE: Run sequencing qc using nanoplot
            NANOPLOT (
                ch_sequencing_summary.map { [ [id:'qc'], it ] }
            )
        } else {
            // Run qc on individual samples if sequencing summary file not provided
            NANOPLOT (
                ch_samplesheet
                .map {  sample_id, dir_path ->
                        tuple( id:sample_id, file("${dir_path}/*.fastq.gz") ) 
                    }
            )

            // Aggregate nanoplot qc report into one report
            MULTIQC (
                NANOPLOT.out.txt
                .map {it[1]}
                .collect(),
                [], [], [], [], []
            )

            report_html = MULTIQC.out.report
        }
    
    emit:
        multiqc_hmtl_report         = report_html
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    END OF SEQUENCING QC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/