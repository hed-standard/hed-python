from hed.scripts.hed_script_util import sort_base_schemas, validate_all_schemas, add_extension
from hed.schema.schema_io import load_dataframes, save_dataframes
from hed.schema.schema_io.hed_id_util import update_dataframes_from_schema
from hed.schema.hed_schema_io import load_schema, from_dataframes
from hed.errors import get_printable_issue_string, HedFileError
import argparse


def convert_and_update(filenames, set_ids):
    """Validate, convert, and update as needed all schemas listed in filenames

        If any schema fails to validate, no schemas will be updated.

    Parameters:
        filenames(list of str): A list of filenames that have been updated
        set_ids(bool): If True, assign missing hedIds
    """
    # Find and group the changed files
    schema_files = sort_base_schemas(filenames)
    all_issues = validate_all_schemas(schema_files)

    if not schema_files:
        print("No schema file changes found in the file list")
        return 0

    if all_issues:
        print("Did not attempt to update schemas due to validation failures")
        return 1

    updated = []
    # If we are here, we have validated the schemas(and if there's more than one version changed, that they're the same)
    for basename, extension_paths in schema_files.items():
        # Skip any with multiple extensions or not in pre-release
        if "prerelease" not in basename:
            print(f"Skipping updates on {basename}, not in a prerelease folder.")
            continue
        # Use the actual file paths to preserve case on case-sensitive filesystems
        source_filename = list(extension_paths.values())[0]  # Load any changed schema version, they're all the same

        # Find TSV file path if it exists
        tsv_path = extension_paths.get(".tsv")
        if tsv_path:
            source_df_filename = tsv_path
        else:
            # Construct TSV path if not found (unlikely in normal workflow)
            source_df_filename = add_extension(basename, ".tsv")
        schema = load_schema(source_filename)
        print(f"Trying to convert/update file {source_filename}")
        source_dataframes = load_dataframes(source_df_filename)
        # todo: We need a more robust system for if some files are missing
        #  (especially for library schemas which will probably lack some)
        if any(value is None for value in source_dataframes.values()):
            source_dataframes = schema.get_as_dataframes()

        try:
            result = update_dataframes_from_schema(source_dataframes, schema, schema.library, assign_missing_ids=set_ids)
        except HedFileError as e:
            print(get_printable_issue_string(e.issues, title="Issues updating schema:"))
            raise e
        schema_reloaded = from_dataframes(result)
        schema_reloaded.save_as_mediawiki(basename + ".mediawiki")
        schema_reloaded.save_as_xml(basename + ".xml")
        schema_reloaded.save_as_json(basename + ".json")

        save_dataframes(source_df_filename, result)
        updated.append(basename)

    for basename in updated:
        print(f"Schema {basename} updated.")

    if not updated:
        print("Did not update any schemas")
    return 0


def main(arg_list=None):
    parser = argparse.ArgumentParser(description="Update other schema formats based on the changed one.")
    parser.add_argument("filenames", nargs="*", help="List of files to process")
    parser.add_argument("--set-ids", action="store_true", help="Add missing HED ids")

    args = parser.parse_args(arg_list)

    filenames = args.filenames
    set_ids = args.set_ids

    return convert_and_update(filenames, set_ids)


if __name__ == "__main__":
    exit(main())
