from hed.schema.hed_schema import HedSchema, HedKey
from hed.schema.hed_schema_constants import HedSectionKey

# This is still in design, means header attributes, epilogue, and prologue
MiscSection = "misc"

SectionEntryNames = {
    HedSectionKey.Tags: "Tag",
    HedSectionKey.Units: "Unit",
    HedSectionKey.UnitClasses: "Unit Class",
    HedSectionKey.ValueClasses: "Value Class",
    HedSectionKey.UnitModifiers: "Unit Modifier",
    HedSectionKey.Properties: "Property",
    HedSectionKey.Attributes: "Attribute",
}

SectionEntryNamesPlural = {
    HedSectionKey.Tags: "Tags",
    HedSectionKey.Units: "Units",
    HedSectionKey.UnitClasses: "Unit Classes",
    HedSectionKey.ValueClasses: "Value Classes",
    HedSectionKey.UnitModifiers: "Unit Modifiers",
    HedSectionKey.Properties: "Properties",
    HedSectionKey.Attributes: "Attributes",
}


def find_matching_tags(schema1, schema2, output='raw', sections=(HedSectionKey.Tags,),
                       include_summary=True):
    """
    Compare the tags in two library schemas.  This finds tags with the same term.

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        output (str): Defaults to returning a python object dicts.
                      'string' returns a single string
                      'dict' returns a json style dictionary
        sections(list): the list of sections to compare.  By default, just the tags section.
                        If None, checks all sections including header, prologue, and epilogue.
        include_summary(bool): If True, adds the 'summary' dict to the dict return option, and prints it with the
                               string option.  Lists the names of all the nodes that are missing or different.
    Returns:
        dict, json style dict, or str: A dictionary containing matching entries in the Tags section of both schemas.
    """
    matches, _, _, unequal_entries = compare_schemas(schema1, schema2, sections=sections)

    for section_key, section_dict in matches.items():
        section_dict.update(unequal_entries[section_key])

    header_summary = _get_tag_name_summary((matches, unequal_entries))

    if output == 'string':
        final_string = ""
        if include_summary:
            final_string += _pretty_print_header(header_summary)
        if sections is None:
            sections = HedSectionKey
        for section_key in sections:
            type_name = SectionEntryNames[section_key]
            entries = matches[section_key]
            if not entries:
                continue
            final_string += f"{type_name} differences:\n"
            final_string += _pretty_print_diff_all(entries, type_name=type_name) + "\n"
        return final_string
    elif output == 'dict':
        output_dict = {}
        if include_summary:
            output_dict["summary"] = {str(key): value for key, value in header_summary.items()}

        for section_name, section_entries in matches.items():
            output_dict[str(section_name)] = {}
            for key, (entry1, entry2) in section_entries.items():
                output_dict[str(section_name)][key] = _dict_diff_entries(entry1, entry2)
        return output_dict
    return matches


def compare_differences(schema1, schema2, output='raw', attribute_filter=None, sections=(HedSectionKey.Tags,),
                        include_summary=True):
    """
    Compare the tags in two schemas, this finds any differences

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        output (str): 'raw' (default) returns a tuple of python object dicts with raw results.
                      'string' returns a single string
                      'dict' returns a json-style python dictionary that can be converted to JSON
        attribute_filter (str, optional): The attribute to filter entries by.
                                          Entries without this attribute are skipped.
                                          The most common use would be HedKey.InLibrary
                                          If it evaluates to False, no filtering is performed.
        sections(list or None): the list of sections to compare.  By default, just the tags section.
                If None, checks all sections including header, prologue, and epilogue.
        include_summary(bool): If True, adds the 'summary' dict to the dict return option, and prints it with the
                               string option.  Lists the names of all the nodes that are missing or different.

    Returns:
        tuple, str or dict: 
        - Tuple with dict entries (not_in_schema1, not_in_schema1, unequal_entries).
        - Formatted string with the output ready for printing.
        - A Python dictionary with the output ready to be converted to JSON (for web output).

    Notes: The underlying dictionaries are:
        - not_in_schema1(dict): Entries present in schema2 but not in schema1.
        - not_in_schema2(dict): Entries present in schema1 but not in schema2.
        - unequal_entries(dict): Entries that differ between the two schemas.

    """
    _, not_in_1, not_in_2, unequal_entries = compare_schemas(schema1, schema2, attribute_filter=attribute_filter,
                                                             sections=sections)

    if sections is None:
        sections = HedSectionKey

    header_summary = _get_tag_name_summary((not_in_1, not_in_2, unequal_entries))
    if output == 'string':
        final_string = ""
        if include_summary:
            final_string += _pretty_print_header(header_summary)
            if not final_string:
                return final_string
            final_string = ("Overall summary:\n================\n" + final_string + \
                            "\n\n\nSummary details:\n================\n\n")
        for section_key in sections:
            val1, val2, val3 = unequal_entries[section_key], not_in_1[section_key], not_in_2[section_key]
            type_name = SectionEntryNames[section_key]
            if val1 or val2 or val3:
                final_string += f"{type_name} differences:\n"
                if val1:
                    final_string += _pretty_print_diff_all(val1, type_name=type_name) + "\n"
                if val2:
                    final_string += _pretty_print_missing_all(val2, "Schema1", type_name) + "\n"
                if val3:
                    final_string += _pretty_print_missing_all(val3, "Schema2", type_name) + "\n"
                final_string += "\n\n"
        return final_string
    elif output == 'dict':
        # todo: clean this part up
        output_dict = {}
        current_section = {}
        if include_summary:
            output_dict["summary"] = {str(key): value for key, value in header_summary.items()}

        output_dict["unequal"] = current_section
        for section_name, section_entries in unequal_entries.items():
            current_section[str(section_name)] = {}
            for key, (entry1, entry2) in section_entries.items():
                current_section[str(section_name)][key] = _dict_diff_entries(entry1, entry2)

        current_section = {}
        output_dict["not_in_1"] = current_section
        for section_name, section_entries in not_in_1.items():
            current_section[str(section_name)] = {}
            for key, entry in section_entries.items():
                current_section[str(section_name)][key] = _entry_to_dict(entry)

        current_section = {}
        output_dict["not_in_2"] = current_section
        for section_name, section_entries in not_in_2.items():
            current_section[str(section_name)] = {}
            for key, entry in section_entries.items():
                current_section[str(section_name)][key] = _entry_to_dict(entry)
        return output_dict
    return not_in_1, not_in_2, unequal_entries


def compare_schemas(schema1, schema2, attribute_filter=HedKey.InLibrary, sections=(HedSectionKey.Tags,)):
    """
    Compare two schemas section by section.
    The function records matching entries, entries present in one schema but not in the other, and unequal entries.

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        attribute_filter (str, optional): The attribute to filter entries by.
                                        Entries without this attribute are skipped.
                                        The most common use would be HedKey.InLibrary
                                        If it evaluates to False, no filtering is performed.
        sections(list): the list of sections to compare.  By default, just the tags section.
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

        attribute = 'short_tag_name' if section_key == HedSectionKey.Tags else 'name'

        # Get the name we're comparing things by
        for entry in section1.all_entries:
            if not attribute_filter or entry.has_attribute(attribute_filter):
                dict1[getattr(entry, attribute)] = entry

        for entry in section2.all_entries:
            if not attribute_filter or entry.has_attribute(attribute_filter):
                dict2[getattr(entry, attribute)] = entry

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
    out_dict = {section_key: [] for section_key in HedSectionKey}
    for tag_dict in tag_dicts:
        for section_key, section in tag_dict.items():
            if section_key == MiscSection:
                continue
            out_dict[section_key].extend(section.keys())

    return out_dict


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


def _pretty_print_entry(entry):
    """ Returns the contents of a HedSchemaEntry object as a list of strings.

    Parameters:
        entry (HedSchemaEntry): The HedSchemaEntry object to be displayed.

    Returns:
        List of strings representing the entry.
    """
    # Initialize the list with the name of the entry
    output = [f"\tName: {entry.name}"]

    # Add the description to the list if it exists
    if entry.description is not None:
        output.append(f"\tDescription: {entry.description}")

    # Iterate over all attributes and add them to the list
    for attr_key, attr_value in entry.attributes.items():
        output.append(f"\tAttribute: {attr_key} - Value: {attr_value}")

    return output


def _entry_to_dict(entry):
    """
    Returns the contents of a HedSchemaEntry object as a dictionary.

    Parameters:
        entry (HedSchemaEntry): The HedSchemaEntry object to be displayed.

    Returns:
        Dictionary representing the entry.
    """
    output = {
        "Name": entry.name,
        "Description": entry.description,
        "Attributes": entry.attributes
    }
    return output


def _dict_diff_entries(entry1, entry2):
    """
    Returns the differences between two HedSchemaEntry objects as a dictionary.

    Parameters:
        entry1 (HedSchemaEntry or str): The first entry.
        entry2 (HedSchemaEntry or str): The second entry.

    Returns:
        Dictionary representing the differences.
    """
    diff_dict = {}

    if isinstance(entry1, str):
        # Handle special case ones like prologue
        if entry1 != entry2:
            diff_dict["value"] = {
                "Schema1": entry1,
                "Schema2": entry2
            }
    else:
        if entry1.name != entry2.name:
            diff_dict["name"] = {
                "Schema1": entry1.name,
                "Schema2": entry2.name
            }

        # Checking if both entries have the same description
        if entry1.description != entry2.description:
            diff_dict["description"] = {
                "Schema1": entry1.description,
                "Schema2": entry2.description
            }

        # Comparing attributes
        for attr in set(entry1.attributes.keys()).union(entry2.attributes.keys()):
            if entry1.attributes.get(attr) != entry2.attributes.get(attr):
                diff_dict[attr] = {
                    "Schema1": entry1.attributes.get(attr),
                    "Schema2": entry2.attributes.get(attr)
                }

    return diff_dict


def _pretty_print_diff_entry(entry1, entry2):
    """
    Returns the differences between two HedSchemaEntry objects as a list of strings.

    Parameters:
        entry1 (HedSchemaEntry): The first entry.
        entry2 (HedSchemaEntry): The second entry.

    Returns:
        List of strings representing the differences.
    """
    diff_dict = _dict_diff_entries(entry1, entry2)
    diff_lines = []

    for key, value in diff_dict.items():
        diff_lines.append(f"\t{key}:")
        for schema, val in value.items():
            diff_lines.append(f"\t\t{schema}: {val}")

    return diff_lines


def _pretty_print_diff_all(entries, type_name=""):
    """
    Formats the differences between pairs of HedSchemaEntry objects.

    Parameters:
        entries (dict): A dictionary where each key maps to a pair of HedSchemaEntry objects.
        type_name(str): The type to identify this as, such as Tag
    Returns:
        diff_string(str): The differences found in the dict
    """
    output = []
    if not type_name.endswith(" "):
        type_name += " "
    if not entries:
        return ""
    for key, (entry1, entry2) in entries.items():
        output.append(f"{type_name}'{key}':")
        output += _pretty_print_diff_entry(entry1, entry2)
        output.append("")

    return "\n".join(output)


def _pretty_print_missing_all(entries, schema_name, type_name):
    """
    Formats the missing entries from schema_name.

    Parameters:
        entries (dict): A dictionary where each key maps to a pair of HedSchemaEntry objects.
        schema_name(str): The name these entries are missing from
        type_name(str): The type to identify this as, such as Tag
    Returns:
        diff_string(str): The differences found in the dict
    """
    output = []
    if not entries:
        return ""
    if not type_name.endswith(" "):
        type_name += " "
    for key, entry in entries.items():
        output.append(f"{type_name}'{key}' not in '{schema_name}':")
        output += _pretty_print_entry(entry)
        output.append("")

    return "\n".join(output)
