/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    PROCESS MASH DATABASE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Subworkflow to provide a valid kraken2 database:
    - Uses provided file (local or remote)
    - Downloads default kraken2 RefSeq DB if no input is given

    Input:  Optional kraken2 path or URL
    Output: Kraken2 file (.db)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { KRAKEN2_KRAKEN2                   } from '../../modules/nf-core/kraken2/kraken2/main'
include { DOWNLOAD_REFERENCE_DATA           } from '../../modules/local/download_reference_data'
include { EXTRACT_TARBALL                   } from '../../modules/local/extract_tarball'
include { GENERATE_KRAKEN2_SUMMARY          } from '../../modules/local/generate_kraken2_summary'
include { GENERATE_KRAKEN2_SUMMARY_HTML     } from '../../modules/local/generate_kraken2_summary_html'



workflow KRAKEN2_WORKFLOW {

    take:
        query                        // [[id:sampleid], fastq]
        kraken2_db                  // [ path ]

    main:
        def kraken2_db_str = kraken2_db.toString()

        if (kraken2_db_str.endsWith('.tar.gz')) {
            if (kraken2_db_str.startsWith('http://') ||
                kraken2_db_str.startsWith('https://') ||
                kraken2_db_str.startsWith('ftp://')) {
                
                DOWNLOAD_REFERENCE_DATA( 
                    // Download existing mash sketch/db                   
                    channel
                        .value(kraken2_db)
                        .map { [ "kraken database", it ] }
                )
               
               EXTRACT_TARBALL (
                    DOWNLOAD_REFERENCE_DATA.out.file
                    .map { [ [id:"Extract kraken db"], it ] }
               )
               
               EXTRACT_TARBALL.out.kraken_db_dir
               .set { kraken2_db }                  

            } else {   
                 // Use a provided tar.gz file                                    
                Channel
                .fromPath(kraken2_db)
                .map { [ [id:"Extract kraken db"], it ] }
                .set { ch_kraken_tar_gz }

                EXTRACT_TARBALL (
                    ch_kraken_tar_gz
                )
                
               EXTRACT_TARBALL.out.kraken_db_dir
               .set { kraken2_db }  
            }
        }
        else if (file(kraken2_db_str).isDirectory()) {
                // Add support for directory
            Channel
                .value(kraken2_db)
                .set { kraken2_db }

        } else {
            error """
            Unsupported kraken2 reference format: ${kraken2_db_str}
            Supported:
              - Kraken2 database folder
              - Kraken2 .tar.gz archive (local or remote)
            """
        }

        // Combine to make a tuple of sample and ref to 
        // [ [id:sample_id, single_end:true], fastq.gz, kraken_db ]
        query.map { meta, fastq_gz ->
                meta.single_end = true
                [ meta, fastq_gz ]
            }.combine(kraken2_db).set{ ref_read_ch }

        // Now use kraken database to classify reads
        KRAKEN2_KRAKEN2 (
           // query.map { meta, fastq_gz ->
           //     meta.single_end = true
           //     [ meta, fastq_gz ]
           // },
           // kraken2_db,             // [ kraken2_dir ]
            ref_read_ch,      // [ [id:sample_id, single_end:true], fastq.gz, kraken_db ]
            true,
            true
        )
        KRAKEN2_KRAKEN2.out.classified_reads_fastq.set {fastq}
        KRAKEN2_KRAKEN2.out.classified_reads_assignment.set {kraken_txt_file}
        KRAKEN2_KRAKEN2.out.report.set {classfication_report}

        // Generate Kraken summary report in json and tsv
        GENERATE_KRAKEN2_SUMMARY (
            kraken_txt_file  // [ [id, paired], kraken2_output ]
        )

        GENERATE_KRAKEN2_SUMMARY.out.tsv.set {kraken_summary_tsv}     // [ id, tsv ]

        // Generate hmtl dashboard to visualize the kraken2 summary reports
        GENERATE_KRAKEN2_SUMMARY_HTML (
            GENERATE_KRAKEN2_SUMMARY.out.json.collect()         //    [x, y, z]
        )

    emit:
        db                  = kraken2_db
        report              = classfication_report       // [ [id, paired], classfication_report ]
        classified_fastq    = fastq                      // [ [id, paired], fastq ]
        kraken2_output_txt  = kraken_txt_file            // [ [id, paired], kraken2_output ]
        kraken_summary      = kraken_summary_tsv         // [ id, tsv ]
}
