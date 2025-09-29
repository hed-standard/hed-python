#!/usr/bin/env python3
"""
Command-line script for validating BIDS datasets with HED annotations.

Logging Options:
- Default: WARNING level logs go to stderr (quiet unless there are issues)
- --verbose or --log-level INFO: Show informational messages about progress
- --log-level DEBUG: Show detailed debugging information
- --log-file FILE: Save logs to a file instead of/in addition to stderr
- --log-quiet: When using --log-file, suppress stderr output (file only)

Examples:
  validate_bids /path/to/dataset                    # Quiet validation
  validate_bids /path/to/dataset --verbose         # Show progress
  validate_bids /path/to/dataset --log-level DEBUG # Detailed debugging
  validate_bids /path/to/dataset --log-file log.txt --log-quiet  # Log to file only
"""

import argparse
import json
import logging
import sys
from hed import _version as vr
from hed.errors import get_printable_issue_string, ErrorHandler
from hed.tools import BidsDataset

def get_parser():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Validate a BIDS-formatted HED dataset.")
    parser.add_argument("data_path", help="Full path of dataset root directory.")
    parser.add_argument("-ec", "--error_count", dest="error_limit", type=int, default=None,
                        help="Limit the number of errors of each code type to report for text output.")
    parser.add_argument("-ef", "--errors_by_file", dest="errors_by_file", type=bool, default=False,
                        help="Apply error limit by file rather than overall for text output.")
    parser.add_argument("-f", "--format", choices=["text", "json", "json_pp"], default="text",
                        help="Output format: 'text' (default) or 'json' ('json_pp' for pretty-printed json)")
    parser.add_argument("-l", "--log-level", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        default="WARNING", help="Log level (case insensitive). Default: INFO")
    parser.add_argument("-lf", "--log-file", dest="log_file", default=None,
                        help="Full path to save log output to file. If not specified, logs go to stderr.")
    parser.add_argument("-lq", "--log-quiet", action='store_true', dest="log_quiet",
                        help="If present, suppress log output to stderr (only applies if --log-file is used).")
    parser.add_argument("-o", "--output_file", dest="output_file", default='',
                        help="Full path of output of validator -- otherwise output written to standard error.")
    parser.add_argument("-p", "--print_output", action='store_true', dest="print_output",
                        help="If present, output the results to standard out in addition to any saving of the files.")
    parser.add_argument("-s", "--suffixes", dest="suffixes", nargs="*", default=['events', 'participants'],
                        help = "Optional list of suffixes (no under_bar) of tsv files to validate." +
                               " If -s with no values, will use all possible suffixes as with single argument '*'.")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses (equivalent to --log-level INFO).")
    parser.add_argument("-w", "--check_for_warnings", action='store_true', dest="check_for_warnings",
                        help="If present, check for warnings as well as errors.")
    parser.add_argument("-x", "--exclude-dirs", nargs="*", default=['sourcedata', 'derivatives', 'code', 'stimuli'],
                        dest="exclude_dirs",
                        help="Directories name to exclude in search for files to validate.")
    return parser


def format_validation_results(issue_list, args, ErrorHandler):
    """Generate and output validation results based on format and options.
    
    Parameters:
        issue_list (list): List of validation issues found
        args: Parsed command line arguments containing format and output options
        ErrorHandler: Error handling class for filtering issues
        
    Returns:
        str: Formatted validation results as a string in the requested format (text, json, or json_pp)
    """
    # Output based on format
    output = ""   
    if args.format == "json_pp":
        output = json.dumps({"issues": issue_list, "hedtools_version": str(vr.get_versions())}, indent=4)
    elif args.format == "json":
        output = json.dumps(issue_list)
    elif args.format == "text":
        output = f"Using HEDTOOLS version: {str(vr.get_versions())}\n"
        output += f"Number of issues: {len(issue_list)}\n"
        if args.error_limit:
            [issue_list, code_counts] = ErrorHandler.filter_issues_by_count(issue_list, args.error_limit,
                                                                            by_file=args.errors_by_file)
            output += "  ".join(f"{code}:{count}" for code, count in code_counts.items()) + "\n"
            output += f"Number of issues after filtering: {len(issue_list)}\n"
        if issue_list:
            output += get_printable_issue_string(issue_list, "HED validation errors: ", skip_filename=False)
    
    return output

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
    print(f"{str(args)}")
    # Setup logging configuration
    log_level = args.log_level.upper() if args.log_level else 'INFO'
    if args.verbose:
        log_level = 'INFO'
    
    # Configure logging format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
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
        file_handler = logging.FileHandler(args.log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Console handler (stderr) unless explicitly quieted and file logging is used
    if not args.log_quiet or not args.log_file:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    logger = logging.getLogger('validate_bids')
    logger.info(f"Starting BIDS validation with log level: {log_level}")
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
    logger = logging.getLogger('validate_bids')
    logger.info(f"Data directory: {args.data_path}")
    logger.info(f"HED tools version: {str(vr.get_versions())}")
    logger.debug(f"Exclude directories: {args.exclude_dirs}")
    logger.debug(f"File suffixes: {args.suffixes}")
    logger.debug(f"Check for warnings: {args.check_for_warnings}")

    if args.suffixes == ['*'] or args.suffixes == []:
        args.suffixes = None
       
    # Validate the dataset
    try:
        logger.info("Creating BIDS dataset object...")
        bids = BidsDataset(args.data_path, suffixes=args.suffixes, exclude_dirs=args.exclude_dirs)
        logger.info(f"BIDS dataset created with schema versions: {bids.schema.get_schema_versions() if bids.schema else 'None'}")
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
        output = format_validation_results(issue_list, args, ErrorHandler)
    else:
        output = ""
    
    # Output to file or print to screen
    if args.output_file:
        with open(args.output_file, 'w') as fp:
            fp.write(output)
    if args.print_output:
        print(output)

     
    return issue_list




if __name__ == "__main__":
    sys.exit(main())
