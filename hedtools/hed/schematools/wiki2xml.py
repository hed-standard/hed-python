"""
This module contains functions that convert a wiki HED schema into a XML HED schema.
"""
from hed.util import file_util
from hed.schematools import parsewiki


def convert_hed_wiki_2_xml(hed_wiki_url, local_wiki_file=None):
    """Converts the HED wiki into a XML file.

    Parameters
    ----------
        hed_wiki_url: string
            url pointing to the .mediawiki file to use
        local_wiki_file: string
            local wiki file to use(overrides hed_wiki_url)
    Returns
    -------
    dictionary
        Contains xml, wiki, and version info.
    """
    if local_wiki_file is None:
        local_wiki_file = file_util.url_to_file(hed_wiki_url)

    hed_xml_file_location = _create_hed_xml_file(local_wiki_file)

    # Placeholder
    errors = []
    return hed_xml_file_location, errors


def _create_hed_xml_file(hed_wiki_file_path):
    """Creates a HED XML file from a HED wiki.

    Parameters
    ----------
    hed_wiki_file_path: string
        The path to the local HED wiki file.

    Returns
    -------
    tuple
        A tuple containing the path to the HED XML file and a HED XML tree.
    """
    hed_xml_tree = parsewiki.hed_wiki_2_xml_tree(hed_wiki_file_path)
    hed_xml_file_location = file_util.write_xml_tree_2_xml_file(hed_xml_tree)
    return hed_xml_file_location
