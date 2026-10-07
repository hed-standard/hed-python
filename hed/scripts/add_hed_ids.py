"""CLI script to add missing HED IDs to a prerelease schema in the hed-schemas repository.

Maintainers run this once, at release time: ``hed_add_ids <hed-schemas> <standard|library> <version>``.
It reads the prerelease TSV set, assigns the lowest free id in the schema's ``library_data.json`` range
to every element without one, and rewrites all four prerelease formats. Contributors never run it.
"""

import argparse
import os

from hed.schema.schema_io.df_util import convert_filenames_to_dict
from hed.scripts.hed_convert_schema import convert_and_update
from hed.scripts.schema_script_util import get_prerelease_path


# Slightly tweaked version of hed_convert_schema.py with a new main function to allow different parameters.
def main(arg_list=None):
    """Entry point: parse arguments and add HED IDs to the specified schema version.

    Parameters:
        arg_list (list[str] or None): Argument list for testing or the hedpy wrapper; uses sys.argv if None.

    Returns:
        int: 0 on success, non-zero on failure.

    """
    parser = argparse.ArgumentParser(description="Add hed ids to a specific schema.")
    parser.add_argument("repo_path", help="The location of the hed-schemas directory")
    parser.add_argument("schema_name", help='The name of the schema("standard" for standard schema) to modify')
    parser.add_argument("schema_version", help="The schema version to modify")

    args = parser.parse_args(arg_list)

    basepath = get_prerelease_path(args.repo_path, schema_name=args.schema_name, schema_version=args.schema_version)
    if not os.path.isdir(basepath):
        print(
            f"No prerelease TSV set at {basepath}. Run hed_update_schemas on the prerelease .mediawiki "
            "first (it writes the TSV set), or pass --set-ids to it."
        )
        return 1
    filenames = list(convert_filenames_to_dict(basepath).values())
    set_ids = True

    return convert_and_update(filenames, set_ids)


if __name__ == "__main__":
    exit(main())
