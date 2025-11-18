#!/usr/bin/env python3
"""
HED Command Line Interface

A unified command-line interface for HED (Hierarchical Event Descriptors) tools.
Provides a git-like interface with subcommands for validation, remodeling, and schema management.
"""

import click
from hed import _version as vr


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=str(vr.get_versions()["version"]), prog_name="hedpy")
def cli():
    """HED (Hierarchical Event Descriptors) command-line tools.

    This tool provides various commands for working with HED annotations,
    including validation, remodeling, and schema management.

    Use 'hedpy COMMAND --help' for more information on a specific command.
    """
    pass


@cli.group()
def remodel():
    """Remodel and transform HED-annotated datasets.

    Commands for running remodeling operations on BIDS datasets
    with HED annotations.
    """
    pass


@cli.group()
def schema():
    """HED schema management and validation tools.

    Commands for validating, updating, and managing HED schemas.
    """
    pass


# Import and register subcommands
@cli.command(name="validate-bids")
@click.argument("data_path", type=click.Path(exists=True))
@click.option("-ec", "--error-count", "error_limit", type=int, default=None, help="Limit errors of each code type to report.")
@click.option("-ef", "--errors-by-file", is_flag=True, help="Apply error limit by file rather than overall.")
@click.option("-f", "--format", type=click.Choice(["text", "json", "json_pp"]), default="text", help="Output format.")
@click.option(
    "-l",
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
    help="Log level.",
)
@click.option("-lf", "--log-file", "log_file", type=click.Path(), default=None, help="File path for saving log output.")
@click.option("-lq", "--log-quiet", is_flag=True, help="Suppress log output to stderr (only if --log-file is used).")
@click.option("-o", "--output-file", "output_file", type=click.Path(), default="", help="Output file for validation results.")
@click.option("-p", "--print-output", is_flag=True, help="Output results to stdout in addition to file.")
@click.option("-s", "--suffixes", multiple=True, default=["events", "participants"], help="Suffixes of tsv files to validate.")
@click.option("-v", "--verbose", is_flag=True, help="Output informational messages (equivalent to --log-level INFO).")
@click.option("-w", "--check-for-warnings", is_flag=True, help="Check for warnings as well as errors.")
@click.option(
    "-x",
    "--exclude-dirs",
    multiple=True,
    default=["sourcedata", "derivatives", "code", "stimuli"],
    help="Directory names to exclude from search.",
)
def validate_bids_cmd(
    data_path,
    error_limit,
    errors_by_file,
    format,
    log_level,
    log_file,
    log_quiet,
    output_file,
    print_output,
    suffixes,
    verbose,
    check_for_warnings,
    exclude_dirs,
):
    """Validate HED annotations in a BIDS dataset.

    DATA_PATH: Full path to the root directory of the BIDS dataset.
    """
    from hed.scripts.validate_bids import main as validate_bids_main

    # Build argument list for the original script
    args = [data_path]
    if error_limit is not None:
        args.extend(["-ec", str(error_limit)])
    if errors_by_file:
        args.append("-ef")
    if format:
        args.extend(["-f", format])
    if log_level:
        args.extend(["-l", log_level])
    if log_file:
        args.extend(["-lf", log_file])
    if log_quiet:
        args.append("-lq")
    if output_file:
        args.extend(["-o", output_file])
    if print_output:
        args.append("-p")
    if suffixes:
        args.append("-s")
        args.extend(suffixes)
    if verbose:
        args.append("-v")
    if check_for_warnings:
        args.append("-w")
    if exclude_dirs:
        args.append("-x")
        args.extend(exclude_dirs)

    validate_bids_main(args)


@remodel.command(name="run")
@click.argument("data_dir", type=click.Path(exists=True))
@click.argument("model_path", type=click.Path(exists=True))
@click.option("-bd", "--backup-dir", default="", help="Directory for the backup being created.")
@click.option("-bn", "--backup-name", default="", help="Name of the default backup for remodeling.")
@click.option("-b", "--bids-format", "use_bids", is_flag=True, help="Dataset is in BIDS format with sidecars.")
@click.option("-fs", "--file-suffix", "suffixes", multiple=True, default=["events"], help="File suffixes to process.")
@click.option(
    "-i",
    "--individual-summaries",
    type=click.Choice(["separate", "consolidated", "none"]),
    default="separate",
    help="Controls individual file summaries.",
)
@click.option("-j", "--json-sidecar", default=None, help="Path to JSON sidecar with HED information.")
@click.option("-ld", "--log-dir", default="", help="Directory for storing log entries for errors.")
@click.option("-nb", "--no-backup", is_flag=True, help="Operations run directly on files with no backup.")
@click.option("-ns", "--no-summaries", is_flag=True, help="Summaries are not saved.")
@click.option("-nu", "--no-update", is_flag=True, help="Files are not saved.")
@click.option("-hv", "--hed-versions", multiple=True, default=[], help="HED schema versions for annotation.")
@click.option("-s", "--save-formats", multiple=True, default=[".json", ".txt"], help="Format for saving summaries.")
@click.option("-t", "--task-names", multiple=True, default=[], help="Task names to process.")
@click.option("-v", "--verbose", is_flag=True, help="Output informational messages.")
@click.option("-w", "--work-dir", default="", help="Path to directory for saving.")
@click.option("-x", "--exclude-dirs", multiple=True, default=[], help="Directory names to exclude.")
def remodel_run_cmd(
    data_dir,
    model_path,
    backup_dir,
    backup_name,
    use_bids,
    suffixes,
    individual_summaries,
    json_sidecar,
    log_dir,
    no_backup,
    no_summaries,
    no_update,
    hed_versions,
    save_formats,
    task_names,
    verbose,
    work_dir,
    exclude_dirs,
):
    """Run remodeling operations on a dataset.

    DATA_DIR: Root directory of the dataset to remodel.
    MODEL_PATH: Path to JSON file with remodeling instructions.
    """
    from hed.tools.remodeling.cli.run_remodel import main as run_remodel_main

    args = [data_dir, model_path]
    if backup_dir:
        args.extend(["-bd", backup_dir])
    if backup_name:
        args.extend(["-bn", backup_name])
    if use_bids:
        args.append("-b")
    if suffixes:
        args.append("-fs")
        args.extend(suffixes)
    if individual_summaries:
        args.extend(["-i", individual_summaries])
    if json_sidecar:
        args.extend(["-j", json_sidecar])
    if log_dir:
        args.extend(["-ld", log_dir])
    if no_backup:
        args.append("-nb")
    if no_summaries:
        args.append("-ns")
    if no_update:
        args.append("-nu")
    if hed_versions:
        args.append("-hv")
        args.extend(hed_versions)
    if save_formats:
        args.append("-s")
        args.extend(save_formats)
    if task_names:
        args.append("-t")
        args.extend(task_names)
    if verbose:
        args.append("-v")
    if work_dir:
        args.extend(["-w", work_dir])
    if exclude_dirs:
        args.append("-x")
        args.extend(exclude_dirs)

    run_remodel_main(args)


@remodel.command(name="backup")
@click.argument("data_dir", type=click.Path(exists=True))
@click.option("-bd", "--backup-dir", default="", help="Directory for the backup being created.")
@click.option("-bn", "--backup-name", default="", help="Name for this backup.")
@click.option("-fs", "--file-suffix", "suffixes", multiple=True, default=["events"], help="File suffixes to backup.")
@click.option("-t", "--task-names", multiple=True, default=[], help="Task names to backup.")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option("-x", "--exclude-dirs", multiple=True, default=["derivatives"], help="Directories to exclude.")
def remodel_backup_cmd(data_dir, backup_dir, backup_name, suffixes, task_names, verbose, exclude_dirs):
    """Create a backup of dataset files before remodeling.

    DATA_DIR: Root directory of the dataset to backup.
    """
    from hed.tools.remodeling.cli.run_remodel_backup import main as backup_main

    args = [data_dir]
    if backup_dir:
        args.extend(["-bd", backup_dir])
    if backup_name:
        args.extend(["-bn", backup_name])
    if suffixes:
        args.append("-fs")
        args.extend(suffixes)
    if task_names:
        args.append("-t")
        args.extend(task_names)
    if verbose:
        args.append("-v")
    if exclude_dirs:
        args.append("-x")
        args.extend(exclude_dirs)

    backup_main(args)


@remodel.command(name="restore")
@click.argument("data_dir", type=click.Path(exists=True))
@click.option("-bd", "--backup-dir", default="", help="Directory containing the backup.")
@click.option("-bn", "--backup-name", default="", help="Name of backup to restore.")
@click.option("-t", "--task-names", multiple=True, default=[], help="Task names to restore.")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def remodel_restore(data_dir, backup_dir, backup_name, task_names, verbose):
    """Restore dataset files from a backup.

    DATA_DIR: Root directory of the dataset to restore.
    """
    from hed.tools.remodeling.cli.run_remodel_restore import main as restore_main

    args = [data_dir]
    if backup_dir:
        args.extend(["-bd", backup_dir])
    if backup_name:
        args.extend(["-bn", backup_name])
    if task_names:
        args.append("-t")
        args.extend(task_names)
    if verbose:
        args.append("-v")

    restore_main(args)


@schema.command(name="validate")
@click.argument("schema_path", type=click.Path(exists=True), nargs=-1, required=True)
@click.option("--add-all-extensions", is_flag=True, help="Always verify all versions of the same schema are equal.")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def schema_validate_cmd(schema_path, add_all_extensions, verbose):
    """Validate HED schema files.

    SCHEMA_PATH: Path(s) to schema file(s) to validate.
    """
    from hed.scripts.validate_schemas import main as validate_schemas_main

    args = list(schema_path)
    if add_all_extensions:
        args.append("--add-all-extensions")
    if verbose:
        args.append("-v")

    validate_schemas_main(args)


@schema.command(name="convert")
@click.argument("schema_path", type=click.Path(exists=True), nargs=-1, required=True)
@click.option("--set-ids", is_flag=True, help="Set/update HED IDs in the schema.")
def schema_convert_cmd(schema_path, set_ids):
    """Convert HED schema between formats (TSV, XML, MediaWiki, JSON).

    SCHEMA_PATH: Path(s) to schema file(s) to convert.
    """
    from hed.scripts.hed_convert_schema import main as convert_main

    args = list(schema_path)
    if set_ids:
        args.append("--set-ids")

    convert_main(args)


@schema.command(name="add-ids")
@click.argument("repo_path", type=click.Path(exists=True))
@click.argument("schema_name")
@click.argument("schema_version")
def schema_add_ids_cmd(repo_path, schema_name, schema_version):
    """Add HED IDs to a schema.

    REPO_PATH: Path to hed-schemas repository.
    SCHEMA_NAME: Schema name (e.g., 'standard').
    SCHEMA_VERSION: Schema version to process.
    """
    from hed.scripts.add_hed_ids import main as add_ids_main

    args = [repo_path, schema_name, schema_version]

    add_ids_main(args)


@schema.command(name="create-ontology")
@click.argument("repo_path", type=click.Path(exists=True))
@click.argument("schema_name")
@click.argument("schema_version")
@click.option("--dest", type=click.Path(), help="Output directory for ontology files.")
def schema_create_ontology_cmd(repo_path, schema_name, schema_version, dest):
    """Create an ontology from a HED schema.

    REPO_PATH: Path to hed-schemas repository.
    SCHEMA_NAME: Schema name (e.g., 'standard').
    SCHEMA_VERSION: Schema version.
    """
    from hed.scripts.create_ontology import main as create_ontology_main

    args = [repo_path, schema_name, schema_version]
    if dest:
        args.extend(["--dest", dest])

    create_ontology_main(args)


@cli.command(name="extract-sidecar")
@click.argument("data_path", type=click.Path(exists=True))
@click.option("-s", "--suffix", required=True, help="File suffix to process (e.g., 'events').")
@click.option("-vc", "--value-columns", multiple=True, help="Column names to treat as value columns.")
@click.option(
    "-sc",
    "--skip-columns",
    multiple=True,
    default=["onset", "duration", "sample"],
    help="Column names to skip.",
)
@click.option("-l", "--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]), default="WARNING")
@click.option("-lf", "--log-file", type=click.Path(), help="Log file path.")
@click.option("-lq", "--log-quiet", is_flag=True, help="Suppress stderr output.")
@click.option("-o", "--output-file", type=click.Path(), help="Output file for sidecar template.")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option(
    "-x",
    "--exclude-dirs",
    multiple=True,
    default=["sourcedata", "derivatives", "code", "stimuli"],
    help="Directories to exclude.",
)
def extract_sidecar_cmd(
    data_path, suffix, value_columns, skip_columns, log_level, log_file, log_quiet, output_file, verbose, exclude_dirs
):
    """Extract a sidecar template from a BIDS dataset.

    DATA_PATH: Root directory of the BIDS dataset.
    """
    from hed.scripts.hed_extract_bids_sidecar import main as extract_main

    args = [data_path, "-s", suffix]
    if value_columns:
        args.append("-vc")
        args.extend(value_columns)
    if skip_columns:
        args.append("-sc")
        args.extend(skip_columns)
    if log_level:
        args.extend(["-l", log_level])
    if log_file:
        args.extend(["-lf", log_file])
    if log_quiet:
        args.append("-lq")
    if output_file:
        args.extend(["-o", output_file])
    if verbose:
        args.append("-v")
    if exclude_dirs:
        args.append("-x")
        args.extend(exclude_dirs)

    extract_main(args)


def main():
    """Main entry point for the HED CLI."""
    cli()


if __name__ == "__main__":
    main()
