import sys
from hed.scripts.hed_script_util import validate_all_schemas, sort_base_schemas
from hed.errors import get_printable_issue_string
import argparse


def get_parser():
    """Create the argument parser for validate_schemas.

    Returns:
        argparse.ArgumentParser: The argument parser.
    """
    parser = argparse.ArgumentParser(description="Validate schema files.")
    parser.add_argument("schema_files", nargs="+", help="List of schema files to validate.")
    parser.add_argument(
        "--add-all-extensions", action="store_true", help="Always verify all versions of the same schema are equal."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()

    schema_files = sort_base_schemas(args.schema_files, args.add_all_extensions)
    issues = validate_all_schemas(schema_files)

    if issues:
        if args.verbose:
            print(get_printable_issue_string(issues, title="Schema Validation Issues:"))
        return 1

    if args.verbose:
        print("All schemas validated successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
