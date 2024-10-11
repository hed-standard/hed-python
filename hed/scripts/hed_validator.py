import argparse
import json
import sys


def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Validate an HED BIDS dataset.")

    # Positional argument for the dataset path
    parser.add_argument("dataset_path", help="Path to the dataset directory")

    # Optional argument for the format
    parser.add_argument("-f", "--format", choices=["text", "json", "json_pp"], default="text",
                        help="Output format: 'text' (default) or 'json' ('json_pp' for pretty-printed json)")

    # Optional argument for the output file
    parser.add_argument("-o", "--output-file", help="File to save the output. If not provided, output is printed to the screen")

    # Optional flag to check for warnings
    parser.add_argument("--check-for-warnings", action="store_true",
                        help="Enable checking for warnings during validation")

    # Parse the arguments
    args = parser.parse_args()

    issue_list = validate_dataset(args)

    # Return 1 if there are issues, 0 otherwise
    return int(bool(issue_list))


def validate_dataset(args):
    # Delayed imports to speed up --help
    from hed.errors import get_printable_issue_string
    from hed.tools import BidsDataset
    from hed import _version as vr

    # Validate the dataset
    bids = BidsDataset(args.dataset_path)
    issue_list = bids.validate(check_for_warnings=args.check_for_warnings)
    # Output based on format
    if args.format in ("json", "json_pp"):
        kw = {"indent": 4} if args.format == "json_pp" else {}
        output = json.dumps(
            {
                "issues": issue_list,
                "hedtools_version": str(vr.get_versions())
            },
            **kw)
    elif args.format == "json":
        output = json.dumps(issue_list)
    elif args.format == "text":
        # Print HEDTOOLS version
        print(f"Using HEDTOOLS version: {str(vr.get_versions())}")

        if issue_list:
            output = get_printable_issue_string(issue_list, "HED validation errors: ", skip_filename=False)
            # Print number of issues
            print(f"Number of issues: {len(issue_list)}")
        else:
            output = "No HED validation errors"
    else:
        raise ValueError(args.format)
    # Output to file or print to screen
    if args.output_file:
        with open(args.output_file, 'w') as fp:
            fp.write(output)
    else:
        print(output)
    return issue_list


if __name__ == "__main__":
    sys.exit(main())

