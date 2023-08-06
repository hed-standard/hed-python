from hed.schema.hed_schema import HedSchema, HedKey
from hed.schema.hed_schema_constants import HedSectionKey


def find_matching_tags(schema1, schema2, return_string=False):
    """
    Compare the tags in two library schemas.  This finds tags with the same term.

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        return_string (bool): Return this as a string if true

    Returns:
        dict or str: A dictionary containing matching entries in the Tags section of both schemas.
    """
    matches, _, _, unequal_entries = compare_schemas(schema1, schema2)

    for section_key, section_dict in matches.items():
        section_dict.update(unequal_entries[section_key])

    if return_string:
        return "\n".join([pretty_print_diff_all(entries,
                                                prompt="Found matching node ") for entries in matches.values()])
    return matches


def compare_differences(schema1, schema2, return_string=False, attribute_filter=None):
    """
    Compare the tags in two schemas, this finds any differences

    Parameters:
        schema1 (HedSchema): The first schema to be compared.
        schema2 (HedSchema): The second schema to be compared.
        return_string (bool): Return this as a string if true
        attribute_filter (str, optional): The attribute to filter entries by.
                                          Entries without this attribute are skipped.
                                          The most common use would be HedKey.InLibrary
                                          If it evaluates to False, no filtering is performed.
    Returns:
    tuple or str: A tuple containing three dictionaries:
        - not_in_schema1(dict): Entries present in schema2 but not in schema1.
        - not_in_schema2(dict): Entries present in schema1 but not in schema2.
        - unequal_entries(dict): Entries that differ between the two schemas.
        - or a formatted string of the differences
    """
    _, not_in_1, not_in_2, unequal_entries = compare_schemas(schema1, schema2, attribute_filter=attribute_filter)

    if return_string:
        str1 = "\n".join([pretty_print_diff_all(entries) for entries in unequal_entries.values()]) + "\n"
        str2 = "\n".join([pretty_print_missing_all(entries, "Schema1") for entries in not_in_1.values()]) + "\n"
        str3 = "\n".join([pretty_print_missing_all(entries, "Schema2") for entries in not_in_2.values()])
        return str1 + str2 + str3
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
                                          If it evaluates to False, no filtering is performed.
        sections(tuple): the list of sections to compare.  By default, just the tags section.

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

    # Iterate over keys in HedSectionKey
    for section_key in HedSectionKey:
        if not sections or section_key not in sections:
            continue
        # Dictionaries to record (short_tag_name or name): entry pairs
        dict1 = {}
        dict2 = {}

        section1 = schema1[section_key]
        section2 = schema2[section_key]

        attribute = 'short_tag_name' if section_key == HedSectionKey.Tags else 'name'

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


def pretty_print_diff_entry(entry1, entry2):
    """
    Returns the differences between two HedSchemaEntry objects as a list of strings

    Parameters:
        entry1 (HedSchemaEntry): The first entry.
        entry2 (HedSchemaEntry): The second entry.

    Returns:
        diff_lines(list): the differences as a list of strings
    """
    output = []
    # Checking if both entries have the same name
    if entry1.name != entry2.name:
        output.append(f"\tName differs: '{entry1.name}' vs '{entry2.name}'")

    # Checking if both entries have the same description
    if entry1.description != entry2.description:
        output.append(f"\tDescription differs: '{entry1.description}' vs '{entry2.description}'")

    # Comparing attributes
    for attr in set(entry1.attributes.keys()).union(entry2.attributes.keys()):
        if entry1.attributes.get(attr) != entry2.attributes.get(attr):
            output.append(f"\tAttribute '{attr}' differs: '{entry1.attributes.get(attr)}' vs '{entry2.attributes.get(attr)}'")

    return output


def pretty_print_entry(entry):
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


def pretty_print_diff_all(entries, prompt="Differences for "):
    """
    Formats the differences between pairs of HedSchemaEntry objects.

    Parameters:
        entries (dict): A dictionary where each key maps to a pair of HedSchemaEntry objects.
        prompt(str): The prompt for each entry
    Returns:
        diff_string(str): The differences found in the dict
    """
    output = []
    for key, (entry1, entry2) in entries.items():
        output.append(f"{prompt}'{key}':")
        output += pretty_print_diff_entry(entry1, entry2)

    return "\n".join(output)


def pretty_print_missing_all(entries, schema_name):
    """
    Formats the missing entries from schema_name.

    Parameters:
        entries (dict): A dictionary where each key maps to a pair of HedSchemaEntry objects.
        schema_name(str): The name these entries are missing from
    Returns:
        diff_string(str): The differences found in the dict
    """
    output = []
    for key, entry in entries.items():
        output.append(f"'{key}' not in {schema_name}':")
        output += pretty_print_entry(entry)

    return "\n".join(output)
