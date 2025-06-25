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
include { TAXONKIT_NAME2TAXID            } from '../modules/nf-core/taxonkit/name2taxid/main'
include { FILTER_PRIORITY_PATHOGENS      } from '../modules/local/filter_priority_pathogen'
include { KRAKENTOOLS_EXTRACTKRAKENREADS } from '../modules/local/extract_kraken_reads'
include { FETCH_FEFERENCE_FASTA          } from '../modules/local/fetch_reference_from_taxid'


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    IMPORT NF-CORE MODULES / SUBWORKFLOWS / FUNCTIONS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { PORECHOP_ABI                   } from '../modules/nf-core/porechop/abi/main' 


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

        channel
        .fromPath(params.target_pathogen)
        .map { tsv_file -> 
            [
                [id: 'pathogen_list'],      // meta
                [],
                tsv_file                    // names_txt
            ]
        }.set {pathogenInput}
    
        // Get the taxid for the priority pathogens from kraken db
        TAXONKIT_NAME2TAXID (
            pathogenInput,              // tuple val(meta), val(name), path(names_txt)
            KRAKEN2_WORKFLOW.out.db     // path taxdb
        )

        // Filter priority pathogen for each sample
        FILTER_PRIORITY_PATHOGENS (
        KRAKEN2_WORKFLOW.out.kraken_summary,       // [ id, tsv ]
        TAXONKIT_NAME2TAXID.out.tsv.map{ it[1] }   // [ tsv ]
        )

        // Filter out taxids with reads < params.min_reads
        FILTER_PRIORITY_PATHOGENS.out.tsv
            .flatMap { sample_id, tsv_file ->
                file(tsv_file)      // convert the channel to a file object
                .splitCsv(sep: '\t', header: true)      // Split the tsv file
                .findAll { row -> row.reads.toInteger() >= params.min_reads_per_taxon }  // Filter first
                .collect { row -> [ sample_id, row.taxid] }       // Then extract
            }
            .set { taxid_ch }

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
            .map {          // [[a,b,c,d], [e,f]]
                [                
                [id: it[0][0], single_end: true],  // meta map
                it[1][1],                         // taxid
                it[0][1],                         // classified_fastq_gz
                it[0][2],                         // kraken output
                it[0][3]                          // kraken report
                ]
            }. set { extract_kraken_ch }

        // Extract reads for priority pathogens
        KRAKENTOOLS_EXTRACTKRAKENREADS (
            extract_kraken_ch
        )

        // Get the unique taxids for references downlod through accessions
        taxid_ch.unique{ it[1] }               // remove duplicate taxids
            .map{ sample_id, taxid -> taxid }
            .set { unique_taxid_ch }

        KRAKEN2_WORKFLOW.out.db
            .map { db_dir -> file("${db_dir}/seqid2taxid.map") }  
            .set { taxid_map_ch }

        FETCH_FEFERENCE_FASTA (
           unique_taxid_ch,         // [ taxid ]
           taxid_map_ch             // [ txt ]
        )

        // FETCH_FEFERENCE_FASTA.out.fasta.view()  
        // KRAKENTOOLS_EXTRACTKRAKENREADS.out.extracted_kraken2_reads.view()      

        // Prepare data for mapping
        FETCH_FEFERENCE_FASTA.out.fasta
        .cross( KRAKENTOOLS_EXTRACTKRAKENREADS.out.extracted_kraken2_reads )
        .map{                   // [ [taxid, ref], [taxid, id, fastq] ]
            [                
                it[0][0],                          // taxid 
                it[1][1],                         // sample id
                it[0][1],                         // ref fasta
                it[1][2]                         // classified_fastq_gz
                ]
        }.set { mapping_data }                   // [ taxid, sample_id, ref, fastq ]

        mapping_data.view()
        

    // Get the taxids as a list of space separated integers
    // TAXONKIT_NAME2TAXID.out.tsv
    // .map { meta, tsv_file ->                    // Destructure tuple
    //    tsv_file                             
    //     .readLines()                            // Read lines from file
    //     .collect {
    //         def cols = it.split('\t')           // Split line into columns
    //         cols.size() > 1 ? cols[1] : null    // Safely access 2nd column
    //     } 
    //     .findAll { it }                     // Remove empty strings or null
    //     .collect { it.toInteger() }         // convert to integer
    //     .join(' ')                          // Join into space-separated string
    // }.set {taxids}                          // 34 67 89 89

    // taxids.view()

    }

    /*
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        END OF RAW READS CLASSIFICATION WORKFLOW
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    */
    

}
    
