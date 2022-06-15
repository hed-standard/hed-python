""" Utilities used in computing dataset annotation. """

from hed.models.hed_tag import HedTag


def breakout_tags(schema, tag_list, breakout_list):
    """ Create a dictionary with tags split into groups.

    Args:
        schema (HedSchema, HedSchemas):   Schemas to use to break out the tags.
        tag_list (list, dict):            Iterable of tags to be broken out.
        breakout_list (list):             List of hed tag node strings that should be summarized separately.

    Returns:
        dict:  Dictionary where the keys are the tags from tag_list and all of their parents. The values are
               each a list of all of the tags from the breakout_list and their parents.

    Notes:
        - The tags that aren't in the breakout list appear in the returned dictionary under "leftovers".

    """
    breakout_dict = {}
    for tag in breakout_list:
        breakout_dict[tag] = {}
    breakout_dict["leftovers"] = {}

    for tag in tag_list:
        tag_parents = get_schema_entries(schema, tag)
        found = False
        for parent in tag_parents:
            if parent.short_tag_name in breakout_list:
                breakout_dict[parent.short_tag_name][tag] = ""
                found = True
                break
        if not found:
            breakout_dict["leftovers"][tag] = ""
    return breakout_dict


def extract_dict_values(tag_dict, tag_name, tags):
    """ Get the tags associated with tag name from the tag dictionary.

    Args:
        tag_dict (dict):  Dictionary with keys that a tag node names and values are dictionaries.
        tag_name (str):   Name of a node.
        tags (list):      List of tags left to process.

    Returns:
        tuple:
            - list: Tags associated with tag_name.
            - bool: True if tag_name was found in tag_dict.

    Notes:
        - Side-effect the tags list is modified.
    """
    if tag_name not in tag_dict:
        return [], False
    tags.remove(tag_name)
    return list(tag_dict[tag_name].keys()), True


def get_schema_entries(hed_schema, tag, schema_prefix=""):
    """ Get schema entries for tag and to its parents.

    Args:
        hed_schema (HedSchema, HedSchemaGroup):  The schema in which to search for tag.
        tag (HedTag, str):       The HED tag to look for.
        schema_prefix (str):    The library prefix to use in the search.

    Returns:
        list:  A list of HedTagEntry objects for the tag and its parent nodes in the schema.

    """

    entry_list = []
    tag_entry, remainder, tag_issues = hed_schema.find_tag_entry(tag, schema_prefix)
    while tag_entry is not None:
        entry_list.append(tag_entry)
        tag_entry = tag_entry._parent_tag
    if remainder and entry_list:
        entry_list = entry_list[1:]
    return entry_list


def add_tag_list_to_dict(tag_list, tag_dict, hed_schema=None):
    """ Convert tags and groups to a dictionary.

    Args:
        tag_list (list): List of HedTag and HedGroup objects to transform.
        tag_dict (dict):
        hed_schema (HedSchema or HedSchemaGroup):  Hed schema to use to convert tags to canonical form.
            If None, assumes already converted

    Returns:
        dict: Dictionary of tags as keys with a dict of values as the value.

    Notes:
        - The returned dictionary has short tag as key and dict of values as the value.

    """
    unfolded_list = unfold_tag_list(tag_list)
    for tag in unfolded_list:
        if hed_schema:
            tag.convert_to_canonical_forms(hed_schema=hed_schema)
        short_base_tag = tag.short_base_tag
        value = tag.extension_or_value_portion
        value_dict = tag_dict.get(short_base_tag, {})
        if value:
            value_dict[value] = ''
        tag_dict[short_base_tag] = value_dict
    return tag_dict


def unfold_tag_list(tag_list):
    """ Unfold a list to a single-level list of HedTags.

     Args:
         tag_list (list):  List of HedTags and HedGroup objects.

     Returns:
         list:    A list of HedTags.

    """
    unfolded_list = []
    for element in tag_list:
        if isinstance(element, HedTag):
            unfolded_list.append(element)
        else:
            unfolded_list = unfolded_list + element.get_all_tags()
    return unfolded_list
