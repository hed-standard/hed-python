from hed.schema.xml2schema import HedSchemaXMLParser
from hed.schema.wiki2schema import HedSchemaWikiParser
from hed.util.exceptions import HedFileError, HedExceptions
from hed.schema import hed_schema_constants
from hed.util import file_util


def load_schema(hed_file_path):
    if not hed_file_path:
        raise HedFileError(HedExceptions.FILE_NOT_FOUND, "Empty file path passed to HedSchema.load_file",
                           filename=hed_file_path)

    if hed_file_path.lower().endswith(".xml"):
        hed_schema = HedSchemaXMLParser.load_xml(hed_file_path)
        return hed_schema
    elif hed_file_path.lower().endswith(".mediawiki"):
        hed_schema = HedSchemaWikiParser.load_wiki(hed_file_path)
        return hed_schema
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=hed_file_path)


def from_string(schema_string, file_type=".xml"):
    if not schema_string:
        raise HedFileError(HedExceptions.BAD_PARAMETERS, "Empty string passed to HedSchema.from_string",
                           filename=schema_string)

    if file_type.endswith(".xml"):
        hed_schema = HedSchemaXMLParser.load_xml(schema_as_string=schema_string)
        return hed_schema
    elif file_type.endswith(".mediawiki"):
        hed_schema = HedSchemaWikiParser.load_wiki(schema_as_string=schema_string)
        return hed_schema
    else:
        raise HedFileError(HedExceptions.INVALID_EXTENSION, "Unknown schema extension", filename=file_type)


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


def convert_schema_to_format(hed_url=None, local_hed_file=None, check_for_issues=True,
                             display_filename=None, save_as_mediawiki=False, save_as_legacy_xml=False):
    """
    Loads a local schema file or from a URL, then outputs a temporary file with the requested format.

    Parameters
    ----------
    hed_url: str or None
        url pointing to the .xml/mediawiki file to use
    local_hed_file: str or None
        filepath to local xml/mediawiki hed schema(overrides hed_url)
    check_for_issues : bool
        After conversion checks for warnings like capitalization or invalid characters.
    display_filename: str
        If present, will use this as the filename for context, rather than using the actual filename
        Useful for temp filenames.
    save_as_mediawiki: bool
        If True, save as .mediawiki.  if False, save as .xml
    save_as_legacy_xml: bool
        If True(and save_as_mediawiki is False), will save using the old legacy XML format.

    Returns
    -------
    output_filename: str
        Location of output converted file, None on complete failure
    issues_list: [{}]
        returns a list of error/warning dictionaries
    """
    if local_hed_file is None:
        local_hed_file = file_util.url_to_file(hed_url)

    hed_schema = load_schema(local_hed_file)

    issue_list = []
    if check_for_issues:
        warnings = hed_schema.check_compliance(display_filename=display_filename)
        issue_list += warnings

    if save_as_mediawiki:
        output_filename = hed_schema.save_as_mediawiki()
    else:
        output_filename = hed_schema.save_as_xml(save_as_legacy_xml)

    return output_filename, issue_list
