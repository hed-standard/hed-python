""" Utilities for loading and outputting HED schema. """
import os
from hed.schema.schema_io.xml2schema import HedSchemaXMLParser
from hed.schema.schema_io.wiki2schema import HedSchemaWikiParser
from hed.schema import hed_schema_constants, hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.schema.hed_schema import HedSchema
from hed.schema.schema_io import schema_util
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.schema.schema_validation_util import validate_version_string


def from_string(schema_string, file_type=".xml", schema_prefix=None):
    """ Create a schema from the given string.

    Parameters:
        schema_string (str):         An XML or mediawiki file as a single long string.
        file_type (str):             The extension(including the .) corresponding to a file source.
        schema_prefix (str, None):  The name_prefix all tags in this schema will accept.

    Returns:
        (HedSchema):  The loaded schema.

    Raises:
        HedFileError:  If empty string or invalid extension is passed.

    Notes:
        - The loading is determined by file type.

    """
    if not schema_string:
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty string passed to HedSchema.from_string",
                           filename=schema_string)

    if file_type.endswith(".xml"):
        hed_schema = HedSchemaXMLParser.load_xml(schema_as_string=schema_string)
    elif file_type.endswith(".mediawiki"):
        hed_schema = HedSchemaWikiParser.load_wiki(schema_as_string=schema_string)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=file_type)

    if schema_prefix:
        hed_schema.set_schema_prefix(schema_prefix=schema_prefix)

    return hed_schema


def get_schema(hed_versions):
    if not hed_versions:
        return None
    elif isinstance(hed_versions, str) or isinstance(hed_versions, list):
        return load_schema_version(hed_versions)
    elif isinstance(hed_versions, HedSchema) or isinstance(hed_versions, HedSchemaGroup):
        return hed_versions
    else:
        raise ValueError("InvalidHedSchemaOrSchemaVersion", "Expected schema or schema version")


def get_schema_versions(hed_schema, as_string=True):
    if not hed_schema and as_string:
        return ''
    elif not hed_schema:
        return None
    elif isinstance(hed_schema, HedSchema) or isinstance(hed_schema, HedSchemaGroup):
        return hed_schema.get_formatted_version(as_string=as_string)
    else:
        raise ValueError("InvalidHedSchemaOrHedSchemaGroup", "Expected schema or schema group")


def load_schema(hed_path=None, schema_prefix=None):
    """ Load a schema from the given file or URL path.

    Parameters:
        hed_path (str or None): A filepath or url to open a schema from.
        schema_prefix (str or None): The name_prefix all tags in this schema will accept.

    Returns:
        HedSchema: The loaded schema.

    Raises:
         HedFileError: If there are any fatal issues when loading the schema.

    """
    if not hed_path:
        raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file",
                           filename=hed_path)

    is_url = hed_cache._check_if_url(hed_path)

    if is_url:
        file_as_string = schema_util.url_to_string(hed_path)
        hed_schema = from_string(file_as_string, file_type=os.path.splitext(hed_path.lower())[1])
    elif hed_path.lower().endswith(".xml"):
        hed_schema = HedSchemaXMLParser.load_xml(hed_path)
    elif hed_path.lower().endswith(".mediawiki"):
        hed_schema = HedSchemaWikiParser.load_wiki(hed_path)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_path)

    if schema_prefix:
        hed_schema.set_schema_prefix(schema_prefix=schema_prefix)

    return hed_schema


# todo: this could be updated to also support .mediawiki format.
def get_hed_xml_version(xml_file_path):
    """ Get the version number from a HED XML file.

    Parameters:
        xml_file_path (str): The path to a HED XML file.

    Returns:
        str: The version number of the HED XML file.

    """
    root_node = HedSchemaXMLParser._parse_hed_xml(xml_file_path)
    return root_node.attrib[hed_schema_constants.VERSION_ATTRIBUTE]


def _load_schema_version(xml_version=None, xml_folder=None):
    """ Return specified version or latest if not specified.

    Parameters:
        xml_folder (str): Path to a folder containing schema.
        xml_version (str or list): HED version format string. Expected format: '[schema_prefix:][library_name_]X.Y.Z'.

    Returns:
        HedSchema or HedSchemaGroup: The requested HedSchema object.

    Raises:
        HedFileError: If the xml_version is not valid.

    Notes:
        - The library schema files have names of the form HED_(LIBRARY_NAME)_(version).xml.
    """
    schema_prefix = ""
    library_name = None
    if xml_version:
        if ":" in xml_version:
            schema_prefix, _, xml_version = xml_version.partition(":")
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
        hed_schema = load_schema(final_hed_xml_file)
    except HedFileError as e:
        if e.error_type == HedExceptions.FILE_NOT_FOUND:
            hed_cache.cache_xml_versions(cache_folder=xml_folder)
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
            if not final_hed_xml_file:
                raise HedFileError(HedExceptions.FILE_NOT_FOUND, f"HED version '{xml_version}' not found in cache: {hed_cache.get_cache_directory()}", filename=xml_folder)
            hed_schema = load_schema(final_hed_xml_file)
        else:
            raise e

    if schema_prefix:
        hed_schema.set_schema_prefix(schema_prefix=schema_prefix)

    return hed_schema


def load_schema_version(xml_version=None, xml_folder=None):
    """ Return a HedSchema or HedSchemaGroup extracted from xml_version field.

    Parameters:
        xml_version (str or list or None): List or str specifying which official HED schemas to use.
                                           An empty string returns the latest version
        xml_folder (str): Path to a folder containing schema.

    Returns:
        HedSchema or HedSchemaGroup: The schema or schema group extracted.

    Raises:
        HedFileError: If the xml_version is not valid.

    Notes:
        - Loads the latest schema value if an empty version is given (string or list).
    """
    if xml_version and isinstance(xml_version, list):
        schemas = [_load_schema_version(xml_version=version, xml_folder=xml_folder) for version in xml_version]
        if len(schemas) == 1:
            return schemas[0]

        return HedSchemaGroup(schemas)
    else:
        return _load_schema_version(xml_version=xml_version, xml_folder=xml_folder)
