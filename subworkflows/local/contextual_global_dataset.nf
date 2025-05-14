//
// Extracts both query and global metadata from assembled query sequences
// and downloaded global sequences

include { DATASETS_SUMMARY                                        } from '../../modules/local/datasets_summary'
include { CLEAN_GLOBAL_METADATA                                   } from '../../modules/local/clean_global_metadata'
include { AUGUR_FILTER                                            } from '../../modules/local/augur_filter'
include { EXTRACT_ACCESSIONS                                      } from '../../modules/local/extract_tsv_column'
include { EPOST_ENTREZ_DIRECT                                     } from '../../modules/local/epost_entrez_direct'
include { RENAME_FASTA_HEADER                                     } from '../../modules/local/rename_fasta_headers'

workflow CONTEXTUAL_GLOBAL_DATASET {
    take:
        virus_host_name
        virus_taxon_name
        min_value               // Mininum genome length
        max_value               // Maximum genome length
        seed_value              // subsampling seed
        max_sequence_value      // maximum number of sequences for the tree
        subsample_creteria      

    main:
        ch_versions = Channel.empty()

        //
        // MODULE: DATASETS_SUMMARY downlaods global sequences from NCBI
        // using ncbi datasets cli tool
        //
        DATASETS_SUMMARY (
            virus_taxon_name,
            virus_host_name
        )
        ch_raw_ncbi_metadata        = DATASETS_SUMMARY.out.tsv
        ch_versions                 = ch_versions.mix(DATASETS_SUMMARY.out.versions)

        //
        // MODULE: CLEAN_GLOBAL_METADATA take global tsv metadata downloaded using
        // ncbi's datasets and dataformat and cleans it
        //
        CLEAN_GLOBAL_METADATA (
            ch_raw_ncbi_metadata,
            min_value,
            max_value
        )
        ch_cleaned_ncbi_datasets_metadata        = CLEAN_GLOBAL_METADATA.out.meta_tsv
        ch_versions                              = ch_versions.mix(CLEAN_GLOBAL_METADATA.out.versions)

        //
        // MODULE: AUGUR_FILTER take the cleaned global tsv metadata perfomes subsampling
        //
        AUGUR_FILTER (
            ch_cleaned_ncbi_datasets_metadata,
            seed_value,
            max_sequence_value,
            subsample_creteria
        )
        ch_subsampled_global_metadata        = AUGUR_FILTER.out.subsamples_tsv
        ch_versions                          = ch_versions.mix(AUGUR_FILTER.out.versions)

        //
        // MODULE: EXTRACT_ACCESSIONS takes a tsv file with one or more columns and
        // extracts the column(s) from the tsv returning it as a tsv file
        //
        EXTRACT_ACCESSIONS (
            ch_subsampled_global_metadata
        )
        ch_subsampled_global_accessions      = EXTRACT_ACCESSIONS.out.acc_tsv
        ch_versions                          = ch_versions.mix(EXTRACT_ACCESSIONS.out.versions)

        //
        // MODULE: EPOST_ENTREZ_DIRECT takes accession of the subsamples global metadata
        // and dowloads the correspoinding fasta seqeunces
        //
        EPOST_ENTREZ_DIRECT (
            ch_subsampled_global_accessions
        )
        ch_subsampled_global_fasta           = EPOST_ENTREZ_DIRECT.out.fasta
        ch_versions                          = ch_versions.mix(EPOST_ENTREZ_DIRECT.out.versions)

        RENAME_FASTA_HEADER (
            ch_subsampled_global_fasta,
            ch_subsampled_global_metadata
        )
        ch_metadata_tsv                     = RENAME_FASTA_HEADER.out.tsv
        ch_sequence_fasta                   = RENAME_FASTA_HEADER.out.fasta
        // ch_versions                          = ch_versions.mix(RENAME_FASTA_HEADER.out.versions)

    emit:
        global_metadata_tsv                     = ch_metadata_tsv     // channel: [ .tsv ]
        global_seqs_fasta                       = ch_sequence_fasta        // channel: [ .fasta ]
        versions                                = ch_versions                       // channel: [ versions.yml ]
}
