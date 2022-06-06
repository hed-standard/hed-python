""" Utilities for writing content to files and for other file manipulation."""

import tempfile
import os
import urllib.request
from xml.dom import minidom
from xml.etree import ElementTree

NO_VERSION_INFO_STRING = "No version info found"


def get_version_from_xml(hed_xml_tree):
    """Get version from root node of an XML tree.

        Args:
            hed_xml_tree (Element):  The root node of an XML tree.

        Returns:
            str: The version of the HED schema (e.g. "8.0.0").

        Raises:
            KeyError or AttributeError: If invalid.

        TODO: This should be moved to the schema module

    """

    if hed_xml_tree is None:
        return NO_VERSION_INFO_STRING

    try:
        return hed_xml_tree.attrib['version']
    except KeyError or AttributeError:
        return NO_VERSION_INFO_STRING


def url_to_file(resource_url):
    """ Write data from a URL resource into a file. Data is decoded as unicode.

    Args:
        resource_url (str): The URL to the resource.

    Returns:
        str: The local temporary filename for the downloaded file,
    """
    url_request = urllib.request.urlopen(resource_url)
    suffix = os.path.splitext(resource_url)[1]
    url_data = str(url_request.read(), 'utf-8')
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)
        return opened_file.name


def url_to_string(resource_url):
    """ Get the data from the specified url as a string.

    Args:
        resource_url (str): The URL to the resource.

    Returns:
        str: The data at the target url.
    """
    url_request = urllib.request.urlopen(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    return url_data


def write_errors_to_file(issues, extension=".txt"):
    """ Write an array of issue dictionaries to a temporary file.

    Args:
        issues (list):    List of 2-element dictionaries containing code and message keys.
        extension (str):  Desired file extension.

    Returns:
        str: The name of the temporary file.
    """
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as error_file:
        for line in issues:
            error_file.write(f"{line['code']}: {line['message']}\n")
        return error_file.name


def write_strings_to_file(output_strings, extension=None):
    """ Write output strings to a temporary file.

    Args:
        output_strings ([str], str):  Strings to output one per line.
        extension (str):              File extension of the temporary file.

    Returns:
        file: Opened temporary file.

    """
    if isinstance(output_strings, str):
        output_strings = [output_strings]
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w', encoding='utf-8') as opened_file:
        for string in output_strings:
            opened_file.write(string)
            opened_file.write('\n')
        return opened_file.name


def write_xml_tree_2_xml_file(xml_tree, extension=".xml"):
    """ Write an XML element tree object into a XML file.

    Args:
        xml_tree (Element):  An element representing an XML file.
        extension (string):  The file extension to use for the temporary file.

    Returns:
        str:  Name of the temporary file.

    TODO:  Should this be in the schema module?

    """
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as hed_xml_file:
        xml_string = _xml_element_2_str(xml_tree)
        hed_xml_file.write(xml_string)
        return hed_xml_file.name


def _xml_element_2_str(elem):
    """ Convert an XML element to an XML string.

    Args:
        elem (Element):  An XML element.

    Returns:
        str: An XML string representing the XML element.

    TODO: Shouldn't this be with the schema?

    """
    rough_string = ElementTree.tostring(elem, method='xml')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="   ")
