/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
 include { GENERATE_SAMPLESHEET                 } from '../modules/local/generate_samplesheet'
 include { ARTIC_GUPPYPLEX                      } from '../modules/local/artic_guppyplex'
 include { ARTIC_MINION                         } from '../modules/local/artic_minion'
 include { COLLAPSE_PRIMER_BED                  } from '../modules/local/collapse_primer_bed'
 include { PLOT_MOSDEPTH_REGIONS                } from '../modules/local/plot_mosdepth_region.nf'
 include { GET_ASSEMBLY_STATS                   } from '../modules/local/get_assembly_stats'
 include { GET_GENOTYPES                        } from '../modules/local/get_genotypes'
 include { AGGREGATE_ASSEMBLY_TSVS              } from '../modules/local/aggregate_assembly_tsv'
 include { FASTA_META_FILTER                    } from '../modules/local/fasta_meta_filter'
 include { CONTEXTUAL_GLOBAL_DATASET            } from '../subworkflows/local/contextual_global_dataset'
 include { PHYLO_COMBINE_TSVS                   } from '../modules/local/phylo_combine_tsv'


 /*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT LOCAL MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { MOSDEPTH                             } from '../modules/nf-core/mosdepth/main'
include { SEQKIT_CONCAT                        } from '../modules/nf-core/seqkit/concat/main'
include { MAFFT_ALIGN                          } from '../modules/nf-core/mafft/align/main'


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

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    START OF SAMPLESHEET GENERATION MODULE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    if (!params.skip_samplesheet_generation) {
    
        // Define fastq_pass directory channel
            Channel                                                     // Get raw fastq directory
                .fromPath(params.fastq_dir, type: 'dir', maxDepth: 1)
                .set { ch_fastq_data_dir }

        // Define input channel for an optional tsv metadata file
            if (params.metadata_tsv) { ch_metadata_tsv = file(params.metadata_tsv) } else { ch_metadata_tsv = [] }


        // MODULE: Run bin/viraphly_samplesheet_generator.py to generate samplesheet
            GENERATE_SAMPLESHEET (
                ch_fastq_data_dir,               // raw reads directory channel
                ch_metadata_tsv                  // tsv metadata channel (can be an empty channel)
            )
            GENERATE_SAMPLESHEET.out.samplesheet
                .splitCsv(header:true)
                .map { row-> tuple(row.strain_id, file(row.fastq_dir)) }
                .set { ch_samplesheet }
    }
    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        END OF SAMPLESHEET GENERATION
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        START ASSEMBLY MODULE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    
    if (!params.skip_assembly) {
        // Define input channel for an optional MSA reference fasta file
        if (params.multi_ref_file) { ch_select_ref_file = file(params.multi_ref_file) } else { ch_select_ref_file = [] }

        // Define input channel for an optional model directory
        if (params.clair3_model_dir) { 
            ch_clair3_model_dir = channel.fromPath(params.clair3_model_dir, type: 'dir') 
        } else { ch_clair3_model_dir = [] }

        // Define input channel for an optional model (string)
        if (params.clair3_model) { ch_clair3_model = Channel.value("${params.clair3_model}") } else { ch_clair3_model = [] }

        // Define reference fasta channel
        Channel.fromPath(params.ref_fasta).set { ch_ref_fasta }                                      

        // Define reference bed channel
        Channel.fromPath(params.ref_bed).set { ch_ref_bed } 

        /*
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            CHANNELS DEFINATIONS
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        */

        // MODULE: Run artic guppyplex
        ARTIC_GUPPYPLEX (
            ch_samplesheet
        )

        // MODULE: Run artic minion
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
                .map { bam_file -> tuple(id:bam_file.simpleName, bam_file) }
                .join( 
                    ARTIC_MINION.out.bai_primertrimmed.map { bai_file -> tuple(id:bai_file.simpleName, bai_file)}, by: [0]
                ).join(
                    COLLAPSE_PRIMER_BED.out.collapsed_bed.map { bed_file -> tuple(id:bed_file.simpleName, bed_file)}, by: [0]
                ),
            [ [:], [] ] 
        )

        // Generate mosdepth plots for visualization
        PLOT_MOSDEPTH_REGIONS (
            MOSDEPTH.out.regions_bed.map {
                bed_gz -> bed_gz[1]
            }.collect()
        )

        // Get assembly statistics
        GET_ASSEMBLY_STATS (
            ARTIC_MINION.out.tsv.collect()
        )

        // Only process genotypes when multiref option has been used
        if (params.genotypes && params.multi_ref_file) {
            GET_GENOTYPES ( ARTIC_MINION.out.fasta.collect() )
            ch_genotypes = GET_GENOTYPES.out.tsv 
        } else {
            ch_genotypes = Channel.empty()
        }

        // Concatenate all tsv channels then collect into a single channel
        AGGREGATE_ASSEMBLY_TSVS {
            GENERATE_SAMPLESHEET.out.samplesheet
                .concat( GET_ASSEMBLY_STATS.out.tsv, ch_genotypes )
                .collect()
        }
       // Clean fasta headers and filter for phylogenetics
        FASTA_META_FILTER (
            ARTIC_MINION.out.fasta.collect(),
            AGGREGATE_ASSEMBLY_TSVS.out.tsv
        )
        
        // Sequences above 75% genome coverage or as set by user for phylogenetics
        assembled_tsv_ch        =   FASTA_META_FILTER.out.high_coverage_tsv
        assembled_fasta_ch      =   FASTA_META_FILTER.out.high_coverage_fasta

    }

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        START PHYLOGENETIC MODULE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */

    if (!params.skip_phylogenetics) { 

        // Declare channels that will hold the final fasta and tsv regardless of source
        global_fasta_ch            = Channel.empty()
        global_tsv_ch              = Channel.empty()

        if (params.global_fasta && params.global_tsv) { 
            // Runs when global fasta and tsv are provided by the user
            global_fasta_ch    = file(params.global_fasta)
            global_tsv_ch      = file(params.global_tsv)

        } else {
            // If global dataset not provided download the global dataset and subsample
            CONTEXTUAL_GLOBAL_DATASET (
                params.viral_host,
                params.viral_taxon,
                params.min_sequence_length,
                params.max_sequence_length,
                params.subsample_seed,
                params.subsample_max_sequences,
                params.subsample_by
            )

            // subsample globa metadata and sequences
            global_tsv_ch        =     CONTEXTUAL_GLOBAL_DATASET.out.global_metadata_tsv  
            global_fasta_ch      =     CONTEXTUAL_GLOBAL_DATASET.out.global_seqs_fasta
        }
    }

    // Combine the assembled tsv and global tsv into a tuple
    PHYLO_COMBINE_TSVS (
        assembled_tsv_ch        // tsv for assembled sequences
            .concat(global_tsv_ch)     // global tsv
            .collect()
    )

    // Concatenate the assembled sequences and the subsampled global sequences
    assembled_fasta_ch           // assembled 
            .concat(global_fasta_ch)
            .collect()
            .map {
                tuple( [:], it)
            }.set {combined_fasta_ch}
    SEQKIT_CONCAT (
                combined_fasta_ch
            )

    // Align the sequences
    MAFFT_ALIGN (
        SEQKIT_CONCAT.out.fastx,
        [[:], []], [[:], []], [[:], []],
        [[:], []], [[:], []], []
        )

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        END PHYLOGENETIC MODULE
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    THE END
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
