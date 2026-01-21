#!/usr/bin/env python
"""
Validates a HED string against a specified schema version.

This script validates a HED annotation string, optionally with definitions,
against a specified HED schema version.
"""

import argparse
import sys
from hed import HedString
from hed.errors import ErrorHandler
from hed.models import DefinitionDict
from hed.schema import load_schema_version
from hed.validator import HedValidator
from hed.scripts.script_utils import setup_logging, format_validation_results


def get_parser():
    """Create the argument parser for validate_hed_string.

    Returns:
        argparse.ArgumentParser: Configured argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Validate a HED annotation string against a schema", formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument("hed_string", help="HED annotation string to validate")
    parser.add_argument(
        "-sv",
        "--schema-version",
        required=True,
        nargs="+",
        dest="schema_version",
        help="HED schema version(s) to validate against (e.g., '8.4.0' or '8.3.0 score_1.1.0' for multiple schemas)",
    )

    # Optional arguments
    parser.add_argument("-d", "--definitions", default="", help="HED definition(s) string to use during validation")
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
    """Main function for validating a HED string.

    Parameters:
        arg_list (list or None): Command line arguments.
    """
    parser = get_parser()
    args = parser.parse_args(arg_list)

    # Set up logging
    setup_logging(args.log_level, args.log_file, args.log_quiet, args.verbose, args.no_log)

    import logging

    logger = logging.getLogger("validate_hed_string")
    effective_level_name = logging.getLevelName(logger.getEffectiveLevel())
    logger.info(
        "Starting HED string validation with effective log level: %s (requested: %s, verbose=%s)",
        effective_level_name,
        args.log_level,
        "on" if args.verbose else "off",
    )

    try:
        # Load schema (handle single version or list of versions)
        schema_versions = args.schema_version[0] if len(args.schema_version) == 1 else args.schema_version
        logging.info(f"Loading HED schema version(s) {schema_versions}")
        schema = load_schema_version(schema_versions)

        # Parse HED string
        logging.info("Parsing HED string")
        hed_string = HedString(args.hed_string, schema)

        # Set up definitions if provided
        def_dict = None
        issues = []
        if args.definitions:
            logging.info("Processing definitions")
            def_dict = DefinitionDict(args.definitions, hed_schema=schema)
            if def_dict.issues:
                issues = def_dict.issues
                logging.warning("Errors found in definitions, skipping HED string validation")

        # Validate HED string only if no definition errors
        if not issues:
            logging.info("Validating HED string")
            error_handler = ErrorHandler(check_for_warnings=args.check_for_warnings)
            validator = HedValidator(schema, def_dict)
            issues = validator.validate(hed_string, True, error_handler=error_handler)

        # Handle output
        if issues:
            # Format validation errors
            output = format_validation_results(
                issues, output_format=args.format, title_message="HED string validation errors:"
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
            success_msg = "HED string is valid!"
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
