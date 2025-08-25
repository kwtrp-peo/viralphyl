![kwtrp-peo/viralphyl logo](https://github.com/kwtrp-peo/logos/blob/main/kwtrp-peo-logos/kwtrp-peo-viralphyl_logo_light.png#gh-light-mode-only)
![kwtrp-peo/viralphyl logo](https://github.com/kwtrp-peo/logos/blob/main/kwtrp-peo-logos/kwtrp-peo-viralphyl_logo_dark.png#gh-dark-mode-only)

[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A524.04.2-23aa62.svg)](https://www.nextflow.io/)
[![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/)
[![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/)
[![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)
[![Launch on Seqera Platform](https://img.shields.io/badge/Launch%20%F0%9F%9A%80-Seqera%20Platform-%234256e7)](https://cloud.seqera.io/launch?pipeline=https://github.com/kwtrp-peo/viralphyl)

## Introduction

**kwtrp-peo/viralphyl** is a bioinformatics pipeline designed for the assembly and phylogenetic analysis of viral samples, supporting linear RNA viruses. The pipeline allows for the use of one or multiple reference sequences and takes FASTQ files as input, alongside an optional metadata file. It performs quality control (QC), trimming, and alignment, and produces an extensive QC report, consensus sequences, and a phylogenetic tree. The pipeline is built on [Nextflow](https://www.nextflow.io) and utilizes containerization via [nf-core/modules](https://github.com/nf-core/modules), supporting Docker, Singularity, or Conda.


<!-- TODO nf-core:
   Complete this sentence with a 2-3 sentence summary of what types of data the pipeline ingests, a brief overview of the
   major pipeline sections and the types of output it produces. You're giving an overview to someone new
   to nf-core here, in 15-20 seconds. For an example, see https://github.com/nf-core/rnaseq/blob/master/README.md#introduction
-->
## Pipeline Steps

![kwtrp-peo/viralphyl logo](https://github.com/kwtrp-peo/logos/blob/main/kwtrp-peo-logos/kwtrp-peo-viralphyl-workflow_nano.png)
<!-- TODO nf-core: Include a figure that guides the user through the major workflow steps. Many nf-core
     workflows use the "tube map" design for that. See https://nf-co.re/docs/contributing/design_guidelines#examples for examples.   -->
<!-- TODO nf-core: Fill in short bullet-pointed list of the default steps in the pipeline -->

The pipeline supports two main workflows:

- **Amplicon-based sequencing analysis**
- **Metagenomic sequencing analysis**

Amplicon Workflow

1. Sample sheet and metadata prep ( [`custom python script`](https://www.python.org/) )
2. Sequencing QC ( [`NanoPlot`](https://github.com/wdecoster/NanoPlot) )
3. Whole genome assembly
   - Filter and aggregate demultiplexed reads from MinKNOW/Guppy ( [artic gupplylex](https://artic.readthedocs.io/en/latest/commands/) )
   - Align reads, call variants, and produce a consensus sequence ( [artic minion](https://artic.readthedocs.io/en/latest/commands/) )
   - Genome-wide and amplicon coverage QC plots ( [mosdepth](https://github.com/brentp/mosdepth/) )
4. Phylogenetics
   - Global sequence alignment ( [mafft](https://github.com/GSLBiotech/mafft) )
   - Generate global phylogenetic trees using maximum likelihood method ( [fasttree](https://github.com/morgannprice/fasttree) )
   - maximum likelihood dating and ancestral sequence inference( [treetime](https://github.com/neherlab/treetime) )
   - Refine global phylogeny and create a JSON file ( [augur refine, trait and export](https://docs.nextstrain.org/projects/augur/en/stable/) )
   - Display global phylogenetic tree interactively ( [auspice](https://auspice.us/) )


Metagenomics workflow:

1. Sample sheet and metadata prep ( [`custom python script`](https://www.python.org/) )
2. Sequencing QC ( [`NanoPlot`](https://github.com/wdecoster/NanoPlot) )
3. Raw Read classification
   - Adapter trimming ( [`porechop_abi`](https://github.com/bonsai-team/Porechop_ABI) )
   - Host (Human) reads removal ( [`minimap2`](https://github.com/lh3/minimap2) and [`samtools`](https://github.com/samtools/samtools) )
   - classification using [`mash`](https://github.com/marbl/Mash) or [`kraken2`](https://github.com/DerrickWood/kraken2)
   - Classification report generation [`python script`] 
4. Read assembly
   Extraction of classified reads ( [`bash script`]() )
   -  De novo
      - Genome assembly ([`flye`](https://github.com/mikolmogorov/Flye) )
      - Assembly quality assessement ( [`quast`](https://github.com/ablab/quast) )
      - Blasting the contigs ( [`blast`](https://github.com/enormandeau/ncbi_blast_tutorial) )
      - Consesus generation ( [`minimap2`](https://github.com/lh3/minimap2) and [`samtools`](https://github.com/samtools/samtools) )
   - Reference-based
      - Reference download ([`efetch`]() )
      - Consesus generation ( [`minimap2`](https://github.com/lh3/minimap2) and [`samtools`](https://github.com/samtools/samtools) )

## Usage

> [!NOTE]
> If you are new to Nextflow and nf-core, please refer to [this page](https://nf-co.re/docs/usage/installation) on how to set-up Nextflow. Make sure to [test your setup](https://nf-co.re/docs/usage/introduction#how-to-run-a-pipeline) with `-profile test` before running the workflow on actual data.

## Quick Start

1. Install [`Nextflow`](https://www.nextflow.io/docs/latest/getstarted.html#installation) (`>=23.04.0`)

2. Install any of [`Docker`](https://docs.docker.com/engine/installation/), [`Singularity`](https://www.sylabs.io/guides/3.0/user-guide/) (you can follow [this tutorial](https://singularity-tutorial.github.io/01-installation/)), [`Podman`](https://podman.io/), [`Shifter`](https://nersc.gitlab.io/development/shifter/how-to-use/) or [`Charliecloud`](https://hpc.github.io/charliecloud/) for full pipeline reproducibility _(you can use [`Conda`](https://conda.io/miniconda.html) both to install Nextflow itself and also to manage software within pipelines. Please only use it within pipelines as a last resort; see [docs](https://nf-co.re/usage/configuration#basic-configuration-profiles))_.

3. Download the pipeline and test it on a minimal dataset with a single command:

   For amplicon dataset:
   ```bash
   nextflow run kwtrp-peo/viralphyl -profile docker,test_amplicon --outdir Results

   nextflow run kwtrp-peo/viralphyl -profile singularity,test_amplicon --outdir Results
   ```
   For metagenomics dataset:
    ```bash
   nextflow run kwtrp-peo/viralphyl -profile docker,test_metagenomics --outdir Results

   nextflow run kwtrp-peo/viralphyl -profile singularity,test_metagenomics --outdir Results
   ```

   Note that some form of configuration will be needed so that Nextflow knows how to fetch the required software. This is usually done in the form of a config profile (`YOURPROFILE` in the example command above). You can chain multiple config profiles in a comma-separated string.

   > - The pipeline comes with config profiles called `docker`, `singularity`, `podman`, `shifter`, `charliecloud` and `conda` which instruct the pipeline to use the named tool for software management. For example, `-profile test,docker`.
   > - Please check [nf-core/configs](https://github.com/nf-core/configs#documentation) to see if a custom config file to run nf-core pipelines already exists for your Institute. If so, you can simply use `-profile <institute>` in your command. This will enable either `docker` or `singularity` and set the appropriate execution settings for your local compute environment.
   > - If you are using `singularity`, please use the [`nf-core download`](https://nf-co.re/tools/#downloading-pipelines-for-offline-use) command to download images first, before running the pipeline. Setting the [`NXF_SINGULARITY_CACHEDIR` or `singularity.cacheDir`](https://www.nextflow.io/docs/latest/singularity.html?#singularity-docker-hub) Nextflow options enables you to store and re-use the images from a central location for future pipeline runs.
   > - If you are using `conda`, it is highly recommended to use the [`NXF_CONDA_CACHEDIR` or `conda.cacheDir`](https://www.nextflow.io/docs/latest/conda.html) settings to store the environments in a central location for future pipeline runs.

## Now, you can run the pipeline! 
> [!WARNING]
> Please provide pipeline parameters via the CLI or Nextflow `-params-file` option. Custom config files including those provided by the `-c` Nextflow option can be used to provide any configuration _**except for parameters**_;
> see [docs](https://nf-co.re/usage/configuration#custom-configuration-files).
  <!-- TODO nf-core: update the following command to include all required parameters for a minimal example -->

To analyze nanopore amplicon dataset, use:

```bash
nextflow run kwtrp-peo/viralphyl \
   --fastq_dir <DATA_DIR> \
   --ref_bed primer_scheme.bed \
   --ref_fasta primer_scheme_ref.fasta \
   --multi_ref_file  msa_references.fasta \
   --metadata_tsv <METADATA.tsv> \
   --protocol nanopore \
   --viral_taxon <TAXON_NAME> \
   --outdir <OUTDIR> \
   -profile <docker/singularity/podman/conda/institute>
```

To analyze nanopore metagenomics dataset, use:

```bash
nextflow run kwtrp-peo/viralphyl \
   --fastq_dir <DATA_DIR>  \
   --metadata_tsv metadata.tsv \
   --protocol metagenomics \
   --kraken2_db  <KRAKEN2_DB> \
   --outdir <OUTDIR> \
   -profile <docker/singularity/podman/conda/institute>
```

## Documentation

The kwtrp-peo/viralphyl pipeline includes comprehensive documentation covering [usage](), [parameters](), and expected [outputs]().

For a quick overview of the available options and parameters, you can access the command-line help by running:

```bash
nextflow run kwtrp-peo/viralphyl --help
```

## Credits

**kwtrp-peo/viralphyl** incorporates some custom R and Python scripts that were originally implemented in [viralrecon](https://github.com/nf-core/viralrecon?tab=readme-ov-file). The pipeline is currently under active development in collaboration with the [KWTRP PEO group](https://github.com/kwtrp-peo). It is coordinated by [George Githinji](https://github.com/ggklf) for the [KEMRI-Wellcome Trust Research Program (KWTRP)](https://kemri-wellcome.org/) and primarily implemented and maintained by [Samuel Odoyo](https://github.com/samordil).

We thank the following people for their extensive assistance in the development of this pipeline\*:
<!-- TODO nf-core: If applicable, make list of people who have also contributed -->
| Name                                                      | Affiliation                                                                           |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| [Arnold Lambisia](https://github.com/arnoldlambisia)      | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |
| [Brenda Kamau](https://github.com/brendamuthonikamau)     | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |
| [Dorcas Okanda](https://github.com/DOkanda)               | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |
| [Edidah Moraa](https://github.com/edidah)                 | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |
| [John Mwita](https://github.com/morobemwita)              | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |
| [Parcelli Jepchirchir](https://github.com/Parcelli)       | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |
| [Sebastain Musundi](https://github.com/sebymusundi)       | [KEMRI-Wellcome Trust Research Program, Kenya](https://kemri-wellcome.org/)           |

> \* Listed in alphabetical order


## Contributions and Support

If you would like to contribute to this pipeline, please see the [contributing guidelines](.github/CONTRIBUTING.md).

## Citations

<!-- TODO nf-core: Add citation for pipeline after first release. Uncomment lines below and update Zenodo doi and badge at the top of this file. -->
<!-- If you use kwtrp-peo/viralphyl for your analysis, please cite it using the following doi: [10.5281/zenodo.XXXXXX](https://doi.org/10.5281/zenodo.XXXXXX) -->

<!-- TODO nf-core: Add bibliography of tools and data used in your pipeline -->

If you use the kwtrp-peo/viralphyl pipeline in your research, please reference it using DOI: xxxx.

An extensive list of references for the tools used by the pipeline can be found in the [`CITATIONS.md`](CITATIONS.md) file.

This pipeline uses code and infrastructure developed and maintained by the [nf-core](https://nf-co.re) community, reused here under the [GNU General Public License v3.0](./LICENSE)

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).
