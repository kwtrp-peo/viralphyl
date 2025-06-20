process EXTRACT_TARBALL {

  tag "$meta.id"
  label 'process_low'

container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    'oras://community.wave.seqera.io/library/wget:1.21.4--1b359e4e806cc792' :
    'community.wave.seqera.io/library/wget:1.21.4--8b0fcde81c17be5e' }" 

  input:
  tuple val(meta), path(tarball)

  output:
  path 'kraken_db',             emit: kraken_db_dir

  script:
  """
  mkdir -p kraken_db
  tar -xvzf ${tarball} -C kraken_db
  """
}
