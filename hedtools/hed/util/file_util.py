"""General functions for writing out our content to files and other file manipulation"""

import tempfile
import os
import urllib.request
from xml.dom import minidom
from xml.etree import ElementTree

NO_VERSION_INFO_STRING = "No version info found"


def delete_file_if_it_exists(file_path):
    """Deletes a other if it exist.

    Parameters
    ----------
    file_path: str
        The path the file.

    Returns
    -------
    bool
        True if the file exists and was deleted.
    """
    if file_path is None:
        return False

    if os.path.isfile(file_path):
        os.remove(file_path)
        return True
    return False


def get_file_extension(file_name_or_path):
    """Get the other extension from the specified filename. This can be the full path or just the name.

       Parameters
       ----------
       file_name_or_path: str
           The name or full path of a file.

       Returns
       -------
       str
           The extension of the other.
       """
    return os.path.splitext(file_name_or_path)[1]


def get_version_from_xml(hed_xml_tree):
    """Gets version info from root node if present

       Parameters
       ----------
       hed_xml_tree: Element
           The root node of an XML tree.

       Returns
       -------
       str
           The version of the HED schema.

    """

    if hed_xml_tree is None:
        return NO_VERSION_INFO_STRING

    try:
        return hed_xml_tree.attrib['version']
    except KeyError or AttributeError:
        return NO_VERSION_INFO_STRING


def url_to_file(resource_url):
    """Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters
    ----------
    resource_url: str
        The URL to the resource.

    Returns
    -------
    str
        The local temporary filename for downloaded file
    """
    url_request = urllib.request.urlopen(resource_url)
    suffix = get_file_extension(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)
        return opened_file.name


def url_to_string(resource_url):
    """Get the data from the specified url as a string

    Parameters
    ----------
    resource_url: str
        The URL to the resource.

    Returns
    -------
    str
       The data at the target url
    """
    url_request = urllib.request.urlopen(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    return url_data


def write_errors_to_file(issues, extension=".txt"):
    """
    Writes an array of issue dictionaries to a temporary file.

    Parameters
    ----------
    issues: list
        List of 2-element dictionaries containing code and message keys.
    extension: str
        Desired file extension.

    Returns
    -------
    str
        The name of the temporary file
    """
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as error_file:
        for line in issues:
            error_file.write(f"{line['code']}: {line['message']}\n")
        return error_file.name


def write_strings_to_file(output_strings, extension=None):
    """
    Writes a list of output strings to a temporary file and returns the open file.

    Parameters
    ----------
    output_strings: [str] or str
        List of strings to output one per line.
    extension: str
        Desired file extension.

    Returns
    -------
        file
            Opened temporary file


    """
    if isinstance(output_strings, str):
        output_strings = [output_strings]
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w', encoding='utf-8') as opened_file:
        for string in output_strings:
            opened_file.write(string)
            opened_file.write('\n')
        return opened_file.name


def write_text_iter_to_file(text_iter, extension=".txt"):
    """
    Writes a text file based on an iterator.

    Parameters
    ----------
    text_iter: text iterator
        Iterates over values and writes to temporary file one per line.  Adds newlines.
    extension: str
        Desired file extension.

    Returns
    -------
        str
            Name of the temporary file.
    """
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as hed_xml_file:
        for line in text_iter:
            hed_xml_file.write(f"{line}\n")
        return hed_xml_file.name


def write_xml_tree_2_xml_file(xml_tree, extension=".xml"):
    """Writes a XML element tree object into a XML file.

    Parameters
    ----------
    xml_tree: Element
        A element representing an XML file.
    extension: string
        The file extension to use for temporary file.

    Returns
    -------

    """
    with tempfile.NamedTemporaryFile(suffix=extension, mode='w', delete=False, encoding='utf-8') as hed_xml_file:
        xml_string = _xml_element_2_str(xml_tree)
        hed_xml_file.write(xml_string)
        return hed_xml_file.name


def _xml_element_2_str(elem):
    """Converts an XML element to an XML string.

    Parameters
    ----------
    elem: Element
        An XML element.

    Returns
    -------
    str
        A XML string representing the XML element.

    """
    rough_string = ElementTree.tostring(elem, method='xml')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="   ")
