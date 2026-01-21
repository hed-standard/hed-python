#!/usr/bin/env python
"""
Validates HED in a tabular file (TSV) against a specified schema version.

This script validates HED in a tabular file, optionally with a JSON sidecar,
against a specified HED schema version.
"""

import argparse
import sys
import os
from hed.models import TabularInput, Sidecar
from hed.errors import ErrorHandler
from hed.schema import load_schema_version
from hed.scripts.script_utils import setup_logging, format_validation_results


def get_parser():
    """Create the argument parser for validate_hed_tabular.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validate HED in a tabular file against a HED schema", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument("tabular_file", help="Tabular file (TSV) to validate")
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
        "-s",
        "--sidecar",
        dest="sidecar_file",
        help="Optional BIDS JSON sidecar file to use during validation",
    )
    parser.add_argument(
        "-w",
        "--check-for-warnings",
        action="store_true",
        dest="check_for_warnings",
        help="Check for warnings in addition to errors",
    )

    # Error limiting
    error_group = parser.add_argument_group("Error limiting options")
    error_group.add_argument(
        "-el",
        "--error-limit",
        type=int,
        dest="error_limit",
        default=None,
        help="Limit number of errors reported per code (default: No limit)",
    )
    error_group.add_argument(
        "-ef",
        "--errors-by-file",
        action="store_true",
        dest="errors_by_file",
        help="If using --error-limit, apply the limit per-file rather than globally",
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
    """Main function for validating HED in a tabular file.

    Parameters:
        arg_list (list or None): Command line arguments.
    """
    parser = get_parser()
    args = parser.parse_args(arg_list)

    # Set up logging
    setup_logging(args.log_level, args.log_file, args.log_quiet, args.verbose, args.no_log)

    import logging

    logger = logging.getLogger("validate_hed_tabular")
    effective_level_name = logging.getLevelName(logger.getEffectiveLevel())
    logger.info(
        "Starting HED validation of tabular file with effective log level: %s (requested: %s, verbose=%s)",
        effective_level_name,
        args.log_level,
        "on" if args.verbose else "off",
    )

    try:
        # Load schema (handle single version or list of versions)
        schema_versions = args.schema_version[0] if len(args.schema_version) == 1 else args.schema_version
        logging.info(f"Loading HED schema version(s) {schema_versions}")
        schema = load_schema_version(schema_versions)

        # Parse Sidecar if provided
        sidecar = None
        issues = []
        error_handler = ErrorHandler(check_for_warnings=args.check_for_warnings)

        if args.sidecar_file:
            logging.info("Loading Sidecar file")
            sidecar = Sidecar(args.sidecar_file, name=os.path.basename(args.sidecar_file))
            sidecar_issues = sidecar.validate(schema, name=sidecar.name, error_handler=error_handler)
            issues += sidecar_issues
            if sidecar_issues:
                logging.warning(f"Found {len(sidecar_issues)} issues in sidecar validation")

        # Parse and Validate Tabular Input
        logging.info("Loading Tabular file")
        tabular_input = TabularInput(args.tabular_file, sidecar=sidecar, name=os.path.basename(args.tabular_file))

        logging.info("Validating Tabular file")
        # Validate tabular input
        tabular_issues = tabular_input.validate(schema, name=tabular_input.name, error_handler=error_handler)
        issues += tabular_issues

        # Handle output
        if issues:
            # Format validation errors
            output = format_validation_results(
                issues,
                output_format=args.format,
                title_message="HED validation issues:",
                error_limit=args.error_limit,
                errors_by_file=args.errors_by_file,
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
            success_msg = "Tabular file has valid HED!"
            if args.output_file:
                with open(args.output_file, "w") as f:
                    f.write(success_msg + "\n")
                logging.info(f"Validation results written to {args.output_file}")
            else:
                print(success_msg)

            return 0

    except Exception as e:
        logging.error(f"Validation failed: {str(e)}")
        # If verbose, print stack trace
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
