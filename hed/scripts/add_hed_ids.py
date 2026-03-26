"""CLI script to add missing HED IDs to a schema in the hed-schemas repository."""

from hed.scripts.schema_script_util import get_prerelease_path
from hed.scripts.hed_convert_schema import convert_and_update
import argparse
from hed.schema.schema_io.df_util import convert_filenames_to_dict


# Slightly tweaked version of hed_convert_schema.py with a new main function to allow different parameters.
def main():
    """Entry point: parse arguments and add HED IDs to the specified schema version.

    Returns:
        int: 0 on success, non-zero on failure.

    """
    parser = argparse.ArgumentParser(description="Add hed ids to a specific schema.")
    parser.add_argument("repo_path", help="The location of the hed-schemas directory")
    parser.add_argument("schema_name", help='The name of the schema("standard" for standard schema) to modify')
    parser.add_argument("schema_version", help="The schema version to modify")

    args = parser.parse_args()

    basepath = get_prerelease_path(args.repo_path, schema_name=args.schema_name, schema_version=args.schema_version)
    filenames = list(convert_filenames_to_dict(basepath).values())
    set_ids = True

    return convert_and_update(filenames, set_ids)


if __name__ == "__main__":
    exit(main())
