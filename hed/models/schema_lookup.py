"""Schema lookup table for ancestor-aware string search.

Generates a compact mapping from every tag's casefolded short name to its
full ``tag_terms`` tuple (all slash-path components from root to self), which
is the same information stored in :attr:`~hed.schema.HedTagEntry.tag_terms` after
schema loading.

This lookup table is used by :func:`~hed.models.string_search.parse_hed_string`
and :class:`~hed.models.string_search.StringQueryHandler` to enable ancestor search
on short-form HED strings without requiring a full schema object at search time.

Typical workflow::

    from hed.schema import load_schema_version
    from hed.models.schema_lookup import generate_schema_lookup, save_schema_lookup

    schema = load_schema_version("8.4.0")
    lookup = generate_schema_lookup(schema)
    # Optionally persist:
    save_schema_lookup(lookup, "hed_8.4.0_lookup.json")

The lookup dict maps::

    {
        "sensory-event": ("event", "sensory-event"),
        "event": ("event",),
        ...
    }

Keys are casefolded short tag names (last slash-component). Values are tuples
of casefolded path components from the schema root to the tag (inclusive),
matching exactly what :attr:`~hed.schema.HedTagEntry.tag_terms` contains.
"""

from __future__ import annotations

import json
from pathlib import Path

from hed.schema.hed_schema_constants import HedSectionKey


def generate_schema_lookup(schema):
    """Build a schema lookup table mapping short tag names to their ``tag_terms``.

    Walks the tags section of *schema* (or all component schemas in a
    :class:`~hed.schema.HedSchemaGroup`) and collects each tag's
    :attr:`~hed.schema.HedTagEntry.tag_terms` tuple, keyed by the tag's
    casefolded short name.

    Parameters:
        schema (HedSchema or HedSchemaGroup): The loaded HED schema.

    Returns:
        dict[str, tuple[str, ...]]: Mapping ``short_tag_casefold`` →
            ``tag_terms`` tuple as stored in the schema entry.

    Notes:
        - Tags whose ``/#`` value placeholder end-entry is skipped (they share
          the parent tag's short name with a trailing ``/#`` which is already
          stripped by the schema loader).
        - For :class:`~hed.schema.HedSchemaGroup`, all member schemas are
          merged; later schemas overwrite earlier ones on key collision.
        - Library namespace prefixes (e.g. ``"sc:"`` in ``"sc:Event"``) are
          **not** stripped — include the namespace when searching if needed.
    """
    lookup = {}

    # Handle HedSchemaGroup by iterating component schemas
    schemas = _iter_schemas(schema)
    for sch in schemas:
        tags_section = sch._sections.get(HedSectionKey.Tags)
        if tags_section is None:
            continue
        for name, entry in tags_section.items():
            # Skip value-placeholder entries (e.g. "Event/#") — they are internal
            if name.endswith("/#"):
                continue
            if not hasattr(entry, "tag_terms") or not entry.tag_terms:
                continue
            # short_tag_name is the last slash component (already set on HedTagEntry)
            short_name = getattr(entry, "short_tag_name", None)
            if short_name is None:
                # Fall back: last slash component of name
                short_name = name.rsplit("/", 1)[-1]
            key = short_name.casefold()
            lookup[key] = entry.tag_terms  # already a tuple of casefolded strings

    return lookup


def _iter_schemas(schema):
    """Yield individual HedSchema objects from a schema or schema group.

    Parameters:
        schema (HedSchema or HedSchemaGroup): The schema to iterate.

    Yields:
        HedSchema: Individual schema objects.
    """
    # HedSchemaGroup has a 'schemas' dict or list attribute
    if hasattr(schema, "schemas"):
        schemas_attr = schema.schemas
        if isinstance(schemas_attr, dict):
            yield from schemas_attr.values()
        else:
            yield from schemas_attr
    else:
        yield schema


def save_schema_lookup(lookup, path):
    """Serialise a schema lookup dict to a JSON file.

    Values (tuples) are saved as JSON arrays and restored as tuples on load.

    Parameters:
        lookup (dict[str, tuple]): The lookup dict from :func:`generate_schema_lookup`.
        path (str or Path): Destination file path.
    """
    serialisable = {k: list(v) for k, v in lookup.items()}
    Path(path).write_text(json.dumps(serialisable, indent=2), encoding="utf-8")


def load_schema_lookup(path):
    """Load a schema lookup dict previously saved with :func:`save_schema_lookup`.

    Parameters:
        path (str or Path): The JSON file to load.

    Returns:
        dict[str, tuple[str, ...]]: The schema lookup dict with tuple values.
    """
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {k: tuple(v) for k, v in raw.items()}
