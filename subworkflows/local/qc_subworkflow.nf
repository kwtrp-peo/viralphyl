/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PREPARE_SAMPLESHEET               } from './samplesheet_subworkflow'
include { NANOPLOT                          } from '../../modules/nf-core/nanoplot/main' 
include { MULTIQC as MULTIQC_AMP            } from '../../modules/nf-core/multiqc/main'
include { MULTIQC as MULTIQC_META           } from '../../modules/nf-core/multiqc/main'

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
        ch_samplesheet  // [sample_id, path_to_fastq_dir]

    main:
        ch_nanoplot_results = Channel.empty()

        if (params.sequencing_summary) {
            Channel
                .fromPath(params.sequencing_summary)
                .set { ch_sequencing_summary }

            // Run NANOPLOT on sequencing_summary
            NANOPLOT(
                ch_sequencing_summary.map { [ [id: 'qc'], it ] }
            )
            NANOPLOT.out.txt
                .set { ch_nanoplot_results }

        } else {
            NANOPLOT(
                ch_samplesheet
                    .map { sample_id, dir_path ->
                        tuple(id: sample_id, file("${dir_path}/*.{fastq.gz,fq.gz,fastq,fq}"))
                    }
            )
            NANOPLOT.out.txt
                .set { ch_nanoplot_results }
        }

        // Aggregate nanoplot qc report into one report for amplicon
        if (params.protocol.toLowerCase() == 'amplicon') {
            MULTIQC_AMP (
                NANOPLOT.out.txt
                .map { it[1] }
                .collect(),
                [], [], [], [], []
            )
            report_html = MULTIQC_AMP.out.report
        } 
        // Aggregate nanoplot qc report into one report for metagenomics
        else if (params.protocol.toLowerCase() == 'metagenomics') {
            MULTIQC_META (
                NANOPLOT.out.txt
                .map { it[1] }
                .collect(),
                [], [], [], [], []
            )
            report_html = MULTIQC_META.out.report
        }
        else {
            error "Invalid protocol specified: ${params.protocol}. Must be 'amplicon' or 'metagenomics'"
        }

    emit:
        multiqc_html_report = report_html
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    END OF SEQUENCING QC
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/