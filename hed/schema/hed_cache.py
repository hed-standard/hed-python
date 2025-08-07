"""Infrastructure for caching HED schema from remote repositories."""
from __future__ import annotations

import shutil
import os

import json
from hashlib import sha1
from shutil import copyfile
import functools


import re
from typing import Union

from semantic_version import Version
from hed.schema.hed_cache_lock import CacheException, CacheLock
from hed.schema.schema_io.schema_util import url_to_file, make_url_request
from pathlib import Path
import urllib
from urllib.error import URLError

# From https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
HED_VERSION_P1 = r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
HED_VERSION_P2 = r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)" \
                 r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
HED_VERSION_P3 = r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
HED_VERSION = HED_VERSION_P1 + HED_VERSION_P2 + HED_VERSION_P3
# Actual local HED filename re.
HED_VERSION_FINAL = r'^[hH][eE][dD](_([a-z0-9]+)_)?(' + HED_VERSION + r')\.[xX][mM][lL]$'

HED_XML_PREFIX = 'HED'
HED_XML_EXTENSION = '.xml'
hedxml_suffix = "/hedxml"  # The suffix for schema and library schema at the given urls
prerelease_suffix = "/prerelease"  # The prerelease schemas at the given URLs

DEFAULT_HED_LIST_VERSIONS_URL = "https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema"
LIBRARY_HED_URL = "https://api.github.com/repos/hed-standard/hed-schemas/contents/library_schemas"
LIBRARY_DATA_URL = "https://raw.githubusercontent.com/hed-standard/hed-schemas/main/library_data.json"
DEFAULT_URL_LIST = (DEFAULT_HED_LIST_VERSIONS_URL,)
DEFAULT_LIBRARY_URL_LIST = (LIBRARY_HED_URL,)


DEFAULT_SKIP_FOLDERS = ('deprecated',)

HED_CACHE_DIRECTORY = os.path.join(Path.home(), '.hedtools/hed_cache/')

# This is the schemas included in the hedtools package.
INSTALLED_CACHE_LOCATION = os.path.realpath(os.path.join(os.path.dirname(__file__), 'schema_data/'))
version_pattern = re.compile(HED_VERSION_FINAL)


def set_cache_directory(new_cache_dir):
    """ Set default global HED cache directory.

    Parameters:
        new_cache_dir (str): Directory to check for versions.

    """
    if new_cache_dir:
        global HED_CACHE_DIRECTORY
        HED_CACHE_DIRECTORY = new_cache_dir
        os.makedirs(new_cache_dir, exist_ok=True)


def get_cache_directory(cache_folder=None) -> str:
    """ Return the current value of HED_CACHE_DIRECTORY.

    Parameters:
        cache_folder (str): Optional cache folder override.

    Returns:
        str: The cache directory path.
    """
    if cache_folder:
        return cache_folder
    return HED_CACHE_DIRECTORY


def get_hed_versions(local_hed_directory=None, library_name=None, check_prerelease=False) -> Union[list, dict]:
    """ Get the HED versions in the HED directory.

    Parameters:
        local_hed_directory (str): Directory to check for versions which defaults to hed_cache.
        library_name (str or None): An optional schema library name.
                                    None retrieves the standard schema only.
                                    Pass "all" to retrieve all standard and library schemas as a dict.
        check_prerelease (bool): If True, results can include prerelease schemas

    Returns:
        Union[list, dict]: List of version numbers or dictionary {library_name: [versions]}.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    if not library_name:
        library_name = None

    all_hed_versions = {}
    local_directories = [local_hed_directory]
    if check_prerelease and not local_hed_directory.endswith(prerelease_suffix):
        local_directories.append(os.path.join(local_hed_directory, "prerelease"))

    hed_files = []
    for hed_dir in local_directories:
        try:
            hed_files += os.listdir(hed_dir)
        except FileNotFoundError:
            pass
    if not hed_files:
        cache_local_versions(local_hed_directory)
        for hed_dir in local_directories:
            try:
                hed_files += os.listdir(hed_dir)
            except FileNotFoundError:
                pass
    for hed_file in hed_files:
        expression_match = version_pattern.match(hed_file)
        if expression_match is not None:
            version = expression_match.group(3)
            found_library_name = expression_match.group(2)
            if library_name != "all" and found_library_name != library_name:
                continue
            if found_library_name not in all_hed_versions:
                all_hed_versions[found_library_name] = []
            all_hed_versions[found_library_name].append(version)
    for name, hed_versions in all_hed_versions.items():
        all_hed_versions[name] = _sort_version_list(hed_versions)
    if library_name in all_hed_versions:
        return all_hed_versions[library_name]
    return all_hed_versions


def get_hed_version_path(xml_version, library_name=None, local_hed_directory=None, check_prerelease=False) -> Union[str, None]:
    """ Get HED XML file path in a directory.  Only returns filenames that exist.

    Parameters:
        library_name (str or None): Optional the schema library name.
        xml_version (str): Returns this version if it exists
        local_hed_directory (str): Path to local HED directory.  Defaults to HED_CACHE_DIRECTORY
        check_prerelease (bool): Also check for prerelease schemas

    Returns:
        Union[str, None]: The path to the latest HED version the HED directory.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    hed_versions = get_hed_versions(local_hed_directory, library_name, check_prerelease)
    if not hed_versions or not xml_version:
        return None
    if xml_version in hed_versions:
        return _create_xml_filename(xml_version, library_name, local_hed_directory, check_prerelease)
    return None


def cache_local_versions(cache_folder) -> Union[int, None]:
    """ Cache all schemas included with the HED installation.

    Parameters:
        cache_folder (str): The folder holding the cache.

    Returns:
        Union[int, None]: Returns -1 on cache access failure.  None otherwise

    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    try:
        with CacheLock(cache_folder, write_time=False):
            _copy_installed_folder_to_cache(cache_folder)
    except CacheException:
        return -1


def cache_xml_versions(hed_base_urls=DEFAULT_URL_LIST, hed_library_urls=DEFAULT_LIBRARY_URL_LIST,
                       skip_folders=DEFAULT_SKIP_FOLDERS, cache_folder=None) -> float:
    """ Cache all schemas at the given URLs.

    Parameters:
        hed_base_urls (str or list): Path or list of paths.   These should point to a single folder.
        hed_library_urls (str or list): Path or list of paths.  These should point to folder containing library folders.
        skip_folders (list): A list of subfolders to skip over when downloading.
        cache_folder (str): The folder holding the cache.

    Returns:
        float: Returns -1 if cache failed for any reason, including having been cached too recently.
               Returns 0 if it successfully cached this time.

    Notes:
        - The Default skip_folders is 'deprecated'.
        - The HED cache folder defaults to HED_CACHE_DIRECTORY.
        - The directories on GitHub are of the form:
            https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema

    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    try:
        with CacheLock(cache_folder):
            if isinstance(hed_base_urls, str):
                hed_base_urls = [hed_base_urls]
            if isinstance(hed_library_urls, str):
                hed_library_urls = [hed_library_urls]
            all_hed_versions = {}
            for hed_base_url in hed_base_urls:
                new_hed_versions = _get_hed_xml_versions_one_library(hed_base_url)
                _merge_in_versions(all_hed_versions, new_hed_versions)
            for hed_library_url in hed_library_urls:
                new_hed_versions = _get_hed_xml_versions_from_url_all_libraries(hed_library_url,
                                                                                skip_folders=skip_folders)
                _merge_in_versions(all_hed_versions, new_hed_versions)

            for library_name, hed_versions in all_hed_versions.items():
                for version, version_info in hed_versions.items():
                    _cache_hed_version(version, library_name, version_info, cache_folder=cache_folder)

    except CacheException or ValueError or URLError:
        return -1

    return 0


@functools.lru_cache(maxsize=50)
def get_library_data(library_name, cache_folder=None) -> dict:
    """Retrieve the library data for the given library.

       Currently, this is just the valid ID range.

       Parameters:
           library_name (str): The schema name.  "" for standard schema.
           cache_folder (str): The cache folder to use if not using the default.

       Returns:
           dict: The data for a specific library.
    """
    if cache_folder is None:
        cache_folder = HED_CACHE_DIRECTORY

    cache_lib_data_folder = os.path.join(cache_folder, "library_data")

    local_library_data_filename = os.path.join(cache_lib_data_folder, "library_data.json")
    try:
        with open(local_library_data_filename) as file:
            library_data = json.load(file)
        specific_library = library_data[library_name]
        return specific_library
    except (OSError, CacheException, ValueError, KeyError):
        pass

    try:
        with CacheLock(cache_lib_data_folder, write_time=False):
            _copy_installed_folder_to_cache(cache_lib_data_folder, "library_data")

        with open(local_library_data_filename) as file:
            library_data = json.load(file)
        specific_library = library_data[library_name]
        return specific_library
    except (OSError, CacheException, ValueError, KeyError):
        pass

    try:
        with CacheLock(cache_lib_data_folder):
            # if this fails it'll fail to load in the next step
            _cache_specific_url(LIBRARY_DATA_URL, local_library_data_filename)
        with open(local_library_data_filename) as file:
            library_data = json.load(file)
        specific_library = library_data[library_name]
        return specific_library
    except (OSError, CacheException, ValueError, URLError, KeyError):
        pass

    # This failed to get any data for some reason
    return {}


def _copy_installed_folder_to_cache(cache_folder, sub_folder=""):
    """Copies the schemas from the install folder to the cache"""
    source_folder = INSTALLED_CACHE_LOCATION
    if sub_folder:
        source_folder = os.path.join(INSTALLED_CACHE_LOCATION, sub_folder)

    installed_files = os.listdir(source_folder)
    for install_name in installed_files:
        _, basename = os.path.split(install_name)
        cache_name = os.path.join(cache_folder, basename)
        install_name = os.path.join(source_folder, basename)
        if not os.path.isdir(install_name) and not os.path.exists(cache_name):
            shutil.copy(install_name, cache_name)


def _check_if_url(hed_xml_or_url):
    """Returns true if this is a url"""
    if hed_xml_or_url.startswith("http://") or hed_xml_or_url.startswith("https://"):
        return True
    return False


def _create_xml_filename(hed_xml_version, library_name=None, hed_directory=None, prerelease=False):
    """Returns the default file name format for the given version"""
    prerelease_prefix = "prerelease/" if prerelease else ""
    if library_name:
        hed_xml_basename = f"{prerelease_prefix}{HED_XML_PREFIX}_{library_name}_{hed_xml_version}{HED_XML_EXTENSION}"
    else:
        hed_xml_basename = prerelease_prefix + HED_XML_PREFIX + hed_xml_version + HED_XML_EXTENSION

    if hed_directory:
        hed_xml_filename = os.path.join(hed_directory, hed_xml_basename)
        return hed_xml_filename
    return hed_xml_basename


def _sort_version_list(hed_versions):
    return sorted(hed_versions, key=Version, reverse=True)


def _get_hed_xml_versions_one_folder(hed_folder_url):
    url_request = make_url_request(hed_folder_url)
    url_data = str(url_request.read(), 'utf-8')
    loaded_json = json.loads(url_data)

    all_hed_versions = {}
    for file_entry in loaded_json:
        if file_entry['type'] == "dir":
            continue
        expression_match = version_pattern.match(file_entry["name"])
        if expression_match is not None:
            version = expression_match.group(3)
            found_library_name = expression_match.group(2)
            if found_library_name not in all_hed_versions:
                all_hed_versions[found_library_name] = {}
            all_hed_versions[found_library_name][version] = (
                file_entry["sha"], file_entry["download_url"], hed_folder_url.endswith(prerelease_suffix))

    return all_hed_versions


def _get_hed_xml_versions_one_library(hed_one_library_url):
    all_hed_versions = {}
    try:
        finalized_versions = \
            _get_hed_xml_versions_one_folder(hed_one_library_url + hedxml_suffix)
        _merge_in_versions(all_hed_versions, finalized_versions)
    except urllib.error.URLError:
        # Silently ignore ones without a hedxml section for now.
        pass
    try:
        pre_release_folder_versions = \
            _get_hed_xml_versions_one_folder(hed_one_library_url + prerelease_suffix)
        _merge_in_versions(all_hed_versions, pre_release_folder_versions)
    except urllib.error.URLError:
        # Silently ignore ones without a prerelease section for now.
        pass

    ordered_versions = {}
    for hed_library_name, hed_versions in all_hed_versions.items():
        ordered_versions1 = _sort_version_list(hed_versions)
        ordered_versions2 = [(version, hed_versions[version]) for version in ordered_versions1]
        ordered_versions[hed_library_name] = dict(ordered_versions2)

    return ordered_versions


def _get_hed_xml_versions_from_url_all_libraries(hed_base_library_url, library_name=None,
                                                 skip_folders=DEFAULT_SKIP_FOLDERS) -> Union[list, dict]:
    """ Get all available schemas and their hash values

    Parameters:
        hed_base_library_url(str): A single GitHub API url to cache, which contains library schema folders
                                   The subfolders should be a schema folder containing hedxml and/or prerelease folders.
        library_name(str or None): If str, cache only the named library schemas.
        skip_folders (list): A list of sub folders to skip over when downloading.

    Returns:
        Union[list, dict]: List of version numbers or dictionary {library_name: [versions]}.

    Notes:
        - The Default skip_folders is 'deprecated'.
        - The HED cache folder defaults to HED_CACHE_DIRECTORY.
        - The directories on GitHub are of the form:
            https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema/hedxml
    """
    url_request = make_url_request(hed_base_library_url)
    url_data = str(url_request.read(), 'utf-8')
    loaded_json = json.loads(url_data)

    all_hed_versions = {}
    for file_entry in loaded_json:
        if file_entry['type'] == "dir":
            if file_entry['name'] in skip_folders:
                continue
            found_library_name = file_entry['name']
            if library_name is not None and found_library_name != library_name:
                continue
            single_library_versions = _get_hed_xml_versions_one_library(hed_base_library_url + "/" + found_library_name)
            _merge_in_versions(all_hed_versions, single_library_versions)
            continue

    if library_name in all_hed_versions:
        return all_hed_versions[library_name]
    return all_hed_versions


def _merge_in_versions(all_hed_versions, sub_folder_versions):
    """Build up the version dictionary, divided by library"""
    for lib_name, hed_versions in sub_folder_versions.items():
        if lib_name not in all_hed_versions:
            all_hed_versions[lib_name] = {}
        all_hed_versions[lib_name].update(sub_folder_versions[lib_name])


def _calculate_sha1(filename):
    """ Calculate sha1 hash for filename

        Can be compared to GitHub hash values
    """
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
        str: The new filename on success or None on failure.

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
    """Cache the given HED version"""
    sha_hash, download_url, prerelease = version_info

    possible_cache_filename = _create_xml_filename(version, library_name, cache_folder, prerelease)
    local_sha_hash = _calculate_sha1(possible_cache_filename)

    if sha_hash == local_sha_hash:
        return possible_cache_filename

    return _cache_specific_url(download_url, possible_cache_filename)


def _cache_specific_url(source_url, cache_filename):
    """Copies a specific url to the cache at the given filename"""
    cache_folder = cache_filename.rpartition("/")[0]
    os.makedirs(cache_folder, exist_ok=True)
    temp_filename = url_to_file(source_url)
    if temp_filename:
        cache_filename = _safe_move_tmp_to_folder(temp_filename, cache_filename)
        os.remove(temp_filename)
        return cache_filename
    return None
