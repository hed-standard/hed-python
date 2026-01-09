#!/usr/bin/env python3
"""
Command-line script for extracting tabular summaries from datasets without BIDS organization.

This script processes TSV (tab-separated values) files and generates summary statistics about
the columns and their values. Unlike hed_extract_bids_sidecar, this script does not assume
BIDS dataset organization and can process any collection of TSV files matching specified
criteria.

Logging Options:
- Default: WARNING level logs go to stderr (quiet unless there are issues)
- --verbose or --log-level INFO: Show informational messages about progress
- --log-level DEBUG: Show detailed debugging information
- --log-file FILE: Save logs to a file instead of/in addition to stderr
- --log-quiet: When using --log-file, suppress stderr output (file only)

Examples:
    # Extract summary from event TSV files (default suffix='events')
    extract_tabular_summary /path/to/data

    # Extract summary from all TSV files using wildcard
    extract_tabular_summary /path/to/data --suffix '*'

    # Extract summary with verbose output and save to file
    extract_tabular_summary /path/to/data --verbose --output-file summary.json

    # Extract summary with categorical value limit
    extract_tabular_summary /path/to/data --categorical-limit 50

    # Process files with specific suffix and exclude certain directories
    extract_tabular_summary /path/to/data --suffix participants --exclude-dirs test backup

    # Filter to only process files containing 'sub-01' in filename
    extract_tabular_summary /path/to/data --filter 'sub-01'

    # Filter to only process files from task 'rest' with all TSV files
    extract_tabular_summary /path/to/data --suffix '*' --filter 'task-rest'
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from hed import _version as vr
from hed.tools.util.io_util import get_file_list
from hed.tools.analysis.tabular_summary import TabularSummary


def get_parser():
    """Create the argument parser for extract_tabular_summary.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Extract tabular summary from a collection of tabular files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=False,
    )

    # Add custom help option with consistent formatting
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
    )

    # Required arguments
    parser.add_argument("data_path", help="Full path of root directory containing TSV files to process")

    # File selection options
    file_group = parser.add_argument_group("File selection options")
    file_group.add_argument(
        "-p",
        "--prefix",
        dest="name_prefix",
        default=None,
        help="Prefix for base filename (e.g., 'sub-' to match 'sub-01_events.tsv')",
    )
    file_group.add_argument(
        "-s",
        "--suffix",
        dest="name_suffix",
        default="events",
        help="Suffix for base filename (e.g., 'events' to match files ending with '_events.tsv'); "
        "use '*' to match all TSV files regardless of suffix (default: %(default)s)",
    )
    file_group.add_argument(
        "-x",
        "--exclude-dirs",
        nargs="*",
        default=[],
        dest="exclude_dirs",
        help="Directory names to exclude from file search (default: none)",
    )
    file_group.add_argument(
        "-fl",
        "--filter",
        dest="filename_filter",
        default=None,
        help="Optional string to filter filenames; only files containing this string in their name will be processed",
    )

    # Column processing options
    column_group = parser.add_argument_group("Column processing options")
    column_group.add_argument(
        "-vc",
        "--value-columns",
        dest="value_columns",
        nargs="*",
        default=None,
        help="List of column names to treat as value columns (numeric/continuous data)",
    )
    column_group.add_argument(
        "-sc",
        "--skip-columns",
        dest="skip_columns",
        nargs="*",
        default=None,
        help="List of column names to skip in the extraction",
    )
    column_group.add_argument(
        "-cl",
        "--categorical-limit",
        dest="categorical_limit",
        type=int,
        default=None,
        help="Maximum number of unique values to store for a categorical column; "
        "if a column has more unique values, it will be truncated (default: None, no limit)",
    )

    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "-o",
        "--output-file",
        dest="output_file",
        default="",
        help="Full path of output file for the tabular summary (JSON format); "
        "if not specified, output written to standard out",
    )
    output_group.add_argument(
        "-f",
        "--format",
        dest="output_format",
        choices=["json", "text"],
        default="json",
        help="Output format: 'json' for JSON structure or 'text' for human-readable summary (default: %(default)s)",
    )

    # Logging options
    logging_group = parser.add_argument_group("Logging options")
    logging_group.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Log level (case insensitive, default: %(default)s)",
    )
    logging_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show progress messages during processing (equivalent to --log-level INFO)",
    )
    logging_group.add_argument(
        "-lf",
        "--log-file",
        dest="log_file",
        default=None,
        help="Full path to save log output to file; if not specified, logs go to stderr",
    )
    logging_group.add_argument(
        "-lq",
        "--log-quiet",
        action="store_true",
        dest="log_quiet",
        help="Suppress log output to stderr (only applies if --log-file is used)",
    )

    return parser


def extract_summary(args):
    """Extract tabular summary from files in the specified directory.

    Parameters:
        args (argparse.Namespace): Parsed command line arguments.

    Returns:
        TabularSummary: The combined summary of all processed files.

    Raises:
        FileNotFoundError: If no files matching criteria are found.
        Exception: For various file processing errors.
    """
    logger = logging.getLogger("extract_tabular_summary")
    logger.info(f"Data directory: {args.data_path}")
    logger.info(f"HED tools version: {str(vr.get_versions())}")
    logger.debug(f"Name prefix: {args.name_prefix}")
    logger.debug(f"Name suffix: {args.name_suffix}")
    logger.debug(f"Exclude directories: {args.exclude_dirs}")
    logger.debug(f"Filename filter: {args.filename_filter}")
    logger.debug(f"Value columns: {args.value_columns}")
    logger.debug(f"Skip columns: {args.skip_columns}")
    logger.debug(f"Categorical limit: {args.categorical_limit}")

    try:
        # Handle wildcard suffix - '*' means match all files
        suffix_filter = None if args.name_suffix == "*" else args.name_suffix

        # Get list of TSV files matching criteria
        logger.info("Searching for TSV files matching criteria...")
        if args.name_suffix == "*":
            logger.debug("Using wildcard suffix - matching all TSV files")

        file_list = get_file_list(
            root_path=args.data_path,
            name_prefix=args.name_prefix,
            name_suffix=suffix_filter,
            extensions=[".tsv"],
            exclude_dirs=args.exclude_dirs,
        )

        # Apply filename filter if specified
        if args.filename_filter:
            original_count = len(file_list)
            file_list = [f for f in file_list if args.filename_filter in Path(f).name]
            logger.info(f"Filename filter '{args.filename_filter}' reduced files from {original_count} to {len(file_list)}")

        if not file_list:
            error_msg = (
                f"No TSV files found matching criteria in {args.data_path}. "
                f"Prefix: {args.name_prefix}, "
                f"Suffix: {args.name_suffix}, "
                f"Filter: {args.filename_filter}"
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        logger.info(f"Found {len(file_list)} files to process")
        if logger.isEnabledFor(logging.DEBUG):
            for file_path in file_list:
                logger.debug(f"  - {file_path}")

        # Create the overall TabularSummary
        logger.info("Creating overall tabular summary...")
        overall_summary = TabularSummary(
            value_cols=args.value_columns,
            skip_cols=args.skip_columns,
            name=f"Summary of {Path(args.data_path).name}",
            categorical_limit=args.categorical_limit,
        )

        # Process each file
        logger.info("Processing files...")
        successful_files = 0
        failed_files = 0

        for file_path in file_list:
            try:
                logger.debug(f"Processing: {file_path}")

                # Create a TabularSummary for this individual file
                file_summary = TabularSummary(
                    value_cols=args.value_columns,
                    skip_cols=args.skip_columns,
                    name=Path(file_path).name,
                    categorical_limit=args.categorical_limit,
                )

                # Update the file summary with the file's data
                file_summary.update(file_path, name=file_path)

                # Add this file's summary to the overall summary
                overall_summary.update_summary(file_summary)

                successful_files += 1
                logger.debug(f"Successfully processed: {file_path}")

            except Exception as e:
                failed_files += 1
                logger.warning(f"Failed to process {file_path}: {e}")
                logger.debug(f"Full exception for {file_path}:", exc_info=True)

        # Log final statistics
        logger.info("Processing complete:")
        logger.info(f"  Successfully processed: {successful_files} files")
        if failed_files > 0:
            logger.warning(f"  Failed to process: {failed_files} files")
        logger.info(f"  Total events across all files: {overall_summary.total_events}")
        logger.info(f"  Categorical columns: {len(overall_summary.categorical_info)}")
        logger.info(f"  Value columns: {len(overall_summary.value_info)}")

        if successful_files == 0:
            raise Exception("No files were successfully processed")

        return overall_summary

    except Exception as e:
        logger.error(f"Error during summary extraction: {e}")
        logger.debug("Full exception details:", exc_info=True)
        raise


def format_output(summary, args):
    """Format the summary for output based on requested format.

    Parameters:
        summary (TabularSummary): The tabular summary to format.
        args (argparse.Namespace): Parsed command line arguments.

    Returns:
        str: Formatted output string.
    """
    if args.output_format == "text":
        # Return human-readable text format
        return str(summary)
    else:
        # Return JSON format
        summary_dict = summary.get_summary(as_json=False)
        output_dict = {
            "tabular_summary": summary_dict,
            "hedtools_version": str(vr.get_versions()),
            "parameters": {
                "data_path": args.data_path,
                "name_prefix": args.name_prefix,
                "name_suffix": args.name_suffix,
                "exclude_dirs": args.exclude_dirs,
                "value_columns": args.value_columns,
                "skip_columns": args.skip_columns,
                "categorical_limit": args.categorical_limit,
            },
        }
        return json.dumps(output_dict, indent=4)


def setup_logging(args):
    """Configure logging based on command line arguments.

    Parameters:
        args (argparse.Namespace): Parsed command line arguments.

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Determine log level
    log_level = args.log_level.upper() if args.log_level else "WARNING"
    if args.verbose:
        log_level = "INFO"

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Clear any existing handlers from root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set the root logger level
    root_logger.setLevel(getattr(logging, log_level))

    # Create formatter
    formatter = logging.Formatter(log_format, datefmt=date_format)

    # File handler if log file specified
    if args.log_file:
        file_handler = logging.FileHandler(args.log_file, mode="w", encoding="utf-8")
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Console handler (stderr) unless explicitly quieted and file logging is used
    if not args.log_quiet or not args.log_file:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    logger = logging.getLogger("extract_tabular_summary")
    logger.info(f"Starting tabular summary extraction with log level: {log_level}")
    if args.log_file:
        logger.info(f"Log output will be saved to: {args.log_file}")

    return logger


def main(arg_list=None):
    """Main entry point for the script.

    Parameters:
        arg_list (list, None): Optional list of command line arguments for testing.
                              If None, uses sys.argv.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    # Create the argument parser
    parser = get_parser()

    # Parse the arguments
    args = parser.parse_args(arg_list)

    # Setup logging
    logger = setup_logging(args)

    try:
        # Extract the summary
        summary = extract_summary(args)

        # Format output
        output = format_output(summary, args)

        # Write to file or print to stdout
        if args.output_file:
            logger.info(f"Writing output to: {args.output_file}")
            with open(args.output_file, "w", encoding="utf-8") as fp:
                fp.write(output)
        else:
            print(output)

        logger.info("Extraction completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Extraction failed with exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
