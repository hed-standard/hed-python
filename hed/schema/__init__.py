"""HED schema loading, caching, and introspection.

This module exposes everything needed to load and inspect HED schemas — the
vocabularies that define valid HED tags.

Typical usage
-------------
Load a released schema by version number (auto-downloaded and cached)::

    from hed.schema import load_schema_version
    schema = load_schema_version("8.3.0")

Load a schema from a local file or URL::

    from hed.schema import load_schema
    schema = load_schema("/path/to/HED8.3.0.xml")

Load a library schema alongside a standard schema::

    schema = load_schema_version(["8.3.0", "sc:score_1.0.0"])

List what versions exist on GitHub before loading one - e.g. to populate a version-picker
in a UI. This reads a small version manifest from GitHub (or, for custom URLs, crawls small
directory listings), but it never fetches an actual schema file's content. Results are cached
on disk for 60 seconds by default, so calling this on every page load (e.g. from a web
service) won't trip GitHub's rate limits - pass force_refresh=True to bypass that cache when
you need an immediate, up-to-date answer::

    from hed.schema import get_available_hed_versions, load_schema_version

    choices = get_available_hed_versions()          # ['8.4.0', '8.3.0', '8.2.0', ...] -
                                                     # one small manifest read (or a listing
                                                     # crawl for custom URLs), no schema
                                                     # content fetched
    schema = load_schema_version(choices[0])        # the actual schema XML is downloaded
                                                     # and cached here, for just this one
                                                     # version, the first time it's used

Key exports
-----------
- :class:`HedSchema` — a single loaded schema; use it to validate tags.
- :class:`HedSchemaGroup` — two or more schemas used together (base + libraries).
- :func:`load_schema` — load from a file path or URL.
- :func:`load_schema_version` — load by version string(s), with caching.
- :func:`from_string` — parse a schema from an in-memory string.
- :func:`from_dataframes` — reconstruct a schema from TSV DataFrames.
- :data:`HedKey` / :data:`HedSectionKey` — enumerations of schema attribute and
  section names used when querying schema entries.
- :func:`get_hed_versions` — list versions already available in the local cache
  (bundled with hedtools, or previously downloaded). No network calls.
- :func:`get_available_hed_versions` — list versions available on GitHub right now,
  without downloading any of them. Caches its own result on disk for a short time (60s by
  default), so it's safe to call on every request without extra throttling by the caller;
  see the example above.
- :func:`get_hed_xml_version` — read the HED version string from an XML schema file on disk.
- :func:`cache_xml_versions` — pre-populate the local cache from the HED GitHub
  releases. This downloads every discovered version's content and should not
  be called on a user-facing hot path; prefer get_available_hed_versions() to
  list what's available and let load_schema_version() fetch a specific
  version lazily, on demand.

See also
--------
``hed.models`` for data structures that *use* a loaded schema (HedString, HedTag,
TabularInput, etc.).
"""

from .hed_schema import HedSchema
from .hed_schema_group import HedSchemaGroup
from .hed_schema_io import load_schema, load_schema_version, from_string, get_hed_xml_version, from_dataframes
from .hed_schema_constants import HedKey, HedSectionKey
from .hed_cache import (
    cache_xml_versions,
    get_hed_versions,
    get_available_hed_versions,
    set_cache_directory,
    get_cache_directory,
)
