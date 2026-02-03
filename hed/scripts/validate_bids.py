#!/usr/bin/env python3
"""
Command-line script for validating BIDS datasets with HED annotations.

This script validates HED annotations in BIDS-formatted datasets, checking for compliance
with HED schema rules and proper annotation structure. It processes TSV files with their
associated JSON sidecars, following BIDS inheritance rules.

Logging Options:
- Default: WARNING level logs go to stderr (quiet unless there are issues)
- --verbose or --log-level INFO: Show informational messages about progress
- --log-level DEBUG: Show detailed debugging information
- --log-file FILE: Save logs to a file instead of/in addition to stderr
- --log-quiet: When using --log-file, suppress stderr output (file only)

Examples:
    # Basic validation with minimal output
    validate_bids /path/to/dataset

    # Validation with progress messages
    validate_bids /path/to/dataset --verbose

    # Validate specific file types
    validate_bids /path/to/dataset --suffixes events

    # Validate multiple file types
    validate_bids /path/to/dataset --suffixes events participants

    # Check for warnings in addition to errors
    validate_bids /path/to/dataset --check_for_warnings

    # Save validation results to JSON file
    validate_bids /path/to/dataset --format json --output_file results.json

    # Detailed debugging with file logging
    validate_bids /path/to/dataset --log-level DEBUG --log-file validation.log --log-quiet

    # Limit error reporting for large datasets
    validate_bids /path/to/dataset --error_limit 10
"""

import argparse
import logging
import sys
from hed import __version__
from hed.errors import ErrorHandler
from hed.scripts.script_utils import setup_logging, format_validation_results
from hed.tools import BidsDataset


def get_parser():
    """Create the argument parser for validate_bids.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validate a BIDS-formatted HED dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
        add_help=False,
    )

    # Add custom help option
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
    )

    # Required arguments
    parser.add_argument("data_path", help="Full path of dataset root directory")

    # File selection options
    file_group = parser.add_argument_group("File selection options")
    file_group.add_argument(
        "-s",
        "--suffixes",
        dest="suffixes",
        nargs="*",
        default=["events", "participants"],
        help="Suffixes (without underscore) of TSV files to validate; use '*' for all TSV files (default: events participants)",
    )
    file_group.add_argument(
        "-x",
        "--exclude-dirs",
        nargs="*",
        default=["sourcedata", "derivatives", "code", "stimuli"],
        dest="exclude_dirs",
        help="Directory names to exclude in search for files to validate (default: sourcedata derivatives code stimuli)",
    )

    # Validation options
    validation_group = parser.add_argument_group("Validation options")
    validation_group.add_argument(
        "-w",
        "--check_for_warnings",
        action="store_true",
        dest="check_for_warnings",
        help="Check for warnings in addition to errors",
    )
    validation_group.add_argument(
        "-el",
        "--error-limit",
        dest="error_limit",
        type=int,
        default=None,
        help="Limit the number of errors of each code type to report for text output",
    )
    validation_group.add_argument(
        "-ef",
        "--errors-by-file",
        action="store_true",
        dest="errors_by_file",
        help="Apply error limit by file rather than overall for text output",
    )

    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "json_pp"],
        default="text",
        help="Output format: 'text' (human-readable with counts), 'json' (compact JSON array), or 'json_pp' (pretty-printed JSON with metadata, default: %(default)s)",
    )
    output_group.add_argument(
        "-o",
        "--output_file",
        dest="output_file",
        default="",
        help="Full path of output file for validation results; if neither this nor --print_output is specified, results are not printed",
    )
    output_group.add_argument(
        "-p",
        "--print_output",
        action="store_true",
        dest="print_output",
        help="Print validation results to stdout; if --output_file is also specified, output to both",
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
        help="Full path to save log output to file; logs still go to stderr unless --log-quiet is also used",
    )
    logging_group.add_argument(
        "-lq",
        "--log-quiet",
        action="store_true",
        dest="log_quiet",
        help="Suppress log output to stderr; only applicable when --log-file is used (logs go only to file)",
    )
    logging_group.add_argument(
        "--no-log",
        action="store_true",
        dest="no_log",
        help="Disable all logging output",
    )
    return parser


def format_final_report(issue_list):
    """Generate a final summary report of the validation results.

    Parameters:
        issue_list (list): List of validation issues found

    Returns:
        str: Summary report of the validation results
    """
    report = f"Validation completed.\n\tFound {len(issue_list)} issues."
    if issue_list:
        unique_codes = ErrorHandler.get_code_counts(issue_list)
        code_summary = ", ".join(f"{code}({count})" for code, count in unique_codes.items())
        report += f"\nCode counts: {code_summary}"
    return report


def main(arg_list=None):
    # Create the argument parser
    parser = get_parser()

    # Parse the arguments
    args = parser.parse_args(arg_list)

    # Set up logging
    setup_logging(args.log_level, args.log_file, args.log_quiet, args.verbose, args.no_log)

    logger = logging.getLogger("validate_bids")
    logger.debug("Parsed arguments: %s", args)
    effective_level_name = logging.getLevelName(logger.getEffectiveLevel())
    logger.info(
        "Starting BIDS validation with effective log level: %s (requested: %s, verbose=%s)",
        effective_level_name,
        args.log_level,
        "on" if args.verbose else "off",
    )
    if args.log_file:
        logger.info(f"Log output will be saved to: {args.log_file}")

    try:
        issue_list = validate_dataset(args)
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        raise

    final_report = format_final_report(issue_list)
    logger.info(final_report)
    print(final_report)
    # Return 1 if there are issues, 0 otherwise
    return int(bool(issue_list))


def validate_dataset(args):
    logger = logging.getLogger("validate_bids")
    logger.info(f"Data directory: {args.data_path}")
    logger.info(f"HEDTools version: {__version__}")
    logger.debug(f"Exclude directories: {args.exclude_dirs}")
    logger.debug(f"File suffixes: {args.suffixes}")
    logger.debug(f"Check for warnings: {args.check_for_warnings}")

    if args.suffixes == ["*"] or args.suffixes == []:
        args.suffixes = None

    # Validate the dataset
    try:
        logger.info("Creating BIDS dataset object...")
        bids = BidsDataset(args.data_path, suffixes=args.suffixes, exclude_dirs=args.exclude_dirs)
        logger.info(
            f"BIDS dataset created with schema versions: {bids.schema.get_schema_versions() if bids.schema else 'None'}"
        )
        logger.info(f"Found file groups: {list(bids.file_groups.keys())}")

        logger.info("Starting validation...")
        issue_list = bids.validate(check_for_warnings=args.check_for_warnings)
        logger.info(f"Validation completed. Found {len(issue_list)} issues")
    except Exception as e:
        logger.error(f"Error during dataset validation: {e}")
        logger.debug("Full exception details:", exc_info=True)
        raise

    # Generate and output the results if there is to be output
    if args.output_file or args.print_output:
        output = format_validation_results(
            issue_list,
            output_format=args.format,
            title_message="HED validation errors:",
            error_limit=args.error_limit,
            errors_by_file=args.errors_by_file,
        )
    else:
        output = ""

    # Output to file or print to screen
    if args.output_file:
        with open(args.output_file, "w") as fp:
            fp.write(output)
    if args.print_output:
        print(output)

    return issue_list


if __name__ == "__main__":
    sys.exit(main())
