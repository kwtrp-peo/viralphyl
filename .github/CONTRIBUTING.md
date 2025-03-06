# kwtrp-peo/viralphyl: Contributing Guidelines

Hi there!
Many thanks for taking an interest in improving kwtrp-peo/viralphyl.

We try to manage the required tasks for kwtrp-peo/viralphyl using GitHub issues, you probably came to this page when creating one.
Please use the pre-filled template to save time.

## Contribution workflow

If you'd like to write some code for kwtrp-peo/viralphyl, the standard workflow is as follows:

1. Check that there isn't already an issue about your idea in the [kwtrp-peo/viralphyl issues](https://github.com/kwtrp-peo/viralphyl/issues) to avoid duplicating work. If there isn't one already, please create one so that others know you're working on this
2. [Fork](https://help.github.com/en/github/getting-started-with-github/fork-a-repo) the [kwtrp-peo/viralphyl repository](https://github.com/kwtrp-peo/viralphyl) to your GitHub account
3. Make the necessary changes / additions within your forked repository following [Pipeline conventions](#pipeline-contribution-conventions)
4. Submit a Pull Request against the `dev` branch and wait for the code to be reviewed and merged

If you're not used to this workflow with git, you can start with some [docs from GitHub](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests) or even their [excellent `git` resources](https://try.github.io/).

## Tests

You have the option to test your changes locally by running the pipeline. For receiving warnings about process selectors and other `debug` information, it is recommended to use the debug profile. Execute all the tests with the following command:

```bash
nf-test test --profile debug,test,docker --verbose
```

When you create a pull request with changes, [GitHub Actions](https://github.com/features/actions) will run automatic tests.
Typically, pull-requests are only fully reviewed when these tests are passing, though of course we can help out before then.

There are typically two types of tests that run:

## Patch

:warning: Only in the unlikely and regretful event of a release happening with a bug.

- On your own fork, make a new branch `hotfix/patch` based on `upstream/master`.
- Fix the bug.
- A PR should be made on `master` from hotfix/patch to directly path this particular bug.

## Pipeline contribution conventions

To make the kwtrp-peo/viralphyl code and processing logic more understandable for new contributors and to ensure quality, we semi-standardise the way the code and other contributions are written.

### Adding a new step

If you wish to contribute a new step, please use the following coding standards:

1. Define the corresponding input channel into your new process from the expected previous process channel
2. Write the process block (see below).
3. Define the output channel if needed (see below).
4. Add any new parameters to `nextflow.config` with a default (see below).
5. Add sanity checks and validation for all relevant parameters.
6. Perform local tests to validate that the new code works as expected.
7. If applicable, add a new test command in `.github/workflow/ci.yml`.
8. Add a description of the output files and if relevant any appropriate images from the MultiQC report to `docs/output.md`.

### Default values

Parameters should be initialised / defined with default values in `nextflow.config` under the `params` scope.

### Default processes resource requirements

Sensible defaults for process resource requirements (CPUs / memory / time) for a process should be defined in `conf/base.config`. These should generally be specified generic with `withLabel:` selectors so they can be shared across multiple processes/steps of the pipeline. A nf-core standard set of labels that should be followed where possible can be seen in the [nf-core pipeline template](https://github.com/nf-core/tools/blob/master/nf_core/pipeline-template/conf/base.config), which has the default process as a single core-process, and then different levels of multi-core configurations for increasingly large memory requirements defined with standardised labels.

The process resources can be passed on to the tool dynamically within the process with the `${task.cpus}` and `${task.memory}` variables in the `script:` block.

### Naming schemes

Please use the following naming schemes, to make it easy to understand what is going where.

- initial process channel: `ch_output_from_<process>`
- intermediate and terminal channels: `ch_<previousprocess>_for_<nextprocess>`

### Images and figures

For overview images and other documents we follow the nf-core [style guidelines and examples](https://nf-co.re/developers/design_guidelines).
