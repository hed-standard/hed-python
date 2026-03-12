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
- :func:`get_hed_versions` — list versions available in the local cache.
- :func:`get_hed_xml_version` — read the HED version string from an XML schema file on disk.
- :func:`cache_xml_versions` — pre-populate the local cache from the HED GitHub
  releases.

See also
--------
``hed.models`` for data structures that *use* a loaded schema (HedString, HedTag,
TabularInput, etc.).
"""

from .hed_schema import HedSchema
from .hed_schema_group import HedSchemaGroup
from .hed_schema_io import load_schema, load_schema_version, from_string, get_hed_xml_version, from_dataframes
from .hed_schema_constants import HedKey, HedSectionKey
from .hed_cache import cache_xml_versions, get_hed_versions, set_cache_directory, get_cache_directory
