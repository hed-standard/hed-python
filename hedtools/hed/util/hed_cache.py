import os
import urllib.request
import tempfile
import json
from hashlib import sha1
from shutil import copyfile
from collections import OrderedDict
import re
from distutils.version import StrictVersion
import portalocker
import time

HED_VERSION_EXPRESSION = r'HED(\d+.\d+.\d+)'
HED_XML_PREFIX = 'HED'
HED_XML_EXTENSION = '.xml'
DEFAULT_HED_LIST_VERSIONS_URL = """https://api.github.com/repos/hed-standard/hed-specification/contents/hedxml"""
HED_CACHE_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../validator/hed_cache/')
TIMESTAMP_FILENAME = "last_update.txt"
CACHE_TIME_THRESHOLD = 300

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


def get_all_hed_versions(local_hed_directory=None):
    """Get all the HED versions in the hed directory.

    Parameters
    ----------
    local_hed_directory: str
        Directory to check for versions.  Defaults to hed_cache

    Returns
    -------
    string
        A list of semantic version numbers

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY
    hed_versions = []
    compiled_expression = re.compile(HED_VERSION_EXPRESSION)
    for _, _, hed_files in os.walk(local_hed_directory):
        for hed_file in hed_files:
            expression_match = compiled_expression.match(hed_file)
            if expression_match is not None:
                hed_versions.append(expression_match.group(1))
    return sorted(hed_versions, key=StrictVersion, reverse=True)


def get_local_file(hed_xml_file, get_specific_version=None):
    """Gets the requested local file from disk.  Defaults to hed cache if not specified.

    Parameters
    ----------
    hed_xml_file: str
        Path to exact XML file, or directory to check for versions.  Defaults to hed_cache if None
    get_specific_version: str
        If not None and hed_xml_file is a directory, return this version or None.
    Returns
    -------
    string
        Path to local hed XML file to use.
    """
    if hed_xml_file and _check_if_specific_xml(hed_xml_file):
        if get_specific_version is not None:
            raise ValueError("get_or_cache_file: Cannot specify version while asking for a specific xml file.")
        final_hed_xml_file = hed_xml_file
    else:
        if not hed_xml_file:
            hed_xml_file = HED_CACHE_DIRECTORY
        final_hed_xml_file = get_latest_hed_version_path(hed_xml_file, get_specific_version)

    return final_hed_xml_file


def cache_specific_url(hed_xml_url, get_specific_version=None, cache_folder=None):
    """Cache a file from a URL.

    Parameters
    ----------
    hed_xml_url: str
        Path to an exact file at a URL, or a github API url to a directory.
    get_specific_version: str
        If not None and hed_xml_url is a directory, return this version or None.
    cache_folder:
        hed cache folder: Defaults to HED_CACHE_DIRECTORY
    Returns
    -------
    string
        Path to local hed XML file to use.
    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    if not _check_if_url(hed_xml_url):
        return None

    if _check_if_api_url(hed_xml_url):
        return _download_latest_hed_xml_version_from_url(hed_xml_url, get_specific_version=get_specific_version, cache_folder=cache_folder)

    if not _check_if_specific_xml(hed_xml_url):
        return None

    filename = hed_xml_url.split('/')[-1]
    cache_filename = os.path.join(cache_folder, filename)

    os.makedirs(cache_folder, exist_ok=True)
    temp_hed_xml_file = _url_to_file(hed_xml_url)
    if temp_hed_xml_file:
        cache_filename = _safe_copy_tmp_to_folder(temp_hed_xml_file, cache_filename)
        return cache_filename
    else:
        return None


def get_latest_hed_version_path(local_hed_directory=None, get_specific_version=None):
    """Get the latest HED XML file path in the hed directory.

    Parameters
    ----------
    local_hed_directory: str
        Path to local hed directory.  Defaults to HED_CACHE_DIRECTORY
    get_specific_version: str
        If not None, return this version or None.
    Returns
    -------
    string
        The path to the latest HED version the hed directory.
    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    hed_versions = get_all_hed_versions(local_hed_directory)
    if get_specific_version:
        if get_specific_version in hed_versions:
            latest_hed_version = get_specific_version
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
    hed_xml_url: str
        Path to a directory on github API.
    cache_folder:
        hed cache folder: Defaults to HED_CACHE_DIRECTORY
    Returns
    -------
    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    os.makedirs(cache_folder, exist_ok=True)
    last_timestamp = _read_last_cached_time(cache_folder)
    current_timestamp = time.time()
    if current_timestamp - last_timestamp < CACHE_TIME_THRESHOLD:
        print(f"Skipped caching.  Cache updated {current_timestamp - last_timestamp:02f} seconds ago."
              f"(cache update interval: {CACHE_TIME_THRESHOLD}s)")
        return

    try:
        cache_lock_filename = os.path.join(cache_folder, "cache_lock.lock")
        with portalocker.Lock(cache_lock_filename, timeout=1) as cache_lock:
            hed_versions = _get_hed_xml_versions_from_url(hed_base_url)

            for version in hed_versions:
                _cache_hed_version(version, hed_versions[version], cache_folder=cache_folder)

            _write_last_cached_time(current_timestamp, cache_folder)
    except portalocker.exceptions.LockException:
        print(f"Cache currently being written to.  Skipping.")


def _read_last_cached_time(cache_folder):
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)

    try:
        with open(timestamp_filename, "r") as f:
            timestamp = float(f.readline())
            return timestamp
    except FileNotFoundError or ValueError or IOError:
        return 0


def _write_last_cached_time(new_time, cache_folder):
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)
    try:
        with open(timestamp_filename, "w") as f:
            f.write(str(new_time))
    except:
        raise ValueError("Error writing timestamp to hed cache")


def _check_if_specific_xml(hed_xml_or_url):
    return hed_xml_or_url.endswith(HED_XML_EXTENSION)


def _check_if_api_url(api_url):
    return api_url.startswith("http://api.github.com") or api_url.startswith("https://api.github.com")


def _check_if_url(hed_xml_or_url):
    if hed_xml_or_url.startswith("http://") or hed_xml_or_url.startswith("https://"):
        return True
    return False


def _url_to_file(resource_url):
    """Write data from a URL resource into a file. Data is decoded as unicode.

    Parameters
    ----------
    resource_url: string
        The URL to the resource.

    Returns
    -------
    string: The local temporary filename for downloaded file.  You are responsible for deleting this.
    """
    url_request = urllib.request.urlopen(resource_url)
    url_data = str(url_request.read(), 'utf-8')
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as opened_file:
        opened_file.write(url_data)
        return opened_file.name


def _create_xml_filename(hed_xml_version, hed_directory=None):
    hed_xml_filename = HED_XML_PREFIX + hed_xml_version + HED_XML_EXTENSION
    if hed_directory:
        hed_xml_filename = os.path.join(hed_directory, hed_xml_filename)
    return hed_xml_filename


def _get_hed_xml_versions_from_url(hed_base_url=DEFAULT_HED_LIST_VERSIONS_URL):
    url_request = urllib.request.urlopen(hed_base_url)
    url_data = str(url_request.read(), 'utf-8')
    loaded_json = json.loads(url_data)

    compiled_expression = re.compile(HED_VERSION_EXPRESSION)
    hed_versions = {}
    for file_entry in loaded_json:
        expression_match = compiled_expression.match(file_entry["name"])
        if expression_match is not None:
            hed_versions[expression_match.group(1)] = file_entry["sha"], file_entry["download_url"]

    ordered_versions1 = sorted(hed_versions, key=StrictVersion, reverse=True)
    ordered_versions2 = [(version, hed_versions[version]) for version in ordered_versions1]
    ordered_versions = OrderedDict(ordered_versions2)

    return ordered_versions


def _download_latest_hed_xml_version_from_url(hed_base_url, get_specific_version, cache_folder):
    latest_version, version_info = _get_latest_hed_xml_version_from_url(hed_base_url, get_specific_version)
    if latest_version:
        cached_xml_file = _cache_hed_version(latest_version, version_info, cache_folder=cache_folder)
        return cached_xml_file


def _get_latest_hed_xml_version_from_url(hed_base_url, get_specific_version=None):
    hed_versions = _get_hed_xml_versions_from_url(hed_base_url)

    if not hed_versions:
        return None

    if get_specific_version and get_specific_version in hed_versions:
        return get_specific_version, hed_versions[get_specific_version]

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


# Attempt to make this multithread safe.
def _safe_copy_tmp_to_folder(temp_hed_xml_file, dest_filename):
    _, temp_xml_file = os.path.split(temp_hed_xml_file)
    dest_folder, _ = os.path.split(dest_filename)

    temp_filename_in_cache = os.path.join(dest_folder, temp_xml_file)
    copyfile(temp_hed_xml_file, temp_filename_in_cache)
    os.remove(temp_hed_xml_file)
    try:
        os.replace(temp_filename_in_cache, dest_filename)
    except:
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
    temp_hed_xml_file = _url_to_file(download_url)
    if temp_hed_xml_file:
        cache_filename = _safe_copy_tmp_to_folder(temp_hed_xml_file, possible_cache_filename)
        return cache_filename
    else:
        return None


def _get_latest_semantic_version_in_list(semantic_version_list):
    """Gets the latest semantic version in a list.

    Parameters
    ----------
    semantic_version_list: list
         A list containing semantic versions.
    Returns
    -------
    string
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
    return first_semantic_version if StrictVersion(first_semantic_version) > StrictVersion(
        second_semantic_version) else second_semantic_version

