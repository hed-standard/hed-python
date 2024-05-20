import os.path
from collections import defaultdict
from hed.schema import from_string, load_schema
from hed.errors import get_printable_issue_string, HedFileError, SchemaWarnings

all_extensions = [".tsv", ".mediawiki", ".xml"]


def validate_schema(file_path):
    """ Validates the given schema, ensuring it can save/load as well as validates.

        This is probably overkill...
    """
    validation_issues = []
    try:
        base_schema = load_schema(file_path)
        issues = base_schema.check_compliance()
        issues = [issue for issue in issues if issue["code"] != SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED]
        if issues:
            error_message = get_printable_issue_string(issues, title=file_path)
            validation_issues.append(error_message)

        mediawiki_string = base_schema.get_as_mediawiki_string()
        reloaded_schema = from_string(mediawiki_string, schema_format=".mediawiki")

        if reloaded_schema != base_schema:
            error_text = f"Failed to reload {file_path} as mediawiki.  " \
                         f"There is either a problem with the source file, or the saving/loading code."
            validation_issues.append(error_text)

        xml_string = base_schema.get_as_xml_string()
        reloaded_schema = from_string(xml_string, schema_format=".xml")

        if reloaded_schema != base_schema:
            error_text = f"Failed to reload {file_path} as xml.  " \
                         f"There is either a problem with the source file, or the saving/loading code."
            validation_issues.append(error_text)
    except HedFileError as e:
        print(f"Saving/loading error: {file_path} {e.message}")
        error_text = e.message
        if e.issues:
            error_text = get_printable_issue_string(e.issues, title=file_path)
        validation_issues.append(error_text)

    return validation_issues


def add_extension(basename, extension):
    """Generate the final name for a given extension.  Only .tsv varies notably."""
    if extension.lower() == ".tsv":
        parent_path, basename = os.path.split(basename)
        return os.path.join(parent_path, "hedtsv", basename)
    return basename + extension


def sort_base_schemas(filenames):
    """ Sort and group the changed files based on basename

        Example input: ["test_schema.mediawiki", "hedtsv/test_schema/test_schema_Tag.tsv", "other_schema.xml"]

        Example output:
        {
        "test_schema": {".mediawiki", ".tsv"},
        other_schema": {".xml"}
        }

    Parameters:
        filenames(list or container): The changed filenames

    Returns:
        sorted_files(dict): A dictionary where keys are the basename, and the values are a set of extensions modified
                            Can include tsv, mediawiki, and xml.
    """
    schema_files = defaultdict(set)
    for file_path in filenames:
        basename, extension = os.path.splitext(file_path)
        if extension.lower() == ".xml" or extension.lower() == ".mediawiki":
            schema_files[basename].add(extension)
            continue
        elif extension.lower() == ".tsv":
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
            schema_files[real_name].add(extension)
        else:
            print(f"Ignoring file {file_path}")

    return schema_files


def validate_all_schema_formats(basename):
    """ Validate all 3 versions of the given schema.

    Parameters:
         basename(str): a schema to check all 3 formats are identical of.

    Returns:
        issue_list(list): A non-empty list if there are any issues.
    """
    # Note if more than one is changed, it intentionally checks all 3 even if one wasn't changed.
    # todo: this needs to be updated to handle capital letters in the extension.
    paths = [add_extension(basename, extension) for extension in all_extensions]
    try:
        schemas = [load_schema(path) for path in paths]
        all_equal = all(obj == schemas[0] for obj in schemas[1:])
        if not all_equal:
            return [
                f"Multiple schemas of type {basename} were modified, and are not equal.\n"
                f"Only modify one source schema type at a time(mediawiki, xml, tsv), or modify all 3 at once."]
    except HedFileError as e:
        error_message = f"Error loading schema: {e.message}"
        return [error_message]

    return []


def validate_all_schemas(schema_files):
    """Validates all the schema files/formats in the schema dict

       If multiple formats were edited, ensures all 3 formats exist and match.

    Parameters:
        schema_files(dict of sets): basename:[extensions] dictionary for all files changed

    Returns:
        issues(list of str): Any issues found validating or loading schemas.
    """
    all_issues = []
    for basename, extensions in schema_files.items():
        single_schema_issues = []
        for extension in extensions:
            full_path = add_extension(basename, extension)
            single_schema_issues += validate_schema(full_path)

        if len(extensions) > 1 and not single_schema_issues and "prerelease" in basename:
            single_schema_issues += validate_all_schema_formats(basename)

        print(f"Validating: {basename}...")
        print(f"Extensions: {extensions}")
        if single_schema_issues:
            for issue in single_schema_issues:
                print(issue)

        all_issues += single_schema_issues
    return all_issues
