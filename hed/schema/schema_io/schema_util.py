""" Utilities for writing content to files and for other file manipulation."""

import tempfile
import os
import urllib.request
from xml.dom import minidom
from xml.etree import ElementTree

# you can fill this in locally if you don't want to add it to environ.
github_api_access_token = ""


def get_api_key():
    """
        Tries to get the GitHub access token from the environment.  Defaults to above value if not found.

    Returns:
        A GitHub access key or an empty string.
    """
    try:
        return os.environ["HED_GITHUB_TOKEN"]
    except KeyError:
        return github_api_access_token


def make_url_request(resource_url, try_authenticate=True):
    """ Make a request and adds the above GitHub access credentials.

    Parameters:
        resource_url (str): The url to retrieve.
        try_authenticate (bool): If true add the above credentials.

    Returns:
        url_request

    """
    request = urllib.request.Request(resource_url)
    if try_authenticate and get_api_key():
        request.add_header('Authorization', 'token %s' % get_api_key())
    return urllib.request.urlopen(request)


def url_to_file(resource_url):
    """ Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters:
        resource_url (str): The URL to the resource.

    Returns:
        str: The local temporary filename for the downloaded file,
    """
    url_request = make_url_request(resource_url)
    suffix = os.path.splitext(resource_url)[1]
    url_data = str(url_request.read(), 'utf-8')
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, mode='w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)
        return opened_file.name


def url_to_string(resource_url):
    """ Get the data from the specified url as a string.

    Parameters:
        resource_url (str): The URL to the resource.

    Returns:
        str: The data at the target url.
    """
    url_request = make_url_request(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    return url_data


def xml_element_2_str(elem):
    """ Convert an XML element to an XML string.

    Parameters:
        elem (Element):  An XML element.

    Returns:
        str: An XML string representing the XML element.

    """
    rough_string = ElementTree.tostring(elem, method='xml')
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="   ")
