""" Utilities for loading and outputting HED schema. """
from __future__ import annotations
import os
import json
import functools
from typing import Union
from hed.schema.hed_schema import HedSchema
from hed.schema.schema_io.xml2schema import SchemaLoaderXML
from hed.schema.schema_io.wiki2schema import SchemaLoaderWiki
from hed.schema.schema_io.df2schema import SchemaLoaderDF
from hed.schema import hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.schema_io import schema_util
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.schema.schema_header_util import validate_version_string
from collections import defaultdict
from urllib.error import URLError

MAX_MEMORY_CACHE = 40


def load_schema_version(xml_version=None, xml_folder=None) -> Union['HedSchema', 'HedSchemaGroup']:
    """ Return a HedSchema or HedSchemaGroup extracted from xml_version

    Parameters:
        xml_version (str or list): List or str specifying which official HED schemas to use.
                                           A json str format is also supported,
                                           based on the output of HedSchema.get_formatted_version
                                           Basic format: `[schema_namespace:][library_name_]X.Y.Z`.
        xml_folder (str): Path to a folder containing schema.

    Returns:
        Union[HedSchema, HedSchemaGroup]: The schema or schema group extracted.

    Raises:
        HedFileError: The xml_version is not valid.
        HedFileError: The specified version cannot be found or loaded.
        HedFileError: Other fatal errors loading the schema (These are unlikely if you are not editing them locally).
        HedFileError: The prefix is invalid.
    """
    # Check if we start and end with a square bracket, or double quote.  This might be valid json
    if xml_version and isinstance(xml_version, str) and \
            ((xml_version[0], xml_version[-1]) in [('[', ']'), ('"', '"')]):
        try:
            xml_version = json.loads(xml_version)
        except json.decoder.JSONDecodeError as e:
            raise HedFileError(HedExceptions.CANNOT_PARSE_JSON, str(e), xml_version) from e
    if xml_version and isinstance(xml_version, list):
        xml_versions = parse_version_list(xml_version)
        schemas = [_load_schema_version(xml_version=version, xml_folder=xml_folder) for version in
                   xml_versions.values()]
        if len(schemas) == 1:
            return schemas[0]

        name = ",".join([schema.version for schema in schemas])
        return HedSchemaGroup(schemas, name=name)
    else:
        return _load_schema_version(xml_version=xml_version, xml_folder=xml_folder)


def load_schema(hed_path, schema_namespace=None, schema=None, name=None) -> 'HedSchema':
    """ Load a schema from the given file or URL path.

    Parameters:
        hed_path (str): A filepath or url to open a schema from.
            If loading a TSV file, this should be a single filename where:
            Template: basename.tsv, where files are named basename_Struct.tsv, basename_Tag.tsv, etc.
            Alternatively, you can point to a directory containing the .tsv files.
        schema_namespace (str or None): The name_prefix all tags in this schema will accept.
        schema (HedSchema or None): A HED schema to merge this new file into
                                   It must be a with-standard schema with the same value.
        name (str or None): User supplied identifier for this schema

    Returns:
        HedSchema: The loaded schema.

    Raises:
        HedFileError: Empty path passed.
        HedFileError: Unknown extension.
        HedFileError: Any fatal issues when loading the schema.

    """
    if not hed_path:
        raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file",
                           filename=hed_path)

    is_url = hed_cache._check_if_url(hed_path)
    if is_url:
        try:
            file_as_string = schema_util.url_to_string(hed_path)
        except URLError as e:
            raise HedFileError(HedExceptions.URL_ERROR, str(e), hed_path) from e
        hed_schema = from_string(file_as_string, schema_format=os.path.splitext(hed_path.lower())[1], name=name)
    elif hed_path.lower().endswith(".xml"):
        hed_schema = SchemaLoaderXML.load(hed_path, schema=schema, name=name)
    elif hed_path.lower().endswith(".mediawiki"):
        hed_schema = SchemaLoaderWiki.load(hed_path, schema=schema, name=name)
    elif hed_path.lower().endswith(".tsv") or os.path.isdir(hed_path):
        if schema is not None:
            raise HedFileError(HedExceptions.INVALID_HED_FORMAT,
                               "Cannot pass a schema to merge into spreadsheet loading currently.", filename=name)
        hed_schema = SchemaLoaderDF.load_spreadsheet(filenames=hed_path, name=name)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_path)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


def from_string(schema_string, schema_format=".xml", schema_namespace=None, schema=None, name=None) -> 'HedSchema':
    """ Create a schema from the given string.

    Parameters:
        schema_string (str): An XML or mediawiki file as a single long string
        schema_format (str):         The schema format of the source schema string.
            Allowed normal values: .mediawiki, .xml
        schema_namespace (str, None):  The name_prefix all tags in this schema will accept.
        schema (HedSchema or None): A HED schema to merge this new file into
                                   It must be a with-standard schema with the same value.
        name (str or None): User supplied identifier for this schema

    Returns:
        HedSchema: The loaded schema.

    :raises HedFileError:
        - If empty string or invalid extension is passed.
        - Other fatal formatting issues with file

    Notes:
        - The loading is determined by file type.

    """
    if not schema_string:
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty string passed to HedSchema.from_string",
                           filename=name)

    if isinstance(schema_string, str):
        # Replace carriage returns with new lines since this might not be done by the caller
        schema_string = schema_string.replace("\r\n", "\n")

    if schema_format.endswith(".xml"):
        hed_schema = SchemaLoaderXML.load(schema_as_string=schema_string, schema=schema, name=name)
    elif schema_format.endswith(".mediawiki"):
        hed_schema = SchemaLoaderWiki.load(schema_as_string=schema_string, schema=schema, name=name)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, f"Unknown schema extension {schema_format}", filename=name)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)
    return hed_schema


def from_dataframes(schema_data, schema_namespace=None, name=None) -> 'HedSchema':
    """ Create a schema from the given string.

    Parameters:
        schema_data (dict of str or None): A dict of DF_SUFFIXES:file_as_string_or_df
                              Should have an entry for all values of DF_SUFFIXES.
        schema_namespace (str, None):  The name_prefix all tags in this schema will accept.
        name (str or None): User supplied identifier for this schema

    Returns:
        HedSchema:  The loaded schema.

    Raises:
        HedFileError: If empty/invalid parameters.
        Exception: Other fatal I/O or formatting issues.

    Notes:
        - The loading is determined by file type.

    """
    if not schema_data or not isinstance(schema_data, dict):
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty or non dict value passed to HedSchema.from_dataframes",
                           filename=name)

    hed_schema = SchemaLoaderDF.load_spreadsheet(schema_as_strings_or_df=schema_data, name=name)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


# If this is actually used, we could easily add other versions/update this one
def get_hed_xml_version(xml_file_path) -> str:
    """ Get the version number from a HED XML file.

    Parameters:
        xml_file_path (str): The path to a HED XML file.

    Returns:
        str: The version number of the HED XML file.

    :raises HedFileError:
        - There is an issue loading the schema
    """
    parser = SchemaLoaderXML(xml_file_path)
    return parser.schema.version


def parse_version_list(xml_version_list) -> dict:
    """Takes a list of xml versions and returns a dictionary split by prefix

        e.g. ["score", "testlib"] will return {"": "score, testlib"}
        e.g. ["score", "testlib", "ol:otherlib"] will return {"": "score, testlib", "ol:": "otherlib"}

    Parameters:
        xml_version_list (list): List of str specifying which HED schemas to use

    Returns:
        dict: A dictionary of version strings split by prefix.
    """
    out_versions = defaultdict(list)
    for version in xml_version_list:
        schema_namespace = ""
        if version and ":" in version:
            schema_namespace, _, version = version.partition(":")

        if not isinstance(version, str):
            raise HedFileError(HedExceptions.SCHEMA_VERSION_INVALID,
                               f"Must specify schema version by number, found no version on {xml_version_list} schema.",
                               filename=None)
        if version in out_versions[schema_namespace]:
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_LIBRARY,
                               f"Attempting to load same library '{version}' twice: {out_versions[schema_namespace]}",
                               filename=None)
        out_versions[schema_namespace].append(version)

    out_versions = {key: ",".join(value) if not key else f"{key}:" + ",".join(value) for key, value in
                    out_versions.items()}

    return out_versions


@functools.lru_cache(maxsize=MAX_MEMORY_CACHE)
def _load_schema_version(xml_version=None, xml_folder=None):
    """ Return specified version

    Parameters:
        xml_version (str): HED version format string. Expected format: '[schema_namespace:][library_name_]X.Y.Z'
                           Further versions can be added comma separated after the version number/library name.
                           e.g. "lib:library_x.y.z,otherlibrary_x.y.z" loads "library" and "otherlibrary" into "lib:"
                           The schema namespace must be the same and not repeated if loading multiple merged schemas.

        xml_folder (str): Path to a folder containing schema.

    Returns:
        Union[HedSchema, HedSchemaGroup]: The requested HedSchema object.

    Raises:
        HedFileError: The xml_version is not valid.
        HedFileError: The specified version cannot be found or loaded.
        HedFileError: Multiple schemas are being loaded with the same prefix, and they have duplicate tags.
        HedFileError: Other fatal errors loading the schema (These are unlikely if you are not editing them locally).
        HedFileError: The prefix is invalid.
    """
    schema_namespace = ""
    name = xml_version
    if xml_version:
        if ":" in xml_version:
            schema_namespace, _, xml_version = xml_version.partition(":")

    if xml_version:
        xml_versions = xml_version.split(",")
    # Add a blank entry to generate an error if we have no xml version
    else:
        xml_versions = [""]

    first_schema = _load_schema_version_sub(xml_versions[0], schema_namespace, xml_folder=xml_folder,
                                            name=name)
    filenames = [os.path.basename(first_schema.filename)]

    # Collect all duplicate issues for proper error reporting
    all_duplicate_issues = []

    for version in xml_versions[1:]:
        _load_schema_version_sub(version, schema_namespace, xml_folder=xml_folder, schema=first_schema,
                                 name=name)

        # Collect duplicate errors when merging schemas in the same namespace
        current_filename = os.path.basename(first_schema.filename)
        duplicate_name = first_schema.has_duplicates()
        if duplicate_name:
            # Collect all duplicate issues rather than raising immediately
            for section in first_schema._sections.values():
                if hasattr(section, 'duplicate_names') and section.duplicate_names:
                    for dup_name in section.duplicate_names.keys():
                        issue = {
                            'code': HedExceptions.SCHEMA_DUPLICATE_NAMES,
                            'message': f"Duplicate tag {dup_name} found when merging schemas: {filenames}",
                            'filename': name
                        }
                        all_duplicate_issues.append(issue)
        filenames.append(current_filename)

    # If we found duplicates, raise error with all issues
    if all_duplicate_issues:
        raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_NAMES,
                          f"Found {len(all_duplicate_issues)} duplicate tags when merging schemas: {filenames}",
                          filename=name, issues=all_duplicate_issues)

    if first_schema._namespace:
        first_schema.set_schema_prefix(first_schema._namespace)

    return first_schema


def _load_schema_version_sub(xml_version, schema_namespace="", xml_folder=None, schema=None, name=""):
    """ Return specified version(single version only for this one)

    Parameters:
        xml_version (str): HED version format string. Expected format: '[library_name_]X.Y.Z'
        schema_namespace (str): The prefix this will have
        xml_folder (str): Path to a folder containing schema
        schema (HedSchema or None): A HED schema to merge this new file into.
        name (str): User supplied identifier for this schema

    Returns:
        HedSchema: The requested HedSchema object.

    Raises:
        HedFileError: For the following issues:
        - The xml_version is not valid.
        - The specified version cannot be found or loaded
        - Other fatal errors loading the schema (These are unlikely if you are not editing them locally)
        - The prefix is invalid
    """
    if not xml_version:
        xml_version = "8.3.0"

    # Parse library name from version string before validation
    library_name = ""
    version_to_validate = xml_version
    if "_" in xml_version:
        library_name, _, version_to_validate = xml_version.partition("_")

    # Validate the version string format
    validation_error = validate_version_string(version_to_validate)
    if validation_error:
        raise HedFileError(HedExceptions.SCHEMA_VERSION_INVALID,
                           f"Invalid version format '{version_to_validate}': {validation_error}", xml_version)

    hed_file_path = hed_cache.get_hed_version_path(version_to_validate, library_name=library_name, local_hed_directory=xml_folder)

    if hed_file_path:
        hed_schema = load_schema(hed_file_path, schema_namespace=schema_namespace, schema=schema, name=name)
    else:
        library_string = f"for library '{library_name}'" if library_name else ""
        known_versions = hed_cache.get_hed_versions(xml_folder, library_name=library_name if library_name else "all")
        raise HedFileError(HedExceptions.FILE_NOT_FOUND,
                           f"HED version {library_string}: '{version_to_validate}' not found. Check {hed_cache.get_cache_directory(xml_folder)} for cache or https://github.com/hed-standard/hed-schemas/tree/main/library_schemas. "
                           f"Known versions {library_string}: {known_versions}.", '')

    return hed_schema
