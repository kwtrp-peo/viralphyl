/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
 include { GENERATE_SAMPLESHEET                 } from '../modules/local/generate_samplesheet'
 include { ARTIC_GUPPYPLEX                      } from '../modules/local/artic_guppyplex'
 include { ARTIC_MINION                         } from '../modules/local/artic_minion'
 include { COLLAPSE_PRIMER_BED                  } from '../modules/local/collapse_primer_bed'


 /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { MOSDEPTH                             } from '../modules/nf-core/mosdepth/main'




/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    RUN MAIN WORKFLOW
    // medaka_model_ch             = Channel.value("${params.medaka_model}")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow AMPLICON_BASED {
    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        CHANNELS DEFINATIONS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    // Define input channel for an optional tsv metadata file
    if (params.metadata_tsv) { ch_metadata_tsv = file(params.metadata_tsv) } else { ch_metadata_tsv = [] }

    // Define input channel for an optional MSA reference fasta file
    if (params.multi_ref_file) { ch_select_ref_file = file(params.multi_ref_file) } else { ch_select_ref_file = [] }

    // Define input channel for an optional model directory
    if (params.clair3_model_dir) { 
        ch_clair3_model_dir = channel.fromPath(params.clair3_model_dir, type: 'dir') 
    } else { ch_clair3_model_dir = [] }

    // Define input channel for an optional model (string)
    if (params.clair3_model) { ch_clair3_model = Channel.value("${params.clair3_model}") } else { ch_clair3_model = [] }


    // Define fastq_pass directory channel
    Channel                                                     // Get raw fastq directory
        .fromPath(params.fastq_dir, type: 'dir', maxDepth: 1)
        .set { ch_fastq_data_dir }

    // Define reference fasta channel
    Channel.fromPath(params.ref_fasta).set { ch_ref_fasta }                                      

     // Define reference bed channel
    Channel.fromPath(params.ref_bed).set { ch_ref_bed } 

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        CHANNELS DEFINATIONS
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

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

    ARTIC_MINION (
        ch_clair3_model,                      // optional claire3 model
        ch_clair3_model_dir,                 // optional claire3 model directory
        ch_select_ref_file,                  // optional multi-reference file
        ch_ref_fasta,                       // reference bed file - required
        ch_ref_bed,                         // reference bed file - required
        ARTIC_GUPPYPLEX.out.fastq_gz        // concatenated sample fastq file
    )

    // Clean up primer bed for plotting
    COLLAPSE_PRIMER_BED (
        ARTIC_MINION.out.bed
    )

    // Generate regions/amplicon  
    // requeires a .BED, .BAM and .BAI files [ seqId, bam, bai, bed ]
    MOSDEPTH (
        ARTIC_MINION.out.bam_primertrimmed
            .map { tuple(id:it.simpleName, it) }
            .join( 
                ARTIC_MINION.out.bai_primertrimmed.map { tuple(id:it.simpleName, it)}, by: [0]
            ).join(
                COLLAPSE_PRIMER_BED.out.collapsed_bed.map { tuple(id:it.simpleName, it)}, by: [0]
            ),
        [ [:], [] ] 
    )

    MOSDEPTH.out.regions_bed.view()
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
