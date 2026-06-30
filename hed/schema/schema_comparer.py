"""Compare HED schemas and generate structured changelog reports.

This module provides tools for analyzing differences between HED schema versions or variants.
It supports fine-grained comparisons at the entry level (tags, units, properties, etc.),
detection of schema metadata changes, and structured changelog generation suitable for
documentation and version control. All changes are categorized by severity (Major, Minor,
Patch, Unknown) and organized by schema section for easy interpretation.

Typical workflow:
    1. Load two HED schema versions using HedSchema or HedSchemaGroup
    2. Create a SchemaComparer with both schemas
    3. Call compare_schemas() for raw comparison data or gather_schema_changes() for
       categorized changes
    4. Use pretty_print_change_dict() to format for human reading or export

Example:
    >>> from hed import load_schema_version
    >>> from hed.schema.schema_comparer import SchemaComparer
    >>> schema_v83 = load_schema_version("8.3.0")
    >>> schema_v84 = load_schema_version("8.4.0")
    >>> comparer = SchemaComparer(schema_v83, schema_v84)
    >>> changes = comparer.gather_schema_changes()
    >>> print(comparer.pretty_print_change_dict(changes))
"""

import pandas as pd
from collections import defaultdict

from hed.schema.hed_schema import HedKey
from hed.schema.hed_schema_constants import HedSectionKey
from hed.schema.schema_io.df_constants import (
    EXTERNAL_ANNOTATION_KEY,
    PREFIXES_KEY,
    SOURCES_KEY,
    UNIQUE_EXTRAS_KEYS,
    in_library as _in_library,
)


class SchemaComparer:
    """Compare two HED schemas and generate structured change documentation.

    This class enables detailed, section-by-section comparison of HED schemas with support
    for filtering by attributes (e.g., InLibrary only). Comparisons identify matching entries,
    entries present only in one schema, and entries with the same name but differing attributes.
    Supports analysis of schema metadata (prologue, epilogue, headers), multi-value attributes
    (suggestedTag, relatedTag), and structured data (Sources, Prefixes, extras).

    All changes are categorized by severity level (Major for significant breaking changes,
    Minor for backward-compatible additions, Patch for attribute updates, Unknown for
    unclassified changes) and organized by schema section for easy navigation and reporting.

    Attributes:
        schema1 (HedSchema): The first schema to compare (typically older or baseline version).
        schema2 (HedSchema): The second schema to compare (typically newer or variant version).
        MISC_SECTION (str): Internal key for schema metadata changes (prologue, epilogue).
        HED_ID_SECTION (str): Internal key for HED ID attribute changes.
        EXTRAS_SECTION (str): Internal key for extras (Sources, Prefixes) changes.
        SOURCES (str): Key for Sources extras section.
        PREFIXES (str): Key for Prefixes extras section.
        ANNOTATION_PROPERTY_EXTERNAL (str): Key for AnnotationPropertyExternal extras.
        SECTION_ENTRY_NAMES (dict): Maps HedSectionKey to singular form (e.g., "Tag").
        SECTION_ENTRY_NAMES_PLURAL (dict): Maps HedSectionKey to plural form (e.g., "Tags").
    """

    # Class-level constants
    MISC_SECTION = "misc"
    HED_ID_SECTION = "HedId changes"
    EXTRAS_SECTION = "Extras changes"
    SOURCES = SOURCES_KEY
    PREFIXES = PREFIXES_KEY
    ANNOTATION_PROPERTY_EXTERNAL = EXTERNAL_ANNOTATION_KEY

    SECTION_ENTRY_NAMES = {
        HedSectionKey.Tags: "Tag",
        HedSectionKey.Units: "Unit",
        HedSectionKey.UnitClasses: "Unit Class",
        HedSectionKey.ValueClasses: "Value Class",
        HedSectionKey.UnitModifiers: "Unit Modifier",
        HedSectionKey.Properties: "Property",
        HedSectionKey.Attributes: "Attribute",
        MISC_SECTION: "Misc Metadata",
        HED_ID_SECTION: "Modified Hed Ids",
        SOURCES: "Sources",
        PREFIXES: "Prefixes",
        ANNOTATION_PROPERTY_EXTERNAL: "AnnotationPropertyExternal",
    }

    SECTION_ENTRY_NAMES_PLURAL = {
        HedSectionKey.Tags: "Tags",
        HedSectionKey.Units: "Units",
        HedSectionKey.UnitClasses: "Unit Classes",
        HedSectionKey.ValueClasses: "Value Classes",
        HedSectionKey.UnitModifiers: "Unit Modifiers",
        HedSectionKey.Properties: "Properties",
        HedSectionKey.Attributes: "Attributes",
        MISC_SECTION: "Misc Metadata",
        HED_ID_SECTION: "Modified Hed Ids",
        EXTRAS_SECTION: "Extras",
        SOURCES: "Sources",
        PREFIXES: "Prefixes",
        ANNOTATION_PROPERTY_EXTERNAL: "AnnotationPropertyExternal",
    }

    def __init__(self, schema1, schema2):
        """Initialize the SchemaComparer with two schemas.

        Parameters:
            schema1 (HedSchema): The first schema to compare (typically older version).
                               Will be treated as the baseline for comparison.
            schema2 (HedSchema): The second schema to compare (typically newer version).
                               Differences are relative to schema1.

        Raises:
            TypeError: If either schema is not a valid HedSchema instance.
        """
        self.schema1 = schema1
        self.schema2 = schema2

    def find_matching_tags(self, sections=(HedSectionKey.Tags,), return_string=True):
        """Find entries with matching names in both schemas.

        This method identifies all entries that exist in both schemas with the same name,
        regardless of whether their attributes differ. Includes both exact matches and
        entries with the same name but different attributes (unequal entries).

        Parameters:
            sections (tuple): Tuple of HedSectionKey values indicating which sections to compare.
                            Default is (HedSectionKey.Tags,). Set to None to compare all sections.
            return_string (bool): If True, return formatted string. If False, return dictionary.
                                 Default is True.

        Returns:
            str or dict: If return_string is True, returns formatted string listing all matching
                        entries organized by section. If False, returns dictionary mapping section
                        keys to dictionaries of matching entries (combines exact matches and
                        unequal entries with same names).

        Example:
            >>> comparer = SchemaComparer(schema1, schema2)
            >>> output = comparer.find_matching_tags(return_string=True)
            >>> print(output)  # Displays formatted list by section
        """
        matches, _, _, unequal_entries = self.compare_schemas(sections=sections)
        header_summary = self._get_tag_name_summary((matches, unequal_entries))

        # Combine the two dictionaries
        for section_key, section_dict in matches.items():
            section_dict.update(unequal_entries[section_key])

        if return_string:
            final_string = "Nodes with matching names:\n"
            final_string += self._pretty_print_header(header_summary)
            return final_string
        return matches

    def compare_schemas(self, attribute_filter=HedKey.InLibrary, sections=(HedSectionKey.Tags,)):
        """Compare two schemas section by section, categorizing entries by match status.

        This is the core comparison method that categorizes all schema entries into four groups:
        matches (identical entries), entries only in schema1, entries only in schema2, and
        entries with the same name but different attributes. For Tags, the short_tag_name
        is used as the matching key; for other sections, the name attribute is used.

        The comparison also examines schema metadata including save header attributes,
        prologue, and epilogue when miscellaneous sections are included.

        Parameters:
            attribute_filter (HedKey or None): If provided, only entries with this attribute are
                                              compared (e.g., HedKey.InLibrary filters to library
                                              entries only). Set to None to compare all entries.
                                              Default is HedKey.InLibrary.
            sections (tuple or None): Tuple of HedSectionKey values to compare. If None, compares
                                     all sections including miscellaneous metadata. Default is
                                     (HedSectionKey.Tags,).

        Returns:
            tuple: Four dictionaries (matches, not_in_schema1, not_in_schema2, unequal_entries):
                - matches (dict): Dict[section_key -> Dict[name -> (entry1, entry2)]]
                  Entries identical in both schemas
                - not_in_schema1 (dict): Dict[section_key -> Dict[name -> entry]]
                  Entries only in schema2 (added in schema2)
                - not_in_schema2 (dict): Dict[section_key -> Dict[name -> entry]]
                  Entries only in schema1 (removed from schema2)
                - unequal_entries (dict): Dict[section_key -> Dict[name -> (entry1, entry2)]]
                  Entries with same name but different attributes or values

        Example:
            >>> matches, added, removed, modified = comparer.compare_schemas(
            ...     attribute_filter=HedKey.InLibrary,
            ...     sections=(HedSectionKey.Tags, HedSectionKey.Units)
            ... )
            >>> for tag, (e1, e2) in matches[HedSectionKey.Tags].items():
            ...     print(f"Tag {tag} unchanged")
        """
        matches, not_in_schema2, not_in_schema1, unequal_entries = {}, {}, {}, {}

        # Handle miscellaneous sections
        if sections is None or self.MISC_SECTION in sections:
            unequal_entries[self.MISC_SECTION] = {}
            if self.schema1.get_save_header_attributes() != self.schema2.get_save_header_attributes():
                unequal_entries[self.MISC_SECTION]["header_attributes"] = (
                    str(self.schema1.get_save_header_attributes()),
                    str(self.schema2.get_save_header_attributes()),
                )
            if self.schema1.prologue != self.schema2.prologue:
                unequal_entries[self.MISC_SECTION]["prologue"] = (self.schema1.prologue, self.schema2.prologue)
            if self.schema1.epilogue != self.schema2.epilogue:
                unequal_entries[self.MISC_SECTION]["epilogue"] = (self.schema1.epilogue, self.schema2.epilogue)

        # Compare sections
        for section_key in HedSectionKey:
            if sections is not None and section_key not in sections:
                continue
            dict1, dict2 = {}, {}
            section1, section2 = self.schema1[section_key], self.schema2[section_key]
            name_attribute = "short_tag_name" if section_key == HedSectionKey.Tags else "name"

            for entry in section1.all_entries:
                if not attribute_filter or entry.has_attribute(attribute_filter):
                    dict1[getattr(entry, name_attribute)] = entry

            for entry in section2.all_entries:
                if not attribute_filter or entry.has_attribute(attribute_filter):
                    dict2[getattr(entry, name_attribute)] = entry

            not_in_schema2[section_key] = {key: dict1[key] for key in dict1 if key not in dict2}
            not_in_schema1[section_key] = {key: dict2[key] for key in dict2 if key not in dict1}
            unequal_entries[section_key] = {
                key: (dict1[key], dict2[key]) for key in dict1 if key in dict2 and dict1[key] != dict2[key]
            }
            matches[section_key] = {
                key: (dict1[key], dict2[key]) for key in dict1 if key in dict2 and dict1[key] == dict2[key]
            }

        return matches, not_in_schema1, not_in_schema2, unequal_entries

    def gather_schema_changes(self, attribute_filter=None):
        """Generate a structured changelog by comparing the two schemas.

        This is the primary method for understanding what changed between schemas. It performs
        a comprehensive comparison, categorizes all differences by severity level, and handles
        specialized comparisons for different entry types (tags, units, etc.) and attributes.
        Results are organized by schema section for easy navigation.

        Severity levels:
        - Major: Breaking changes (tag removed, unit class removed from tag)
        - Minor: Backward-compatible additions or inherited attribute changes (tag added, unit added)
        - Patch: Non-breaking modifications (attribute changed, description updated, position moved)
        - Unknown: Unclassified changes

        Parameters:
            attribute_filter (HedKey or None): If provided, only entries with this attribute are
                                              compared (e.g., compare only library entries).
                                              Set to None to compare all entries. Default is None.

        Returns:
            dict: Dictionary mapping section keys to lists of change dictionaries. Organized as:
                  {section_key -> [{"change_type": str, "change": str, "tag": str}, ...]}
                  where:
                  - section_key: HedSectionKey (Tags, Units, etc.) or special key (Misc, HedId)
                  - change_type: "Major", "Minor", "Patch", or "Unknown"
                  - change: Description of the change
                  - tag: Name of affected entry

        Example:
            >>> changes = comparer.gather_schema_changes()
            >>> for section, changes_list in changes.items():
            ...     print(f"\n{section}:")
            ...     for change in changes_list:
            ...         print(f"  {change['tag']}: {change['change']}")
        """
        _, not_in_1, not_in_2, unequal_entries = self.compare_schemas(attribute_filter=attribute_filter, sections=None)
        change_dict = defaultdict(list)
        self._add_removed_items(change_dict, not_in_2)
        self._add_added_items(change_dict, not_in_1)
        self._add_unequal_entries(change_dict, unequal_entries)
        self._add_extras_changes(change_dict)
        self._sort_changes_by_severity(change_dict)
        return {key: change_dict[key] for key in self.SECTION_ENTRY_NAMES if key in change_dict}

    def pretty_print_change_dict(self, change_dict, title="Schema changes", use_markdown=True):
        """Format a change dictionary into a human-readable string.

        Converts the structured change dictionary from gather_schema_changes into a formatted
        text report suitable for display in terminals, documentation, or markdown files.
        Changes are sorted by severity level within each section and organized by section type.

        Parameters:
            change_dict (dict): Dictionary of changes as returned by gather_schema_changes.
                              Format: {section_key -> [{"change_type": str, "change": str, "tag": str}]}
            title (str): Title for the change report. Default is "Schema changes".
            use_markdown (bool): If True, use markdown formatting with bold headers (** **) and
                                bullet point prefixes (" - "). If False, use plain text with
                                tabs for indentation. Default is True.

        Returns:
            str: Formatted string representation of the changes. Sections are sorted by order
                 in SECTION_ENTRY_NAMES, changes within each section sorted by severity
                 (Major → Minor → Patch → Unknown). Empty if change_dict is empty.

        Example:
            >>> changes = comparer.gather_schema_changes()
            >>> output = comparer.pretty_print_change_dict(
            ...     changes,
            ...     title="HED 8.3.0 → 8.4.0 Changes",
            ...     use_markdown=True
            ... )
            >>> print(output)
            >>> # Can be written to file for changelog documentation
        """
        final_strings = []
        line_prefix = " - " if use_markdown else "\t"
        if change_dict:
            final_strings.append(title)
            final_strings.append("")  # add blank line
            for section_key, section_dict in change_dict.items():
                name = self.SECTION_ENTRY_NAMES_PLURAL.get(section_key, section_key)
                line_endings = "**" if use_markdown else ""
                final_strings.append(f"{line_endings}{name}:{line_endings}")
                for item in section_dict:
                    change, tag, change_type = item["change"], item["tag"], item["change_type"]
                    final_strings.append(f"{line_prefix}{tag} ({change_type}): {change}")
                final_strings.append("")
        return "\n".join(final_strings)

    def compare_differences(self, attribute_filter=None, title=""):
        """Compare two schemas and return a formatted report of all differences.

        Convenience method that combines gather_schema_changes() and pretty_print_change_dict()
        to produce a complete, human-readable comparison report in one call. If no title is
        provided, generates a descriptive title from the schema names.

        Parameters:
            attribute_filter (HedKey or None): If provided, only entries with this attribute are
                                              compared. Set to None to compare all entries.
                                              Default is None.
            title (str): Custom title for the report. If empty string (default), generates a
                        title like "Differences between SchemaName1 and SchemaName2".

        Returns:
            str: Formatted markdown string describing all differences between the schemas.
                 Suitable for printing, saving to changelog files, or displaying in documentation.

        Example:
            >>> report = comparer.compare_differences()
            >>> print(report)
            >>> # Or save to file
            >>> with open("CHANGELOG.md", "a") as f:
            ...     f.write(report)
        """
        changelog = self.gather_schema_changes(attribute_filter=attribute_filter)
        if not title:
            title = f"Differences between {self.schema1.name} and {self.schema2.name}"
        return self.pretty_print_change_dict(changelog, title=title)

    # Private helper methods

    def _pretty_print_header(self, summary_dict):
        """Format a summary dictionary of tag names by section into a string.

        Converts a dictionary of section names to tag/entry names into a human-readable
        multi-line summary. Each section appears as a header with comma-separated names.

        Parameters:
            summary_dict (dict): Dictionary mapping section keys to lists of tag/entry names.
                              Format: {section_key -> [name1, name2, ...]}

        Returns:
            str: Formatted string with section headers (from SECTION_ENTRY_NAMES_PLURAL)
                 and comma-separated, sorted tag names. Sections without entries are skipped.
                 Includes newlines between sections.

        Example:
            >>> summary = {HedSectionKey.Tags: ["Event", "Action"],
            ...           HedSectionKey.Units: ["s", "Hz"]}
            >>> print(comparer._pretty_print_header(summary))
            Tags: Action, Event
            Units: Hz, s
        """
        output_string = ""
        first_entry = True
        for section_key, tag_names in summary_dict.items():
            if not tag_names:
                continue
            type_name = self.SECTION_ENTRY_NAMES_PLURAL[section_key]
            if not first_entry:
                output_string += "\n"
            output_string += f"{type_name}: "
            output_string += ", ".join(sorted(tag_names))
            output_string += "\n"
            first_entry = False
        return output_string

    @staticmethod
    def _get_tag_name_summary(tag_dicts):
        """Combine multiple tag dictionaries into a unified summary organized by section.

        Merges entries from one or more dictionaries (typically matches and unequal_entries)
        into a single summary dictionary where each section maps to a list of tag/entry names.
        Useful for generating summaries across multiple comparison categories.

        Parameters:
            tag_dicts (tuple or list): Collection of dictionaries mapping section keys to
                                      dictionaries of tag/entry entries.
                                      Format: [{section_key -> {name -> entry, ...}}, ...]

        Returns:
            dict: Dictionary mapping section keys to lists of all tag/entry names from all
                 input dictionaries. Format: {section_key -> [name1, name2, ...]}
                 Entries are deduplicated (sets converted to lists).

        Example:
            >>> dict1 = {HedSectionKey.Tags: {"Event": entry1, "Action": entry2}}
            >>> dict2 = {HedSectionKey.Tags: {"Event": entry3, "State": entry4}}
            >>> summary = SchemaComparer._get_tag_name_summary((dict1, dict2))
            >>> print(summary[HedSectionKey.Tags])  # ["Event", "Action", "State"]
        """
        out_dict = {section_key: [] for section_key in HedSectionKey}
        for tag_dict in tag_dicts:
            for section_key, section in tag_dict.items():
                out_dict[section_key].extend(section.keys())
        return out_dict

    def _add_removed_items(self, change_dict, not_in_2):
        """Add entries for items removed from schema2 to the change dictionary.

        Processes entries that exist in schema1 but have been removed from schema2.
        Categorizes removals as Major severity for Tags (breaking changes) and Unknown
        severity for other section types.

        Parameters:
            change_dict (defaultdict): Change dictionary to append change entries to.
            not_in_2 (dict): Dictionary of entries present in schema1 but not in schema2.
                           Format: {section_key -> {name -> entry, ...}}
        """
        for section_key, section in not_in_2.items():
            for tag, _ in section.items():
                type_name = self.SECTION_ENTRY_NAMES_PLURAL[section_key]
                change_type = "Major" if section_key == HedSectionKey.Tags else "Unknown"
                change_dict[section_key].append(
                    {"change_type": change_type, "change": f"Tag {tag} deleted from {type_name}", "tag": tag}
                )

    @staticmethod
    def _add_added_items(change_dict, not_in_1):
        """Add entries for items added to schema2 to the change dictionary.

        Processes entries that exist in schema2 but are new (not in schema1).
        All additions are categorized as Minor severity (backward-compatible additions).

        Parameters:
            change_dict (defaultdict): Change dictionary to append change entries to.
            not_in_1 (dict): Dictionary of entries present in schema2 but not in schema1.
                           Format: {section_key -> {name -> entry, ...}}
        """
        for section_key, section in not_in_1.items():
            for tag, _ in section.items():
                change_dict[section_key].append({"change_type": "Minor", "change": f"Item {tag} added", "tag": tag})

    def _add_unequal_entries(self, change_dict, unequal_entries):
        """Add entries for items with differing attributes to the change dictionary.

        Handles entries that exist in both schemas but have different attributes, descriptions,
        or other properties. Dispatches to specialized handlers based on section type:
        - Misc section: metadata changes (prologue, epilogue, headers)
        - Unit classes: unit addition/removal
        - Tags: unit/value classes, hierarchy position, suggested/related tags
        - Other sections: generic attribute comparisons

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
            unequal_entries (dict): Dictionary mapping section keys to tuples of (entry1, entry2)
                                   for entries with the same name but different attributes.
                                   Format: {section_key -> {name -> (entry1, entry2), ...}}
        """
        for section_key, changes in unequal_entries.items():
            if section_key == self.MISC_SECTION:
                self._add_misc_section_changes(change_dict, section_key, changes)
            else:
                for tag, (entry1, entry2) in changes.items():
                    if section_key == HedSectionKey.UnitClasses:
                        self._add_unit_classes_changes(change_dict, section_key, entry1, entry2)
                    elif section_key == HedSectionKey.Tags:
                        self._add_tag_changes(change_dict, section_key, entry1, entry2)
                    self._check_other_attributes(change_dict, section_key, entry1, entry2)
                    if entry1.description != entry2.description:
                        change_dict[section_key].append(
                            {"change_type": "Patch", "change": f"Description of {tag} modified", "tag": tag}
                        )

    @staticmethod
    def _add_misc_section_changes(change_dict, section_key, changes):
        """Add changes for miscellaneous metadata sections to the change dictionary.

        Processes changes to schema-level metadata such as prologue, epilogue, and header
        attributes. All metadata changes are categorized as Patch severity (non-breaking).

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
            section_key (str): The section identifier (typically MISC_SECTION).
            changes (dict): Dictionary mapping metadata field names to (old_value, new_value)
                          tuples. Format: {field_name -> (old_val, new_val), ...}
        """
        for misc_section, (value1, value2) in changes.items():
            change_type = "Patch" if "prologue" in misc_section or "epilogue" in misc_section else "Patch"
            change_desc = (
                f"{misc_section} changed"
                if "prologue" in misc_section or "epilogue" in misc_section
                else f"{misc_section} changed from {value1} to {value2}"
            )
            change_dict[section_key].append({"change_type": change_type, "change": change_desc, "tag": misc_section})

    @staticmethod
    def _add_unit_classes_changes(change_dict, section_key, entry1, entry2):
        """Add changes in unit class definitions to the change dictionary.

        Compares the units contained in two unit class entries and records additions/removals.
        Unit removals are Major severity (breaking), unit additions are Patch severity.

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
            section_key (HedSectionKey): The section identifier (should be HedSectionKey.UnitClasses).
            entry1 (HedSchemaEntry): Unit class entry from schema1.
            entry2 (HedSchemaEntry): Unit class entry from schema2 with the same name.
        """
        for unit in entry1.units:
            if unit not in entry2.units:
                change_dict[section_key].append(
                    {"change_type": "Major", "change": f"Unit {unit} removed from {entry1.name}", "tag": entry1.name}
                )
        for unit in entry2.units:
            if unit not in entry1.units:
                change_dict[section_key].append(
                    {"change_type": "Patch", "change": f"Unit {unit} added to {entry2.name}", "tag": entry1.name}
                )

    def _add_tag_changes(self, change_dict, section_key, entry1, entry2):
        """Add changes in tag definitions to the change dictionary.

        Comprehensive comparison of tag-specific attributes:
        - Unit classes: removals are Major, additions are Patch
        - Value classes: removals are Unknown, additions are Minor
        - Hierarchy position (long_tag_name): Minor severity
        - Multi-value attributes (suggestedTag, relatedTag): Patch severity

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
            section_key (HedSectionKey): The section identifier (should be HedSectionKey.Tags).
            entry1 (HedTagEntry): Tag entry from schema1.
            entry2 (HedTagEntry): Tag entry from schema2 with the same short name.
        """
        for unit_class in entry1.unit_classes:
            if unit_class not in entry2.unit_classes:
                change_dict[section_key].append(
                    {
                        "change_type": "Major",
                        "change": f"Unit class {unit_class} removed from {entry1.short_tag_name}",
                        "tag": entry1.short_tag_name,
                    }
                )
        for unit_class in entry2.unit_classes:
            if unit_class not in entry1.unit_classes:
                change_dict[section_key].append(
                    {
                        "change_type": "Patch",
                        "change": f"Unit class {unit_class} added to {entry2.short_tag_name}",
                        "tag": entry1.short_tag_name,
                    }
                )
        for value_class in entry1.value_classes:
            if value_class not in entry2.value_classes:
                change_dict[section_key].append(
                    {
                        "change_type": "Unknown",
                        "change": f"Value class {value_class} removed from {entry1.short_tag_name}",
                        "tag": entry1.short_tag_name,
                    }
                )
        for value_class in entry2.value_classes:
            if value_class not in entry1.value_classes:
                change_dict[section_key].append(
                    {
                        "change_type": "Minor",
                        "change": f"Value class {value_class} added to {entry2.short_tag_name}",
                        "tag": entry1.short_tag_name,
                    }
                )
        if entry1.long_tag_name != entry2.long_tag_name:
            change_dict[section_key].append(
                {
                    "change_type": "Minor",
                    "change": f"Tag {entry1.short_tag_name} moved in schema from {entry1.long_tag_name} to {entry2.long_tag_name}",
                    "tag": entry1.short_tag_name,
                }
            )
        self._add_suggested_tag_changes(change_dict, entry1, entry2, HedKey.SuggestedTag, "Suggested tag")
        self._add_suggested_tag_changes(change_dict, entry1, entry2, HedKey.RelatedTag, "Related tag")

    @staticmethod
    def _add_suggested_tag_changes(change_dict, entry1, entry2, attribute, label):
        """Add changes for suggested or related tag attributes to the change dictionary.

        Compares multi-value tag attributes (like suggestedTag or relatedTag) between two
        entries. Values are sorted before comparison to normalize differences. Changes are
        categorized as Patch severity. If the attribute is empty, it is represented as "empty".

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
            entry1 (HedTagEntry): Tag entry from schema1.
            entry2 (HedTagEntry): Tag entry from schema2 with the same short name.
            attribute (HedKey): The attribute to compare (e.g., HedKey.SuggestedTag,
                              HedKey.RelatedTag).
            label (str): Human-readable label for the attribute (e.g., "Suggested tag",
                        "Related tag").
        """
        related_tag1 = ", ".join(sorted(entry1.inherited_attributes.get(attribute, "").split(",")))
        related_tag2 = ", ".join(sorted(entry2.inherited_attributes.get(attribute, "").split(",")))
        if related_tag1 != related_tag2:
            if not related_tag1:
                related_tag1 = "empty"
            if not related_tag2:
                related_tag2 = "empty"
            change_dict[HedSectionKey.Tags].append(
                {
                    "change_type": "Patch",
                    "change": f"{label} changed on {entry1.short_tag_name} from {related_tag1} to {related_tag2}",
                    "tag": entry1.short_tag_name,
                }
            )

    def _check_other_attributes(self, change_dict, section_key, entry1, entry2):
        """Compare general attributes not handled by specialized methods.

        Checks all attributes except those already handled by specialized comparison methods
        (suggestedTag, relatedTag, unitClass, valueClass). Distinguishes between directly
        set attributes and inherited attributes for tags:
        - Direct attributes: Patch severity
        - Inherited-only attributes (not direct): Minor severity
        - HedID changes: routed to HED_ID_SECTION

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
            section_key (HedSectionKey): The section identifier.
            entry1 (HedSchemaEntry): Entry from schema1.
            entry2 (HedSchemaEntry): Entry from schema2 with the same name.
        """
        already_checked_attributes = [HedKey.RelatedTag, HedKey.SuggestedTag, HedKey.ValueClass, HedKey.UnitClass]
        unique_keys = set(entry1.attributes.keys()).union(entry2.attributes.keys())
        if section_key == HedSectionKey.Tags:
            unique_inherited_keys = set(entry1.inherited_attributes.keys()).union(entry2.inherited_attributes.keys())
        else:
            unique_inherited_keys = unique_keys
        all_unique_keys = unique_keys.union(unique_inherited_keys).difference(already_checked_attributes)

        for key in all_unique_keys:
            is_inherited = key in unique_inherited_keys
            is_direct = key in unique_keys

            if section_key == HedSectionKey.Tags:
                value1 = entry1.inherited_attributes.get(key)
                value2 = entry2.inherited_attributes.get(key)
            else:
                value1 = entry1.attributes.get(key)
                value2 = entry2.attributes.get(key)

            if value1 != value2:
                change_type = "Patch"
                start_text = f"Attribute {key} "
                if is_inherited and not is_direct:
                    change_type = "Minor"
                    start_text = f"Inherited attribute {key} "

                if value1 is True and value2 is None:
                    end_text = "removed"
                elif value1 is None and value2 is True:
                    end_text = "added"
                else:
                    end_text = f"modified from {value1} to {value2}"

                use_section_key = section_key
                if key == HedKey.HedID:
                    use_section_key = self.HED_ID_SECTION
                change_dict[use_section_key].append(
                    {
                        "change_type": change_type,
                        "change": f"{start_text}{end_text}",
                        "tag": entry1.name if section_key != HedSectionKey.Tags else entry1.short_tag_name,
                        "section": section_key,
                    }
                )

    def _add_extras_changes(self, change_dict):
        """Compare extras dataframes between schemas and record differences.

        Extras are schema-level structured data stored as pandas DataFrames (Sources, Prefixes,
        AnnotationPropertyExternal). Compares row-by-row using key columns defined in
        UNIQUE_EXTRAS_KEYS to identify additions, removals, and modifications. Column names
        are normalized to lowercase for comparison.

        Parameters:
            change_dict (defaultdict): Change dictionary to append to.
        """
        extras1 = getattr(self.schema1, "extras", {}) or {}
        extras2 = getattr(self.schema2, "extras", {}) or {}

        all_keys = set(extras1.keys()).union(extras2.keys())
        for key in all_keys:
            df1 = extras1.get(key)
            df2 = extras2.get(key)
            if df1 is None and df2 is not None:
                change_dict[key].append(
                    {"change_type": "Minor", "change": f"Entire {key} section missing in first schema", "tag": key}
                )
                continue
            if df2 is None and df1 is not None:
                change_dict[key].append(
                    {"change_type": "Minor", "change": f"Entire {key} section missing in second schema", "tag": key}
                )
                continue
            if df1 is None and df2 is None:
                continue

            df1 = df1.copy()
            df2 = df2.copy()
            df1.columns = [c.lower() for c in df1.columns]
            df2.columns = [c.lower() for c in df2.columns]

            key_cols = UNIQUE_EXTRAS_KEYS.get(key)
            if not key_cols:
                key_cols = sorted(c for c in set(df1.columns) & set(df2.columns) if c != _in_library)

            compare_cols = sorted(c for c in set(df1.columns) & set(df2.columns) if c != _in_library)
            if not compare_cols:
                continue

            df1 = df1[compare_cols]
            df2 = df2[compare_cols]

            diff_results = self._compare_dataframes(df1, df2, key_cols)
            for diff in diff_results:
                row_key = diff["row"]
                cols = diff["cols"]
                msg = diff["message"]
                if msg == "Row missing in first schema":
                    change_dict[key].append(
                        {
                            "change_type": "Minor",
                            "change": f"Row {row_key} missing in first schema",
                            "tag": str(row_key),
                        }
                    )
                elif msg == "Row missing in second schema":
                    change_dict[key].append(
                        {
                            "change_type": "Minor",
                            "change": f"Row {row_key} missing in second schema",
                            "tag": str(row_key),
                        }
                    )
                elif msg == "Duplicate keys found":
                    change_dict[key].append(
                        {
                            "change_type": "Unknown",
                            "change": f"Duplicate key {row_key} found in one or both schemas",
                            "tag": str(row_key),
                        }
                    )
                elif msg == "Column values differ":
                    col_str = ", ".join(cols) if cols else ""
                    change_dict[key].append(
                        {
                            "change_type": "Patch",
                            "change": f"Row {row_key} columns differ: {col_str}",
                            "tag": str(row_key),
                        }
                    )

    @staticmethod
    def _compare_dataframes(df1, df2, key_cols):
        """Compare two dataframes row-by-row using key columns.

        Identifies rows that exist only in one dataframe, duplicate keys (detected when
        indexing produces a DataFrame instead of a Series), and rows with differing column
        values. Uses the specified columns as the row identifier for comparison.

        Parameters:
            df1 (pd.DataFrame): First dataframe to compare. Should have the key columns.
            df2 (pd.DataFrame): Second dataframe to compare. Should have the key columns.
            key_cols (list): List of column names to use as unique row identifiers.
                           All key columns must exist in both dataframes.

        Returns:
            list: List of difference dictionaries, each containing:
                  - 'row' (tuple or value): The key value(s) identifying the row
                  - 'cols' (list or None): List of column names with differing values, or
                                          None if row is missing or has duplicate keys
                  - 'message' (str): Description of difference type:
                    * "Row missing in first schema"
                    * "Row missing in second schema"
                    * "Duplicate keys found"
                    * "Column values differ"
        """
        results = []

        df1_indexed = df1.set_index(key_cols)
        df2_indexed = df2.set_index(key_cols)

        all_keys = set(df1_indexed.index).union(df2_indexed.index)

        for key in all_keys:
            if key not in df1_indexed.index:
                results.append({"row": key, "cols": None, "message": "Row missing in first schema"})
            elif key not in df2_indexed.index:
                results.append({"row": key, "cols": None, "message": "Row missing in second schema"})
            else:
                row1 = df1_indexed.loc[key]
                row2 = df2_indexed.loc[key]

                if isinstance(row1, pd.DataFrame) or isinstance(row2, pd.DataFrame):
                    results.append({"row": key, "cols": None, "message": "Duplicate keys found"})
                    continue

                unequal_cols = [col for col in df1.columns if col not in key_cols and row1[col] != row2[col]]
                if unequal_cols:
                    results.append({"row": key, "cols": unequal_cols, "message": "Column values differ"})

        return results

    @staticmethod
    def _sort_changes_by_severity(changes_dict):
        """Sort the changelist by severity level.

        In-place sorting of change lists by severity order: Major (breaking changes) first,
        followed by Minor, Patch, then Unknown. Used to present the most significant changes
        to users first in formatted output.

        Parameters:
            changes_dict (dict): Dictionary mapping section keys to lists of change dicts.
                               Each change dict must contain a 'change_type' key.
                               Format: {section_key -> [{"change_type": str, ...}, ...]}
        """
        for section in changes_dict.values():
            order = {"Major": 1, "Minor": 2, "Patch": 3, "Unknown": 4}
            section.sort(key=lambda x: order.get(x["change_type"], order["Unknown"]))
