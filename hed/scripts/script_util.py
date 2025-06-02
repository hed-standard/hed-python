import os.path
from collections import defaultdict
from hed.schema import from_string, load_schema, from_dataframes
from hed.errors import get_printable_issue_string, HedFileError, SchemaWarnings
from hed.schema.schema_comparer import SchemaComparer

all_extensions = [".tsv", ".mediawiki", ".xml"]

def validate_schema_object(base_schema, schema_name):
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

        tsv_dataframes = base_schema.get_as_dataframes(save_merged=True)
        reloaded_schema = from_dataframes(tsv_dataframes)

        validation_issues += _get_schema_comparison(base_schema, reloaded_schema,schema_name, "tsv")
    except HedFileError as e:
        print(f"Saving/loading error: {schema_name} {e.message}")
        error_text = e.message
        if e.issues:
            error_text = get_printable_issue_string(e.issues, title=schema_name)
        validation_issues.append(error_text)

    return validation_issues


def validate_schema(file_path):
    """ Validates the given schema, ensuring it can save/load as well as validates.

    Parameters:
        file_path(str): the specific schema file to validate

    Returns:
        validation_issues(list): A list of issues found
    """

    _, extension = os.path.splitext(file_path)
    if extension.lower() != extension:
        return [f"Only fully lowercase extensions are allowed for schema files.  "
                f"Invalid extension on file: {file_path}"]

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
    """Generate the final name for a given extension.  Only .tsv varies notably."""
    if extension == ".tsv":
        parent_path, basename = os.path.split(basename)
        return os.path.join(parent_path, "hedtsv", basename)
    return basename + extension


def sort_base_schemas(filenames, add_all_extensions=False):
    """ Sort and group the changed files based on basename

        Example input: ["test_schema.mediawiki", "hedtsv/test_schema/test_schema_Tag.tsv", "other_schema.xml"]

        Example output:
        {
        "test_schema": {".mediawiki", ".tsv"},
        other_schema": {".xml"}
        }

    Parameters:
        filenames(list or container): The changed filenames
        add_all_extensions(bool): If True, always return all 3 filenames for any schemas found.

    Returns:
        sorted_files(dict): A dictionary where keys are the basename, and the values are a set of extensions modified
                            Can include tsv, mediawiki, and xml.
    """
    schema_files = defaultdict(set)
    for file_path in filenames:
        if not os.path.exists(file_path):
            print(f"Ignoring deleted file {file_path}.")
            continue
        basename, extension = os.path.splitext(file_path)
        if extension == ".xml" or extension == ".mediawiki":
            schema_files[basename].add(extension)
            continue
        elif extension == ".tsv":
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

    if add_all_extensions:
        for schema_name in schema_files:
            for extension in all_extensions:
                schema_files[schema_name].add(extension)

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


def get_schema_filename(schema_name, schema_version):
    """ Returns the assembled name of a schema given the name and version

        e.g. "standard" and "8.3.0" returns "HED8.3.0"

    Parameters:
        schema_name(str): The name of the schema we're interested in.  "standard" for the standard schema
        schema_version(str): The semantic version number

    Returns:
        schema_filename(str): the assembled filename, without extension or folder.
    """
    schema_name = schema_name.lower()
    if schema_name == "standard" or schema_name == "":
        return f"HED{schema_version}"
    else:
        return f"HED_{schema_name}_{schema_version}"


def get_prerelease_path(repo_path, schema_name, schema_version):
    """ Returns the location of the given pre-release schema in the repo

    Parameters:
        repo_path(str): the location of the hed-schemas folder relative to this one.  Should point into the folder.
        schema_name(str): The name of the schema we're interested in.  "standard" for the standard schema
        schema_version(str): The semantic version number

    Returns:
        schema_path(str): The fully assembled location of this schema tsv version.
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
    if schema_reload != schema:
        error_text = f"Failed to reload {file_path} as {file_format}.  " \
                     f"There is either a problem with the source file, or the saving/loading code."
        title_prompt = ("If the problem is in the schema file, "
                        "the following comparison should indicate the approximate source of the issues:")
        error_text += "\n" + SchemaComparer(schema, schema_reload).compare_differences(title=title_prompt)
        return [error_text]

    return []
