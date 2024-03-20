from hed.schema.hed_schema import HedKey
from hed.schema.hed_schema_constants import HedSectionKey
from collections import defaultdict

MiscSection = "misc"

SectionEntryNames = {
    HedSectionKey.Tags: "Tag",
    HedSectionKey.Units: "Unit",
    HedSectionKey.UnitClasses: "Unit Class",
    HedSectionKey.ValueClasses: "Value Class",
    HedSectionKey.UnitModifiers: "Unit Modifier",
    HedSectionKey.Properties: "Property",
    HedSectionKey.Attributes: "Attribute",
    MiscSection: "Misc Metadata"
}

SectionEntryNamesPlural = {
    HedSectionKey.Tags: "Tags",
    HedSectionKey.Units: "Units",
    HedSectionKey.UnitClasses: "Unit Classes",
    HedSectionKey.ValueClasses: "Value Classes",
    HedSectionKey.UnitModifiers: "Unit Modifiers",
    HedSectionKey.Properties: "Properties",
    HedSectionKey.Attributes: "Attributes",
    MiscSection: "Misc Metadata"
}


def find_matching_tags(schema1, schema2, sections=(HedSectionKey.Tags,), return_string=True):
    """Compare the tags in two library schemas.  This finds tags with the same term.

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        sections(list): the list of sections to compare.  By default, just the tags section.
                        If None, checks all sections including header, prologue, and epilogue.
        return_string(bool): If False, returns the raw python dictionary(for tools etc. possible use)
    Returns:
        str or dict: Returns a formatted string or python dict
    """
    matches, _, _, unequal_entries = compare_schemas(schema1, schema2, sections=sections)
    header_summary = _get_tag_name_summary((matches, unequal_entries))

    # Combine the two dictionaries
    for section_key, section_dict in matches.items():
        section_dict.update(unequal_entries[section_key])

    if return_string:
        final_string = "Nodes with matching names:\n"
        final_string += _pretty_print_header(header_summary)
        # Do we actually want this...?  I'm just going to remove and add back later if needed.
        # for section_key, entries in matches.items():
        #     type_name = SectionEntryNames[section_key]
        #     if not entries:
        #         continue
        #     final_string += f"{type_name} differences:\n"
        #     final_string += _pretty_print_diff_all(entries, type_name=type_name) + "\n"
        return final_string
    return matches


def _pretty_print_header(summary_dict):
    output_string = ""
    first_entry = True
    for section_key, tag_names in summary_dict.items():
        if not tag_names:
            continue
        type_name = SectionEntryNamesPlural[section_key]
        if not first_entry:
            output_string += "\n"
        output_string += f"{type_name}: "

        output_string += ", ".join(sorted(tag_names))

        output_string += "\n"
        first_entry = False
    return output_string


def compare_schemas(schema1, schema2, attribute_filter=HedKey.InLibrary, sections=(HedSectionKey.Tags,)):
    """ Compare two schemas section by section.

    The function records matching entries, entries present in one schema but not in the other, and unequal entries.

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        attribute_filter (str, optional): The attribute to filter entries by.
            Entries without this attribute are skipped.
            The most common use would be HedKey.InLibrary
            If it evaluates to False, no filtering is performed.
        sections(list or None): the list of sections to compare.  By default, just the tags section.
            If None, checks all sections including header, prologue, and epilogue.

    Returns:
        tuple: A tuple containing four dictionaries:
        - matches(dict): Entries present in both schemas and are equal.
        - not_in_schema1(dict): Entries present in schema2 but not in schema1.
        - not_in_schema2(dict): Entries present in schema1 but not in schema2.
        - unequal_entries(dict): Entries present in both schemas but are not equal.
    """
    # Result dictionaries to hold matches, keys not in schema2, keys not in schema1, and unequal entries
    matches = {}
    not_in_schema2 = {}
    not_in_schema1 = {}
    unequal_entries = {}

    if sections is None or MiscSection in sections:
        unequal_entries[MiscSection] = {}
        if schema1.get_save_header_attributes() != schema2.get_save_header_attributes():
            unequal_entries[MiscSection]['header_attributes'] = \
                (str(schema1.get_save_header_attributes()), str(schema2.get_save_header_attributes()))
        if schema1.prologue != schema2.prologue:
            unequal_entries[MiscSection]['prologue'] = (schema1.prologue, schema2.prologue)
        if schema1.epilogue != schema2.epilogue:
            unequal_entries[MiscSection]['epilogue'] = (schema1.epilogue, schema2.epilogue)

    # Iterate over keys in HedSectionKey
    for section_key in HedSectionKey:
        if sections is not None and section_key not in sections:
            continue
        # Dictionaries to record (short_tag_name or name): entry pairs
        dict1 = {}
        dict2 = {}

        section1 = schema1[section_key]
        section2 = schema2[section_key]

        name_attribute = 'short_tag_name' if section_key == HedSectionKey.Tags else 'name'

        # Get the name we're comparing things by
        for entry in section1.all_entries:
            if not attribute_filter or entry.has_attribute(attribute_filter):
                dict1[getattr(entry, name_attribute)] = entry

        for entry in section2.all_entries:
            if not attribute_filter or entry.has_attribute(attribute_filter):
                dict2[getattr(entry, name_attribute)] = entry

        # Find keys present in dict1 but not in dict2, and vice versa
        not_in_schema2[section_key] = {key: dict1[key] for key in dict1 if key not in dict2}
        not_in_schema1[section_key] = {key: dict2[key] for key in dict2 if key not in dict1}

        # Find keys present in both but with unequal entries
        unequal_entries[section_key] = {key: (dict1[key], dict2[key]) for key in dict1
                                        if key in dict2 and dict1[key] != dict2[key]}

        # Find matches
        matches[section_key] = {key: (dict1[key], dict2[key]) for key in dict1
                                if key in dict2 and dict1[key] == dict2[key]}

    return matches, not_in_schema1, not_in_schema2, unequal_entries


def _get_tag_name_summary(tag_dicts):
    """Combines the given dicts, so the output is section_key:list of keys"""
    out_dict = {section_key: [] for section_key in HedSectionKey}
    for tag_dict in tag_dicts:
        for section_key, section in tag_dict.items():
            out_dict[section_key].extend(section.keys())

    return out_dict


def _group_changes_by_section_with_unique_tags(change_dict):
    """Similar to above, but on the patch note changes"""
    organized_changes = defaultdict(set)
    for change in change_dict:
        section_key = change['section']
        tag = change['tag']
        organized_changes[section_key].add(tag)
    return dict(organized_changes)


def _sort_changes_by_severity(changes_dict):
    """Sort the changelist by severity"""
    for section in changes_dict.values():
        order = {'Major': 1, 'Minor': 2, 'Patch': 3, 'Unknown': 4}
        section.sort(key=lambda x: order.get(x['change_type'], order['Unknown']))


def gather_schema_changes(schema1, schema2, attribute_filter=None):
    """ Compare two schemas section by section, generating a changelog

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        attribute_filter (str, optional): The attribute to filter entries by.
            Entries without this attribute are skipped.
            The most common use would be HedKey.InLibrary
            If it evaluates to False, no filtering is performed.

    Returns:
        changelog(dict): A dict organized by section with the changes
    """
    _, not_in_1, not_in_2, unequal_entries = compare_schemas(schema1, schema2, attribute_filter=attribute_filter,
                                                             sections=None)
    change_dict = defaultdict(list)

    # Items removed from schema
    for section_key, section in not_in_2.items():
        for tag, _ in section.items():
            type_name = SectionEntryNamesPlural[section_key]
            if section_key == HedSectionKey.Tags:
                change_dict[section_key].append(
                    {'change_type': 'Major', 'change': f'Tag {tag} deleted from {type_name}',
                     'tag': tag})
            else:
                # Only here for completeness - these aren't in the list
                change_dict[section_key].append(
                    {'change_type': 'Unknown', 'change': f"Item {tag} removed from {type_name}",
                     'tag': tag})

    # Items added to schema
    for section_key, section in not_in_1.items():
        for tag, _ in section.items():
            type_name = SectionEntryNamesPlural[section_key]
            change_dict[section_key].append({'change_type': 'Minor', 'change': f'Item {tag} added to {type_name}',
                                             'tag': tag})

    # Now the much more complex comparing an individual tag changes
    for section_key, changes in unequal_entries.items():
        if section_key == MiscSection:
            for misc_section, (value1, value2) in changes.items():
                # todo: consider fine grained header changes
                change_dict[section_key].append(
                    {'change_type': 'Patch', 'change': f'{misc_section} changed from "{value1}" to "{value2}"',
                     'tag': misc_section})
            continue
        for tag, (entry1, entry2) in changes.items():
            if section_key == HedSectionKey.UnitClasses:
                for unit in entry1.units:
                    if unit not in entry2.units:
                        change_dict[section_key].append(
                            {'change_type': 'Major', 'change': f'Unit {unit} removed from {entry1.name}',
                             'tag': tag})
                for unit in entry2.units:
                    if unit not in entry1.units:
                        change_dict[section_key].append(
                            {'change_type': 'Patch', 'change': f'Unit {unit} added to {entry2.name}',
                             'tag': tag})
            if section_key == HedSectionKey.Tags:
                for unit_class in entry1.unit_classes:
                    if unit_class not in entry2.unit_classes:
                        change_dict[section_key].append(
                            {'change_type': 'Major',
                             'change': f'Unit class {unit_class} removed from {entry1.short_tag_name}',
                             'tag': tag})
                for unit_class in entry2.unit_classes:
                    if unit_class not in entry1.unit_classes:
                        change_dict[section_key].append(
                            {'change_type': 'Patch',
                             'change': f'Unit class {unit_class} added to {entry2.short_tag_name}',
                             'tag': tag})

                for value_class in entry1.value_classes:
                    if value_class not in entry2.value_classes:
                        change_dict[section_key].append(
                            {'change_type': 'Unknown',
                             'change': f'Value class {value_class} removed from {entry1.short_tag_name}',
                             'tag': tag})
                for value_class in entry2.value_classes:
                    if value_class not in entry1.value_classes:
                        change_dict[section_key].append(
                            {'change_type': 'Minor',
                             'change': f'Value class {value_class} added to {entry2.short_tag_name}',
                             'tag': tag})

                if entry1.long_tag_name != entry2.long_tag_name:
                    change_dict[section_key].append(
                        {'change_type': 'Minor', 'change': f'Tag {entry1.short_tag_name} moved in schema',
                         'tag': tag})

                suggested_tag1 = sorted(entry1.inherited_attributes.get(HedKey.SuggestedTag, "").split(","))
                suggested_tag2 = sorted(entry2.inherited_attributes.get(HedKey.SuggestedTag, "").split(","))
                if suggested_tag1 != suggested_tag2:
                    change_dict[section_key].append(
                        {'change_type': 'Patch', 'change': f'Suggested tag changed on {entry1.name}',
                         'tag': tag})

                related_tag1 = sorted(entry1.inherited_attributes.get(HedKey.RelatedTag, "").split(","))
                related_tag2 = sorted(entry2.inherited_attributes.get(HedKey.RelatedTag, "").split(","))
                if related_tag1 != related_tag2:
                    change_dict[section_key].append(
                        {'change_type': 'Patch', 'change': f'Related tag changed on {entry1.name}',
                         'tag': tag})

            _check_other_attributes(entry1, entry2, tag, section_key, change_dict)
            if entry1.description != entry2.description:
                change_dict[section_key].append({'change_type': 'Patch', 'change': f'Description of {tag} modified',
                                                 'tag': tag})

    _sort_changes_by_severity(change_dict)
    return change_dict


def pretty_print_change_dict(change_dict, title="Schema changes"):
    """Formats the change_dict into a string.

    Parameters:
        change_dict(dict): The result from calling gather_schema_changes
        title(str): Optional header to add, a default on will be added otherwise.

    Returns:
        changelog(str): the changes listed out by section
    """
    final_strings = []
    if change_dict:
        final_strings.append(title)
        for section_key, section_dict in change_dict.items():
            name = SectionEntryNamesPlural.get(section_key, section_key)
            final_strings.append(f"{name}:")
            for item in section_dict:
                change, tag, change_type = item['change'], item['tag'], item['change_type']
                final_strings.append(f"\t{tag} ({change_type}): {change}")
    return "\n".join(final_strings)


def compare_differences(schema1, schema2, attribute_filter=None, title=""):
    """Compare the tags in two schemas, this finds any differences

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        attribute_filter (str, optional): The attribute to filter entries by.
                                          Entries without this attribute are skipped.
                                          The most common use would be HedKey.InLibrary
                                          If it evaluates to False, no filtering is performed.
        title(str): Optional header to add, a default on will be added otherwise.

    Returns:
        changelog(str): the changes listed out by section
    """
    changelog = gather_schema_changes(schema1, schema2, attribute_filter=attribute_filter)
    if not title:
        title = f"Differences between {schema1.name} and {schema2.name}"
    changelog_string = pretty_print_change_dict(changelog, title=title)

    return changelog_string


def _check_other_attributes(entry1, entry2, tag, section_key, change_dict):
    """Compare non specialized attributes"""
    already_checked_attributes = [HedKey.RelatedTag, HedKey.SuggestedTag, HedKey.ValueClass, HedKey.UnitClass]
    unique_keys = set(entry1.attributes.keys()).union(entry2.attributes.keys())
    if section_key == HedSectionKey.Tags:
        unique_inherited_keys = set(entry1.inherited_attributes.keys()).union(entry2.inherited_attributes.keys())
    else:
        unique_inherited_keys = unique_keys
    # Combine unique keys from both attributes and inherited attributes, then remove already checked attributes
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
            if is_inherited and not is_direct:
                change_dict[section_key].append({
                    "change_type": "Minor",
                    "change": f"Inherited attribute '{key}' modified from '{value1}' to '{value2}'",
                    "tag": tag,
                    "section": section_key
                })
            else:
                change_dict[section_key].append({
                    "change_type": "Patch",
                    "change": f"Attribute '{key}' modified from '{value1}' to '{value2}'",
                    "tag": tag,
                    "section": section_key
                })
