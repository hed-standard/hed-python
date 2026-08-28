"""Combine the schemas of a merge group into one vocabulary (HED spec 3.1.2.4).

Loading a version specification has three separable steps, and this module owns the last two:

1. Resolve each version string to a file (``hed.schema.hed_schema_io`` and the cache).
2. **Prepass** (:func:`resolve_group`): construct a loader for every file. Constructing a
   :class:`~hed.schema.schema_io.base2schema.SchemaLoader` reads only the header attributes, so
   the group rules - duplicates, two versions of one schema, a single standard partner, an
   unpartnered library alone, a listed standard matching the partner - are decided and the load
   order chosen before any file body is parsed. A group that breaks a rule fails here.
3. **Merge** (:func:`merge_group`): pick the base - a merged library file if the group has one
   (it already contains the whole standard, so the standard is never loaded separately), else one
   copy of the cached standard partner - then parse each remaining member as what its file is
   (library-only for unmerged files, full for merged files) and insert its elements with the
   element compatibility rules applied to whatever is already present.

``load_schema`` on a single unmerged file is the degenerate case: one member, standard copied once.

Package-internal: nothing here is part of the public ``hed.schema`` API.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field

from hed.errors.exceptions import HedExceptions, HedFileError
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_constants import (
    LIBRARY_ATTRIBUTE,
    UNMERGED_ATTRIBUTE,
    VERSION_ATTRIBUTE,
    WITH_STANDARD_ATTRIBUTE,
    HedKey,
    HedSectionKey,
)
from hed.schema.hed_schema_entry import HedSchemaEntry
from hed.schema.schema_io.base2schema import SchemaLoader

# Sections merged by name, in loader order (domains before their users). Unit classes
# and their units are handled together; tags last.
_SIMPLE_SECTIONS = (
    HedSectionKey.Properties,
    HedSectionKey.Attributes,
    HedSectionKey.UnitModifiers,
)


@dataclass
class GroupSpec:
    """The load plan for one merge group, decided from headers before any body is parsed.

    Attributes:
        partner (str): The standard schema version the group's libraries are partnered with
            ("" only when the group is a single unpartnered library or a single standard).
        members (list[SchemaLoader]): Header-only loaders for the library schemas, in listed
            order with duplicates and listed standards removed. Each is parsed by ``merge_group``.
        base (SchemaLoader or None): The member whose file already contains the whole standard
            (a merged library file), or the lone standard/unpartnered schema when there are no
            partnered libraries. None means "copy the cached standard partner".
        name (str): User supplied identifier for the group, used in error messages.
    """

    partner: str
    members: list[SchemaLoader]
    base: SchemaLoader | None = None
    name: str = field(default="")


def resolve_group(loaders: list[SchemaLoader], name: str = "") -> GroupSpec:
    """Decide from headers alone whether a merge group is legal and how to load it.

    Parameters:
        loaders (list[SchemaLoader]): One header-only loader per version string, in listed order.
        name (str): Identifier for messages.

    Returns:
        GroupSpec: The load plan.

    Raises:
        HedFileError: SCHEMA_LOAD_FAILED with one issue per violated rule (all rules are checked).
    """
    members = _drop_duplicates(loaders)
    issues = []
    issues += _check_one_version_per_schema(members)
    libraries = [loader for loader in members if loader.schema.library]
    standards = [loader for loader in members if not loader.schema.library]
    if len(members) > 1:
        for loader in libraries:
            if not loader.schema.with_standard:
                issues.append(
                    _rule_issue(f"Unpartnered library schema '{loader.schema.version}' must be alone in its namespace")
                )
    partners = sorted({loader.schema.with_standard for loader in libraries if loader.schema.with_standard})
    if len(partners) > 1:
        issues.append(_rule_issue(f"Library schemas in one merge group have different partners: {partners}"))
    partner = partners[0] if len(partners) == 1 else ""
    for loader in standards:
        if partner and loader.schema.version_number != partner:
            issues.append(
                _rule_issue(
                    f"Standard schema '{loader.schema.version_number}' differs from the group partner '{partner}'"
                )
            )
    if issues:
        versions = [loader.schema.version for loader in loaders]
        raise HedFileError(
            HedExceptions.SCHEMA_LOAD_FAILED,
            f"Cannot combine schemas {versions}: " + "; ".join(issue["message"] for issue in issues),
            filename=name,
            issues=issues,
        )

    if not libraries:
        # Only (identical) standards, or nothing partnered: the single remaining schema is the result.
        return GroupSpec(partner=partner, members=[], base=members[0], name=name)
    base = next((loader for loader in libraries if loader.schema.merged), None)
    if not partner:
        base = libraries[0]  # a single unpartnered library
    return GroupSpec(partner=partner, members=libraries, base=base, name=name)


def merge_group(spec: GroupSpec, load_partner: Callable[[str], HedSchema]) -> HedSchema:
    """Execute a load plan: parse the members and combine them into one finished schema.

    Parameters:
        spec (GroupSpec): The plan from :func:`resolve_group` (or a single-member plan).
        load_partner (Callable[[str], HedSchema]): Returns the shared, cached standard schema for a
            version string; used only when ``spec.base`` is None. The result is deep-copied, never
            modified.

    Returns:
        HedSchema: A finished, finalized schema.

    Raises:
        HedFileError: SCHEMA_LOAD_FAILED with one issue per incompatible element.
        HedFileError: SCHEMA_LIBRARY_INVALID when a rooted tag names an anchor that is not a
            standard schema tag.
    """
    if spec.base is not None:
        result = spec.base._load()
    else:
        result = copy.deepcopy(load_partner(spec.partner))
        for section in result._sections.values():
            section._attribute_cache = {}
    if not spec.members:
        return result

    loaded = [result if member is spec.base else member._load() for member in spec.members]
    issues = []
    for member, library in zip(spec.members, loaded, strict=True):
        if member is not spec.base:
            issues += merge_into(result, library)
    if issues:
        raise HedFileError(
            HedExceptions.SCHEMA_LOAD_FAILED,
            f"{len(issues)} incompatible element(s) found while merging schemas {[s.version for s in loaded]}",
            filename=spec.name or loaded[0].name,
            issues=issues,
        )

    first = loaded[0]
    result.header_attributes = _merged_header(spec, loaded)
    result.filename = first.filename
    result.name = first._name
    result.source_format = first.source_format
    result.prologue = first.prologue
    result.epilogue = first.epilogue
    if first is not result:
        # Single-file loading never carried the partner's extras into an unmerged library's result;
        # the extras_in_library item covers inLibrary bookkeeping on extras rows.
        result.extras = {key: df.copy() for key, df in first.extras.items()}
    result.finalize_dictionaries()
    return result


def merge_into(result: HedSchema, library: HedSchema) -> list[dict]:
    """Insert one library's elements into ``result``, checking compatibility with what is present.

    Only entries carrying ``inLibrary`` in their own attributes are considered: the rest of a
    merged-form library is the shared standard. Elements absent from ``result`` are inserted as
    fresh entries built by ``result``'s own sections; elements already present must match
    (same attributes apart from ``inLibrary``, same description, same ancestor path, same ``#``
    child presence) and then accumulate the library name in their ``inLibrary`` value. An element
    that collides with a standard schema element, or that its own library declares twice, is
    inserted through the section so that it is recorded in ``duplicate_names`` and reported by
    schema compliance, as single-file loading does.

    Parameters:
        result (HedSchema): The schema being built (a private object, already finalized once).
        library (HedSchema): The library to insert, full or library-only form.

    Returns:
        list[dict]: One issue dict per incompatible element; empty if the library merged cleanly.
    """
    issues = []
    for key in _SIMPLE_SECTIONS:
        for entry in library[key].all_entries:
            if HedKey.InLibrary in entry.attributes:
                issues += _merge_named_entry(result, library, entry, key, entry.name)
    issues += _merge_unit_classes(result, library)
    for entry in library.value_classes.all_entries:
        if HedKey.InLibrary in entry.attributes:
            issues += _merge_named_entry(result, library, entry, HedSectionKey.ValueClasses, entry.name)
    issues += _merge_tags(result, library)
    return issues


def element_differences(existing: HedSchemaEntry, entry: HedSchemaEntry) -> list[str]:
    """Describe how two declarations of the same-named element differ, ignoring ``inLibrary``.

    Parameters:
        existing (HedSchemaEntry): The entry already in the merged result.
        entry (HedSchemaEntry): The library's declaration.

    Returns:
        list[str]: Human-readable differences; empty when the declarations are compatible.
    """
    differences = []
    if (existing.description or "") != (entry.description or ""):
        differences.append("description differs")
    left = {k: v for k, v in existing.attributes.items() if k != HedKey.InLibrary}
    right = {k: v for k, v in entry.attributes.items() if k != HedKey.InLibrary}
    if not HedSchemaEntry._compare_attributes_no_order(left, right):
        differences.append(f"attributes differ ({left} vs {right})")
    return differences


# ---------------------------------------------------------------------------
# Prepass helpers
# ---------------------------------------------------------------------------


def _drop_duplicates(loaders):
    """Keep the first loader for each (library, version) header pair (spec: duplicates are ignored)."""
    seen = set()
    kept = []
    for loader in loaders:
        key = (loader.schema.library, loader.schema.version_number)
        if key not in seen:
            seen.add(key)
            kept.append(loader)
    return kept


def _check_one_version_per_schema(members):
    by_library = {}
    for loader in members:
        by_library.setdefault(loader.schema.library, []).append(loader.schema.version_number)
    issues = []
    for library, versions in by_library.items():
        if len(versions) > 1:
            what = f"library '{library}'" if library else "the standard schema"
            issues.append(_rule_issue(f"Different versions of {what} in one merge group: {versions}"))
    return issues


def _rule_issue(message):
    return {"code": HedExceptions.SCHEMA_LOAD_FAILED, "message": message}


# ---------------------------------------------------------------------------
# Section-specific merging
# ---------------------------------------------------------------------------


def _merge_named_entry(result, library, entry, key, target_name, unit_class=None):
    """Merge one non-tag entry looked up by name; returns issues."""
    existing = result[key].get(target_name)
    if existing is None or _is_duplicate_declaration(existing, library):
        # New element, or a duplicate declaration (recorded in duplicate_names by the section).
        new_entry = _insert_entry(result, entry, key, target_name)
        if unit_class is not None:
            unit_class.add_unit(new_entry)
        return []
    differences = element_differences(existing, entry)
    if differences:
        return [_conflict_issue(library, existing, entry, key, differences)]
    _accumulate_in_library(existing, library.library)
    return []


def _merge_unit_classes(result, library):
    issues = []
    for unit_class in library.unit_classes.all_entries:
        target_class = result.unit_classes.get(unit_class.name)
        if HedKey.InLibrary in unit_class.attributes and (
            target_class is None or not _is_unit_class_placeholder(unit_class)
        ):
            # A new class, or a redeclaration of an existing one; a bare redeclaration of an existing
            # class is the placeholder that only adds units (HedSchemaUnitClassSection._check_if_duplicate).
            issues += _merge_named_entry(result, library, unit_class, HedSectionKey.UnitClasses, unit_class.name)
            target_class = result.unit_classes.get(unit_class.name)
        if target_class is None:
            continue
        for unit in unit_class._units:
            if HedKey.InLibrary in unit.attributes:
                issues += _merge_named_entry(result, library, unit, HedSectionKey.Units, unit.name, target_class)
    return issues


def _is_duplicate_declaration(existing, library):
    """True if ``library`` redeclares an element it cannot share: a standard element, or its own.

    Sharing (spec 3.1.2.4 element compatibility) is between DIFFERENT libraries. A library element
    colliding with a standard schema element, or declared twice by the same library, is a duplicate
    and is recorded as such, exactly as single-file loading records it.
    """
    declared_by = existing.attributes.get(HedKey.InLibrary)
    return not declared_by or library.library in declared_by.split(",")


def _is_unit_class_placeholder(unit_class):
    """A unit class declared only to add units to an existing class (see HedSchemaUnitClassSection)."""
    return len(unit_class.attributes) == 1 and HedKey.InLibrary in unit_class.attributes and not unit_class.description


def _merge_tags(result, library):
    issues = []
    # all_entries is in parse (depth-first, parents-first) order in both library forms; keep it so the
    # merged result orders siblings exactly as a merged file would.
    entries = [entry for entry in library.tags.all_entries if HedKey.InLibrary in entry.attributes]
    rooted_paths = {}
    for entry in entries:
        target_name = _target_tag_name(result, library, entry, rooted_paths)
        is_placeholder = target_name.endswith("/#")
        existing = result.tags.get(target_name) if is_placeholder else result.tags.get(entry.short_tag_name)
        if existing is None or _is_duplicate_declaration(existing, library):
            # New element, or a duplicate declaration (recorded in duplicate_names by the section).
            _insert_entry(result, entry, HedSectionKey.Tags, target_name)
            continue
        differences = element_differences(existing, entry)
        target_long = target_name[:-2] if is_placeholder else target_name
        if existing.long_tag_name.casefold() != target_long.casefold():
            differences.append(f"ancestor path differs ('{existing.long_tag_name}' vs '{target_long}')")
        elif not is_placeholder:
            has_placeholder_here = result.tags.get(existing.long_tag_name + "/#") is not None
            has_placeholder_there = library.tags.get(entry.name + "/#") is not None
            if has_placeholder_here != has_placeholder_there:
                differences.append("'#' child present in only one declaration")
        if differences:
            issues.append(_conflict_issue(library, existing, entry, HedSectionKey.Tags, differences))
            continue
        _accumulate_in_library(existing, library.library)
    return issues


def _target_tag_name(result, library, entry, rooted_paths):
    """Return the long name the entry gets in the merged result.

    Merged-form libraries already carry full paths. Library-only schemas keep rooted tags at the
    root, so a root tag with ``rooted=X`` is placed under the standard tag ``X`` and its
    descendants follow - the placement the loaders perform when the partner is present.
    """
    if library.merged:
        return entry.name
    first, separator, rest = entry.name.partition("/")
    if not separator:
        anchor_name = entry.attributes.get(HedKey.Rooted)
        if not anchor_name:
            return entry.name
        anchor = result.tags.get(anchor_name)
        if anchor is None or HedKey.InLibrary in anchor.attributes:
            message = f"Rooted tag '{entry.short_tag_name}' not found in paired standard schema"
            raise HedFileError(
                HedExceptions.SCHEMA_LIBRARY_INVALID,
                message,
                library.name,
                issues=[{"code": HedExceptions.SCHEMA_LIBRARY_INVALID, "message": message, "filename": library.name}],
            )
        rooted_paths[first] = anchor.long_tag_name + "/" + first
        return rooted_paths[first]
    if first in rooted_paths:
        return rooted_paths[first] + "/" + rest
    return entry.name


# ---------------------------------------------------------------------------
# Entry construction and bookkeeping
# ---------------------------------------------------------------------------


def _insert_entry(result, entry, key, target_name):
    """Create a fresh entry in ``result``'s section from ``entry``'s declaration and add it."""
    new_entry = result._create_tag_entry(target_name, key)
    # Update in place: a new HedTagEntry aliases inherited_attributes to this dict until finalize,
    # and the tag section sorts on inLibrary through that alias before finalizing entries.
    new_entry.attributes.update(entry.attributes)
    new_entry.description = entry.description
    if entry._unknown_attributes:
        new_entry._unknown_attributes = dict(entry._unknown_attributes)
    result._add_tag_to_dict(target_name, new_entry, key)
    return new_entry


def _accumulate_in_library(existing, library_name):
    libraries = existing.attributes[HedKey.InLibrary].split(",")
    if library_name not in libraries:
        existing.attributes[HedKey.InLibrary] = ",".join(libraries + [library_name])
        inherited = getattr(existing, "inherited_attributes", None)
        if inherited is not None and inherited is not existing.attributes:
            inherited[HedKey.InLibrary] = existing.attributes[HedKey.InLibrary]


def _conflict_issue(library, existing, entry, key, differences):
    return {
        "code": HedExceptions.SCHEMA_LOAD_FAILED,
        "message": (
            f"Element '{entry.name}' in section '{key.value}' declared by "
            f"'{existing.attributes[HedKey.InLibrary]}' and '{library.library}' is incompatible: "
            + "; ".join(differences)
        ),
        "filename": library.name,
    }


def _merged_header(spec, loaded):
    header = dict(loaded[0].header_attributes)
    header.pop(UNMERGED_ATTRIBUTE, None)
    header[VERSION_ATTRIBUTE] = ",".join(schema.version_number for schema in loaded)
    header[LIBRARY_ATTRIBUTE] = ",".join(schema.library for schema in loaded)
    if spec.partner:
        header[WITH_STANDARD_ATTRIBUTE] = spec.partner
    return header
