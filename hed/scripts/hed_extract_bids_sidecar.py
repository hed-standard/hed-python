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
  extract_bids_sidecar /path/to/dataset --suffix events
  extract_bids_sidecar /path/to/dataset --suffix events --verbose
  extract_bids_sidecar /path/to/dataset --suffix events --log-file log.txt --log-quiet
"""

import argparse
import json
import logging
import sys
from hed import _version as vr
from hed.tools import BidsDataset


def get_parser():
    """Create the argument parser for extract_bids_sidecar."""
    parser = argparse.ArgumentParser(description="Extract sidecar template from a BIDS dataset.")
    parser.add_argument("data_path", help="Full path of BIDS dataset root directory.")
    parser.add_argument(
        "-s",
        "--suffix",
        dest="suffix",
        required=True,
        help="Suffix (without underscore) of tsv files to process (e.g., 'events', 'participants').",
    )
    parser.add_argument(
        "-vc",
        "--value-columns",
        dest="value_columns",
        nargs="*",
        default=None,
        help="List of column names to treat as value columns.",
    )
    parser.add_argument(
        "-sc",
        "--skip-columns",
        dest="skip_columns",
        nargs="*",
        default=["onset", "duration", "sample"],
        help="List of column names to skip in the extraction.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Log level (case insensitive). Default: WARNING",
    )
    parser.add_argument(
        "-lf",
        "--log-file",
        dest="log_file",
        default=None,
        help="Full path to save log output to file. If not specified, logs go to stderr.",
    )
    parser.add_argument(
        "-lq",
        "--log-quiet",
        action="store_true",
        dest="log_quiet",
        help="If present, suppress log output to stderr (only applies if --log-file is used).",
    )
    parser.add_argument(
        "-o",
        "--output_file",
        dest="output_file",
        default="",
        help="Full path of output file for the sidecar template -- otherwise output written to standard out.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="If present, output informative messages as computation progresses (equivalent to --log-level INFO).",
    )
    parser.add_argument(
        "-x",
        "--exclude-dirs",
        nargs="*",
        default=["sourcedata", "derivatives", "code", "stimuli"],
        dest="exclude_dirs",
        help="Directories name to exclude in search for files to process.",
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

    # Set the root logger level - this is crucial for filtering
    root_logger.setLevel(getattr(logging, log_level))

    # Create and configure handlers
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

    logger = logging.getLogger("extract_bids_sidecar")
    logger.info(f"Starting BIDS sidecar extraction with log level: {log_level}")
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
