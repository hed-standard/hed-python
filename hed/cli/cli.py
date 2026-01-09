#!/usr/bin/env python3
"""
HED Command Line Interface.

A unified command-line interface for HED (Hierarchical Event Descriptors) tools.
Provides a git-like interface with subcommands for validation and schema management.
"""

import click
from click_option_group import optgroup
from hed import _version as vr

# Consistent metavar definitions used across all commands
METAVAR_PATH = "PATH"
METAVAR_FILE = "FILE"
METAVAR_NAME = "NAME"
METAVAR_STRING = "STRING"
METAVAR_PREFIX = "PREFIX"
METAVAR_N = "N"


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=str(vr.get_versions()["version"]), prog_name="hedpy")
def cli():
    """HED (Hierarchical Event Descriptors) command-line tools.

    This tool provides various commands for working with HED annotations,
    including validation and schema management.

    Use 'hedpy --help' for a list of commands.

    Use 'hedpy COMMAND --help' for more information on a specific command.
    """
    pass


@cli.group()
def schema():
    """HED schema management and validation tools

    Commands for validating, updating, and managing HED schemas.
    """
    pass


@cli.group()
def validate():
    """HED validation tools.

    Commands for validating HED annotations in datasets, files, and strings.
    """
    pass


# Import and register subcommands
@validate.command(
    name="bids-dataset",
    epilog="""
This command validates HED annotations in BIDS-formatted datasets, checking for
compliance with HED schema rules and proper annotation structure. It processes
TSV files with their associated JSON sidecars, following BIDS inheritance rules.

\b
Examples:
    # Basic validation with minimal output
    hedpy validate bids-dataset /path/to/dataset

    # Validation with progress messages
    hedpy validate bids-dataset /path/to/dataset --verbose

    # Validate specific file types
    hedpy validate bids-dataset /path/to/dataset -s events

    # Validate multiple file types
    hedpy validate bids-dataset /path/to/dataset -s events -s participants

    # Check for warnings in addition to errors
    hedpy validate bids-dataset /path/to/dataset --check-for-warnings

    # Save validation results to JSON file
    hedpy validate bids-dataset /path/to/dataset -f json -o results.json

    # Detailed debugging with file logging
    hedpy validate bids-dataset /path/to/dataset -l DEBUG --log-file validation.log --log-quiet

    # Limit error reporting for large datasets
    hedpy validate bids-dataset /path/to/dataset --error-limit 10
""",
)
@click.argument("data_path", type=click.Path(exists=True))
# File selection options
@optgroup.group("File selection options")
@optgroup.option(
    "-s",
    "--suffixes",
    multiple=True,
    default=["events", "participants"],
    show_default="events participants",
    metavar=METAVAR_NAME,
    help="Suffix(es) for base filename(s) to match (e.g., '-s events' matches files ending with 'events.tsv'); repeat to specify multiple suffixes (e.g., '-s events -s participants')",
)
@optgroup.option(
    "-x",
    "--exclude-dirs",
    multiple=True,
    default=["sourcedata", "derivatives", "code", "stimuli"],
    show_default="sourcedata derivatives code stimuli",
    metavar=METAVAR_NAME,
    help="Directory names (relative to root) to exclude (e.g.,'-x sourcedata -x derivatives' excludes data_root/sourcedata and data_root/derivatives)",
)
# Validation options
@optgroup.group("Validation options")
@optgroup.option(
    "-w",
    "--check-for-warnings",
    is_flag=True,
    help="Check for warnings as well as errors",
)
@optgroup.option(
    "-el",
    "--error-limit",
    type=int,
    default=None,
    metavar=METAVAR_N,
    help="Limit number of each error code to report",
)
@optgroup.option(
    "-ef",
    "--errors-by-file",
    is_flag=True,
    help="Apply error limit by file rather than overall",
)
# Output options
@optgroup.group("Output options")
@optgroup.option(
    "-f",
    "--format",
    type=click.Choice(["text", "json", "json_pp"]),
    default="text",
    show_default="text",
    help="Output format (e.g., '-f json_pp' outputs errors in pretty-printed JSON)",
)
@optgroup.option(
    "-o",
    "--output-file",
    "output_file",
    type=click.Path(),
    default="",
    metavar=METAVAR_FILE,
    help="Output file for validation results; if neither this nor --print-output is specified, results are not printed",
)
@optgroup.option(
    "-p",
    "--print-output",
    is_flag=True,
    help="Print validation results to stdout; if --output-file is also specified, output to both",
)
# Logging options
@optgroup.group("Logging options")
@optgroup.option(
    "-l",
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
    show_default="WARNING",
    help="Log level gives the level of detail in the logging output (e.g., '-l INFO' outputs basic informational messages)",
)
@optgroup.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Output informational messages (equivalent to --log-level INFO)",
)
@optgroup.option(
    "-lf",
    "--log-file",
    "log_file",
    type=click.Path(),
    default=None,
    metavar=METAVAR_FILE,
    help="File path for saving log output; logs still go to stderr unless --log-quiet is also used",
)
@optgroup.option(
    "-lq",
    "--log-quiet",
    is_flag=True,
    help="Suppress log output to stderr; only applicable when --log-file is used (logs go only to file)",
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
        args.extend(["-el", str(error_limit)])
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


@schema.command(name="validate")
@click.argument("schema_path", type=click.Path(exists=True), nargs=-1, required=True)
@click.option("--add-all-extensions", is_flag=True, help="Always verify all versions of the same schema are equal")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def schema_validate_cmd(schema_path, add_all_extensions, verbose):
    """Validate HED schema files.

    This command validates HED schema files for correctness, checking structure,
    syntax, and compliance with HED schema specification requirements.

    \b
    Examples:
        # Validate a single schema file
        hedpy schema validate /path/to/HED8.3.0.xml

        # Validate multiple schema files
        hedpy schema validate schema1.xml schema2.mediawiki

        # Validate with verbose output
        hedpy schema validate /path/to/schema.xml --verbose

        # Verify all versions of the same schema are equal
        hedpy schema validate schema.xml schema.tsv --add-all-extensions

    \b
    Arguments:
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
@click.option("--set-ids", is_flag=True, help="Set/update HED IDs in the schema")
def schema_convert_cmd(schema_path, set_ids):
    """Convert HED schema between formats (TSV, XML, MEDIAWIKI, JSON).

    This command converts HED schema files between different formats while
    maintaining semantic equivalence. Optionally updates HED IDs during conversion.

    \b
    Examples:
        # Convert schema (format auto-detected)
        hedpy schema convert /path/to/schema.xml

        # Convert and assign/update HED IDs
        hedpy schema convert /path/to/schema.xml --set-ids

        # Convert multiple schemas
        hedpy schema convert schema1.xml schema2.mediawiki

    \b
    Arguments:
        SCHEMA_PATH: Path(s) to schema file(s) to convert
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

    This command adds unique HED IDs to schema elements that don't have them,
    typically used during schema development and maintenance.

    \b
    Examples:
        # Add IDs to standard schema version 8.3.0
        hedpy schema add-ids /path/to/hed-schemas standard 8.3.0

        # Add IDs to a library schema
        hedpy schema add-ids /path/to/hed-schemas SCORE 1.0.0

    \b
    Arguments:
        REPO_PATH: Path to hed-schemas repository
        SCHEMA_NAME: Schema name (e.g., 'standard', 'SCORE')
        SCHEMA_VERSION: Schema version to process (e.g., '8.3.0')
    """
    from hed.scripts.add_hed_ids import main as add_ids_main

    args = [repo_path, schema_name, schema_version]

    add_ids_main(args)


@cli.group()
def extract():
    """HED extraction and analysis tools.

    Commands for extracting summaries and templates from tabular data.
    """
    pass


@extract.command(
    name="bids-sidecar",
    epilog="""
This command extracts a JSON sidecar template from BIDS datasets by analyzing
TSV files and identifying unique values in categorical columns. The template
can be used as a starting point for adding HED annotations to the dataset.

\b
Examples:
    # Extract from event files (default suffix)
    hedpy extract bids-sidecar /path/to/dataset

    # Extract with verbose progress output
    hedpy extract bids-sidecar /path/to/dataset --verbose

    # Extract from participant files instead of events
    hedpy extract bids-sidecar /path/to/dataset -s participants

    # Save output to a file instead of stdout
    hedpy extract bids-sidecar /path/to/dataset -o template.json

    # Exclude specific columns from the template
    hedpy extract bids-sidecar /path/to/dataset -sc onset -sc duration -sc response_time

    # Save logs to file and suppress console output
    hedpy extract bids-sidecar /path/to/dataset --log-file extraction.log --log-quiet
""",
)
@click.argument("data_path", type=click.Path(exists=True))
# File selection options
@optgroup.group("File selection options")
@optgroup.option(
    "-s",
    "--suffix",
    default="events",
    show_default="events",
    metavar=METAVAR_NAME,
    help="Suffix for base filename(s) (e.g., '-s participants' to match files ending with participants.tsv",
)
@optgroup.option(
    "-x",
    "--exclude-dirs",
    multiple=True,
    default=["sourcedata", "derivatives", "code", "stimuli"],
    show_default="sourcedata derivatives code stimuli",
    metavar=METAVAR_NAME,
    help="Directory names (relative to root) to exclude (e.g., -x sourcedata -x derivatives)",
)
# Column processing options
@optgroup.group("Column processing options")
@optgroup.option(
    "-vc",
    "--value-columns",
    multiple=True,
    metavar=METAVAR_NAME,
    help="Column names to treat as value columns (e.g., -vc response_time -vc accuracy)",
)
@optgroup.option(
    "-sc",
    "--skip-columns",
    multiple=True,
    default=["onset", "duration", "sample"],
    show_default="onset duration sample",
    metavar=METAVAR_NAME,
    help="Column names to skip (e.g., -sc onset -sc duration)",
)
# Output options
@optgroup.group("Output options")
@optgroup.option(
    "-o",
    "--output-file",
    type=click.Path(),
    metavar=METAVAR_FILE,
    help="Output file for sidecar template; if not specified, output written to stdout",
)
# Logging options
@optgroup.group("Logging options")
@optgroup.option(
    "-l",
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
    show_default="WARNING",
)
@optgroup.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@optgroup.option(
    "-lf",
    "--log-file",
    type=click.Path(),
    metavar=METAVAR_FILE,
    help="File path for saving log output; logs still go to stderr unless --log-quiet is also used",
)
@optgroup.option(
    "-lq",
    "--log-quiet",
    is_flag=True,
    help="Suppress log output to stderr; only applicable when --log-file is used (logs go only to file)",
)
def extract_bids_sidecar_cmd(
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


@extract.command(
    name="tabular-summary",
    epilog="""
This command processes TSV (tab-separated values) files and generates summary
statistics about the columns and their values. Unlike extract bids-sidecar,
this command does not assume BIDS dataset organization and can process any
collection of TSV files matching specified criteria.

\b
Examples:
    # Extract summary from event TSV files (default suffix='events')
    hedpy extract tabular-summary /path/to/data

    # Extract summary from all TSV files using wildcard
    hedpy extract tabular-summary /path/to/data -s '*'

    # Extract summary with verbose output and save to file
    hedpy extract tabular-summary /path/to/data --verbose -o summary.json

    # Extract summary with categorical value limit
    hedpy extract tabular-summary /path/to/data --categorical-limit 50

    # Process files with specific suffix and exclude certain directories
    hedpy extract tabular-summary /path/to/data -s participants -x test -x backup

    # Filter to only process files containing 'sub-01' in filename
    hedpy extract tabular-summary /path/to/data --filter 'sub-01'

    # Filter to only process files from task 'rest' with all TSV files
    hedpy extract tabular-summary /path/to/data -s '*' --filter 'task-rest'
""",
)
@click.argument("data_path", type=click.Path(exists=True))
# File selection options
@optgroup.group("File selection options")
@optgroup.option(
    "-p",
    "--prefix",
    "name_prefix",
    metavar=METAVAR_PREFIX,
    help="Prefix for base filename (e.g., -p sub- to match 'sub-01_events.tsv')",
)
@optgroup.option(
    "-s",
    "--suffix",
    "name_suffix",
    default="events",
    show_default="events",
    metavar=METAVAR_NAME,
    help="Suffix for base filename (e.g., -s events to match files ending with '_events.tsv'); use '*' to match all TSV files regardless of suffix",
)
@optgroup.option(
    "-x",
    "--exclude-dirs",
    multiple=True,
    default=[],
    metavar=METAVAR_NAME,
    help="Directory names (relative to root) to exclude (e.g., -x derivatives -x code)",
)
@optgroup.option(
    "-fl",
    "--filter",
    "filename_filter",
    metavar=METAVAR_STRING,
    help="Filter files to keep only those whose basename contains the designated filter (e.g., -fl task-rest retains files with 'task-rest' in the filename)",
)
# Column processing options
@optgroup.group("Column processing options")
@optgroup.option(
    "-vc",
    "--value-columns",
    multiple=True,
    metavar=METAVAR_NAME,
    help="Column names to treat as value columns (e.g., -vc response_time -vc accuracy)",
)
@optgroup.option(
    "-sc",
    "--skip-columns",
    multiple=True,
    metavar=METAVAR_NAME,
    help="Column names to skip (e.g., -sc onset -sc duration)",
)
@optgroup.option(
    "-cl",
    "--categorical-limit",
    type=int,
    metavar=METAVAR_N,
    help="Maximum unique values for categorical columns",
)
# Output options
@optgroup.group("Output options")
@optgroup.option(
    "-o",
    "--output-file",
    type=click.Path(),
    metavar=METAVAR_FILE,
    help="Output file for summary; if not specified, output written to stdout",
)
@optgroup.option(
    "-f",
    "--format",
    "output_format",
    type=click.Choice(["json", "text"]),
    default="json",
    show_default="json",
    help="Output format",
)
# Logging options
@optgroup.group("Logging options")
@optgroup.option(
    "-l",
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="WARNING",
    show_default="WARNING",
)
@optgroup.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@optgroup.option(
    "-lf",
    "--log-file",
    type=click.Path(),
    metavar=METAVAR_FILE,
    help="File path for saving log output; logs still go to stderr unless --log-quiet is also used",
)
@optgroup.option(
    "-lq",
    "--log-quiet",
    is_flag=True,
    help="Suppress log output to stderr; only applicable when --log-file is used (logs go only to file)",
)
def extract_tabular_summary_cmd(
    data_path,
    name_prefix,
    name_suffix,
    exclude_dirs,
    filename_filter,
    value_columns,
    skip_columns,
    categorical_limit,
    output_file,
    output_format,
    log_level,
    log_file,
    log_quiet,
    verbose,
):
    """Extract tabular summary from TSV files.

    DATA_PATH: Root directory containing TSV files to process.
    """
    from hed.scripts.extract_tabular_summary import main as extract_summary_main

    args = [data_path]
    if name_prefix:
        args.extend(["-p", name_prefix])
    if name_suffix:
        args.extend(["-s", name_suffix])
    if exclude_dirs:
        args.append("-x")
        args.extend(exclude_dirs)
    if filename_filter:
        args.extend(["-fl", filename_filter])
    if value_columns:
        args.append("-vc")
        args.extend(value_columns)
    if skip_columns:
        args.append("-sc")
        args.extend(skip_columns)
    if categorical_limit is not None:
        args.extend(["-cl", str(categorical_limit)])
    if output_file:
        args.extend(["-o", output_file])
    if output_format:
        args.extend(["-f", output_format])
    if log_level:
        args.extend(["-l", log_level])
    if log_file:
        args.extend(["-lf", log_file])
    if log_quiet:
        args.append("-lq")
    if verbose:
        args.append("-v")

    extract_summary_main(args)


def main():
    """Main entry point for the HED CLI."""
    cli()


if __name__ == "__main__":
    main()
