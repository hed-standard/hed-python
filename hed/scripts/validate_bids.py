import argparse
import json
import sys

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
    parser.add_argument("-o", "--output_file", dest="output_file", default='',
                        help="Full path of output of validator -- otherwise output written to standard error.")

    parser.add_argument("-p", "--print_output", action='store_true', dest="print_output",
                        help="If present, output the results to standard out in addition to any saving of the files.")
    parser.add_argument("-s", "--suffixes", dest="suffixes", nargs="*", default=['events', 'participants'],
                        help = "Optional list of suffixes (no under_bar) of tsv files to validate." +
                               " If -s with no values, will use all possible suffixes as with single argument '*'.")

    parser.add_argument("-v", "--verbose", action='store_true',
                        help="If present, output informative messages as computation progresses.")
    parser.add_argument("-w", "--check_for_warnings", action='store_true', dest="check_for_warnings",
                        help="If present, check for warnings as well as errors.")
    parser.add_argument("-x", "--exclude-dirs", nargs="*", default=['sourcedata', 'derivatives', 'code', 'stimuli'],
                        dest="exclude_dirs",
                        help="Directories name to exclude in search for files to validate.")
    return parser


def main(arg_list=None):
    # Create the argument parser
    parser = get_parser()

    # Parse the arguments
    args = parser.parse_args(arg_list)
    issue_list = validate_dataset(args)

    # Return 1 if there are issues, 0 otherwise
    return int(bool(issue_list))


def validate_dataset(args):
    # Delayed imports to speed up --help
    from hed.errors import get_printable_issue_string, ErrorHandler
    from hed.tools import BidsDataset
    from hed import _version as vr

    if args.verbose:
        print(f"Data directory: {args.data_path}")

    if args.suffixes == ['*'] or args.suffixes == []:
        args.suffixes = None

    # Validate the dataset
    bids = BidsDataset(args.data_path, suffixes=args.suffixes, exclude_dirs=args.exclude_dirs)
    issue_list = bids.validate(check_for_warnings=args.check_for_warnings)

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

    # Output to file or print to screen
    if args.output_file:
        with open(args.output_file, 'w') as fp:
            fp.write(output)
    if args.print_output:
        print(output)
    return issue_list


if __name__ == "__main__":
    sys.exit(main())
