""" Utilities for loading and outputting HED schema."""
import os


from hed.schema.schema_io.xml2schema import HedSchemaXMLParser
from hed.schema.schema_io.wiki2schema import HedSchemaWikiParser
from hed.schema import hed_schema_constants, hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.util import file_util


def from_string(schema_string, file_type=".xml", library_prefix=None):
    """ Create a schema from the given string.

    Args:
        schema_string (str):         An XML or mediawiki file as a single long string.
        file_type (str):             The extension(including the .) corresponding to a file source.
        library_prefix (str, None):  The name_prefix all tags in this schema will accept.

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

    if library_prefix:
        hed_schema.set_library_prefix(library_prefix=library_prefix)

    return hed_schema


def load_schema(hed_path=None, library_prefix=None):
    """ Load a schema from the given file or URL path.

    Args:
        hed_path (str or None): A filepath or url to open a schema from.
        library_prefix (str or None): The name_prefix all tags in this schema will accept.

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
        file_as_string = file_util.url_to_string(hed_path)
        hed_schema = from_string(file_as_string, file_type=os.path.splitext(hed_path.lower())[1])
    elif hed_path.lower().endswith(".xml"):
        hed_schema = HedSchemaXMLParser.load_xml(hed_path)
    elif hed_path.lower().endswith(".mediawiki"):
        hed_schema = HedSchemaWikiParser.load_wiki(hed_path)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_path)

    if library_prefix:
        hed_schema.set_library_prefix(library_prefix=library_prefix)

    return hed_schema


# todo: this could be updated to also support .mediawiki format.
def get_hed_xml_version(xml_file_path):
    """ Get the version number from a HED XML file.

    Args:
        xml_file_path (str): The path to a HED XML file.

    Returns:
        str: The version number of the HED XML file.

    """
    root_node = HedSchemaXMLParser._parse_hed_xml(xml_file_path)
    return root_node.attrib[hed_schema_constants.VERSION_ATTRIBUTE]


def load_schema_version(xml_folder=None, xml_version=None, library_name=None,
                        library_prefix=None):
    """ Return specified version or latest if not specified.

    Args:
        xml_folder (str): Path to a folder containing schema.
        xml_version (str): HED version format string. Expected format: 'X.Y.Z'.
        library_name (str or None): Optional library name
        library_prefix  (str or None): The name_prefix all tags in this schema will accept.

    Returns:
        HedSchema: The requested HedSchema object.

    Notes:
        - The library schema files have names of the form HED_(LIBRARY_NAME)_(version).xml.
    """
    try:
        final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
        hed_schema = load_schema(final_hed_xml_file)
    except HedFileError as e:
        if e.error_type == HedExceptions.FILE_NOT_FOUND:
            hed_cache.cache_xml_versions()
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
            hed_schema = load_schema(final_hed_xml_file)
        else:
            raise e
        
    if library_prefix:
        hed_schema.set_library_prefix(library_prefix=library_prefix)

    return hed_schema
