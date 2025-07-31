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
include { KRAKEN2_WORKFLOW               } from '../subworkflows/local/kraken2_classification_workflow'
include { FILTER_PRIORITY_PATHOGENS      } from '../modules/local/filter_priority_pathogen'
include { KRAKENTOOLS_EXTRACTKRAKENREADS } from '../modules/local/extract_kraken_reads'
include { FETCH_FEFERENCE_FASTA          } from '../modules/local/fetch_reference_from_taxid'
include { GENERATE_CONSENSUS             } from '../modules/local/generate_consensus'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NF-CORE MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { PORECHOP_ABI                   } from '../modules/nf-core/porechop/abi/main' 
include { TAXONKIT_NAME2TAXID            } from '../modules/nf-core/taxonkit/name2taxid/main'


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

        // Combine to make a tuple of sample and ref
        PORECHOP_ABI.out.reads.combine(
            HUMAN_GENOME_PROCESSING.out.indexed_HG.map{it[1]}
        ).set{ ref_read_ch }

        // Deplete human reads
        DEPLETE_HUMAN_READS (
            ref_read_ch        // [[id:samplexx], fastq, ref]
        )

        // Raw read classification
        switch (params.classifier.toLowerCase()) {
            case 'kraken2':
                KRAKEN2_WORKFLOW (
                    DEPLETE_HUMAN_READS.out.fast_gz,
                    params.kraken2_db
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

    // Assembly module
    if (!params.skip_assembly) {

        if (params.target_pathogen) {
            // User provides a list of pathogen names (1 per line)

            channel
                .fromPath(params.target_pathogen)
                .map { tsv_file -> 
                    [
                        [id: 'pathogen_list'],  // meta
                        [],
                        tsv_file                // path to pathogen list
                    ]
                }
                .set { pathogenInput }

            // Convert pathogen names to TaxIDs using taxonkit and Kraken DB
            TAXONKIT_NAME2TAXID(
                pathogenInput,                  // [ meta, empty, txt ]
                KRAKEN2_WORKFLOW.out.db         // Kraken taxonomy DB
            )

            // Filter Kraken summary to retain only listed pathogens
            FILTER_PRIORITY_PATHOGENS(
                KRAKEN2_WORKFLOW.out.kraken_summary,      // [ id, tsv ]
                TAXONKIT_NAME2TAXID.out.tsv.map { it[1] } // [ tsv with taxids ]
            )

            // Filter taxids with low read count
            FILTER_PRIORITY_PATHOGENS.out.tsv
                .flatMap { sample_id, tsv_file ->
                    file(tsv_file)
                        .splitCsv(sep: '\t', header: true)
                        .findAll { row -> row.reads.toInteger() >= params.min_reads_per_taxon }
                        .collect { row -> [sample_id, row.taxid, row.name] }
                }
                .set { taxid_ch }

        } else {
            // No pathogen list provided → fall back to all taxa from Kraken2 above threshold
            KRAKEN2_WORKFLOW.out.kraken_summary
                .flatMap { sample_id, tsv_file ->
                    file(tsv_file)
                        .splitCsv(sep: '\t', header: true)
                        .findAll { row -> row.reads.toInteger() >= params.min_reads_per_taxon }
                        .collect{ row -> [sample_id, row.taxid, row.name] }
                }
                .set { taxid_ch }       // [run1_bc01, 186538, Zaire ebolavirus]
                
        }

        // 2. Create a map of sample→files (one entry per sample)
        KRAKEN2_WORKFLOW.out.classified_fastq                       // kraken classified fastq
            .join(KRAKEN2_WORKFLOW.out.kraken2_output_txt)          // kraken output txt file
            .map { fastq_meta, fastq_path, report_path ->
                [ fastq_meta.id, fastq_path, report_path ]
            }
            .join(
                KRAKEN2_WORKFLOW.out.report                         // Kraken report
                    .map { report_meta, kraken_report ->
                        [report_meta.id, kraken_report]
                    }
            ).set { sample_files_ch }

        // Prepare data for extract_kraken.py
        sample_files_ch.cross(taxid_ch)
            .map {          // [[a,b,c,d], [e,f,g]]
                [                
                [id: it[0][0], single_end: true],  // meta map
                it[1][1],                         // taxid
                it[0][1],                         // classified_fastq_gz
                it[0][2],                         // kraken output
                it[0][3],                          // kraken report
                it[1][2]                          // pathogen name
                ]
            }. set { extract_kraken_ch }

        // Extract reads for priority/identified pathogens
        KRAKENTOOLS_EXTRACTKRAKENREADS (
            extract_kraken_ch        // [[a,b,c,d], [e,f,g]]
        )

        // Get the unique taxids for references downlod through accessions
        taxid_ch.unique{ it[1] }               // remove duplicate taxids
            .map{ sample_id, taxid, name -> 
                    taxid }
            .set { unique_taxid_ch }
            
        // Get the map file for taxid:acession from kraken db directory
        KRAKEN2_WORKFLOW.out.db
            .map { db_dir -> file("${db_dir}/seqid2taxid.map") }  
            .set { taxid_map_ch }

        // Download the refrence using the accession number obtained
        // after the mappiong of taxid to accessions
        FETCH_FEFERENCE_FASTA (
           unique_taxid_ch,         // [ taxid ]
           taxid_map_ch             // [ txt ]
        )

        // Prepare data for mapping
        FETCH_FEFERENCE_FASTA.out.fasta
        .cross( KRAKENTOOLS_EXTRACTKRAKENREADS.out.extracted_kraken2_reads )
        .map{                   // [ [taxid, ref], [taxid, sample_id, virus_name, fastq] ]
            [                
                it[0][0],                          // taxid 
                it[1][1],                          // sample id
                it[0][1],                          // ref fasta
                it[1][3],                          // classified_fastq_gz
                it[1][2]                           // pathogen name
                ]
        }.set { mapping_data }                   // [ taxid, sample_id, ref, fastq, pathogen ]

        // Select the best reference incase of mutliple references and generate consensus
        GENERATE_CONSENSUS (
            mapping_data                // [ taxid, sample_id, ref, fastq, pathogen ]
        )

    }

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        END OF RAW READS CLASSIFICATION WORKFLOW
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    
}