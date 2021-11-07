import os
import urllib.request

import json
from hashlib import sha1
from shutil import copyfile
from collections import OrderedDict
import re
from semantic_version import Version
import portalocker
import time
from hed.util.file_util import url_to_file


# From https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
HED_VERSION_P1 = r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
HED_VERSION_P2 = r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)" \
                 r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
HED_VERSION_P3 = r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
# Actual local hed filename re.
HED_VERSION_FINAL = r'^[hH][eE][dD](' + HED_VERSION_P1 + HED_VERSION_P2 + HED_VERSION_P3 + r')\.[xX][mM][lL]$'

HED_XML_PREFIX = 'HED'
HED_XML_EXTENSION = '.xml'
DEFAULT_HED_LIST_VERSIONS_URL = """https://api.github.com/repos/hed-standard/hed-specification/contents/hedxml"""
DEPRECATED_URL_SUFFIX = "/deprecated"
EXTRA_HED_CACHE_URL_SUFFIX = [DEPRECATED_URL_SUFFIX]

HED_CACHE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../validator/hed_cache/')
TIMESTAMP_FILENAME = "last_update.txt"
CACHE_TIME_THRESHOLD = 300

version_pattern = re.compile(HED_VERSION_FINAL)


def set_cache_directory(new_cache_dir):
    """Set default global hed cache directory

    Parameters
    ----------
    new_cache_dir: str
        Directory to check for versions.

    """
    if new_cache_dir:
        global HED_CACHE_DIRECTORY
        HED_CACHE_DIRECTORY = new_cache_dir
        os.makedirs(new_cache_dir, exist_ok=True)


def get_all_hed_versions(local_hed_directory=None, include_deprecated=False):
    """Get all the HED versions in the hed directory.

    Parameters
    ----------
    local_hed_directory: str
        Directory to check for versions.  Defaults to hed_cache
    include_deprecated: bool
        If True, also return any schemas found in the deprecated folder
    Returns
    -------
    string
        A list of semantic version numbers

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY
    hed_versions = []
    suffixes = [""]
    if include_deprecated:
        suffixes += EXTRA_HED_CACHE_URL_SUFFIX
    for suffix in suffixes:
        local_directory = local_hed_directory + suffix
        try:
            hed_files = os.listdir(local_directory)
        except FileNotFoundError:
            hed_files = []
        for hed_file in hed_files:
            expression_match = version_pattern.match(hed_file)
            if expression_match is not None:
                hed_versions.append(expression_match.group(1))
    return _sort_version_list(hed_versions)


def cache_specific_url(hed_xml_url, xml_version_number=None, cache_folder=None):
    """Cache a file from a URL.

    Parameters
    ----------
    hed_xml_url: str
        Path to an exact file at a URL, or a github API url to a directory.
    xml_version_number: str
        If not None and hed_xml_url is a directory, return this version or None.
    cache_folder:
        hed cache folder: Defaults to HED_CACHE_DIRECTORY
    Returns
    -------
    str
        Path to local hed XML file to use.
    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    if not _check_if_url(hed_xml_url):
        return None

    if _check_if_api_url(hed_xml_url):
        return _download_latest_hed_xml_version_from_url(hed_xml_url,
                                                         xml_version_number=xml_version_number,
                                                         cache_folder=cache_folder)

    if not _check_if_specific_xml(hed_xml_url):
        return None

    filename = hed_xml_url.split('/')[-1]
    cache_filename = os.path.join(cache_folder, filename)

    os.makedirs(cache_folder, exist_ok=True)
    temp_hed_xml_file = url_to_file(hed_xml_url)
    if temp_hed_xml_file:
        cache_filename = _safe_copy_tmp_to_folder(temp_hed_xml_file, cache_filename)
        return cache_filename
    else:
        return None


def get_hed_version_path(local_hed_directory=None, xml_version_number=None, include_deprecated=True):
    """Get the latest HED XML file path in the hed directory.

    Parameters
    ----------
    local_hed_directory: str
        Path to local hed directory.  Defaults to HED_CACHE_DIRECTORY
    xml_version_number: str
        If not None, return this version or None.
    include_deprecated: bool
        If true, will also check deprecated folder for this version number.
    Returns
    -------
    str
        The path to the latest HED version the hed directory.
    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    hed_versions = get_all_hed_versions(local_hed_directory, include_deprecated=include_deprecated)
    if xml_version_number:
        if xml_version_number in hed_versions:
            latest_hed_version = xml_version_number
        else:
            return None
    else:
        latest_hed_version = _get_latest_semantic_version_in_list(hed_versions)
    return _create_xml_filename(latest_hed_version, local_hed_directory)


def get_path_from_hed_version(hed_version, local_hed_directory=None):
    """Gets the HED XML file path in the hed directory that corresponds to the hed version specified.

    Parameters
    ----------
    hed_version: str
         The HED version that is in the hed directory.
    local_hed_directory: str
        Local hed path.  Defaults to HED_CACHE_DIRECTORY
    Returns
    -------
    string
        The HED XML file path in the hed directory that corresponds to the hed version specified.
    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY
    return _create_xml_filename(hed_version, local_hed_directory)


def cache_all_hed_xml_versions(hed_base_url=DEFAULT_HED_LIST_VERSIONS_URL, cache_folder=None):
    """Cache a file from a URL.

    Parameters
    ----------
    hed_base_url: str
        Path to a directory on github API.
        eg: https://api.github.com/repos/hed-standard/hed-specification/contents/hedxml
    cache_folder:
        hed cache folder: Defaults to HED_CACHE_DIRECTORY
    Returns
    -------
    time_since_update: float
        -1 if cache failed
        positive number meaning time in seconds since last update if it didn't cache
        0 if it cached successfully this time
    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    os.makedirs(cache_folder, exist_ok=True)
    last_timestamp = _read_last_cached_time(cache_folder)
    current_timestamp = time.time()
    time_since_update = current_timestamp - last_timestamp
    if time_since_update < CACHE_TIME_THRESHOLD:
        return time_since_update

    try:
        cache_lock_filename = os.path.join(cache_folder, "cache_lock.lock")
        with portalocker.Lock(cache_lock_filename, timeout=1):
            suffixes = [""] + EXTRA_HED_CACHE_URL_SUFFIX
            for url_suffix in suffixes:
                hed_versions = _get_hed_xml_versions_from_url(hed_base_url + url_suffix)
                for version in hed_versions:
                    _cache_hed_version(version, hed_versions[version], cache_folder=cache_folder + url_suffix)

            _write_last_cached_time(current_timestamp, cache_folder)
    except portalocker.exceptions.LockException:
        return -1

    return 0


def _read_last_cached_time(cache_folder):
    """
    Checks the given cache folder to see when it was last updated.

    Parameters
    ----------
    cache_folder : str
        The folder we're caching hed schema in.

    Returns
    -------
    time_stamp: float
        The time we last updated the cache.  Zero if no update found.
    """
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)

    try:
        with open(timestamp_filename, "r") as f:
            timestamp = float(f.readline())
            return timestamp
    except FileNotFoundError or ValueError or IOError:
        return 0


def _write_last_cached_time(new_time, cache_folder):
    """
    Sets the given time as when we last updated cache_folder.

    Parameters
    ----------
    new_time : float
        The time this was updated
    cache_folder : str
        The folder we're caching hed schema in.
    """
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)
    try:
        with open(timestamp_filename, "w") as f:
            f.write(str(new_time))
    except Exception:
        raise ValueError("Error writing timestamp to hed cache")


def _check_if_specific_xml(hed_xml_or_url):
    return hed_xml_or_url.endswith(HED_XML_EXTENSION)


def _check_if_api_url(api_url):
    return api_url.startswith("http://api.github.com") or api_url.startswith("https://api.github.com")


def _check_if_url(hed_xml_or_url):
    if hed_xml_or_url.startswith("http://") or hed_xml_or_url.startswith("https://"):
        return True
    return False


def _create_xml_filename(hed_xml_version, hed_directory=None):
    hed_xml_basename = HED_XML_PREFIX + hed_xml_version + HED_XML_EXTENSION
    suffixes = [""] + EXTRA_HED_CACHE_URL_SUFFIX

    if hed_directory:
        for suffix in suffixes:
            hed_xml_filename = os.path.join(hed_directory + suffix, hed_xml_basename)
            if os.path.exists(hed_xml_filename):
                return hed_xml_filename
        return os.path.join(hed_directory, hed_xml_basename)
    return hed_xml_basename


def _sort_version_list(hed_versions):
    return sorted(hed_versions, key=Version, reverse=True)


def _get_hed_xml_versions_from_url(hed_base_url=DEFAULT_HED_LIST_VERSIONS_URL):
    url_request = urllib.request.urlopen(hed_base_url)
    url_data = str(url_request.read(), 'utf-8')
    loaded_json = json.loads(url_data)

    hed_versions = {}
    for file_entry in loaded_json:
        expression_match = version_pattern.match(file_entry["name"])
        if expression_match is not None:
            hed_versions[expression_match.group(1)] = file_entry["sha"], file_entry["download_url"]

    ordered_versions1 = _sort_version_list(hed_versions)
    ordered_versions2 = [(version, hed_versions[version]) for version in ordered_versions1]
    ordered_versions = OrderedDict(ordered_versions2)

    return ordered_versions


def _download_latest_hed_xml_version_from_url(hed_base_url, xml_version_number, cache_folder):
    latest_version, version_info = _get_latest_hed_xml_version_from_url(hed_base_url, xml_version_number)
    if latest_version:
        cached_xml_file = _cache_hed_version(latest_version, version_info, cache_folder=cache_folder)
        return cached_xml_file


def _get_latest_hed_xml_version_from_url(hed_base_url, xml_version_number=None):
    hed_versions = _get_hed_xml_versions_from_url(hed_base_url)

    if not hed_versions:
        return None

    if xml_version_number and xml_version_number in hed_versions:
        return xml_version_number, hed_versions[xml_version_number]

    for version in hed_versions:
        return version, hed_versions[version]


def _calculate_sha1(filename):
    try:
        with open(filename, 'rb') as f:
            data = f.read()
            githash = sha1()
            githash.update(f"blob {len(data)}\0".encode('utf-8'))
            githash.update(data)
            return githash.hexdigest()
    except FileNotFoundError:
        return None


def _safe_copy_tmp_to_folder(temp_hed_xml_file, dest_filename):
    """
    Copies the schema file to destination folder, and renames it.

    Parameters
    ----------
    temp_hed_xml_file : str
        An XML file, generally from a temp folder.  Will be deleted on a successful copy.
    dest_filename : str
        A destination folder and filename
    Returns
    -------
    dest_filename: str
        Returns the new filename on success, returns None on failure.
    """
    _, temp_xml_file = os.path.split(temp_hed_xml_file)
    dest_folder, _ = os.path.split(dest_filename)

    temp_filename_in_cache = os.path.join(dest_folder, temp_xml_file)
    copyfile(temp_hed_xml_file, temp_filename_in_cache)
    os.remove(temp_hed_xml_file)
    try:
        os.replace(temp_filename_in_cache, dest_filename)
    except Exception:
        os.remove(temp_filename_in_cache)
        return None

    return dest_filename


def _cache_hed_version(version, version_info, cache_folder):
    sha_hash, download_url = version_info

    possible_cache_filename = _create_xml_filename(version, cache_folder)
    local_sha_hash = _calculate_sha1(possible_cache_filename)

    if sha_hash == local_sha_hash:
        return possible_cache_filename

    os.makedirs(cache_folder, exist_ok=True)
    temp_hed_xml_file = url_to_file(download_url)
    if temp_hed_xml_file:
        cache_filename = _safe_copy_tmp_to_folder(temp_hed_xml_file, possible_cache_filename)
        return cache_filename
    else:
        return None


def _get_latest_semantic_version_in_list(semantic_version_list):
    """Gets the latest semantic version in a list.

    Parameters
    ----------
    semantic_version_list: [str]
         A list containing semantic versions.
    Returns
    -------
    str
        The latest semantic version in the list.

    """
    if not semantic_version_list:
        return ''
    latest_semantic_version = semantic_version_list[0]
    if len(semantic_version_list) > 1:
        for semantic_version in semantic_version_list[1:]:
            latest_semantic_version = _compare_semantic_versions(latest_semantic_version,
                                                                 semantic_version)
    return latest_semantic_version


def _compare_semantic_versions(first_semantic_version, second_semantic_version):
    """Compares two semantic versions.

    Parameters
    ----------
    first_semantic_version: str
         The first semantic version.
    second_semantic_version: str
         The second semantic version.
    Returns
    -------
    string
        The later semantic version.

    """
    if Version(first_semantic_version) > Version(second_semantic_version):
        return first_semantic_version
    return second_semantic_version
