""" Utilities for loading and outputting HED schema. """
import os
import json
import functools

from hed.schema.schema_io.xml2schema import SchemaLoaderXML
from hed.schema.schema_io.wiki2schema import SchemaLoaderWiki
from hed.schema.schema_io.df2schema import SchemaLoaderDF
# from hed.schema.schema_io.owl2schema import SchemaLoaderOWL
from hed.schema import hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.schema_io import schema_util
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.schema.schema_header_util import validate_version_string
from collections import defaultdict
# from hed.schema.schema_io.owl_constants import ext_to_format
from urllib.error import URLError

MAX_MEMORY_CACHE = 40


def from_string(schema_string, schema_format=".xml", schema_namespace=None, schema=None, name=None):
    """ Create a schema from the given string.

    Parameters:
        schema_string (str or dict): An XML, mediawiki or OWL, file as a single long string
            If tsv, Must be a dict of spreadsheets as strings.
        schema_format (str):         The schema format of the source schema string.
            Allowed normal values: .mediawiki, .xml, .tsv
            Note: tsv is in progress and has limited features
        schema_namespace (str, None):  The name_prefix all tags in this schema will accept.
        schema(HedSchema or None): A hed schema to merge this new file into
                                   It must be a with-standard schema with the same value.
        name(str or None): User supplied identifier for this schema

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
                           filename=name)

    if isinstance(schema_string, str):
        # Replace carriage returns with new lines since this might not be done by the caller
        schema_string = schema_string.replace("\r\n", "\n")

    if schema_format.endswith(".xml"):
        hed_schema = SchemaLoaderXML.load(schema_as_string=schema_string, schema=schema, name=name)
    elif schema_format.endswith(".mediawiki"):
        hed_schema = SchemaLoaderWiki.load(schema_as_string=schema_string, schema=schema, name=name)
    elif schema_format.endswith(".tsv"):
        if schema is not None:
            raise HedFileError(HedExceptions.INVALID_HED_FORMAT, "Cannot pass a schema to merge into spreadsheet loading currently.", filename=name)
        hed_schema = SchemaLoaderDF.load_spreadsheet(schema_as_strings=schema_string, name=name)
    # elif schema_format:
    #     hed_schema = SchemaLoaderOWL.load(schema_as_string=schema_string, schema=schema, file_format=schema_format,
    #                                       name=name)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, f"Unknown schema extension {schema_format}", filename=name)

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)
    return hed_schema


def load_schema(hed_path, schema_namespace=None, schema=None, name=None):
    """ Load a schema from the given file or URL path.

    Parameters:
        hed_path (str or dict): A filepath or url to open a schema from.
            If loading a TSV file, this can be a single filename template, or a dict of filenames.
            Template: basename.tsv, where files are named basename_Struct.tsv and basename_Tag.tsv
        schema_namespace (str or None): The name_prefix all tags in this schema will accept.
        schema(HedSchema or None): A hed schema to merge this new file into
                                   It must be a with-standard schema with the same value.
        name(str or None): User supplied identifier for this schema

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
        try:
            file_as_string = schema_util.url_to_string(hed_path)
        except URLError as e:
            raise HedFileError(HedExceptions.URL_ERROR, str(e), hed_path) from e
        hed_schema = from_string(file_as_string, schema_format=os.path.splitext(hed_path.lower())[1], name=name)
    # elif ext in ext_to_format:
    #     hed_schema = SchemaLoaderOWL.load(hed_path, schema=schema, file_format=ext_to_format[ext], name=name)
    # elif file_format:
    #     hed_schema = SchemaLoaderOWL.load(hed_path, schema=schema, file_format=file_format, name=name)
    elif hed_path.lower().endswith(".xml"):
        hed_schema = SchemaLoaderXML.load(hed_path, schema=schema, name=name)
    elif hed_path.lower().endswith(".mediawiki"):
        hed_schema = SchemaLoaderWiki.load(hed_path, schema=schema, name=name)
    elif hed_path.lower().endswith(".tsv"):
        if schema is not None:
            raise HedFileError(HedExceptions.INVALID_HED_FORMAT,
                               "Cannot pass a schema to merge into spreadsheet loading currently.", filename=name)
        hed_schema = SchemaLoaderDF.load_spreadsheet(filenames=hed_path, name=name)
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
    """ Return specified version

    Parameters:
        xml_version (str): HED version format string. Expected format: '[schema_namespace:][library_name_]X.Y.Z'
                                Further versions can be added comma separated after the version number/library name.
                                e.g. "lib:library_x.y.z,otherlibrary_x.y.z" will load "library" and "otherlibrary" into "lib:"
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
    for version in xml_versions[1:]:
        _load_schema_version_sub(version, schema_namespace, xml_folder=xml_folder, schema=first_schema,
                                 name=name)

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


def _load_schema_version_sub(xml_version, schema_namespace="", xml_folder=None, schema=None, name=""):
    """ Return specified version

    Parameters:
        xml_version (str): HED version format string. Expected format: '[schema_namespace:][library_name_]X.Y.Z'
        schema_namespace(str): Namespace to add this schema to, default none
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

    if not xml_version:
        out_name = schema_namespace if schema_namespace else "standard"
        raise HedFileError(HedExceptions.SCHEMA_VERSION_INVALID,
                           f"Must specify a schema version by number, found no version on {out_name} schema.",
                           filename=None)

    if "_" in xml_version:
        library_name, _, xml_version = xml_version.rpartition("_")

    if validate_version_string(xml_version):
        raise HedFileError(HedExceptions.SCHEMA_VERSION_INVALID,
                           f"Must specify a schema version by number, found no version on {xml_version} schema.",
                           filename=name)
    try:
        # 1. Try fully local copy
        final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
        if not final_hed_xml_file:
            hed_cache.cache_local_versions(xml_folder)
            # 2. Cache the schemas included in hedtools and try local again
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
        hed_schema = load_schema(final_hed_xml_file, schema=schema, name=name)
    except HedFileError as e:
        if e.code == HedExceptions.FILE_NOT_FOUND:
            # Cache all schemas if we haven't recently.
            hed_cache.cache_xml_versions(cache_folder=xml_folder)
            # 3. See if we got a copy from online
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
            # 4. Finally check for a pre-release one
            if not final_hed_xml_file:
                final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder, check_prerelease=True)
            if not final_hed_xml_file:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND,
                                   f"HED version '{xml_version}' not found in cache: {hed_cache.get_cache_directory()}",
                                   filename=xml_folder)
            hed_schema = load_schema(final_hed_xml_file, schema=schema, name=name)
        else:
            raise e

    if schema_namespace:
        hed_schema.set_schema_prefix(schema_namespace=schema_namespace)

    return hed_schema


def load_schema_version(xml_version=None, xml_folder=None):
    """ Return a HedSchema or HedSchemaGroup extracted from xml_version

    Parameters:
        xml_version (str or list): List or str specifying which official HED schemas to use.
                                           A json str format is also supported,
                                           based on the output of HedSchema.get_formatted_version
                                           Basic format: `[schema_namespace:][library_name_]X.Y.Z`.
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
        schemas = [_load_schema_version(xml_version=version, xml_folder=xml_folder) for version in
                   xml_versions.values()]
        if len(schemas) == 1:
            return schemas[0]

        name = ",".join([schema.version for schema in schemas])
        return HedSchemaGroup(schemas, name=name)
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

        if not isinstance(version, str):
            raise HedFileError(HedExceptions.SCHEMA_VERSION_INVALID,
                               f"Must specify a schema version by number, found no version on {xml_version_list} schema.",
                               filename=None)
        if version in out_versions[schema_namespace]:
            raise HedFileError(HedExceptions.SCHEMA_DUPLICATE_LIBRARY,
                               f"Attempting to load the same library '{version}' twice: {out_versions[schema_namespace]}",
                               filename=None)
        out_versions[schema_namespace].append(version)

    out_versions = {key: ",".join(value) if not key else f"{key}:" + ",".join(value) for key, value in
                    out_versions.items()}

    return out_versions
