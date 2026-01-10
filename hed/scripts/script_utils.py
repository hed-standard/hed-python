"""
Utility functions for HED command-line scripts.

This module provides common functionality used across multiple HED scripts,
including logging configuration and argument handling.
"""

import json
import logging
import sys
from hed import _version as vr
from hed.errors import get_printable_issue_string, ErrorHandler, iter_errors


def setup_logging(log_level, log_file=None, log_quiet=False, verbose=False, no_log=False):
    """Configure logging for HED scripts.

    Sets up the root logger with appropriate handlers for console (stderr) and/or
    file output based on the provided arguments.

    Parameters:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str or None): Path to log file, or None for no file logging
        log_quiet (bool): If True and log_file is specified, suppress stderr output
        verbose (bool): If True, override log_level to INFO
        no_log (bool): If True, disable all logging output

    Returns:
        logging.Logger: Configured logger instance
    """
    # Disable logging completely if requested
    if no_log:
        logging.basicConfig(level=logging.CRITICAL + 1, handlers=[logging.NullHandler()], force=True)
        return logging.getLogger()

    # Determine effective log level
    level = logging.INFO if verbose else getattr(logging, log_level.upper())

    # Configure handlers
    handlers = []
    if log_file:
        handlers.append(logging.FileHandler(log_file, mode="w", encoding="utf-8"))
    if not (log_file and log_quiet):
        handlers.append(logging.StreamHandler(sys.stderr))

    # Configure root logger
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", handlers=handlers, force=True)

    return logging.getLogger()


def format_validation_results(
    issue_list, output_format="text", title_message="Validation errors:", error_limit=None, errors_by_file=False
):
    """Format validation results in the requested output format.

    This function provides a consistent way to format validation issues across
    different HED validation scripts. It supports text, JSON, and pretty-printed
    JSON formats, with optional error limiting for large result sets.

    Parameters:
        issue_list (list): List of validation issues (HedIssue objects)
        output_format (str): Output format - 'text', 'json', or 'json_pp' (default: 'text')
        title_message (str): Title/header for text output (default: 'Validation errors:')
        error_limit (int or None): Maximum errors per code type to include in text output (default: None)
        errors_by_file (bool): Apply error limit per file rather than globally (default: False)

    Returns:
        str: Formatted validation results as a string

    Examples:
        >>> issues = validator.validate(hed_string)
        >>> output = format_validation_results(issues, "text", "HED string validation:")
        >>> output = format_validation_results(issues, "json")
        >>> output = format_validation_results(issues, "json_pp")
    """
    if output_format == "json_pp":
        # Pretty-printed JSON with version metadata
        # Convert issues to JSON-serializable format
        serializable_issues = list(iter_errors(issue_list))
        return json.dumps({"issues": serializable_issues, "hedtools_version": str(vr.get_versions())}, indent=4)

    elif output_format == "json":
        # Compact JSON array of issues
        # Convert issues to JSON-serializable format
        serializable_issues = list(iter_errors(issue_list))
        return json.dumps(serializable_issues)

    elif output_format == "text":
        # Human-readable text format with counts and optional filtering
        output = f"Using HEDTools version: {str(vr.get_versions())}\n"
        output += f"Number of issues: {len(issue_list)}\n"

        # Apply error limiting if requested
        if error_limit:
            filtered_issues, code_counts = ErrorHandler.filter_issues_by_count(issue_list, error_limit, by_file=errors_by_file)
            output += "Error counts by code: "
            output += "  ".join(f"{code}:{count}" for code, count in code_counts.items()) + "\n"
            output += f"Number of issues after filtering: {len(filtered_issues)}\n"
            issue_list = filtered_issues

        # Format the issues with title
        if issue_list:
            output += get_printable_issue_string(issue_list, title_message, skip_filename=False)

        return output

    else:
        raise ValueError(f"Unknown output format: {output_format}")
