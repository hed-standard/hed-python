"""Infrastructure for caching HED schema from remote repositories."""

from __future__ import annotations

import shutil
import os
import time
import math

import json
from hashlib import sha1
from shutil import copyfile
import functools


import re
from typing import Union

from semantic_version import Version
from hed.schema.hed_cache_lock import CacheError, CacheLock
from hed.schema.schema_io.schema_util import url_to_file, make_url_request
from pathlib import Path
import urllib
from urllib.error import URLError

# From https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
HED_VERSION_P1 = r"(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
HED_VERSION_P2 = (
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)" r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
)
HED_VERSION_P3 = r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?"
HED_VERSION = HED_VERSION_P1 + HED_VERSION_P2 + HED_VERSION_P3
# Actual local HED filename re.
HED_VERSION_FINAL = r"^[hH][eE][dD](_([a-z0-9]+)_)?(" + HED_VERSION + r")\.[xX][mM][lL]$"

HED_XML_PREFIX = "HED"
HED_XML_EXTENSION = ".xml"
hedxml_suffix = "/hedxml"  # The suffix for schema and library schema at the given urls
prerelease_suffix = "/prerelease"  # The prerelease schemas at the given URLs

DEFAULT_HED_LIST_VERSIONS_URL = "https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema"
LIBRARY_HED_URL = "https://api.github.com/repos/hed-standard/hed-schemas/contents/library_schemas"
LIBRARY_DATA_URL = "https://raw.githubusercontent.com/hed-standard/hed-schemas/main/library_data.json"
# Cheap, path-scoped endpoints used to detect whether the standard-schema directory or the
# library-schemas directory has changed since the last full crawl of that directory, without
# touching any of the per-version URLs below. Each is scoped (via GitHub's commits-list
# `?path=` filter) to just the one top-level directory a caller actually needs, so a commit
# elsewhere in the repo (docs, CI config, README, etc.) never forces a recrawl here. See
# _get_last_commit_sha() and its use in get_available_hed_versions().
STANDARD_SCHEMA_HEAD_URL = (
    "https://api.github.com/repos/hed-standard/hed-schemas/commits?path=standard_schema&per_page=1"
)
LIBRARY_SCHEMAS_HEAD_URL = (
    "https://api.github.com/repos/hed-standard/hed-schemas/commits?path=library_schemas&per_page=1"
)
DEFAULT_URL_LIST = (DEFAULT_HED_LIST_VERSIONS_URL,)
DEFAULT_LIBRARY_URL_LIST = (LIBRARY_HED_URL,)


DEFAULT_SKIP_FOLDERS = ("deprecated",)

# Short-lived listing cache used by get_available_hed_versions() - deliberately much shorter
# than hed_cache_lock.CACHE_TIME_THRESHOLD (which throttles the much more expensive
# cache_xml_versions() download path).
AVAILABLE_VERSIONS_CACHE_FILENAME = "available_versions_cache.json"
AVAILABLE_VERSIONS_TIME_THRESHOLD = 60

# Keys inside available_versions_cache.json (alongside the per-URL entries) recording the
# last commit SHA affecting each top-level directory, as of the last time that directory's
# per-folder cache entries were actually crawled.
_STANDARD_HEAD_CACHE_KEY = "_standard_schema_head_sha_at_last_crawl"
_LIBRARY_HEAD_CACHE_KEY = "_library_schemas_head_sha_at_last_crawl"

HED_CACHE_DIRECTORY = os.path.join(Path.home(), ".hedtools/hed_cache/")

# This is the schemas included in the hedtools package.
INSTALLED_CACHE_LOCATION = os.path.realpath(os.path.join(os.path.dirname(__file__), "schema_data/"))
version_pattern = re.compile(HED_VERSION_FINAL)


def set_cache_directory(new_cache_dir):
    """Set default global HED cache directory.

    Parameters:
        new_cache_dir (str): Directory to check for versions.

    """
    if new_cache_dir:
        global HED_CACHE_DIRECTORY
        HED_CACHE_DIRECTORY = new_cache_dir
        os.makedirs(new_cache_dir, exist_ok=True)


def get_cache_directory(cache_folder=None) -> str:
    """Return the current value of HED_CACHE_DIRECTORY.

    Parameters:
        cache_folder (str): Optional cache folder override.

    Returns:
        str: The cache directory path.
    """
    if cache_folder:
        return cache_folder
    return HED_CACHE_DIRECTORY


def get_hed_versions(local_hed_directory=None, library_name=None, check_prerelease=False) -> Union[list, dict]:
    """Get the HED versions in the HED directory.

    Parameters:
        local_hed_directory (str): Directory to check for versions which defaults to hed_cache.
        library_name (str or None): An optional schema library name.
                                    None retrieves the standard schema only.
                                    Pass "all" to retrieve all standard and library schemas as a dict.
        check_prerelease (bool): If True, results can include prerelease schemas.
                                 Default is False, returning only released versions.

    Returns:
        Union[list, dict]: List of version numbers or dictionary {library_name: [versions]}.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    if not library_name:
        library_name = None

    all_hed_versions = {}
    local_directories = [local_hed_directory]
    if check_prerelease and Path(local_hed_directory).name != "prerelease":
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
    if library_name == "all":
        return all_hed_versions
    if library_name in all_hed_versions:
        return all_hed_versions[library_name]
    return []


def get_hed_version_path(xml_version, library_name=None, local_hed_directory=None) -> Union[str, None]:
    """Get the HED XML file path for a given version.

    Searches the local cache first. If the version is not found and local_hed_directory
    is the default HED cache, the cache is refreshed from GitHub before a second lookup.
    No network call is made for custom directories.

    Parameters:
        xml_version (str): The version string to look up.
        library_name (str or None): Optional schema library name.
        local_hed_directory (str or None): Path to local HED directory. Defaults to HED_CACHE_DIRECTORY.
            Passing a custom path disables the automatic GitHub refresh.

    Returns:
        Union[str, None]: The path to the requested HED XML file, or None.

    """
    if not local_hed_directory:
        local_hed_directory = HED_CACHE_DIRECTORY

    result = _find_hed_version_path(xml_version, library_name, local_hed_directory)
    if result:
        return result

    # Version not found locally — try refreshing cache from GitHub (default cache only).
    # cache_xml_versions() returns -1 on failure (network error, lock contention, rate limit).
    # In that case the second lookup will return None, which the caller treats as "version not found".
    if not xml_version or local_hed_directory != HED_CACHE_DIRECTORY:
        return None

    cache_xml_versions()
    return _find_hed_version_path(xml_version, library_name, local_hed_directory)


def _find_hed_version_path(xml_version, library_name, local_hed_directory):
    """Look up a HED version path in the given directory without downloading.

    Parameters:
        xml_version (str): The version to find.
        library_name (str or None): Optional schema library name.
        local_hed_directory (str): Directory to search.

    Returns:
        Union[str, None]: The path if found, None otherwise.
    """
    hed_versions = get_hed_versions(local_hed_directory, library_name, check_prerelease=True)
    if not hed_versions or not xml_version:
        return None
    if xml_version in hed_versions:
        # Check regular directory first
        regular_path = _create_xml_filename(xml_version, library_name, local_hed_directory, False)
        if os.path.exists(regular_path):
            return regular_path

        # Also check prerelease directory
        prerelease_path = _create_xml_filename(xml_version, library_name, local_hed_directory, True)
        if os.path.exists(prerelease_path):
            return prerelease_path
    return None


def cache_local_versions(cache_folder) -> Union[int, None]:
    """Cache all schemas included with the HED installation.

    Parameters:
        cache_folder (str): The folder holding the cache.

    Returns:
        Union[int, None]: Returns -1 on cache access failure. None otherwise

    """
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    try:
        with CacheLock(cache_folder, write_time=False):
            _copy_installed_folder_to_cache(cache_folder)
    except CacheError:
        return -1


def cache_xml_versions(
    hed_base_urls=DEFAULT_URL_LIST,
    hed_library_urls=DEFAULT_LIBRARY_URL_LIST,
    skip_folders=DEFAULT_SKIP_FOLDERS,
    cache_folder=None,
) -> float:
    """Cache all schemas at the given URLs.

    Parameters:
        hed_base_urls (str or list): Path or list of paths. These should point to a single folder.
        hed_library_urls (str or list): Path or list of paths. These should point to folder containing library folders.
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
                new_hed_versions = _get_hed_xml_versions_from_url_all_libraries(
                    hed_library_url, skip_folders=skip_folders
                )
                _merge_in_versions(all_hed_versions, new_hed_versions)

            for library_name, hed_versions in all_hed_versions.items():
                for version, version_info in hed_versions.items():
                    _cache_hed_version(version, library_name, version_info, cache_folder=cache_folder)

    except (CacheError, ValueError, URLError):
        return -1

    return 0


def _get_last_commit_sha(url, etag_cache, force_refresh=False, cache_time_threshold=0):
    """Best-effort fetch of the latest commit SHA affecting one top-level directory.

    Used by get_available_hed_versions() as a single, cheap gate ahead of the much more
    expensive per-folder crawl of that same directory (standard schema, or library listing plus
    every library's own hedxml/prerelease folders): if this SHA is unchanged since the last full
    crawl of that directory, nothing under it could have changed, so every per-folder URL under
    it can be treated as still fresh without individually re-checking - let alone re-fetching -
    any of them. Scoping the check to one directory, via GitHub's commits-list `?path=` filter,
    means an unrelated commit elsewhere in the repo (docs, CI config, README, etc.) never forces
    a recrawl here. hed-schemas changes on the order of days or weeks, so in steady state this
    turns what would otherwise be a recurring multi-request burst into a single request per
    directory actually needed.

    This participates in the exact same two-tier caching (time-based, then ETag-conditional)
    that every other URL here does, via the same etag_cache dict and _get_json_with_etag() -
    it is not a separate caching mechanism, just one more URL in the same cache.

    Parameters:
        url (str): STANDARD_SCHEMA_HEAD_URL or LIBRARY_SCHEMAS_HEAD_URL.
        etag_cache (dict or None): Same per-URL cache dict get_available_hed_versions() uses.
        force_refresh (bool): Passed through to _get_json_with_etag().
        cache_time_threshold (int): Passed through to _get_json_with_etag().

    Returns:
        str or None: The latest commit SHA touching this directory, or None if it couldn't be
                    determined - network error, rate limit, an empty commit history, or a
                    response shaped differently than expected. Callers must treat None as
                    "unknown", not "unchanged": every caller of this function falls back to the
                    pre-existing per-folder behavior whenever this returns None, so a problem
                    with this one extra endpoint can never produce a stale answer - at worst, it
                    costs the same (already-optimized) per-folder crawl that would have run
                    without this gate at all.
    """
    try:
        loaded_json = _get_json_with_etag(url, etag_cache, force_refresh, cache_time_threshold)
        if not loaded_json:
            return None
        sha = loaded_json[0].get("sha")
        return sha if isinstance(sha, str) else None
    except Exception:
        return None


def get_available_hed_versions(
    hed_base_urls=DEFAULT_URL_LIST,
    hed_library_urls=DEFAULT_LIBRARY_URL_LIST,
    skip_folders=DEFAULT_SKIP_FOLDERS,
    library_name=None,
    check_prerelease=False,
    cache_folder=None,
    force_refresh=False,
    cache_time_threshold=AVAILABLE_VERSIONS_TIME_THRESHOLD,
    repo_check_interval=None,
) -> Union[list, dict]:
    """List HED schema versions available on GitHub, without downloading or caching their content.

    This still talks to the network - it never fetches a schema file's actual XML content, but
    listing everything can still add up to a couple dozen small JSON directory-listing requests
    in one call: 1-2 for the standard schema (plus its prerelease folder), 1 to enumerate the
    library folders, and 1-2 more per library folder found. That worst case only applies to
    library_name="all"; passing library_name=None (the default) skips every library-related
    request entirely, and passing a specific library name skips the standard-schema request and
    restricts the library side to just that one library's folder. It's the live-from-GitHub counterpart
    to get_hed_versions() (which only reports what's already bundled with hedtools or previously
    cached on disk, with zero network calls), and it's still far cheaper than cache_xml_versions()
    (which makes those same listing calls AND then downloads every version's full content - fine
    to do once for a version you're about to use, wasteful to do just to show a list of names).
    Because of the request count, this function caches its own results on disk (see Notes) so
    that a caller polling it frequently - e.g. a web service handling many requests - doesn't
    trip GitHub's API rate limits. Callers don't need to implement their own throttling on top
    of this.

    Typical usage is: call this to populate something like a version-picker dropdown, then only
    fetch the one version the user actually selects, via load_schema_version() (which downloads
    and caches just that version, lazily, the first time it's needed).

    Parameters:
        hed_base_urls (str or list): Path or list of paths for the standard schema folder(s).
        hed_library_urls (str or list): Path or list of paths for folder(s) containing library
                                        schema subfolders.
        skip_folders (list): A list of library subfolders to skip. Default is 'deprecated'.
        library_name (str or None): None retrieves the standard schema only. Pass "all" to
                                    retrieve all standard and library schemas as a dict.
                                    Pass a specific library name to retrieve just that library.
        check_prerelease (bool): If True, results can include prerelease schemas.
                                 Default is False, returning only released versions.
        cache_folder (str or None): Where to read/write the listing cache (see Notes). None
                                    uses the default HED cache folder.
        force_refresh (bool): If True, skip the "don't even check yet" shortcut described in
                              Notes and always at least ask GitHub whether anything changed.
                              Use this when you specifically need a confirmed up-to-date
                              answer - e.g. right after publishing a new release.
        cache_time_threshold (int): How long, in seconds, a URL that was just checked is
                                   reused without even asking GitHub whether it changed.
                                   Default is 60 seconds - short enough that new releases
                                   show up quickly, long enough that a caller polling this in
                                   a tight loop doesn't generate a request per call.
        repo_check_interval (int or None): How long, in seconds, to go between the cheap
                                   top-level-directory gate checks described in Notes, before
                                   even asking GitHub whether that directory's latest commit
                                   changed. None (the default) reuses cache_time_threshold, so
                                   behavior is unchanged unless this is set explicitly. A
                                   longer interval directly helps an unauthenticated caller:
                                   GitHub's 60-requests/hour anonymous cap is charged even for
                                   a confirmed-unchanged (304) response, unlike for
                                   authenticated requests, where conditional 304s are free.
                                   Since hed-schemas typically only changes every few days or
                                   weeks, an unauthenticated long-running caller (e.g. a web
                                   service polling this periodically) can safely set this much
                                   larger - minutes to hours - without meaningfully delaying
                                   when a real change is noticed.

    Returns:
        Union[list, dict]: List of version numbers, or {library_name: [versions]} if
                           library_name is "all". Returns an empty list/dict for any URL that
                           couldn't be reached rather than raising - this is meant to degrade
                           gracefully for use in unattended user-facing listings.

    Examples:
        Standard schema only (the default) - just a list of version strings, newest first::

            >>> get_available_hed_versions()
            ['8.4.0', '8.3.0', '8.2.0', '8.1.0', '8.0.0']

        Everything - standard schema plus every library, as a dict keyed by library name
        (the standard schema is under the None key)::

            >>> get_available_hed_versions(library_name="all")
            {None: ['8.4.0', '8.3.0', '8.2.0'], 'score': ['2.1.0', '1.0.0'], 'lang': ['1.1.0']}

        Just one library, by name::

            >>> get_available_hed_versions(library_name="score")
            ['2.1.0', '1.0.0']

        Including prereleases (adds anything only found in GitHub's "prerelease" folders)::

            >>> get_available_hed_versions(check_prerelease=True)
            ['8.5.0', '8.4.0', '8.3.0', '8.2.0', '8.1.0', '8.0.0']

        Once the user picks a version from a list like the above, fetch that one version's
        actual XML content (this is the step that downloads a schema file - the calls above
        only ever downloaded small directory listings, never a schema itself)::

            >>> from hed.schema import load_schema_version
            >>> schema = load_schema_version("8.4.0")

        Force a fresh listing right after publishing a release, instead of possibly getting
        a cached result from just before it went live::

            >>> get_available_hed_versions(force_refresh=True)
            ['8.5.0', '8.4.0', '8.3.0', ...]

    Notes:
        - Caching happens per GitHub URL (there are several under the hood: the standard
          schema folder and its prerelease folder, the library-folder listing, and each
          library's own folder and prerelease folder), in a small metadata file
          (available_versions_cache.json) inside the cache folder, in two layers:
          1. If a given URL was checked within cache_time_threshold seconds (default 60),
             it's reused with no network call at all.
          2. Otherwise, a conditional GET is made using the ETag from the last time that URL
             was fetched. A 304 response means GitHub confirms nothing changed there, so the
             prior result is reused - and, per GitHub's own documented behavior, this doesn't
             count against the primary rate limit for authenticated requests. A 200 means
             something changed, and the new content and ETag are stored for next time.
        - A URL that failed (GitHub unreachable, rate-limited, etc.) is also remembered for
          cache_time_threshold seconds, so a string of calls during an outage doesn't retry
          it on every single one - it raises immediately instead, same as if it were just
          fetched and failed.
        - This uses a much shorter threshold than the one in hed_cache_lock.py, which throttles
          cache_xml_versions()'s far more expensive per-version download step.
        - Unlike cache_xml_versions(), this never writes schema content - the on-disk cache
          used here holds only the same small directory-listing JSON GitHub itself returns
          (version names, SHAs, and download URLs), never a schema file itself. It has no
          interaction with get_hed_versions(), cache_local_versions(), or the schema files
          cache_xml_versions() downloads.
        - force_refresh=True skips layer 1 above but still uses layer 2 (the conditional GET),
          so it stays cheap when nothing has actually changed.
        - Before crawling either the standard schema or the library folders, one extra cheap
          check runs first, scoped to just that one top-level directory: the latest commit SHA
          affecting standard_schema/ (if the result could include it) or library_schemas/ (if
          the result could include library data) - see _get_last_commit_sha() - compared
          against the SHA that was current the last time that directory was actually fully
          crawled. hed-schemas changes on the order of days or weeks, so if the SHA still
          matches, every per-folder URL under that directory is known to still be correct
          without checking - or fetching - any of them individually; the "couple dozen
          requests" figure above is the cold-start/actual-change case, not the (far more common)
          steady-state case. Scoping each gate to just the directory it protects means a commit
          elsewhere in the repo (docs, CI config, README, etc.) never forces either directory to
          be recrawled. If a gate check itself fails for any reason, it's treated as "unknown"
          and that directory falls back to the per-URL behavior described above, unaffected by
          the gate ever having existed. When the gate confirms a directory is unchanged, that
          directory's per-folder URLs are treated as fresh indefinitely - but only the ones that
          were actually fetched successfully; see the "Note" on _get_json_with_etag() for why a
          per-URL failure is never shielded from retry by this, no matter how long the gate goes
          without seeing a change.
        - The gate checks use repo_check_interval (defaulting to cache_time_threshold) rather
          than cache_time_threshold directly, so the (already very cheap) gate checks can be
          made even less frequent without affecting how fresh a genuinely-changed directory's
          own content is once a change is actually detected. This matters most for
          unauthenticated callers - see repo_check_interval above.
    """
    if isinstance(hed_base_urls, str):
        hed_base_urls = [hed_base_urls]
    if isinstance(hed_library_urls, str):
        hed_library_urls = [hed_library_urls]
    if not cache_folder:
        cache_folder = HED_CACHE_DIRECTORY

    url_cache = _read_available_versions_cache(cache_folder)
    cache_before = json.dumps(url_cache, sort_keys=True)

    # Only fetch the standard-schema URLs when the result could actually include them
    # (library_name is None or "all") - a request for one specific library has no use for
    # this data, and fetching it anyway would be pure wasted requests.
    needs_standard = library_name is None or library_name == "all"
    # Likewise, only touch any library URL when the result could include library data at
    # all - a plain standard-schema request (library_name=None) never looks at it.
    needs_libraries = library_name is not None

    if repo_check_interval is None:
        repo_check_interval = cache_time_threshold

    all_hed_versions = {}
    if needs_standard:
        # A single, cheap check ahead of the standard-schema crawl below, scoped to just that
        # directory: if standard_schema/ hasn't changed since the last time this crawl actually
        # ran, nothing any of its per-folder URLs would return could have changed either, so
        # every one of them can be treated as still fresh - regardless of how much wall-clock
        # time has passed - without individually re-checking or re-fetching any of them. A None
        # result (network error, rate limit, unexpected response) means "unknown", so these are
        # simply left equal to the caller's own values, i.e. exactly the pre-existing behavior.
        standard_head_sha = _get_last_commit_sha(
            STANDARD_SCHEMA_HEAD_URL, url_cache, force_refresh, repo_check_interval
        )
        standard_folder_force_refresh = force_refresh
        standard_folder_cache_time_threshold = cache_time_threshold
        if standard_head_sha is not None and standard_head_sha == url_cache.get(_STANDARD_HEAD_CACHE_KEY):
            standard_folder_force_refresh = False
            standard_folder_cache_time_threshold = math.inf
        if standard_head_sha is not None:
            url_cache[_STANDARD_HEAD_CACHE_KEY] = standard_head_sha

        for hed_base_url in hed_base_urls:
            try:
                new_hed_versions = _get_hed_xml_versions_one_library(
                    hed_base_url, url_cache, standard_folder_force_refresh, standard_folder_cache_time_threshold
                )
                _merge_in_versions(all_hed_versions, new_hed_versions)
            except Exception:
                # GitHub unreachable, or an unexpected/malformed response, for this
                # particular URL - skip it so the caller still gets whatever else could be
                # listed. Deliberately broad: this function's whole contract is to degrade
                # gracefully rather than raise, so this isn't limited to network-level
                # errors (URLError/HTTPError) - a rate-limited or otherwise unexpected
                # response body (e.g. missing an expected JSON key) should be just as
                # harmless to the caller as a plain connection failure.
                continue
    if needs_libraries:
        # Same idea as the standard-schema gate above, scoped to library_schemas/ instead -
        # kept as an entirely separate gate (rather than one whole-repo check) so a commit
        # under, say, standard_schema/ or docs/ never forces a library recrawl, and vice versa.
        library_head_sha = _get_last_commit_sha(LIBRARY_SCHEMAS_HEAD_URL, url_cache, force_refresh, repo_check_interval)
        library_folder_force_refresh = force_refresh
        library_folder_cache_time_threshold = cache_time_threshold
        if library_head_sha is not None and library_head_sha == url_cache.get(_LIBRARY_HEAD_CACHE_KEY):
            library_folder_force_refresh = False
            library_folder_cache_time_threshold = math.inf
        if library_head_sha is not None:
            url_cache[_LIBRARY_HEAD_CACHE_KEY] = library_head_sha

        # "all" means no filter (list every library); a specific name restricts the
        # helper to just that one library's folder, instead of listing and fetching
        # every library found under hed_library_urls.
        library_filter = None if library_name == "all" else library_name
        for hed_library_url in hed_library_urls:
            try:
                new_hed_versions = _get_hed_xml_versions_from_url_all_libraries(
                    hed_library_url,
                    library_name=library_filter,
                    skip_folders=skip_folders,
                    etag_cache=url_cache,
                    force_refresh=library_folder_force_refresh,
                    cache_time_threshold=library_folder_cache_time_threshold,
                )
                if library_filter is not None and new_hed_versions:
                    # When filtered to one library, _get_hed_xml_versions_from_url_all_libraries()
                    # returns that library's {version: (...)} dict directly, unwrapped, rather
                    # than nested under its name - re-nest it here so _merge_in_versions() sees
                    # the same {lib_name: {version: (...)}} shape it gets from the "all" case.
                    new_hed_versions = {library_filter: new_hed_versions}
                _merge_in_versions(all_hed_versions, new_hed_versions)
            except Exception:
                continue

    # Only rewrite the cache file if something was actually checked over the network (a fresh
    # fetch or a conditional 304) - if every URL was served from tier 1 above, nothing changed
    # and there's no reason to touch the file.
    if json.dumps(url_cache, sort_keys=True) != cache_before:
        _write_available_versions_cache(cache_folder, url_cache)

    result = {}
    for lib_name, versions_info in all_hed_versions.items():
        filtered = [
            version
            for version, (_sha, _download_url, prerelease) in versions_info.items()
            if check_prerelease or not prerelease
        ]
        if filtered:
            result[lib_name] = _sort_version_list(filtered)

    if library_name == "all":
        return result
    if library_name in result:
        return result[library_name]
    return []


def _read_available_versions_cache(cache_folder):
    """Load the on-disk per-URL listing cache used by get_available_hed_versions().

    Parameters:
        cache_folder (str): Folder the listing cache file lives in.

    Returns:
        dict: {url: {"etag": str or None, "body": <parsed GitHub JSON>, "timestamp": float}}.
             Empty dict if the file is absent, corrupt, or otherwise unreadable - this is
             treated the same as "nothing cached yet" rather than raising.
    """
    cache_filename = os.path.join(cache_folder, AVAILABLE_VERSIONS_CACHE_FILENAME)
    try:
        with open(cache_filename, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def _write_available_versions_cache(cache_folder, url_cache):
    """Best-effort write of the per-URL listing cache back to disk.

    Writes to a temp file and renames it into place so a reader never sees a partial file.
    Any failure here is silently ignored - this cache is a performance optimization, not a
    correctness requirement, so it should never turn a successful listing into an error.

    Parameters:
        cache_folder (str): Folder to write the listing cache file into.
        url_cache (dict): {url: {"etag", "body", "timestamp"}} to persist, as produced by
                          _read_available_versions_cache() and updated by _get_json_with_etag().
    """
    cache_filename = os.path.join(cache_folder, AVAILABLE_VERSIONS_CACHE_FILENAME)
    tmp_filename = cache_filename + ".tmp"
    try:
        os.makedirs(cache_folder, exist_ok=True)
        with open(tmp_filename, "w") as f:
            json.dump(url_cache, f)
        os.replace(tmp_filename, cache_filename)
    except OSError:
        pass


def _get_json_with_etag(url, etag_cache, force_refresh=False, cache_time_threshold=0):
    """Fetch a GitHub JSON listing, reusing a recent or confirmed-unchanged result when possible.

    Three tiers, cheapest first:
      1. If this exact URL was checked within cache_time_threshold seconds (and force_refresh
         is not set), skip the network entirely and reuse the stored body.
      2. Otherwise, make a conditional GET using the stored ETag, if any (If-None-Match). A 304
         response means GitHub confirms nothing changed - reuse the stored body. Per GitHub's
         documented behavior, this doesn't count against the primary rate limit for
         authenticated requests (see https://docs.github.com/en/rest/using-the-rest-api/
         best-practices-for-using-the-rest-api#use-conditional-requests-if-appropriate).
      3. A 200 response means something changed (or there was no prior ETag) - parse it and
         store the new body and ETag for next time.

    Parameters:
        url (str): The URL to fetch.
        etag_cache (dict or None): Maps url -> {"etag", "body", "timestamp"}, updated in place.
                                   A failed attempt is recorded too, as {"etag": None, "body":
                                   None, "timestamp": <now>} - this is what keeps a URL that's
                                   currently unreachable (GitHub down, rate-limited) from being
                                   retried on every single call; tier 1 re-raises immediately
                                   for a recent failure instead of hitting the network again.
                                   Pass None to always do a plain, unconditional fetch with none
                                   of this caching behavior (used by callers, like
                                   cache_xml_versions(), that don't want it). A per-URL entry
                                   that isn't a dict (corrupted cache file, older/newer format)
                                   is treated as a cache miss rather than raising.
        force_refresh (bool): Skip tier 1 (the time-based shortcut) even if the cached entry is
                              still within cache_time_threshold. Tier 2's conditional GET is
                              still used, so this remains cheap when nothing has changed.
        cache_time_threshold (int): How long, in seconds, tier 1 applies for. For a *recorded
                                   failure* specifically, this is capped at
                                   AVAILABLE_VERSIONS_TIME_THRESHOLD regardless of the value
                                   passed in - see the note below.

    Returns:
        The parsed JSON body for this URL - freshly fetched, or reused from etag_cache.

    Raises:
        urllib.error.URLError: If the URL could not be reached (including a recent, still-fresh
                               failure recorded by an earlier call - see etag_cache above).

    Note:
        A successful result and a recorded failure are not equally safe to hold onto for a long
        cache_time_threshold. get_available_hed_versions() has two independent directory-level
        gates - one for standard_schema/, one for library_schemas/ - and each deliberately passes
        a very large (or infinite) threshold here once it's confirmed its own directory hasn't
        changed, so that already-fetched, successful per-folder entries under that directory can
        be reused indefinitely without individually re-checking each one. This applies equally to
        both gates, since they funnel through this same function. But a *failure* entry (body is
        None) isn't "known good data" that staying unchanged makes safe to keep reusing - it's
        the absence of data, typically from a transient rate-limit or network error unrelated to
        whether the directory's content has actually changed. Honoring a large threshold for a
        failure would mean a transient error picked up during one crawl keeps being silently
        skipped (see the broad except clauses in _get_hed_xml_versions_one_library() and
        _get_hed_xml_versions_from_url_all_libraries()) for as long as the directory happens not
        to change - potentially days or weeks - even though the underlying problem may have
        resolved within minutes. To prevent that, for either gate, a recorded failure is always
        retried within AVAILABLE_VERSIONS_TIME_THRESHOLD seconds, no matter how large a
        cache_time_threshold was passed in for this call.
    """
    cached_entry = etag_cache.get(url) if etag_cache is not None else None
    if not isinstance(cached_entry, dict):
        # A non-dict entry (e.g. a corrupted cache file, or one written by a future/older
        # format) can't be trusted - treat it exactly like "nothing cached yet" rather than
        # letting cached_entry.get(...) raise AttributeError below.
        cached_entry = None

    if cached_entry and not force_refresh:
        effective_threshold = cache_time_threshold
        if cached_entry.get("body") is None:
            # See the "Note" above: never let a recorded failure be shielded from retry by a
            # large threshold that was only ever meant to apply to confirmed-good data.
            effective_threshold = min(cache_time_threshold, AVAILABLE_VERSIONS_TIME_THRESHOLD)
        age = time.time() - cached_entry.get("timestamp", 0)
        if age <= effective_threshold:
            if cached_entry.get("body") is None:
                raise URLError(f"A recent attempt to reach {url} failed; not retrying yet")
            return cached_entry["body"]

    extra_headers = {}
    if cached_entry and cached_entry.get("etag"):
        extra_headers["If-None-Match"] = cached_entry["etag"]

    try:
        url_request = make_url_request(url, extra_headers=extra_headers or None)
    except urllib.error.HTTPError as e:
        if e.code == 304 and cached_entry is not None and cached_entry.get("body") is not None:
            # GitHub confirmed nothing changed since our last fetch of this URL.
            cached_entry["timestamp"] = time.time()
            return cached_entry["body"]
        if etag_cache is not None:
            etag_cache[url] = {"etag": None, "body": None, "timestamp": time.time()}
        raise
    except URLError:
        if etag_cache is not None:
            etag_cache[url] = {"etag": None, "body": None, "timestamp": time.time()}
        raise

    url_data = str(url_request.read(), "utf-8")
    loaded_json = json.loads(url_data)
    if etag_cache is not None:
        etag_cache[url] = {
            "etag": url_request.headers.get("ETag"),
            "body": loaded_json,
            "timestamp": time.time(),
        }
    return loaded_json


@functools.lru_cache(maxsize=50)
def get_library_data(library_name, cache_folder=None) -> dict:
    """Retrieve the library data for the given library.

    Currently, this is just the valid ID range.

    Parameters:
        library_name (str): The schema name. "" for standard schema.
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
    except (OSError, CacheError, ValueError, KeyError):
        pass

    try:
        with CacheLock(cache_lib_data_folder, write_time=False):
            _copy_installed_folder_to_cache(cache_lib_data_folder, "library_data")

        with open(local_library_data_filename) as file:
            library_data = json.load(file)
        specific_library = library_data[library_name]
        return specific_library
    except (OSError, CacheError, ValueError, KeyError):
        pass

    try:
        with CacheLock(cache_lib_data_folder):
            # if this fails it'll fail to load in the next step
            _cache_specific_url(LIBRARY_DATA_URL, local_library_data_filename)
        with open(local_library_data_filename) as file:
            library_data = json.load(file)
        specific_library = library_data[library_name]
        return specific_library
    except (OSError, CacheError, ValueError, URLError, KeyError):
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


def _get_hed_xml_versions_one_folder(hed_folder_url, etag_cache=None, force_refresh=False, cache_time_threshold=0):
    loaded_json = _get_json_with_etag(hed_folder_url, etag_cache, force_refresh, cache_time_threshold)

    all_hed_versions = {}
    for file_entry in loaded_json:
        if file_entry["type"] == "dir":
            continue
        expression_match = version_pattern.match(file_entry["name"])
        if expression_match is not None:
            version = expression_match.group(3)
            found_library_name = expression_match.group(2)
            if found_library_name not in all_hed_versions:
                all_hed_versions[found_library_name] = {}
            all_hed_versions[found_library_name][version] = (
                file_entry["sha"],
                file_entry["download_url"],
                hed_folder_url.endswith(prerelease_suffix),
            )

    return all_hed_versions


def _get_hed_xml_versions_one_library(
    hed_one_library_url, etag_cache=None, force_refresh=False, cache_time_threshold=0
):
    all_hed_versions = {}
    try:
        finalized_versions = _get_hed_xml_versions_one_folder(
            hed_one_library_url + hedxml_suffix, etag_cache, force_refresh, cache_time_threshold
        )
        _merge_in_versions(all_hed_versions, finalized_versions)
    except Exception:
        # Silently ignore ones without a hedxml section for now. Deliberately broad (not just
        # URLError) - a rate-limited or otherwise unexpected GitHub response can fail with a
        # KeyError/ValueError while parsing rather than a network-level error, and this
        # function's contract is to degrade gracefully either way.
        pass
    try:
        pre_release_folder_versions = _get_hed_xml_versions_one_folder(
            hed_one_library_url + prerelease_suffix, etag_cache, force_refresh, cache_time_threshold
        )
        _merge_in_versions(all_hed_versions, pre_release_folder_versions)
    except Exception:
        # Silently ignore ones without a prerelease section for now. See note above.
        pass

    ordered_versions = {}
    for hed_library_name, hed_versions in all_hed_versions.items():
        ordered_versions1 = _sort_version_list(hed_versions)
        ordered_versions2 = [(version, hed_versions[version]) for version in ordered_versions1]
        ordered_versions[hed_library_name] = dict(ordered_versions2)

    return ordered_versions


def _get_hed_xml_versions_from_url_all_libraries(
    hed_base_library_url,
    library_name=None,
    skip_folders=DEFAULT_SKIP_FOLDERS,
    etag_cache=None,
    force_refresh=False,
    cache_time_threshold=0,
) -> Union[list, dict]:
    """Get all available schemas and their hash values

    Parameters:
        hed_base_library_url(str): A single GitHub API url to cache, which contains library schema folders
                                   The subfolders should be a schema folder containing hedxml and/or prerelease folders.
        library_name(str or None): If str, cache only the named library schemas.
        skip_folders (list): A list of sub folders to skip over when downloading.
        etag_cache (dict or None): Passed through to _get_json_with_etag() for every request
                                   this makes, including one per discovered library subfolder.
                                   None (the default) disables conditional/cached requests.
        force_refresh (bool): Passed through to _get_json_with_etag().
        cache_time_threshold (int): Passed through to _get_json_with_etag().

    Returns:
        Union[list, dict]: List of version numbers or dictionary {library_name: [versions]}.

    Notes:
        - The Default skip_folders is 'deprecated'.
        - The HED cache folder defaults to HED_CACHE_DIRECTORY.
        - The directories on GitHub are of the form:
            https://api.github.com/repos/hed-standard/hed-schemas/contents/standard_schema/hedxml
    """
    loaded_json = _get_json_with_etag(hed_base_library_url, etag_cache, force_refresh, cache_time_threshold)

    all_hed_versions = {}
    for file_entry in loaded_json:
        if file_entry["type"] == "dir":
            if file_entry["name"] in skip_folders:
                continue
            found_library_name = file_entry["name"]
            if library_name is not None and found_library_name != library_name:
                continue
            single_library_versions = _get_hed_xml_versions_one_library(
                hed_base_library_url + "/" + found_library_name, etag_cache, force_refresh, cache_time_threshold
            )
            _merge_in_versions(all_hed_versions, single_library_versions)
            continue

    if library_name in all_hed_versions:
        return all_hed_versions[library_name]
    return all_hed_versions


def _merge_in_versions(all_hed_versions, sub_folder_versions):
    """Build up the version dictionary, divided by library"""
    for lib_name, _hed_versions in sub_folder_versions.items():
        if lib_name not in all_hed_versions:
            all_hed_versions[lib_name] = {}
        all_hed_versions[lib_name].update(sub_folder_versions[lib_name])


def _calculate_sha1(filename):
    """Calculate sha1 hash for filename

    Can be compared to GitHub hash values
    """
    try:
        with open(filename, "rb") as f:
            data = f.read()
            githash = sha1()
            githash.update(f"blob {len(data)}\0".encode("utf-8"))
            githash.update(data)
            return githash.hexdigest()
    except FileNotFoundError:
        return None


def _safe_move_tmp_to_folder(temp_hed_xml_file, dest_filename):
    """Copy to destination folder and rename.

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
