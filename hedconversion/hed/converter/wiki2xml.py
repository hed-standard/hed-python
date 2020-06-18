"""
This module contains functions that convert a wiki HED schema into a XML HED schema.
"""

import urllib.request
from hed.converter import parsewiki
import tempfile

HED_XML_TREE_KEY = 'hed_xml_tree'
HED_XML_VERSION_KEY = 'version'
HED_CHANGE_LOG_KEY = 'hed_change_log'
HED_WIKI_PAGE_KEY = 'HED_WIKI_PAGE'
HED_XML_LOCATION_KEY = 'hed_xml_file_location'
HED_WIKI_LOCATION_KEY = 'hed_wiki_file_location'


def url_to_file(resource_url, file_path):
    """Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters
    ----------
    resource_url: string
        The URL to the resource.
    file_path: string
        A file path

    Returns
    -------
    """
    url_request = urllib.request.urlopen(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    with open(file_path, 'w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)


def download_hed_wiki(wiki_file_path, hed_wiki_url):
    """Downloads the HED wiki from github into a specified file.

    Parameters
    ----------
    wiki_file_path: string
        The file path where the wiki file is stored locally

    hed_wiki_url: string
        The URL to the .mediawiki file containing the spec.

    Returns
    -------
    string
        The tag line with the nowiki tag remove.
    """
    url_to_file(hed_wiki_url, wiki_file_path)
    return wiki_file_path


def write_xml_tree_2_xml_file(xml_tree, xml_file_path):
    """Writes a XML element tree object into a XML file.

    Parameters
    ----------
    xml_tree: Element
        A element representing an XML file.
    xml_file_path: string
        The path to an XML file.

    Returns
    -------

    """
    with open(xml_file_path, 'w', encoding='utf-8') as xml_file:
        xml_string = parsewiki.xml_element_2_str(xml_tree)
        xml_file.write(xml_string)


def convert_hed_wiki_2_xml(hed_wiki_url, use_local_wiki_file=None):
    """Converts the HED wiki into a XML file.

    Parameters
    ----------

    Returns
    -------
    dictionary
        The tag line with the nowiki tag remove.
    """
    if use_local_wiki_file is None:
        hed_wiki_file_location = create_hed_wiki_file(hed_wiki_url)
    else:
        hed_wiki_file_location = use_local_wiki_file

    hed_xml_file_location, hed_xml_tree = create_hed_xml_file(hed_wiki_file_location)
    hed_change_log = parsewiki.get_hed_change_log(hed_wiki_file_location)
    hed_info_dictionary = {HED_XML_TREE_KEY: hed_xml_tree,
                           HED_CHANGE_LOG_KEY: hed_change_log,
                           HED_WIKI_LOCATION_KEY: hed_wiki_file_location,
                           HED_XML_LOCATION_KEY: hed_xml_file_location}
    return hed_info_dictionary


def create_hed_xml_file(hed_wiki_file_path):
    """Creates a HED XML file from a HED wiki.

    Parameters
    ----------
    hed_wiki_file_path: string
        The path to the HED wiki file.

    Returns
    -------
    tuple
        A tuple containing the path to the HED XML file and a HED XML tree.
    """
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as hed_xml_file:
        hed_xml_file_location = hed_xml_file.name
        hed_xml_tree = parsewiki.hed_wiki_2_xml_tree(hed_wiki_file_path)
        xml_string = parsewiki.xml_element_2_str(hed_xml_tree)
        hed_xml_file.write(xml_string)
        return hed_xml_file_location, hed_xml_tree


def create_hed_wiki_file(hed_wiki_url):
    """Creates a HED wiki file from the github wiki.

    Parameters
    ----------

    Returns
    -------
    string
        The tag line with the nowiki tag remove.
    """
    with tempfile.NamedTemporaryFile(delete=False) as hed_wiki_file:
        hed_wiki_file_location = hed_wiki_file.name
        download_hed_wiki(hed_wiki_file_location, hed_wiki_url)
        return hed_wiki_file_location
