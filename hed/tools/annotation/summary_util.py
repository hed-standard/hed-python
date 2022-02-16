""" Utilities used in computing dataset annotation. """
from hed.models.hed_tag import HedTag


def breakout_tags(schema, tag_list, breakout_list):
    """ Create a dictionary where the tags are broken up into specific tags
    Parameters:
    -----------
        schema: HedSchema


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
        if tag_name not in tag_dict:
            return [], False
        tags.remove(tag_name)
        return list(tag_dict[tag_name].keys()), True


def get_schema_entries(hed_schema, tag, library_prefix=""):
    entry_list = []
    tag_entry, remainder, tag_issues=hed_schema.find_tag_entry(tag, library_prefix)
    while tag_entry is not None:
        entry_list.append(tag_entry)
        tag_entry = tag_entry._parent_tag
    if remainder and entry_list:
        entry_list = entry_list[1:]
    return entry_list


def add_tag_list_to_dict(tag_list, tag_dict, hed_schema=None):
    """ Convert a list of tags and groups into a single list of tags and create a dictionary

    Parameters:
        tag_list: list
            List of HedTag and HedGroup to transform
        hed_schema: HedSchema or HedSchemaGroup
            Hed schema to use to convert tags to canonical form. If None, assumes already converted

    Returns: dict
        Dictionary of tags with a list of values
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
    """ Unfold a list consisting of HedTag and HedGroup objects """
    unfolded_list = []
    for element in tag_list:
        if isinstance(element, HedTag):
            unfolded_list.append(element)
        else:
            unfolded_list = unfolded_list + element.get_all_tags()
    return unfolded_list
