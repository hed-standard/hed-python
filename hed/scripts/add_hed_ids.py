from hed.schema import load_schema_version
from hed.scripts.script_util import get_prerelease_path
from hed.scripts.convert_and_update_schema import convert_and_update
import argparse
from hed.schema.schema_io.df2schema import SchemaLoaderDF

# Slightly tweaked version of convert_and_update_schema.py with a new main function to allow different parameters.
def main():
    parser = argparse.ArgumentParser(description='Add hed ids to a specific schema.')
    parser.add_argument('repo_path', help='The location of the hed-schemas directory')
    parser.add_argument('schema_name', help='The name of the schema("standard" for standard schema) to modify')
    parser.add_argument('schema_version', help='The schema version to modify')

    args = parser.parse_args()

    basepath = get_prerelease_path(args.repo_path, schema_name=args.schema_name, schema_version=args.schema_version)
    filenames = list(SchemaLoaderDF.convert_filenames_to_dict(basepath).values())
    set_ids = True

    # Trigger a local cache hit (this ensures trying to load withStandard schemas will work properly)
    _ = load_schema_version("8.2.0")

    return convert_and_update(filenames, set_ids)


if __name__ == "__main__":
    exit(main())