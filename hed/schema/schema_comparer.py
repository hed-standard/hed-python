""" Functions supporting comparison of schemas. """
import pandas as pd
from hed.schema.hed_schema import HedKey
from hed.schema.hed_schema_constants import HedSectionKey
from collections import defaultdict


class SchemaComparer:
    """Class for comparing HED schemas and generating change logs."""

    # Class-level constants
    MISC_SECTION = "misc"
    HED_ID_SECTION = "HedId changes"
    EXTRAS_SECTION = "Extras changes"
    SOURCES = "Sources"
    PREFIXES = "Prefixes"
    ANNOTATION_PROPERTY_EXTERNAL = "AnnotationPropertyExternal"

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
    }

    # TODO: Check that the cases of these are correct.
    DF_EXTRAS = {SOURCES, PREFIXES, ANNOTATION_PROPERTY_EXTERNAL}

    def __init__(self, schema1, schema2):
        """Initialize the SchemaComparer with two schemas."""
        self.schema1 = schema1
        self.schema2 = schema2

    def find_matching_tags(self, sections=(HedSectionKey.Tags,), return_string=True):
        """Compare the tags in the two schemas."""
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
        """Compare the two schemas section by section."""
        matches, not_in_schema2, not_in_schema1, unequal_entries = {}, {}, {}, {}

        # Handle miscellaneous sections
        if sections is None or self.MISC_SECTION in sections:
            unequal_entries[self.MISC_SECTION] = {}
            if self.schema1.get_save_header_attributes() != self.schema2.get_save_header_attributes():
                unequal_entries[self.MISC_SECTION]['header_attributes'] = \
                    (str(self.schema1.get_save_header_attributes()), str(self.schema2.get_save_header_attributes()))
            if self.schema1.prologue != self.schema2.prologue:
                unequal_entries[self.MISC_SECTION]['prologue'] = (self.schema1.prologue, self.schema2.prologue)
            if self.schema1.epilogue != self.schema2.epilogue:
                unequal_entries[self.MISC_SECTION]['epilogue'] = (self.schema1.epilogue, self.schema2.epilogue)

        # Compare sections
        for section_key in HedSectionKey:
            if sections is not None and section_key not in sections:
                continue
            dict1, dict2 = {}, {}
            section1, section2 = self.schema1[section_key], self.schema2[section_key]
            name_attribute = 'short_tag_name' if section_key == HedSectionKey.Tags else 'name'

            for entry in section1.all_entries:
                if not attribute_filter or entry.has_attribute(attribute_filter):
                    dict1[getattr(entry, name_attribute)] = entry

            for entry in section2.all_entries:
                if not attribute_filter or entry.has_attribute(attribute_filter):
                    dict2[getattr(entry, name_attribute)] = entry

            not_in_schema2[section_key] = {key: dict1[key] for key in dict1 if key not in dict2}
            not_in_schema1[section_key] = {key: dict2[key] for key in dict2 if key not in dict1}
            unequal_entries[section_key] = {key: (dict1[key], dict2[key]) for key in dict1
                                            if key in dict2 and dict1[key] != dict2[key]}
            matches[section_key] = {key: (dict1[key], dict2[key]) for key in dict1
                                    if key in dict2 and dict1[key] == dict2[key]}

        return matches, not_in_schema1, not_in_schema2, unequal_entries

    def gather_schema_changes(self, attribute_filter=None):
        """Generate a changelog by comparing the two schemas."""
        _, not_in_1, not_in_2, unequal_entries = self.compare_schemas(attribute_filter=attribute_filter, sections=None)
        change_dict = defaultdict(list)
        self._add_removed_items(change_dict, not_in_2)
        self._add_added_items(change_dict, not_in_1)
        self._add_unequal_entries(change_dict, unequal_entries)
        self._add_extras_changes(change_dict)
        self._sort_changes_by_severity(change_dict)
        return {key: change_dict[key] for key in self.SECTION_ENTRY_NAMES if key in change_dict}

    def pretty_print_change_dict(self, change_dict, title="Schema changes", use_markdown=True):
        """Format the change dictionary into a string."""
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
                    change, tag, change_type = item['change'], item['tag'], item['change_type']
                    final_strings.append(f"{line_prefix}{tag} ({change_type}): {change}")
                final_strings.append("")
        return "\n".join(final_strings)

    def compare_differences(self, attribute_filter=None, title=""):
        """Compare the tags and extras in the two schemas, reporting all differences."""
        changelog = self.gather_schema_changes(attribute_filter=attribute_filter)
        if not title:
            title = f"Differences between {self.schema1.name} and {self.schema2.name}"
        return self.pretty_print_change_dict(changelog, title=title)

    # Private helper methods
    def _pretty_print_header(self, summary_dict):
        """Format a summary dictionary of tag names by section into a string."""
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
        """Combine dictionaries into a summary of tag names by section."""
        out_dict = {section_key: [] for section_key in HedSectionKey}
        for tag_dict in tag_dicts:
            for section_key, section in tag_dict.items():
                out_dict[section_key].extend(section.keys())
        return out_dict

    def _add_removed_items(self, change_dict, not_in_2):
        """Add removed items to the change dictionary."""
        for section_key, section in not_in_2.items():
            for tag, _ in section.items():
                type_name = self.SECTION_ENTRY_NAMES_PLURAL[section_key]
                change_type = 'Major' if section_key == HedSectionKey.Tags else 'Unknown'
                change_dict[section_key].append(
                    {'change_type': change_type, 'change': f'Tag {tag} deleted from {type_name}', 'tag': tag}
                )

    @staticmethod
    def _add_added_items(change_dict, not_in_1):
        """Add added items to the change dictionary."""
        for section_key, section in not_in_1.items():
            for tag, _ in section.items():
                change_dict[section_key].append(
                    {'change_type': 'Minor', 'change': f'Item {tag} added', 'tag': tag}
                )

    def _add_unequal_entries(self, change_dict, unequal_entries):
        """Add unequal entries to the change dictionary."""
        for section_key, changes in unequal_entries.items():
            if section_key == self.MISC_SECTION:
                self._add_misc_section_changes(change_dict, section_key, changes)
            elif section_key in self.DF_EXTRAS:
                self._add_extras_section_changes(change_dict, section_key, changes)
            else:
                for tag, (entry1, entry2) in changes.items():
                    if section_key == HedSectionKey.UnitClasses:
                        self._add_unit_classes_changes(change_dict, section_key, entry1, entry2)
                    elif section_key == HedSectionKey.Tags:
                        self._add_tag_changes(change_dict, section_key, entry1, entry2)
                    self._check_other_attributes(change_dict, section_key, entry1, entry2)
                    if entry1.description != entry2.description:
                        change_dict[section_key].append(
                            {'change_type': 'Patch', 'change': f'Description of {tag} modified', 'tag': tag})

    @staticmethod
    def _add_misc_section_changes(change_dict, section_key, changes):
        """Add changes for the misc section to the change dictionary."""
        for misc_section, (value1, value2) in changes.items():
            change_type = 'Patch' if "prologue" in misc_section or "epilogue" in misc_section else 'Patch'
            change_desc = f'{misc_section} changed' if "prologue" in misc_section or "epilogue" in misc_section \
                else f'{misc_section} changed from {value1} to {value2}'
            change_dict[section_key].append({'change_type': change_type, 'change': change_desc, 'tag': misc_section})

    def _add_extras_section_changes(self, change_dict, section_key, changes):
        """Add changes for extras sections (dataframes) to the change dictionary."""
        pass  # Placeholder for extras section changes logic.

    @staticmethod
    def _add_unit_classes_changes(change_dict, section_key, entry1, entry2):
        """Add changes for unit classes to the change dictionary."""
        for unit in entry1.units:
            if unit not in entry2.units:
                change_dict[section_key].append(
                    {'change_type': 'Major', 'change': f'Unit {unit} removed from {entry1.name}', 'tag': entry1.name}
                )
        for unit in entry2.units:
            if unit not in entry1.units:
                change_dict[section_key].append(
                    {'change_type': 'Patch', 'change': f'Unit {unit} added to {entry2.name}', 'tag': entry1.name}
                )

    def _add_tag_changes(self, change_dict, section_key, entry1, entry2):
        """Add changes for tags to the change dictionary."""
        for unit_class in entry1.unit_classes:
            if unit_class not in entry2.unit_classes:
                change_dict[section_key].append(
                    {'change_type': 'Major', 'change': f'Unit class {unit_class} removed from {entry1.short_tag_name}',
                     'tag': entry1.short_tag_name}
                )
        for unit_class in entry2.unit_classes:
            if unit_class not in entry1.unit_classes:
                change_dict[section_key].append(
                    {'change_type': 'Patch', 'change': f'Unit class {unit_class} added to {entry2.short_tag_name}',
                     'tag': entry1.short_tag_name}
                )
        for value_class in entry1.value_classes:
            if value_class not in entry2.value_classes:
                change_dict[section_key].append(
                    {'change_type': 'Unknown', 'change': f'Value class {value_class} removed from {entry1.short_tag_name}',
                     'tag': entry1.short_tag_name}
                )
        for value_class in entry2.value_classes:
            if value_class not in entry1.value_classes:
                change_dict[section_key].append(
                    {'change_type': 'Minor', 'change': f'Value class {value_class} added to {entry2.short_tag_name}',
                     'tag': entry1.short_tag_name}
                )
        if entry1.long_tag_name != entry2.long_tag_name:
            change_dict[section_key].append(
                {'change_type': 'Minor',
                 'change': f'Tag {entry1.short_tag_name} moved in schema from {entry1.long_tag_name} to {entry2.long_tag_name}',
                 'tag': entry1.short_tag_name}
            )
        self._add_suggested_tag_changes(change_dict, entry1, entry2, HedKey.SuggestedTag, "Suggested tag")
        self._add_suggested_tag_changes(change_dict, entry1, entry2, HedKey.RelatedTag, "Related tag")

    @staticmethod
    def _add_suggested_tag_changes(change_dict, entry1, entry2, attribute, label):
        """Add changes for suggested or related tags to the change dictionary."""
        related_tag1 = ", ".join(sorted(entry1.inherited_attributes.get(attribute, "").split(",")))
        related_tag2 = ", ".join(sorted(entry2.inherited_attributes.get(attribute, "").split(",")))
        if related_tag1 != related_tag2:
            if not related_tag1:
                related_tag1 = "empty"
            if not related_tag2:
                related_tag2 = "empty"
            change_dict[HedSectionKey.Tags].append(
                {'change_type': 'Patch',
                 'change': f'{label} changed on {entry1.short_tag_name} from {related_tag1} to {related_tag2}',
                 'tag': entry1.short_tag_name})

    def _check_other_attributes(self, change_dict, section_key, entry1, entry2):
        """Compare non-specialized attributes and add differences to the change dictionary."""
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
                change_dict[use_section_key].append({
                    "change_type": change_type,
                    "change": f"{start_text}{end_text}",
                    "tag": entry1.name if section_key != HedSectionKey.Tags else entry1.short_tag_name,
                    "section": section_key
                })

    def _add_extras_changes(self, change_dict):
        """Compare the extras (dataframes) in two schemas and add differences to the change dictionary."""
        from hed.schema.schema_io.df_constants import extras_column_dict, UNIQUE_EXTRAS_KEYS

        extras1 = getattr(self.schema1, "extras", {}) or {}
        extras2 = getattr(self.schema2, "extras", {}) or {}

        all_keys = set(extras1.keys()).union(extras2.keys())
        for key in all_keys:
            df1 = extras1.get(key)
            df2 = extras2.get(key)
            if df1 is None and df2 is not None:
                change_dict[key].append({'change_type': 'Minor', 'change': f'Entire {key} section missing in first schema', 'tag': key})
                continue
            if df2 is None and df1 is not None:
                change_dict[key].append({'change_type': 'Minor', 'change': f'Entire {key} section missing in second schema', 'tag': key})
                continue
            if df1 is None and df2 is None:
                continue

            df1 = df1.copy()
            df2 = df2.copy()
            df1.columns = [c.lower() for c in df1.columns]
            df2.columns = [c.lower() for c in df2.columns]

            key_cols = UNIQUE_EXTRAS_KEYS.get(key)
            if not key_cols:
                key_cols = list(set(df1.columns) & set(df2.columns))

            compare_cols = list(set(df1.columns) & set(df2.columns))
            if not compare_cols:
                continue

            df1 = df1[compare_cols]
            df2 = df2[compare_cols]

            diff_results = self._compare_dataframes(df1, df2, key_cols)
            for diff in diff_results:
                row_key = diff['row']
                cols = diff['cols']
                msg = diff['message']
                if msg == 'Row missing in first schema':
                    change_dict[key].append({'change_type': 'Minor', 'change': f'Row {row_key} missing in first schema', 'tag': str(row_key)})
                elif msg == 'Row missing in second schema':
                    change_dict[key].append({'change_type': 'Minor', 'change': f'Row {row_key} missing in second schema', 'tag': str(row_key)})
                elif msg == 'Duplicate keys found':
                    change_dict[key].append({'change_type': 'Unknown', 'change': f'Duplicate key {row_key} found in one or both schemas', 'tag': str(row_key)})
                elif msg == 'Column values differ':
                    col_str = ', '.join(cols) if cols else ''
                    change_dict[key].append({'change_type': 'Patch', 'change': f'Row {row_key} columns differ: {col_str}', 'tag': str(row_key)})

    @staticmethod
    def _compare_dataframes(df1, df2, key_cols):
        """Compare two dataframes by key columns and report row/column differences."""
        results = []

        df1_indexed = df1.set_index(key_cols)
        df2_indexed = df2.set_index(key_cols)

        all_keys = set(df1_indexed.index).union(df2_indexed.index)

        for key in all_keys:
            if key not in df1_indexed.index:
                results.append({'row': key, 'cols': None, 'message': 'Row missing in first schema'})
            elif key not in df2_indexed.index:
                results.append({'row': key, 'cols': None, 'message': 'Row missing in second schema'})
            else:
                row1 = df1_indexed.loc[key]
                row2 = df2_indexed.loc[key]

                if isinstance(row1, pd.DataFrame) or isinstance(row2, pd.DataFrame):
                    results.append({'row': key, 'cols': None, 'message': 'Duplicate keys found'})
                    continue

                unequal_cols = [col for col in df1.columns if col not in key_cols and row1[col] != row2[col]]
                if unequal_cols:
                    results.append({'row': key, 'cols': unequal_cols, 'message': 'Column values differ'})

        return results

    @staticmethod
    def _sort_changes_by_severity(changes_dict):
        """Sort the changelist by severity.

        Parameters:
            changes_dict (dict): Dictionary mapping section keys to lists of change dicts.
        """
        for section in changes_dict.values():
            order = {'Major': 1, 'Minor': 2, 'Patch': 3, 'Unknown': 4}
            section.sort(key=lambda x: order.get(x['change_type'], order['Unknown']))

