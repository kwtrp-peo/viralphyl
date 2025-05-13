//
// Extract ectodmain sequences from consensus seqences given ref ectodamain

include { AUGUR_REFINE                              } from '../../modules/local/augur_refine'
include { AUGUR_TRAIT                               } from '../../modules/local/augur_trait'
include { AUGUR_EXPORT                              } from '../../modules/local/augur_export'
include { AUSPICE_CONFIG                            } from '../../modules/local/auspice_config'

workflow AUGUR_TRANSFORM {
    take:
        ch_newick_file              // fasttree newick file
        ch_aligned_fasta            // mafft aligned fasta file
        ch_metadata                 // combined metadata

    main:
        ch_versions = Channel.empty()

        //
        // Module: Generates color and json configuration files for augur export
        //
        AUSPICE_CONFIG (
            ch_metadata
        )
        ch_config_json      =   AUSPICE_CONFIG.out.json
        ch_config_color     =   AUSPICE_CONFIG.out.tsv
        ch_versions         =   ch_versions.mix(AUSPICE_CONFIG.out.versions)

        //
        // Module: Refines the newick file from IQTREE
        //
        AUGUR_REFINE  (
            ch_newick_file,
            ch_aligned_fasta,
            ch_metadata
        )
        ch_refined_nwk          = AUGUR_REFINE.out.refined_newick
        ch_branch_len_json      = AUGUR_REFINE.out.branch_len_json
        ch_versions = ch_versions.mix(AUGUR_REFINE.out.versions)

        //
        // Module: Generates traits from metadata
        //
        AUGUR_TRAIT  (
            ch_refined_nwk.map{ [ [:], it ] },
            ch_metadata
        )
        ch_traits_json    = AUGUR_TRAIT.out.traits_json
        ch_versions = ch_versions.mix(AUGUR_TRAIT.out.versions)

        //
        // Module: Generates a json file for auspice visualization
        //
        AUGUR_EXPORT (
            ch_refined_nwk.map{ [ [:], it ] },
            ch_metadata,
            ch_branch_len_json.map { [ [:], it ] },
            ch_traits_json.map { [ [:], it ] },
            ch_config_json.map { [ [:], it ] },
            ch_config_color.map { [ [:], it ] }
        )
        ch_auspice_file    = AUGUR_EXPORT.out.auspice_json
        ch_versions = ch_versions.mix(AUGUR_EXPORT.out.versions)

    emit:
        auspice_visual              =      ch_auspice_file
        versions                    =      ch_versions          // channel: [ versions.yml ]
}