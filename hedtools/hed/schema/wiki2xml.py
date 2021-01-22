"""
This module contains functions that convert a wiki HED schema into a XML HED schema.
"""
from hed.util import file_util
from hed.schema import parsewiki
from hed.schema.schema_validator import validate_schema
from hed.util.exceptions import HedFileError


def convert_hed_wiki_2_xml(hed_wiki_url, local_wiki_file=None, check_for_issues=True,
                           display_filename=None):
    """Converts the HED wiki into a XML file.

    Parameters
    ----------
    hed_wiki_url: string or None
        url pointing to the .mediawiki file to use
    local_wiki_file: str or None
        local wiki file to use(overrides hed_wiki_url)
    check_for_issues : bool
        After conversion checks for warnings like capitalization or invalid characters.
    display_filename: str
        If present, it will display errors as coming from this filename instead of the actual source.
        Useful for temporary files and similar.
    Returns
    -------
    xml_filename: str
        Location of output XML file, None on complete failure
    issues_list: [{}]
        returns a list of error/warning dictionaries
    """
    if local_wiki_file is None:
        local_wiki_file = file_util.url_to_file(hed_wiki_url)

    try:
        hed_xml_file_location = _create_hed_xml_file(local_wiki_file, display_filename)
    except HedFileError as e:
        return None, e.format_error_message()

    issue_list = []
    if check_for_issues:
        warnings = validate_schema(hed_xml_file_location, display_filename=display_filename)
        issue_list += warnings

    return hed_xml_file_location, issue_list


def _create_hed_xml_file(hed_wiki_file_path, display_filename):
    """Creates a HED XML file from a HED wiki.

    Parameters
    ----------
    hed_wiki_file_path: string
        The path to the local HED wiki file.
    display_filename: str
        If present, it will display errors as coming from this filename instead of the actual source.
        Useful for temporary files and similar.

    Returns
    -------
    filename: str
        Path to hed XML file
    """
    hed_xml_tree = parsewiki.hed_wiki_2_xml_tree(hed_wiki_file_path, display_filename)
    hed_xml_file_location = file_util.write_xml_tree_2_xml_file(hed_xml_tree)
    return hed_xml_file_location
