from hed.models.hed_tag import HedTag
from hed.models.hed_group import HedGroup


# def group_to_dict(group, hed_schema=None):
#     tag_dict = {}
#     tags = group.get_all_tags()
#     for tag in tags:
#         if hed_schema:
#             tag.convert_to_canonical_forms(hed_schema)
#         short_tag = tag.short_tag
#         value = tag.extension_or_value_portion
#         value_dict = tag_dict.get(short_tag, {})
#         value_dict[value] = ''
#         tag_dict[short_tag] = value_dict
#         return tag_dict


def tag_list_to_dict(tag_list, hed_schema=None):
    tag_dict = {}
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
