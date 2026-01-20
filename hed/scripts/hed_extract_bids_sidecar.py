#!/usr/bin/env python3
"""
Command-line script for extracting sidecar templates from BIDS datasets.

Logging Options:
- Default: WARNING level logs go to stderr (quiet unless there are issues)
- --verbose or --log-level INFO: Show informational messages about progress
- --log-level DEBUG: Show detailed debugging information
- --log-file FILE: Save logs to a file instead of/in addition to stderr
- --log-quiet: When using --log-file, suppress stderr output (file only)

Examples:
    # Extract from event files (default suffix='events')
    hed_extract_bids_sidecar /path/to/dataset

    # Extract from event files with verbose progress output
    hed_extract_bids_sidecar /path/to/dataset --verbose

    # Extract from participant files instead of events
    hed_extract_bids_sidecar /path/to/dataset --suffix participants

    # Save output to a file instead of stdout
    hed_extract_bids_sidecar /path/to/dataset --output_file template.json

    # Exclude specific columns from the template
    hed_extract_bids_sidecar /path/to/dataset --skip-columns onset duration response_time

    # Save logs to file and suppress console output
    hed_extract_bids_sidecar /path/to/dataset --log-file extraction.log --log-quiet
"""

import argparse
import json
import logging
from hed import _version as vr
from hed.tools import BidsDataset
from hed.scripts.script_utils import setup_logging


def get_parser():
    """Create the argument parser for extract_bids_sidecar."""
    parser = argparse.ArgumentParser(
        description="Extract sidecar template from a BIDS dataset.",
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
    parser.add_argument("data_path", help="Full path of BIDS dataset root directory")

    # File selection options
    file_group = parser.add_argument_group("File selection options")
    file_group.add_argument(
        "-s",
        "--suffix",
        dest="suffix",
        default="events",
        help="Suffix (without underscore) of filenames for TSV files to process (e.g., 'events', 'participants', default: %(default)s)",
    )
    file_group.add_argument(
        "-x",
        "--exclude-dirs",
        nargs="*",
        default=["sourcedata", "derivatives", "code", "stimuli"],
        dest="exclude_dirs",
        help="Directory names (relative to data_path) to exclude in search for files to process (default: sourcedata derivatives code stimuli)",
    )

    # Column processing options
    column_group = parser.add_argument_group("Column processing options")
    column_group.add_argument(
        "-vc",
        "--value-columns",
        dest="value_columns",
        nargs="*",
        default=None,
        help="List of column names to treat as value columns",
    )
    column_group.add_argument(
        "-sc",
        "--skip-columns",
        dest="skip_columns",
        nargs="*",
        default=["onset", "duration", "sample"],
        help="List of column names to skip in the extraction (default: onset duration sample)",
    )

    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "-o",
        "--output_file",
        dest="output_file",
        default="",
        help="Optional full path of output file for the sidecar template; otherwise output written to standard out",
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


def extract_template(args):
    """Extract sidecar template from the BIDS dataset.

    Parameters:
        args: Parsed command line arguments

    Returns:
        dict: Sidecar template dictionary
    """
    logger = logging.getLogger("extract_bids_sidecar")
    logger.info(f"Data directory: {args.data_path}")
    logger.info(f"HED tools version: {str(vr.get_versions())}")
    logger.debug(f"Exclude directories: {args.exclude_dirs}")
    logger.debug(f"File suffix: {args.suffix}")
    logger.debug(f"Value columns: {args.value_columns}")
    logger.debug(f"Skip columns: {args.skip_columns}")

    try:
        logger.info("Creating BIDS dataset object...")
        bids = BidsDataset(args.data_path, suffixes=[args.suffix], exclude_dirs=args.exclude_dirs)
        logger.info("BIDS dataset created")
        logger.info(f"Found file groups: {list(bids.file_groups.keys())}")

        # Get the file group for the specified suffix
        file_group = bids.get_file_group(args.suffix)
        if not file_group:
            logger.warning(f"No file group found for suffix '{args.suffix}'")
            return {}

        logger.debug(f"File group '{args.suffix}' has {len(file_group.datafile_dict)} data files")

        # Combine default skip columns with user-specified ones
        # Default skips: onset, duration, sample (timing/indexing columns)
        default_skip = ["onset", "duration", "sample"]
        skip_cols = default_skip.copy()
        if args.skip_columns:
            skip_cols.extend(args.skip_columns)

        logger.debug(f"Skip columns: {skip_cols}")

        # Create TabularSummary using the summarize method of BidsFileGroup
        logger.info("Creating tabular summary...")
        summary = file_group.summarize(value_cols=args.value_columns, skip_cols=skip_cols)

        logger.info(f"Processed {summary.total_files} files")
        logger.info(f"Total events: {summary.total_events}")

        # Extract the sidecar template
        logger.info("Extracting sidecar template...")
        template = summary.extract_sidecar_template()
        logger.info(f"Template extracted with {len(template)} columns")

        return template

    except Exception as e:
        logger.error(f"Error during template extraction: {e}")
        logger.debug("Full exception details:", exc_info=True)
        raise


def format_output(template, args):
    """Format the template as JSON output.

    Parameters:
        template (dict): The sidecar template dictionary
        args: Parsed command line arguments

    Returns:
        str: JSON-formatted output
    """
    output_dict = {"sidecar_template": template, "hedtools_version": str(vr.get_versions())}
    return json.dumps(output_dict, indent=4)


def main(arg_list=None):
    """Main entry point for the script."""
    # Create the argument parser
    parser = get_parser()

    # Parse the arguments
    args = parser.parse_args(arg_list)

    # Setup logging configuration
    setup_logging(args.log_level, args.log_file, args.log_quiet, args.verbose, False)

    logger = logging.getLogger("extract_bids_sidecar")
    logger.info(f"Starting BIDS sidecar extraction with log level: {args.log_level}")
    if args.log_file:
        logger.info(f"Log output will be saved to: {args.log_file}")

    try:
        template = extract_template(args)
    except Exception as e:
        logger.error(f"Extraction failed with exception: {e}")
        raise

    # Format output as JSON
    output = format_output(template, args)

    # Write to file or print to stdout
    if args.output_file:
        logger.info(f"Writing output to: {args.output_file}")
        with open(args.output_file, "w", encoding="utf-8") as fp:
            fp.write(output)
    else:
        print(output)

    logger.info("Extraction completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
