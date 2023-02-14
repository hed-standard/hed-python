"""Infrastructure for caching HED schema from remote repositories."""

import shutil
import os

import json
from hashlib import sha1
from shutil import copyfile
import re
from semantic_version import Version
import portalocker
import time
from hed.schema.schema_io.schema_util import url_to_file, make_url_request
from pathlib import Path

# From https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
HED_VERSION_P1 = r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
HED_VERSION_P2 = r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)" \
                 r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
HED_VERSION_P3 = r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
HED_VERSION = HED_VERSION_P1 + HED_VERSION_P2 + HED_VERSION_P3
# Actual local hed filename re.
HED_VERSION_FINAL = r'^[hH][eE][dD](_([a-z0-9]+)_)?(' + HED_VERSION + r')\.[xX][mM][lL]$'

HED_XML_PREFIX = 'HED'
HED_XML_EXTENSION = '.xml'
hedxml_suffix = "/hedxml"  # The suffix for schema and library schema at the given urls

DEFAULT_HED_LIST_VERSIONS_URL = "https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema/hedxml"
LIBRARY_HED_URL = "https://api.github.com/repos/hed-standard/hed-schemas/contents/library_schemas"
DEFAULT_URL_LIST = (DEFAULT_HED_LIST_VERSIONS_URL, LIBRARY_HED_URL, )

DEFAULT_SKIP_FOLDERS = ('deprecated', )

HED_CACHE_DIRECTORY = os.path.join(Path.home(), '.hedtools/hed_cache/')
TIMESTAMP_FILENAME = "last_update.txt"
CACHE_TIME_THRESHOLD = 300 * 6

# This is the schemas included in the hedtools package.
INSTALLED_CACHE_LOCATION = os.path.realpath(os.path.join(os.path.dirname(__file__), 'schema_data/'))
version_pattern = re.compile(HED_VERSION_FINAL)


def set_cache_directory(new_cache_dir):
    """ Set default global hed cache directory.

    Parameters:
        new_cache_dir (str): Directory to check for versions.

    """
    if new_cache_dir:
        global HED_CACHE_DIRECTORY
        HED_CACHE_DIRECTORY = new_cache_dir
        os.makedirs(new_cache_dir, exist_ok=True)


def get_cache_directory():
    """ Return the current value of HED_CACHE_DIRECTORY. """
    return HED_CACHE_DIRECTORY


def get_hed_versions(local_hed_directory=None, library_name=None, get_libraries=False):
    """ Get the HED versions in the hed directory.

    Parameters:
        local_hed_directory (str): Directory to check for versions which defaults to hed_cache.
        library_name (str or None): An optional schema library name.
        get_libraries (bool): If true, return a dictionary of version numbers, with an entry for each library name.

    Returns:
        list or dict: List of version numbers or dictionary {library_name: [versions]}.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    if not library_name:
        library_name = None

    all_hed_versions = {}
    local_directory = local_hed_directory
    try:
        hed_files = os.listdir(local_directory)
    except FileNotFoundError:
        hed_files = []
    for hed_file in hed_files:
        expression_match = version_pattern.match(hed_file)
        if expression_match is not None:
            version = expression_match.group(3)
            found_library_name = expression_match.group(2)
            if found_library_name != library_name:
                continue
            if found_library_name not in all_hed_versions:
                all_hed_versions[found_library_name] = []
            all_hed_versions[found_library_name].append(version)
    for name, hed_versions in all_hed_versions.items():
        all_hed_versions[name] = _sort_version_list(hed_versions)
    if get_libraries:
        return all_hed_versions
    if library_name in all_hed_versions:
        return all_hed_versions[library_name]
    return []


def cache_specific_url(hed_xml_url, xml_version=None, library_name=None, cache_folder=None):
    """ Cache a file from a URL.

    Parameters:
        hed_xml_url (str): Path to an exact file at a URL, or a GitHub API url to a directory.
        xml_version (str): If not None and hed_xml_url is a directory, return this version or None.
        library_name (str or None): Optional schema library name.
        cache_folder (str): The path of the hed cache. Defaults to HED_CACHE_DIRECTORY.

    Returns:
        str: Path to local hed XML file to use.

    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    if not _check_if_url(hed_xml_url):
        return None

    if _check_if_api_url(hed_xml_url):
        return _download_latest_hed_xml_version_from_url(hed_xml_url,
                                                         xml_version=xml_version,
                                                         library_name=library_name,
                                                         cache_folder=cache_folder)

    if not _check_if_specific_xml(hed_xml_url):
        return None

    filename = hed_xml_url.split('/')[-1]
    cache_filename = os.path.join(cache_folder, filename)

    return _cache_specific_url(hed_xml_url, cache_filename)


def _cache_specific_url(hed_xml_url, cache_filename):
    cache_folder = cache_filename.rpartition("/")[0]
    os.makedirs(cache_folder, exist_ok=True)
    temp_hed_xml_file = url_to_file(hed_xml_url)
    if temp_hed_xml_file:
        cache_filename = _safe_move_tmp_to_folder(temp_hed_xml_file, cache_filename)
        os.remove(temp_hed_xml_file)
        return cache_filename
    return None


def get_hed_version_path(xml_version=None, library_name=None, local_hed_directory=None):
    """ Get latest HED XML file path in a directory.  Only returns filenames that exist.

    Parameters:
        library_name (str or None): Optional the schema library name.
        xml_version (str or None): If not None, return this version or None.
        local_hed_directory (str): Path to local hed directory.  Defaults to HED_CACHE_DIRECTORY

    Returns:
        str: The path to the latest HED version the hed directory.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    hed_versions = get_hed_versions(local_hed_directory, library_name)
    if not hed_versions:
        return None
    if xml_version:
        if xml_version in hed_versions:
            latest_hed_version = xml_version
        else:
            return None
    else:
        latest_hed_version = _get_latest_semantic_version_in_list(hed_versions)
    return _create_xml_filename(latest_hed_version, library_name, local_hed_directory)


def get_path_from_hed_version(hed_version, library_name=None, local_hed_directory=None):
    """ Return the HED XML file path for a version.

    Parameters:
        hed_version (str): The HED version that is in the hed directory.
        library_name (str or None): An optional schema library name.
        local_hed_directory (str): The local hed path to use.

    Returns:
        str: The HED XML file path in the hed directory that corresponds to the hed version specified.

    Notes:
        - Note if no local directory is given, it defaults to HED_CACHE_DIRECTORY.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY
    return _create_xml_filename(hed_version, library_name, local_hed_directory)


def _copy_installed_schemas_to_cache(cache_folder):
    installed_files = os.listdir(INSTALLED_CACHE_LOCATION)
    for install_name in installed_files:
        _, basename = os.path.split(install_name)
        cache_name = os.path.join(cache_folder, basename)
        install_name = os.path.join(INSTALLED_CACHE_LOCATION, basename)
        if not os.path.exists(cache_name):
            shutil.copy(install_name, cache_name)


def cache_local_versions(cache_folder):
    """ Cache all schemas included with the hed installation.

    Parameters:
        cache_folder (str): The folder holding the cache.

    Returns:
        int or None: Returns -1 on cache access failure.  None otherwise

    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY
    os.makedirs(cache_folder, exist_ok=True)

    try:
        cache_lock_filename = os.path.join(cache_folder, "cache_lock.lock")
        with portalocker.Lock(cache_lock_filename, timeout=1):
            _copy_installed_schemas_to_cache(cache_folder)
    except portalocker.exceptions.LockException:
        return -1


def cache_xml_versions(hed_base_urls=DEFAULT_URL_LIST, skip_folders=DEFAULT_SKIP_FOLDERS, cache_folder=None):
    """ Cache all schemas at the given URLs.

    Parameters:
        hed_base_urls (str or list): Path or list of paths.
        skip_folders (list): A list of subfolders to skip over when downloading.
        cache_folder (str): The folder holding the cache.

    Returns:
        float: Returns -1 if cache failed, a positive number meaning time in seconds since last update
            if it didn't cache, 0 if it cached successfully this time.

    Notes:
        - The Default skip_folders is 'deprecated'.
        - The HED cache folder defaults to HED_CACHE_DIRECTORY.
        - The directories on Github are of the form:
            https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema/hedxml

    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    if not isinstance(hed_base_urls, (list, tuple)):
        hed_base_urls = [hed_base_urls]
    os.makedirs(cache_folder, exist_ok=True)
    last_timestamp = _read_last_cached_time(cache_folder)
    current_timestamp = time.time()
    time_since_update = current_timestamp - last_timestamp
    if time_since_update < CACHE_TIME_THRESHOLD:
        return time_since_update

    try:
        cache_lock_filename = os.path.join(cache_folder, "cache_lock.lock")
        with portalocker.Lock(cache_lock_filename, timeout=1):
            for hed_base_url in hed_base_urls:
                all_hed_versions = _get_hed_xml_versions_from_url(hed_base_url, skip_folders=skip_folders,
                                                                  get_libraries=True)
                for library_name, hed_versions in all_hed_versions.items():
                    for version, version_info in hed_versions.items():
                        _cache_hed_version(version, library_name, version_info, cache_folder=cache_folder)

            _write_last_cached_time(current_timestamp, cache_folder)
    except portalocker.exceptions.LockException:
        return -1

    return 0


def _read_last_cached_time(cache_folder):
    """ Check the given cache folder to see when it was last updated.

    Parameters:
        cache_folder (str): The folder we're caching hed schema in.

    Returns:
        float: The time we last updated the cache.  Zero if no update found.

    """
    timestamp_filename = os.path.join(cache_folder, TIMESTAMP_FILENAME)

    try:
        with open(timestamp_filename, "r") as f:
            timestamp = float(f.readline())
            return timestamp
    except FileNotFoundError or ValueError or IOError:
        return 0


def _write_last_cached_time(new_time, cache_folder):
    """ Set the time of last cache update.

    Parameters:
        new_time (float): The time this was updated.
        cache_folder (str): The folder used for caching the hed schema.

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


def _create_xml_filename(hed_xml_version, library_name=None, hed_directory=None):
    if library_name:
        hed_xml_basename = f"{HED_XML_PREFIX}_{library_name}_{hed_xml_version}{HED_XML_EXTENSION}"
    else:
        hed_xml_basename = HED_XML_PREFIX + hed_xml_version + HED_XML_EXTENSION

    if hed_directory:
        hed_xml_filename = os.path.join(hed_directory, hed_xml_basename)
        return hed_xml_filename
    return hed_xml_basename


def _sort_version_list(hed_versions):
    return sorted(hed_versions, key=Version, reverse=True)


def _get_hed_xml_versions_from_url(hed_base_url, library_name=None,
                                   skip_folders=DEFAULT_SKIP_FOLDERS, get_libraries=False):
    """ Get all available schemas and their hash values

    Parameters:
        hed_base_url (str): A single GitHub API url to cache
        library_name(str or None): If str, cache only the named library schemas
        skip_folders (list): A list of subfolders to skip over when downloading.
        get_libraries (bool): If true, return a dictionary of version numbers, with an entry for each library name.

    Returns:
        list or dict: List of version numbers or dictionary {library_name: [versions]}.

    Notes:
        - The Default skip_folders is 'deprecated'.
        - The HED cache folder defaults to HED_CACHE_DIRECTORY.
        - The directories on Github are of the form:
            https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema/hedxml
    """
    url_request = make_url_request(hed_base_url)
    url_data = str(url_request.read(), 'utf-8')
    loaded_json = json.loads(url_data)

    all_hed_versions = {}
    for file_entry in loaded_json:
        if file_entry['type'] == "dir":
            if hed_base_url.endswith(hedxml_suffix):
                continue
            if file_entry['name'] in skip_folders:
                continue
            sub_folder_versions = \
                _get_hed_xml_versions_from_url(hed_base_url + "/" + file_entry['name'] + hedxml_suffix,
                                               skip_folders=skip_folders, get_libraries=True)
            _merge_in_versions(all_hed_versions, sub_folder_versions)
        expression_match = version_pattern.match(file_entry["name"])
        if expression_match is not None:
            version = expression_match.group(3)
            found_library_name = expression_match.group(2)
            if not get_libraries and found_library_name != library_name:
                continue
            if found_library_name not in all_hed_versions:
                all_hed_versions[found_library_name] = {}
            all_hed_versions[found_library_name][version] = file_entry["sha"], file_entry["download_url"]

    ordered_versions = {}
    for hed_library_name, hed_versions in all_hed_versions.items():
        ordered_versions1 = _sort_version_list(hed_versions)
        ordered_versions2 = [(version, hed_versions[version]) for version in ordered_versions1]
        ordered_versions[hed_library_name] = dict(ordered_versions2)

    if get_libraries:
        return ordered_versions
    if library_name in ordered_versions:
        return ordered_versions[library_name]
    return {}


def _merge_in_versions(all_hed_versions, sub_folder_versions):
    for lib_name, hed_versions in sub_folder_versions.items():
        if lib_name not in all_hed_versions:
            all_hed_versions[lib_name] = {}
        all_hed_versions[lib_name].update(sub_folder_versions[lib_name])


def _download_latest_hed_xml_version_from_url(hed_base_url, xml_version, library_name, cache_folder):
    latest_version, version_info = _get_latest_hed_xml_version_from_url(hed_base_url, xml_version, library_name)
    if latest_version:
        cached_xml_file = _cache_hed_version(latest_version, library_name, version_info, cache_folder=cache_folder)
        return cached_xml_file


def _get_latest_hed_xml_version_from_url(hed_base_url, library_name=None, xml_version=None):
    hed_versions = _get_hed_xml_versions_from_url(hed_base_url, library_name=library_name)

    if not hed_versions:
        return None

    if xml_version and xml_version in hed_versions:
        return xml_version, hed_versions[xml_version]

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


def _safe_move_tmp_to_folder(temp_hed_xml_file, dest_filename):
    """ Copy to destination folder and rename.

    Parameters:
        temp_hed_xml_file (str): An XML file, generally from a temp folder.
        dest_filename (str): A destination folder and filename.

    Returns:
        dest_filename (str): The new filename on success or None on failure.

    """
    _, temp_xml_file = os.path.split(temp_hed_xml_file)
    dest_folder, _ = os.path.split(dest_filename)

    temp_filename_in_cache = os.path.join(dest_folder, temp_xml_file)
    copyfile(temp_hed_xml_file, temp_filename_in_cache)
    try:
        os.replace(temp_filename_in_cache, dest_filename)
    except OSError:
        os.remove(temp_filename_in_cache)
        return None

    return dest_filename


def _cache_hed_version(version, library_name, version_info, cache_folder):
    sha_hash, download_url = version_info

    possible_cache_filename = _create_xml_filename(version, library_name, cache_folder)
    local_sha_hash = _calculate_sha1(possible_cache_filename)

    if sha_hash == local_sha_hash:
        return possible_cache_filename

    return _cache_specific_url(download_url, possible_cache_filename)


def _get_latest_semantic_version_in_list(semantic_version_list):
    """ Get the latest semantic version in a list.

    Parameters:
        semantic_version_list (list): A list containing semantic versions.

    Returns:
        str: The latest semantic version in the list.

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
    """ Compare two semantic versions.

    Parameters:
        first_semantic_version (str): The first semantic version.
        second_semantic_version (str): The second semantic version.

    Returns:
        str: The later semantic version.

    """
    if Version(first_semantic_version) > Version(second_semantic_version):
        return first_semantic_version
    return second_semantic_version
