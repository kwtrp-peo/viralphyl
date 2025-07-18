/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    PROCESS HUMAN GENOME REFERENCE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Subworkflow to handle human genome reference input in multiple formats:
    - Direct MMI index file
    - Compressed FASTA file
    - Remote URL (HTTP/HTTPS/FTP)
    
    Input:  Genome reference (path or URL)
    Output: Minimap2 index file (MMI)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { DOWNLOAD_REFERENCE_DATA } from '../../modules/local/download_reference_data'
include { MINIMAP2_INDEX        } from '../../modules/nf-core/minimap2/index/main'


workflow HUMAN_GENOME_PROCESSING {

    take:
        genome_input

    main:
        def input_str = genome_input.toString()

        if (input_str.endsWith('.mmi')) {
            Channel                         // Just return the *.mmi file as a path channel
                .fromPath(genome_input)
                .map { [ [:], it ] }
                .set { genome_index }
        }
        else if (input_str.startsWith('http://') ||
                 input_str.startsWith('https://') ||
                 input_str.startsWith('ftp://')) {

            // Download using url provided by default
            DOWNLOAD_REFERENCE_DATA (
                channel
                    .value(genome_input)
                    .map { [ "Human Genome", it ] }
                )
            // Index the dowloaded genome
            MINIMAP2_INDEX (
                DOWNLOAD_REFERENCE_DATA.out.file
                .map { [ [:], it ] }
            )
            genome_index = MINIMAP2_INDEX.out.index
        }

        else if (input_str ==~ /.*\.(fna|fa|fasta)\.gz$/) {
            MINIMAP2_INDEX(
                Channel
                    .fromPath(genome_input)
                    .map { [ [:], it ] }
            )
            genome_index = MINIMAP2_INDEX.out.index
        }

        else {
            error """
            Unsupported genome reference format: ${input_str}
            Supported formats:
            - Minimap2 index (.mmi)
            - Gzipped FASTA (.fna.gz, .fa.gz, .fasta.gz)
            - Remote URL (http://, https://, ftp://)
            """
        }

    emit:
        indexed_HG     =     genome_index        // [[:], path_to_mmi]
}
