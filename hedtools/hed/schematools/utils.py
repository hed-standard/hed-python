"""
This module contains utility functions used by either or both converters.
"""

import urllib.request
from xml.dom import minidom
from xml.etree import ElementTree as et
import tempfile
from hed.schematools import constants


def url_to_file(resource_url):
    """Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters
    ----------
    resource_url: string
        The URL to the resource.

    Returns
    -------
    string: The local temporary filename for downloaded file
    """
    url_request = urllib.request.urlopen(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)
        return opened_file.name

def write_strings_to_file(output_strings, extension=None):
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w', encoding='utf-8') as opened_file:
        for string in output_strings:
            opened_file.write(string)
            opened_file.write('\n')
        return opened_file.name




def xml_element_2_str(elem):
    """Converts an XML element to an XML string.

    Parameters
    ----------
    elem: Element
        An XML element.

    Returns
    -------
    string
        A XML string representing the XML element.

    """
    rough_string = et.tostring(elem, method='xml')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="   ")

def write_xml_tree_2_xml_file(xml_tree, extension=".xml"):
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
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as hed_xml_file:
        xml_string = xml_element_2_str(xml_tree)
        hed_xml_file.write(xml_string)
        return hed_xml_file.name

def write_text_iter_to_file(iter, extension=".txt"):
    """Writes a text file based on an iterator.

    Parameters
    ----------
    iter: text iterator
        Iterates over the lines you wish to write to a file.  Adds newlines.
    extension: string
        Desired file extension.

    Returns
    -------

    """
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as hed_xml_file:
        for line in iter:
            hed_xml_file.write(f"{line}\n")
        return hed_xml_file.name

def get_version_from_xml(hed_xml_tree):
    """Gets version info from root node if present"""
    if hed_xml_tree is None:
        return constants.NO_VERSION_INFO_STRING

    try:
        return hed_xml_tree.attrib['version']
    except KeyError or AttributeError:
        return constants.NO_VERSION_INFO_STRING
