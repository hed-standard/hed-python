import os


from hed.schema.fileio.xml2schema import HedSchemaXMLParser
from hed.schema.fileio.wiki2schema import HedSchemaWikiParser
from hed.schema import hed_schema_constants, hed_cache

from hed.errors.exceptions import HedFileError, HedExceptions
from hed.util import file_util


def from_string(schema_string, file_type=".xml"):
    """
        Creates a schema from the given string as if it was loaded from the given file type.

    Parameters
    ----------
    schema_string : str
        An XML or mediawiki file as a single long string.
    file_type : str
        The extension(including the .) we should treat this string as

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

    hed_schema.update_old_hed_schema()
    return hed_schema


def load_schema(hed_file_path=None, hed_url_path=None, library_prefix=None):
    """
        Load a schema from the given file or URL path.  Must be one or the other

        Raises HedFileError if there are any fatal issues.

    Parameters
    ----------
    hed_file_path : str or None
        A local filepath to open a schema from
    hed_url_path : str or None
        A url to open a schema from
    library_prefix : str or None
        The prefix all tags in this schema will accept.

    Returns
    -------
    schema: HedSchema
        The loaded schema
    """
    if not hed_file_path and not hed_url_path:
        raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file",
                           filename=hed_file_path)

    if hed_file_path and hed_url_path:
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Passed both a filename and a url to load_schema",
                           filename=hed_file_path)

    if hed_url_path:
        file_as_string = file_util.url_to_string(hed_url_path)
        return from_string(file_as_string, file_type=os.path.splitext(hed_url_path.lower())[1])
    elif hed_file_path.lower().endswith(".xml"):
        hed_schema = HedSchemaXMLParser.load_xml(hed_file_path)
    elif hed_file_path.lower().endswith(".mediawiki"):
        hed_schema = HedSchemaWikiParser.load_wiki(hed_file_path)
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_file_path)

    hed_schema.update_old_hed_schema()

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


def load_schema_version(xml_folder=None, xml_version_number=None):
    """
    Gets a HedSchema object based on the hed xml file specified. If no HED file is specified then the latest
       file will be retrieved.
    Parameters
    ----------
    xml_folder: str
        Path to a
    xml_version_number: str
        HED version format string. Expected format: 'X.Y.Z'
    Returns
    -------
    HedSchema
        A HedSchema object.
    """
    try:
        final_hed_xml_file = hed_cache.get_hed_version_path(xml_folder, xml_version_number)
        hed_schema = load_schema(final_hed_xml_file)
    except HedFileError as e:
        if e.error_type == HedExceptions.FILE_NOT_FOUND:
            hed_cache.cache_all_hed_xml_versions()
            final_hed_xml_file = hed_cache.get_hed_version_path(xml_folder, xml_version_number)
            hed_schema = load_schema(final_hed_xml_file)
        else:
            raise e
    return hed_schema


def convert_schema_to_format(hed_schema, check_for_issues=True,
                             name=None, save_as_mediawiki=False, save_as_legacy_xml=False):
    """
    Loads a local schema file or from a URL, then outputs a temporary file with the requested format.
    Parameters
    ----------
    hed_schema: HedSchema
        The schema to convert
    check_for_issues : bool
        After conversion checks for warnings like capitalization or invalid characters.
    name: str
        If present, will use this as the filename for context, rather than using the actual filename
        Useful for temp filenames.
    save_as_mediawiki: bool
        If True, save as .mediawiki.  if False, save as .xml
    save_as_legacy_xml: bool
        If True(and save_as_mediawiki is False), will save using the old legacy XML format.
    Returns
    -------
    output_string: [str]
        The file as a list of strings
    issues_list: [{}]
        returns a list of error/warning dictionaries
    """
    issue_list = []
    if check_for_issues:
        warnings = hed_schema.check_compliance(name=name)
        issue_list += warnings

    if save_as_mediawiki:
        output_string = hed_schema.get_as_mediawiki_string()
    else:
        output_string = hed_schema.get_as_xml_string(save_as_legacy_xml)

    return output_string, issue_list
