""" Utilities for writing content to files and for other file manipulation."""

import tempfile
import os
import urllib.request
from xml.dom import minidom
from xml.etree import ElementTree
from semantic_version import Version

from hed.errors import HedExceptions, ErrorContext

# you can fill this in locally if you don't want to add it to environ.
github_api_access_token = ""


def get_api_key():
    """
        Tries to get the GitHub access token from the environment.  Defaults to above value if not found.

    Returns:
        srt: A GitHub access key or an empty string.
    """
    try:
        return os.environ["HED_GITHUB_TOKEN"]
    except KeyError:
        return github_api_access_token


def make_url_request(resource_url, try_authenticate=True):
    """ Make a request and adds the above GitHub access credentials.

    Parameters:
        resource_url (str): The url to retrieve.
        try_authenticate (bool): If True add the above credentials.

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


def schema_version_greater_equal(hed_schema, target_version):
    """ Check if the given schema standard version is above target version

    Parameters:
        hed_schema (HedSchema or HedSchemaGroup): If a schema group, checks if any version is above.
        target_version (str): The semantic version to check against

    Returns:
        bool: True if the version is above target_version
              False if it is not, or it is ambiguous.
    """
    # Do exhaustive checks for now, assuming nothing
    schemas = [hed_schema.schema_for_namespace(schema_namespace) for schema_namespace in hed_schema.valid_prefixes]
    candidate_versions = [schema.with_standard for schema in schemas if schema.with_standard]
    if not candidate_versions:
        # Check for a standard schema(potentially, but unlikely, more than one)
        for schema in schemas:
            if schema.library == "":
                candidate_versions.append(schema.version_number)
    target_version = Version(target_version)
    for version in candidate_versions:
        if Version(version) >= target_version:
            return True

    return False


def format_error(row_number, row, warning_message="Schema term is empty or the line is malformed",
                 error_code=HedExceptions.GENERIC_ERROR):
    error = {'code': error_code,
             ErrorContext.ROW: row_number,
             ErrorContext.LINE: str(row),
             "message": f"{warning_message}"
             }

    return [error]
