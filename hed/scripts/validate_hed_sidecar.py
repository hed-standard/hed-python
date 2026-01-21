#!/usr/bin/env python
"""
Validates a BIDS sidecar against a specified schema version.

This script validates HED in a BIDS JSON sidecar file
against a specified HED schema version.
"""

import argparse
import sys
import os
from hed.models import Sidecar
from hed.errors import ErrorHandler
from hed.schema import load_schema_version
from hed.scripts.script_utils import setup_logging, format_validation_results


def get_parser():
    """Create the argument parser for validate_hed_sidecar.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validate a BIDS sidecar file against a HED schema", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument("sidecar_file", help="BIDS sidecar file to validate")
    parser.add_argument(
        "-sv",
        "--schema-version",
        required=True,
        nargs="+",
        dest="schema_version",
        help="HED schema version(s) to validate against (e.g., '8.4.0' or '8.3.0 score_1.1.0' for multiple schemas)",
    )

    # Optional arguments
    parser.add_argument(
        "-w",
        "--check-for-warnings",
        action="store_true",
        dest="check_for_warnings",
        help="Check for warnings in addition to errors",
    )

    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument(
        "-f",
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for validation results (default: %(default)s)",
    )
    output_group.add_argument(
        "-o",
        "--output-file",
        default="",
        dest="output_file",
        help="Output file for validation results; if not specified, output to stdout",
    )

    # Logging options
    logging_group = parser.add_argument_group("Logging options")
    logging_group.add_argument(
        "-l",
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        dest="log_level",
        help="Logging level (default: %(default)s)",
    )
    logging_group.add_argument("-lf", "--log-file", default="", dest="log_file", help="File path for saving log output")
    logging_group.add_argument(
        "-lq", "--log-quiet", action="store_true", dest="log_quiet", help="Suppress log output to stderr when using --log-file"
    )
    logging_group.add_argument("--no-log", action="store_true", dest="no_log", help="Disable all logging output")
    logging_group.add_argument("-v", "--verbose", action="store_true", help="Output informational messages")

    return parser


def main(arg_list=None):
    """Main function for validating a BIDS sidecar.

    Parameters:
        arg_list (list or None): Command line arguments.
    """
    parser = get_parser()
    args = parser.parse_args(arg_list)

    # Set up logging
    setup_logging(args.log_level, args.log_file, args.log_quiet, args.verbose, args.no_log)

    import logging

    logger = logging.getLogger("validate_hed_sidecar")
    effective_level_name = logging.getLevelName(logger.getEffectiveLevel())
    logger.info(
        "Starting BIDS sidecar HED validation with effective log level: %s (requested: %s, verbose=%s)",
        effective_level_name,
        args.log_level,
        "on" if args.verbose else "off",
    )

    try:
        # Load schema (handle single version or list of versions)
        schema_versions = args.schema_version[0] if len(args.schema_version) == 1 else args.schema_version
        logging.info(f"Loading HED schema version(s) {schema_versions}")
        schema = load_schema_version(schema_versions)

        # Parse Sidecar
        logging.info("Loading BIDS sidecar file")
        sidecar = Sidecar(args.sidecar_file, name=os.path.basename(args.sidecar_file))

        # Validate BIDS sidecar
        logging.info("Validating BIDS sidecar")
        error_handler = ErrorHandler(check_for_warnings=args.check_for_warnings)
        issues = sidecar.validate(schema, name=sidecar.name, error_handler=error_handler)

        # Handle output
        if issues:
            # Format validation errors
            output = format_validation_results(
                issues, output_format=args.format, title_message="BIDS sidecar validation errors:"
            )

            # Write output
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write(output)
                logging.info(f"Validation errors written to {args.output_file}")
            else:
                print(output)

            return 1  # Exit with error code if validation failed
        else:
            # Success message
            success_msg = "BIDS sidecar has valid HED!"
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write(success_msg + "\n")
                logging.info(f"Validation results written to {args.output_file}")
            else:
                print(success_msg)

            return 0

    except Exception as e:
        logging.error(f"Validation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
