"""CLI script to validate HED schema files for compliance and format consistency."""

import argparse
import sys

from hed.errors import HedFileError, get_printable_issue_string
from hed.schema import load_schema
from hed.scripts.schema_script_util import missing_hed_ids, sort_base_schemas, validate_all_schemas


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
    parser.add_argument(
        "--require-ids",
        action="store_true",
        help="Fail if any schema element has no hedId (a release candidate must have one on every element).",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output.")
    return parser


def check_required_ids(schema_files):
    """Report every element without a hedId in the given schema files.

    Parameters:
        schema_files (dict): The ``sort_base_schemas`` result: basename -> {extension: path}.

    Returns:
        list[str]: One line per missing id, prefixed by the file it was found in. Empty when none.
    """
    report = []
    for extension_paths in schema_files.values():
        file_path = next(iter(extension_paths.values()))
        try:
            schema = load_schema(file_path)
        except HedFileError as e:
            report.append(f"{file_path}: cannot load ({e.message})")
            continue
        report += [f"{file_path}: {line}" for line in missing_hed_ids(schema)]
    return report


def main(arg_list=None):
    """Entry point: parse arguments and validate the specified schema files.

    Parameters:
        arg_list (list[str] or None): Argument list for testing; uses sys.argv if None.

    Returns:
        int: 0 if all schemas are valid, 1 if any issues are found.

    """
    parser = get_parser()
    args = parser.parse_args(arg_list)

    schema_files = sort_base_schemas(args.schema_files, args.add_all_extensions)
    issues = validate_all_schemas(schema_files)

    if issues:
        if args.verbose:
            print(get_printable_issue_string(issues, title="Schema Validation Issues:"))
        return 1

    if args.require_ids:
        missing = check_required_ids(schema_files)
        if missing:
            print(f"{len(missing)} schema element(s) have no hedId:")
            for line in missing:
                print(f"  {line}")
            return 1

    if args.verbose:
        print("All schemas validated successfully.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
