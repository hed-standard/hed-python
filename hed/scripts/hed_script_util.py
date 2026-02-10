import os.path
from collections import defaultdict
from hed.schema import from_string, load_schema, from_dataframes
from hed.errors import get_printable_issue_string, HedFileError, SchemaWarnings
from hed.schema.schema_comparer import SchemaComparer

all_extensions = [".tsv", ".mediawiki", ".xml", ".json"]


def validate_schema_object(base_schema, schema_name):
    """Validate a schema object by checking compliance and roundtrip conversion.

    Tests the schema for compliance issues and validates that it can be successfully
    converted to and reloaded from all four formats (MEDIAWIKI, XML, JSON, TSV).

    Parameters:
        base_schema (HedSchema): The schema object to validate.
        schema_name (str): The name/path of the schema for error reporting.

    Returns:
        list: A list of validation issue strings. Empty if no issues found.
    """
    validation_issues = []
    try:
        issues = base_schema.check_compliance()
        issues = [issue for issue in issues if issue["code"] != SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED]
        if issues:
            error_message = get_printable_issue_string(issues, title=schema_name)
            validation_issues.append(error_message)
            return validation_issues

        mediawiki_string = base_schema.get_as_mediawiki_string(save_merged=True)
        reloaded_schema = from_string(mediawiki_string, schema_format=".mediawiki")

        validation_issues += _get_schema_comparison(base_schema, reloaded_schema, schema_name, "mediawiki")

        xml_string = base_schema.get_as_xml_string(save_merged=True)
        reloaded_schema = from_string(xml_string, schema_format=".xml")

        validation_issues += _get_schema_comparison(base_schema, reloaded_schema, schema_name, "xml")

        json_string = base_schema.get_as_json_string(save_merged=True)
        reloaded_schema = from_string(json_string, schema_format=".json")

        validation_issues += _get_schema_comparison(base_schema, reloaded_schema, schema_name, "json")

        tsv_dataframes = base_schema.get_as_dataframes(save_merged=True)
        reloaded_schema = from_dataframes(tsv_dataframes)

        validation_issues += _get_schema_comparison(base_schema, reloaded_schema, schema_name, "tsv")
    except HedFileError as e:
        print(f"Saving/loading error: {schema_name} {e.message}")
        error_text = e.message
        if e.issues:
            error_text = get_printable_issue_string(e.issues, title=schema_name)
        validation_issues.append(error_text)

    return validation_issues


def validate_schema(file_path):
    """Validate a schema file, ensuring it can save/load and passes validation.

    Loads the schema from file, checks the file extension is lowercase,
    and validates the schema object for compliance and roundtrip conversion.

    Parameters:
        file_path (str): The path to the schema file to validate.

    Returns:
        list: A list of validation issue strings. Empty if no issues found.
    """

    _, extension = os.path.splitext(file_path)
    if extension.lower() != extension:
        return [f"Only fully lowercase extensions are allowed for schema files.  " f"Invalid extension on file: {file_path}"]

    validation_issues = []
    try:
        base_schema = load_schema(file_path)
        validation_issues = validate_schema_object(base_schema, file_path)
    except HedFileError as e:
        print(f"Saving/loading error: {file_path} {e.message}")
        error_text = e.message
        if e.issues:
            error_text = get_printable_issue_string(e.issues, title=file_path)
        validation_issues.append(error_text)

    return validation_issues


def add_extension(basename, extension):
    """Generate the final filename for a given extension.

    TSV files are placed in a 'hedtsv' subdirectory, while other formats
    simply append the extension to the basename.

    Note: This function preserves the case of the extension to maintain
    compatibility with case-sensitive filesystems. Extensions should only
    be normalized (lowercased) for comparison purposes, not for file path
    construction.

    Parameters:
        basename (str): The base path/name of the schema file without extension.
        extension (str): The file extension including the dot (e.g., '.xml', '.tsv').
            Case is preserved as-is.

    Returns:
        str: The complete file path with extension applied.

    Raises:
        TypeError: If extension is not a string.
    """
    if not isinstance(extension, str):
        raise TypeError(f"extension must be a string, got {type(extension).__name__}")
    # Normalize only for comparison, not for path construction
    extension_lower = extension.lower()
    if extension_lower == ".tsv":
        parent_path, basename = os.path.split(basename)
        return os.path.join(parent_path, "hedtsv", basename)
    return basename + extension


def sort_base_schemas(filenames, add_all_extensions=False):
    """Sort and group changed schema files by their basename.

    Groups schema files by their base name, tracking which formats (extensions)
    have been modified. Handles special TSV directory structure (hedtsv subfolder).

    Returns a nested dict that maps basename -> normalized_extension -> actual_filepath.
    This preserves the original file casing for case-sensitive filesystems while
    still allowing normalized extension comparisons.

    Example input:
        ["test_schema.mediawiki", "hedtsv/test_schema/test_schema_Tag.tsv", "other_schema.XML"]

    Example output:
        {
            "test_schema": {".mediawiki": "test_schema.mediawiki", ".tsv": "hedtsv/.../test_schema_Tag.tsv"},
            "other_schema": {".xml": "other_schema.XML"}
        }

    Parameters:
        filenames (list or container): The changed filenames to process.
        add_all_extensions (bool): If True, always return all 4 extensions for any schemas found.
            Default is False.

    Returns:
        dict: A nested dictionary where keys are basenames (str), values are dicts mapping
            normalized extensions (str, lowercase) to actual file paths (str, preserving case).
            Can include .tsv, .mediawiki, .xml, and .json as keys.
    """
    schema_files = defaultdict(dict)
    for file_path in filenames:
        if not os.path.exists(file_path):
            print(f"Ignoring deleted file {file_path}.")
            continue
        basename, extension = os.path.splitext(file_path)
        extension_lower = extension.lower()  # Normalize for comparison only
        if extension_lower == ".xml" or extension_lower == ".mediawiki":
            schema_files[basename][extension_lower] = file_path
            continue
        elif extension_lower == ".tsv":
            tsv_basename = basename.rpartition("_")[0]
            full_parent_path, real_basename = os.path.split(tsv_basename)
            full_parent_path, real_basename2 = os.path.split(full_parent_path)
            real_parent_path, hedtsv_folder = os.path.split(full_parent_path)
            if hedtsv_folder != "hedtsv":
                print(f"Ignoring file {file_path}.  .tsv files must be in an 'hedtsv' subfolder.")
                continue
            if real_basename != real_basename2:
                print(f"Ignoring file {file_path}.  .tsv files must be in a subfolder with the same name.")
                continue
            real_name = os.path.join(real_parent_path, real_basename)
            schema_files[real_name][extension_lower] = file_path
        else:
            print(f"Ignoring file {file_path}")

    if add_all_extensions:
        for schema_name in schema_files:
            for extension in all_extensions:
                # Only add if not already present - don't overwrite actual paths
                if extension not in schema_files[schema_name]:
                    # Construct path for missing extensions - use the add_extension logic
                    schema_files[schema_name][extension] = add_extension(schema_name, extension)

    return schema_files


def validate_all_schema_formats(basename):
    """Validate that all 4 format versions of a schema are identical.

    Loads the schema from all four formats (MEDIAWIKI, XML, JSON, TSV) and
    verifies they are equivalent. Used when multiple formats are modified
    simultaneously to ensure consistency.

    Parameters:
        basename (str): The base path/name of the schema (without extension) to check.

    Returns:
        list: A list of issue strings if formats differ or loading fails. Empty if all identical.
    """
    # Note if more than one is changed, it intentionally checks all 4 even if one wasn't changed.
    paths = [add_extension(basename, extension) for extension in all_extensions]
    try:
        schemas = [load_schema(path) for path in paths]
        all_equal = all(obj == schemas[0] for obj in schemas[1:])
        if not all_equal:
            return [
                f"Multiple schemas of type {basename} were modified, and are not equal.\n"
                f"Only modify one source schema type at a time(mediawiki, xml, tsv), or modify all 3 at once."
            ]
    except HedFileError as e:
        error_message = f"Error loading schema: {e.message}"
        return [error_message]

    return []


def validate_all_schemas(schema_files):
    """Validate all schema files and formats in the schema dictionary.

    Validates each schema file individually and, if multiple formats were edited
    for a prerelease schema, ensures all formats exist and are identical.

    Parameters:
        schema_files (dict): Dictionary mapping basenames (str) to dicts of
            {normalized_extension (str) -> actual_filepath (str)} representing
            all files changed.

    Returns:
        list: A list of all validation issues found across all schemas.
    """
    all_issues = []
    for basename, extension_paths in schema_files.items():
        single_schema_issues = []
        for _extension, file_path in extension_paths.items():
            # Use the actual file path to preserve case on case-sensitive filesystems
            single_schema_issues += validate_schema(file_path)

        if len(extension_paths) > 1 and not single_schema_issues and "prerelease" in basename:
            single_schema_issues += validate_all_schema_formats(basename)

        print(f"Validating: {basename}...")
        print(f"Extensions: {set(extension_paths.keys())}")
        if single_schema_issues:
            for issue in single_schema_issues:
                print(issue)

        all_issues += single_schema_issues
    return all_issues


def get_schema_filename(schema_name, schema_version):
    """Assemble the standard filename for a schema given its name and version.

    Constructs the conventional HED schema filename without extension or folder path.
    Standard schema uses "HED" prefix, library schemas use "HED_name_" prefix.

    Example:
        get_schema_filename("standard", "8.3.0") returns "HED8.3.0"
        get_schema_filename("score", "1.0.0") returns "HED_score_1.0.0"

    Parameters:
        schema_name (str): The name of the schema. Use "standard" or "" for the standard schema.
        schema_version (str): The semantic version number (e.g., "8.3.0").

    Returns:
        str: The assembled filename without extension or folder path.
    """
    schema_name = schema_name.lower()
    if schema_name == "standard" or schema_name == "":
        return f"HED{schema_version}"
    else:
        return f"HED_{schema_name}_{schema_version}"


def get_prerelease_path(repo_path, schema_name, schema_version):
    """Get the full path to a prerelease schema's TSV directory in the repository.

    Constructs the standard repository path for prerelease schema TSV files,
    following the hed-schemas repository structure.

    Parameters:
        repo_path (str): The path to the hed-schemas folder. Should point into the repository.
        schema_name (str): The name of the schema. Use "standard" or "" for the standard schema.
        schema_version (str): The semantic version number (e.g., "8.3.0").

    Returns:
        str: The fully assembled path to the schema's TSV directory.
    """
    schema_name = schema_name.lower()
    if schema_name == "" or schema_name == "standard":
        base_path = "standard_schema"
    else:
        base_path = os.path.join("library_schemas", schema_name)

    base_path = os.path.join(repo_path, base_path, "prerelease")

    schema_filename = get_schema_filename(schema_name, schema_version)

    return os.path.join(base_path, "hedtsv", schema_filename)


def _get_schema_comparison(schema, schema_reload, file_path, file_format):
    """Compare two schema objects and generate error message if they differ.

    Private helper function for validating schema roundtrip conversion.
    Uses SchemaComparer to identify differences when schemas don't match.

    Parameters:
        schema (HedSchema): The original schema object.
        schema_reload (HedSchema): The reloaded schema object to compare against.
        file_path (str): The file path being validated (for error messages).
        file_format (str): The format being tested (e.g., "xml", "mediawiki").

    Returns:
        list: A list containing an error message if schemas differ, empty list if identical.
    """
    if schema_reload != schema:
        error_text = (
            f"Failed to reload {file_path} as {file_format}.  "
            f"There is either a problem with the source file, or the saving/loading code."
        )
        title_prompt = (
            "If the problem is in the schema file, "
            "the following comparison should indicate the approximate source of the issues:"
        )
        error_text += "\n" + SchemaComparer(schema, schema_reload).compare_differences(title=title_prompt)
        return [error_text]

    return []
