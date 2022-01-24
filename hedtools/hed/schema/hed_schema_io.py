import os


from hed.schema.io.xml2schema import HedSchemaXMLParser
from hed.schema.io.wiki2schema import HedSchemaWikiParser
from hed.schema import hed_schema_constants, hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.util import file_util


def from_string(schema_string, file_type=".xml", library_prefix=None):
    """
        Creates a schema from the given string as if it was loaded from the given file type.

    Parameters
    ----------
    schema_string : str
        An XML or mediawiki file as a single long string.
    file_type : str
        The extension(including the .) we should treat this string as
    library_prefix : str or None
        The name_prefix all tags in this schema will accept.
    Returns
    -------
    schema: HedSchema
        The loaded schema
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
    """
        Load a schema from the given file or URL path.

        Raises HedFileError if there are any fatal issues.

    Parameters
    ----------
    hed_path : str or None
        A filepath or url to open a schema from
    library_prefix : str or None
        The name_prefix all tags in this schema will accept.

    Returns
    -------
    schema: HedSchema
        The loaded schema
    """
    if not hed_path:
        raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file",
                           filename=hed_path)

    is_url = hed_cache._check_if_url(hed_path)

    if is_url:
        file_as_string = file_util.url_to_string(hed_path)
        return from_string(file_as_string, file_type=os.path.splitext(hed_path.lower())[1])
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
def get_hed_xml_version(hed_xml_file_path):
    """Gets the version number from a HED XML file.
    Parameters
    ----------
    hed_xml_file_path: str
        The path to a HED XML file.
    Returns
    -------
    str
        The version number of the HED XML file.
    """
    root_node = HedSchemaXMLParser._parse_hed_xml(hed_xml_file_path)
    return root_node.attrib[hed_schema_constants.VERSION_ATTRIBUTE]


def load_schema_version(xml_folder=None, xml_version=None, library_name=None,
                        library_prefix=None):
    """
    Gets a HedSchema object based on the hed xml file specified. If no HED file is specified then the latest
       file will be retrieved.
    Parameters
    ----------
    xml_folder: str
        Path to a folder containing schemas
    xml_version: str
        HED version format string. Expected format: 'X.Y.Z'
    library_name: str or None, optional
        The schema library name.  HED_(LIBRARY_NAME)_(version).xml
    library_prefix : str or None
        The name_prefix all tags in this schema will accept.
    Returns
    -------
    HedSchema
        A HedSchema object.
    """
    try:
        final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
        hed_schema = load_schema(final_hed_xml_file)
    except HedFileError as e:
        if e.error_type == HedExceptions.FILE_NOT_FOUND:
            hed_cache.cache_all_hed_xml_versions()
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_version, library_name, xml_folder)
            hed_schema = load_schema(final_hed_xml_file)
        else:
            raise e
        
    if library_prefix:
        hed_schema.set_library_prefix(library_prefix=library_prefix)

    return hed_schema
