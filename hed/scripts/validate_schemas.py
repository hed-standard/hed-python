import sys
from hed.scripts.script_util import validate_all_schemas, sort_base_schemas
import argparse


def main():
    parser = argparse.ArgumentParser(description='Validate schema files.')
    parser.add_argument('schema_files', nargs='+', help='List of schema files to validate.')
    parser.add_argument('--add-all-extensions', action='store_true',
                        help='Always verify all versions of the same schema are equal.')

    args = parser.parse_args()

    schema_files = sort_base_schemas(args.schema_files, args.add_all_extensions)
    issues = validate_all_schemas(schema_files)

    if issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
