""" Utilities for loading and outputting HED schema. """
import os
import json
import functools
from hed.schema.schema_io.xml2schema import SchemaLoaderXML
from hed.schema.schema_io.wiki2schema import SchemaLoaderWiki
from hed.schema import hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.schema_io import schema_util
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.schema.schema_validation_util import validate_version_string
from collections import defaultdict


MAX_MEMORY_CACHE = 40


def from_string(schema_string, schema_format=".xml", schema_namespace=None, schema=None):
    """ Create a schema from the given string.

    Parameters:
        schema_string (str):         An XML or mediawiki file as a single long string.
        schema_format (str):         The schema format of the source schema string.
        schema_namespace (str, None):  The name_prefix all tags in this schema will accept.
        schema(HedSchema or None): A hed schema to merge this new file into
                                   It must be a with-standard schema with the same value.

    Returns:
        (HedSchema):  The loaded schema.

    :raises HedFileError:
        - If empty string or invalid extension is passed.
        - Other fatal formatting issues with file

    Notes:
        - The loading is determined by file type.

    """
    if not schema_string:
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty string passed to HedSchema.from_string",
                           filename=schema_string)

    if schema_format.endswith(".xml"):
        hed_schema = SchemaLoaderXML.load(schema_as_string=schema_string, schema=schema)
    elif schema_format.endswith(".mediawiki"):
        hed_schema = SchemaLoaderWiki.load(schema_as_string=schema_string, schema=schema)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=schema_format)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


def load_schema(hed_path=None, schema_namespace=None, schema=None):
    """ Load a schema from the given file or URL path.

    Parameters:
        hed_path (str or None): A filepath or url to open a schema from.
        schema_namespace (str or None): The name_prefix all tags in this schema will accept.
        schema(HedSchema or None): A hed schema to merge this new file into
                                   It must be a with-standard schema with the same value.

    Returns:
        HedSchema: The loaded schema.

    :raises HedFileError:
        - Empty path passed
        - Unknown extension
        - Any fatal issues when loading the schema.

    """
    if not hed_path:
        raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file",
                           filename=hed_path)

    is_url = hed_cache._check_if_url(hed_path)

    if is_url:
        file_as_string = schema_util.url_to_string(hed_path)
        hed_schema = from_string(file_as_string, schema_format=os.path.splitext(hed_path.lower())[1])
    elif hed_path.lower().endswith(".xml"):
        hed_schema = SchemaLoaderXML.load(hed_path, schema=schema)
    elif hed_path.lower().endswith(".mediawiki"):
        hed_schema = SchemaLoaderWiki.load(hed_path, schema=schema)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_path)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


# If this is actually used, we could easily add other versions/update this one
def get_hed_xml_version(xml_file_path):
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


@functools.lru_cache(maxsize=MAX_MEMORY_CACHE)
def _load_schema_version(xml_version=None, xml_folder=None):
    """ Return specified version or latest if not specified.

    Parameters:
        xml_version (str): HED version format string. Expected format: '[schema_namespace:][library_name_][X.Y.Z]'
                                Further versions can be added comma separated after the version number/library name.
                                e.g. "lib:library,otherlibrary" will load "library" and "otherlibrary" into "lib:"
                                The schema namespace must be the same and not repeated if loading multiple merged schemas.

        xml_folder (str): Path to a folder containing schema.

    Returns:
        HedSchema or HedSchemaGroup: The requested HedSchema object.

    :raises HedFileError:
        - The xml_version is not valid.
        - The specified version cannot be found or loaded
        - Multiple schemas are being loaded with the same prefix, and they have duplicate tags
        - Other fatal errors loading the schema (These are unlikely if you are not editing them locally)
        - The prefix is invalid
    """
    schema_namespace = ""
    if xml_version:
        if ":" in xml_version:
            schema_namespace, _, xml_version = xml_version.partition(":")

    if xml_version:
        xml_versions = xml_version.split(",")
    # Add a blank entry if we have no xml version
    else:
        xml_versions = [""]

    first_schema = _load_schema_version_sub(schema_namespace, xml_versions[0], xml_folder=xml_folder)
    filenames = [os.path.basename(first_schema.filename)]
    for version in xml_versions[1:]:
        _load_schema_version_sub(schema_namespace, version, xml_folder=xml_folder, schema=first_schema)

        # Detect duplicate errors when merging schemas in the same namespace
        current_filename = os.path.basename(first_schema.filename)
        duplicate_name = first_schema.has_duplicates()
        if duplicate_name:
            issues = first_schema.check_compliance(check_for_warnings=False)
            filename_string = ",".join(filenames)
            msg = (f"A duplicate tag, '{duplicate_name}', was detected in the schema file '{current_filename}'. "
                   f"Previously loaded schemas include: {filename_string}. "
                   f"To resolve this, consider prefixing the final schema during load: "
                   f"custom_prefix:schema_version.")
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_NAMES, msg, first_schema.filename, issues)
        filenames.append(current_filename)
    return first_schema


def _load_schema_version_sub(schema_namespace="", xml_version=None, xml_folder=None, schema=None):
    """ Return specified version or latest if not specified.

    Parameters:
        xml_version (str): HED version format string. Expected format: '[schema_namespace:][library_name_][X.Y.Z]'

        xml_folder (str): Path to a folder containing schema.
        schema(HedSchema or None): A hed schema to merge this new file into
                                   It must be a with-standard schema with the same value.

    Returns:
        HedSchema: The requested HedSchema object.

    :raises HedFileError:
        - The xml_version is not valid.
        - The specified version cannot be found or loaded
        - Other fatal errors loading the schema (These are unlikely if you are not editing them locally)
        - The prefix is invalid
    """
    library_name = None

    if xml_version:
        if "_" in xml_version:
            library_name, _, xml_version = xml_version.rpartition("_")
        elif validate_version_string(xml_version):
            library_name = xml_version
            xml_version = None
    try:
        final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
        if not final_hed_xml_file:
            hed_cache.cache_local_versions(xml_folder)
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
        hed_schema = load_schema(final_hed_xml_file, schema=schema)
    except HedFileError as e:
        if e.code == HedExceptions.FILE_NOT_FOUND:
            hed_cache.cache_xml_versions(cache_folder=xml_folder)
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
            if not final_hed_xml_file:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND,
                                   f"HED version '{xml_version}' not found in cache: {hed_cache.get_cache_directory()}",
                                   filename=xml_folder)
            hed_schema = load_schema(final_hed_xml_file, schema=schema)
        else:
            raise e

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


def load_schema_version(xml_version=None, xml_folder=None):
    """ Return a HedSchema or HedSchemaGroup extracted from xml_version

    Parameters:
        xml_version (str or list or None): List or str specifying which official HED schemas to use.
                                           An empty string returns the latest version
                                           A json str format is also supported,
                                           based on the output of HedSchema.get_formatted_version
                                           Basic format: `[schema_namespace:][library_name_][X.Y.Z]`.
        xml_folder (str): Path to a folder containing schema.

    Returns:
        HedSchema or HedSchemaGroup: The schema or schema group extracted.

    :raises HedFileError:
        - The xml_version is not valid.
        - The specified version cannot be found or loaded
        - Other fatal errors loading the schema (These are unlikely if you are not editing them locally)
        - The prefix is invalid
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
        schemas = [_load_schema_version(xml_version=version, xml_folder=xml_folder) for version in xml_versions.values()]
        if len(schemas) == 1:
            return schemas[0]

        return HedSchemaGroup(schemas)
    else:
        return _load_schema_version(xml_version=xml_version, xml_folder=xml_folder)


def parse_version_list(xml_version_list):
    """Takes a list of xml versions and returns a dictionary split by prefix

        e.g. ["score", "testlib"] will return {"": "score, testlib"}
        e.g. ["score", "testlib", "ol:otherlib"] will return {"": "score, testlib", "ol:": "otherlib"}

    Parameters:
        xml_version_list (list): List of str specifying which hed schemas to use

    Returns:
        HedSchema or HedSchemaGroup: The schema or schema group extracted.
    """
    out_versions = defaultdict(list)
    for version in xml_version_list:
        schema_namespace = ""
        if version and ":" in version:
            schema_namespace, _, version = version.partition(":")

        if version is None:
            version = ""
        if version in out_versions[schema_namespace]:
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_LIBRARY, f"Attempting to load the same library '{version}' twice: {out_versions[schema_namespace]}",
                               filename=None)
        out_versions[schema_namespace].append(version)

    out_versions = {key: ",".join(value) if not key else f"{key}:" + ",".join(value) for key, value in out_versions.items()}

    return out_versions