"""Repo-level manifest fast path for HED schema version discovery.

hed-schemas publishes a single ``schema_versions.json`` at its repository root listing every schema
version (released / prerelease / deprecated) for the standard schema and each library, with each
XML file's git blob SHA. hedtools can read that one file from the raw/CDN host instead of crawling
the GitHub REST API directory listings (which are metered - 60 requests/hour unauthenticated, with
even conditional 304s counting against that cap).

This module is deliberately I/O-light and has no dependency on the rest of ``hed.schema`` (it never
imports :mod:`hed.schema.hed_cache`), so hed_cache can use it as a drop-in fast path while keeping
the REST API crawl as a fallback. The network fetch itself is performed by the caller (hed_cache)
via its existing ETag-aware helper; the functions here only parse an already-loaded manifest dict.

Deprecated versions are recorded in the manifest so that the static HED schema browser can list and
display them directly (no hedtools call involved). hedtools' own compute paths do not operate on
deprecated schemas, so neither the listing nor the load/download helpers here surface them.

Manifest shape (``manifest_format_version`` 1)::

    {
      "manifest_format_version": 1,
      "generated": "<iso timestamp>",
      "repo_commit": "<hed-schemas HEAD sha>",
      "libraries": {
        "":      {"released": [{"version", "file", "sha", "date"}], "prerelease": [...], "deprecated": [...]},
        "score": {...},
        ...
      }
    }

The standard schema is keyed by the empty string ``""`` in the manifest; internally hedtools uses
``None`` for the standard schema, so that mapping is applied here.
"""

from __future__ import annotations

from semantic_version import Version

# The manifest is served as raw file content (CDN-backed), not through the REST API, so it is not
# subject to the GitHub REST API rate limit.
RAW_CONTENT_BASE = "https://raw.githubusercontent.com/hed-standard/hed-schemas"
MANIFEST_FILE = "schema_versions.json"
MANIFEST_URL = f"{RAW_CONTENT_BASE}/main/{MANIFEST_FILE}"

# Only this on-disk format is understood; a manifest advertising anything else is ignored so a
# future format change can never be silently misread (the caller falls back to the REST API crawl).
SUPPORTED_MANIFEST_FORMAT_VERSION = 1

_STANDARD_MANIFEST_KEY = ""  # the standard schema's key inside manifest["libraries"]


def is_supported(manifest) -> bool:
    """Return True if ``manifest`` is a dict in a format version this module understands.

    Parameters:
        manifest: The parsed manifest (any type - non-dicts and unknown formats return False).

    Returns:
        bool: True only for a dict whose ``manifest_format_version`` matches the supported version
              and whose ``libraries`` value is a dict (the shape all downstream helpers require).
    """
    return (
        isinstance(manifest, dict)
        and manifest.get("manifest_format_version") == SUPPORTED_MANIFEST_FORMAT_VERSION
        and isinstance(manifest.get("libraries"), dict)
    )


def raw_url_for(file_path: str, ref: str) -> str:
    """Build the raw/CDN URL for a repo-relative file path at a given git ref (commit/branch/tag)."""
    return f"{RAW_CONTENT_BASE}/{ref}/{file_path}"


def _sort_versions(versions):
    """Sort version strings newest-first using semantic-versioning precedence."""
    return sorted(versions, key=Version, reverse=True)


def _versions_for_key(manifest, manifest_key, check_prerelease):
    """Collect (and sort, newest-first) the versions for one manifest library key."""
    categories = manifest.get("libraries", {}).get(manifest_key, {})
    versions = [entry["version"] for entry in categories.get("released", [])]
    if check_prerelease:
        versions += [entry["version"] for entry in categories.get("prerelease", [])]
    # ``deprecated`` is intentionally never included, matching the default skip_folders behavior of
    # the REST API crawl (which skips the ``deprecated`` folder).
    return _sort_versions(versions)


def available_versions(manifest, library_name=None, check_prerelease=False):
    """Return versions from ``manifest`` in the exact shape of get_available_hed_versions().

    Parameters:
        manifest (dict): A supported manifest (see :func:`is_supported`).
        library_name (str or None): None for the standard schema only; "all" for every library as a
                                    dict; or a specific library name.
        check_prerelease (bool): If True, include prerelease versions.

    Returns:
        Union[list, dict]: A list of version strings, or - for "all" - a dict
                           {library_name_or_None: [versions]} with the standard schema under None.
    """
    libraries = manifest.get("libraries", {})
    if library_name == "all":
        result = {}
        for manifest_key in libraries:
            internal_key = None if manifest_key == _STANDARD_MANIFEST_KEY else manifest_key
            versions = _versions_for_key(manifest, manifest_key, check_prerelease)
            if versions:
                result[internal_key] = versions
        return result

    manifest_key = _STANDARD_MANIFEST_KEY if library_name is None else library_name
    return _versions_for_key(manifest, manifest_key, check_prerelease)


def find_version_info(manifest, xml_version, library_name, ref=None):
    """Locate one version in ``manifest`` and return its download info, or None if absent.

    Parameters:
        manifest (dict): A supported manifest.
        xml_version (str): The version string to find.
        library_name (str or None): The library name, None for the standard schema.
        ref (str or None): Git ref for the raw URL. Defaults to the manifest's ``repo_commit`` (so
                           the fetched bytes are immutable and match the recorded SHA), then "main".

    Returns:
        tuple or None: ``(sha, download_url, prerelease)`` matching the ``version_info`` shape that
                       hed_cache._cache_hed_version() consumes, or None if the version is not
                       listed as a released or prerelease version.

    Notes:
        - Only ``released`` and ``prerelease`` versions are searched; ``deprecated`` versions are
          intentionally NOT loadable through this path. Deprecated schemas exist only so the static
          HED schema browser can display them (reading them straight from the manifest); hedtools'
          compute paths (validation, etc.) do not operate on deprecated schemas. This also keeps
          behavior consistent with the REST API fallback, whose crawl skips the ``deprecated``
          folder.
    """
    manifest_key = _STANDARD_MANIFEST_KEY if library_name is None else library_name
    categories = manifest.get("libraries", {}).get(manifest_key, {})
    if ref is None:
        ref = manifest.get("repo_commit") or "main"
    for category, is_prerelease in (("released", False), ("prerelease", True)):
        for entry in categories.get(category, []):
            if entry["version"] == xml_version:
                return (entry["sha"], raw_url_for(entry["file"], ref), is_prerelease)
    return None
