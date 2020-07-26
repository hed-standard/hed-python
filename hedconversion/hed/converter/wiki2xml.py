"""
This module contains functions that convert a wiki HED schema into a XML HED schema.
"""

from hed.converter import parsewiki
from hed.converter import utils
from hed.converter import constants

def convert_hed_wiki_2_xml(hed_wiki_url, local_wiki_file=None):
    """Converts the HED wiki into a XML file.

    Parameters
    ----------
        hed_wiki_url: string
            url pointing to the .mediawiki file to use
        use_local_wiki_file: string
            local wiki file to use(overrides hed_wiki_url)
    Returns
    -------
    dictionary
        Contains xml, wiki, and version info.
    """
    if local_wiki_file is None:
        local_wiki_file = utils.url_to_file(hed_wiki_url)

    hed_xml_file_location, hed_xml_tree = _create_hed_xml_file(local_wiki_file)
    hed_change_log = parsewiki.get_hed_change_log(local_wiki_file)
    hed_version = utils.get_version_from_xml(hed_xml_tree)
    hed_info_dictionary = {constants.HED_XML_TREE_KEY: hed_xml_tree,
                           constants.HED_XML_VERSION_KEY: hed_version,
                           constants.HED_CHANGE_LOG_KEY: hed_change_log,
                           constants.HED_WIKI_PAGE_KEY: hed_wiki_url,
                           constants.HED_INPUT_LOCATION_KEY: local_wiki_file,
                           constants.HED_OUTPUT_LOCATION_KEY: hed_xml_file_location}
    return hed_info_dictionary


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
    hed_xml_file_location = utils.write_xml_tree_2_xml_file(hed_xml_tree)
    return hed_xml_file_location, hed_xml_tree
