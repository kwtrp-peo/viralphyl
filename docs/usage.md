# Viralphyl: Usage
This documentation provides an overview of how the pipeline works, and a description of the required command-line flags 

## Standard Usage 

Below is an example of the expected command for the pipeline to sucessfully run

```
nextflow run main.nf -profile docker,local --fastq_dir raw_reads/ --outdir Results/ --metadata_tsv metadata.tsv

```

##  Input Options [Files/Directories]:

```--fastq_dir ```

 This parameter is used to specify the the path to the sequencing output files/runs. The expected data should be in subdirectories named 'runxx' (e.g., run1, rsv_run2, hmpv_run03_data). The 'runxx' subdirectories should contain 'barcodeXX' folders inside (e.g., barcode01, barcode02).

 Example of the path structure:
 ```
 /path/to/raw_data/
                                ├── run1/
                                │   ├── barcode01/
                                │   ├── barcode02/
                                ├── hMPV_run2_2025/
                                │   ├── barcode01/
```

```--metadata_tsv ```

This specifies the path to a tab separated values (tsv) file that contains the sample metadata. The tsv must include the following data partaining the samples; 'sequence_run', 'barcode_num', 'sample_id' and 'collection_date' columns. If these conditions are not met, the samples missing required metadata will be excluded from the run. 

An example of the tsv is given below 

Example tsv format



| Sequence_run | Barcode_num |sample_id  | collection_date|
|----------|----------|----------|----------|
| run1  | barcode01   | SMP001  | 2025-04-20   |
| run2   | barcode02   | SMP049   | 2025-06-29   |





```--multi_ref_file ```    (Optional ) 

This provides a path to a FASTA MSA reference file. See the "Artic MinION Parameters" section for details.

```--sequencing_summary ``` (Optional)

This provides a path to ont sequencing summary file generated after Nanopore run completion.


## Input Options:

```--viral_taxon```

For the viral_taxon  of the data processed, you have the option to provide different taxon, including ["hMPV", "hRV", "hRSVA", "hRSVB", "CA", "CB"]. However, the pipeline's default taxon is "hMPV". 

```--viral_host```

To successfully remove any host reads, you're provided with an option to specify the viral host. The default host for the pipeline is human (default: human)

```--protocol```

This input parameter allows you to select the applicable protocol, depending on the sequencing approch for the data. 
The provided options include  "amplicon" or "metagenomics" (The default protocol is : "amplicon").


## Output Options:

```--outdir ```

This provided the path to the directory where results will be saved. The default path is ```'./Results'``` Which is placed  within the pipeline run directory.


##  Module options

These are boolean options (True/False) provided by the pipeline, that allows you to skip or perform some of the pipeline modlues. 

```--skip_assembly```

This gives the option to skip the assembly step for the selected protocol (nanopore or metagenomic).  The default is : false

```--skip_qc```

This gives the option to skip the quality check step for the selected protocol (default: false)

```--skip_phylogenetics```

This gives the option, if set, to skip the nanopore phylogenetics module (default: false)

```--skip_classification```

If set, this skips the metagenomic classification module (The default is : false)


## Assembly Step Parameters:

###  Artic Guppyplex Parameters:

```--min_read_length```

This sets the minimum length for raw reads to be retained (The default is : 10).

```--max_read_length```

This sets the maximum length for raw reads (The default is : null - no maximum length restriction).

```--min_read_quality```

This sets the minimum read quality threshold.  (The default is : null - no quality restriction).  

 
 ### Artic MinION Parameters:

 ```--normalise```

For normalise option, you can normalise down to moderate coverage to save runtime (The default is : 100, to deactivate the default, use  `--normalise 0`)

```--multi_ref_file```

This is an option to provide the pipeline with a FASTA file with multiple aligned references; where the closest match is select. The primer scheme reference must be included. If the file is not provided, only the primer scheme reference sequence is used.

```--genotypes```

This enables genotype output for the closest reference match. *Requires --multi_ref_file*. [The default is : true]

```--no-indel```

This is an option to not report InDels (uses SNP-only mode of nanopolish/medaka). (The default is: InDels are reported).


```--primer-match-threshold```

This allows fuzzy primer matching within this threshold (The default is: 35)

```--min_mapq```

This gives the option to choose the minimum mapping quality to consider (The default is: 20)

```--min_depth```

This provides the minimum coverage required for a position to be included in the consensus sequence (The default is: 20)

```--sequence_threshold```

This is the minimum coverage cutoff for tree construction (The acceptable range is between 0.0-1.0, and the default is : 0.7)

**Reference FASTA and BED file (Required if --protocol="amplicon"):**

 ```--ref_fasta```

  This is the reference FASTA sequence for the scheme (required for amplicon mode).

 ``` --ref_bed```

 This provides a BED file containing the primer scheme which is required for the amplicon mode

 ```--clair3_model```

  You can specify the clair3 model to use. if not provided, pipeline uses models available in the container.

  ```--clair3_model_dir```
  
  This is the path to directory containing Clair3 models specified (the path defaults to container model directory).


  ## Phylogenetics Step Parameters:

  ### GLOBAL DATASET OPTIONS:
  ```--global_fasta FILE``` 

  This provided a FASTA file input option of global genomes (The default is : download, allowing auto-download of the FASTA file if not provided)

  ```--global_metadata_tsv FILE```

This provides a TSV file containing global metadata (The default is : download)
Must include these columns:
 - "strain": Unique sequence identifiers
- "country": Country information
- "region": One of the six global continents (Africa, Asia, Europe, N/S America or Oceania)

```--min_sequence_length INT```

This allows for the specification of the minimum sequence length to keep (-1 = no limit, the default is: -1)

```--max_sequence_length INT```

This flag allows for the specification of the maximum sequence length to keep (-1 = no limit, the default is: -1)


###  SUBSAMPLING OPTIONS:

```--subsample_seed INT```

The Seed for subsampling option is provided under the subsample options. (-1 = random, the default is: 123)

```--subsample_max_sequences INT```

The flag gives you the option to choose the max sequences in tree (the default is: 250)

 ```--subsample_by STR ```
 Criteria: "country", "region", "year", etc. (default: "country year month")

 ### AUGUR AUSPICE OPTIONS

 ```--color_by``` 

 This is a column name in the metadata TSV file to use for coloring (the default is color by: 'region')

 ##  Metagenomics Workflow Parameters:
 ### GLOBAL PARAMETER OPTIONS:

  ```--human_genome```

  This provides the path to the human genome which is acceptable in MMI index, .fna.gz|.fa.gz file, or URL formats. If not provided with the files, the system auto-downloads from NCBI FTP

  ```--classifier```

  You can specify the read classifier to use for your metagenome. The pipeline gives two options; 'mash' or 'kraken2' and the default is : kraken2

  ```--mash_db```

  This gives the path to the mash read classifier database(mash sketch DB, .msh). If the path to the database is not provided, then it is auto-downloaded. This applies if for the classifier you've specified mash 

  ```--kraken2_db```

  This gives a path to the Kraken2 DB, which can be provided as a link or a db directory. The database will be auto-downloaded if not provided. This applies if the default parameters are applied

  ```--show_organisms```

For the number of top organisms to report per sample from the mash classifier, you can select using this flag. (The default number of the report is : 3) 

 ```--target_pathogen```

 This provides the path to a text file with pathogen(s) (one per line) for genome assembly. The required syntax is to use a single space between words in multi-word names.

```--min_reads_per_taxon```


This gives the specification of the minimum reads required per taxon (species/strain) to qualify for assembly.





