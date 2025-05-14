process AUGUR_REFINE {
    tag "refining phylogeny"
    label 'process_medium'

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/augur%3A30.0.1--pyhdfd78af_0' :
        'biocontainers/augur:30.0.1--pyhdfd78af_0' }"

    input:
        tuple val(meta) , path(newick_file)
        tuple val(meta) , path(aln_fasta)
        tuple val(meta) , path(metadata_tsv)

    output:
        path "${filename}_refined.nwk"                  , emit: refined_newick
        path "${filename}_branch_lengths.json"          , emit: branch_len_json
        path "versions.yml"                             , emit: versions

    script:     // This script is bundled with the pipeline, in kwtrp-peo/viralphyl/bin/
    filename = newick_file.simpleName

    """
    augur \\
        refine \\
        --root mid_point \\
        --tree $newick_file \\
        --alignment $aln_fasta \\
        --metadata $metadata_tsv \\
        --output-tree ${filename}_refined.nwk \\
        --output-node-data ${filename}_branch_lengths.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        augur: \$(augur version)
    END_VERSIONS
    """
}
