""" Creates a summary from a list containing HedTags and HedGroups but no definitions """


class TagSummary:

    def __init__(self, name, contents):
        self.name = name



# def group_to_dict(group, hed_schema=None):
#             tag_dict = {}
#             tags = group.get_all_tags()
#             for tag in tags:
#                 if hed_schema:
#                     tag.convert_to_canonical_forms(hed_schema)
#                 short_tag = tag.short_tag
#                 value = tag.extension_or_value_portion
#                 value_dict = tag_dict.get(short_tag, {})
#                 value_dict[value] = ''
#                 tag_dict[short_tag] = value_dict
#                 return tag_dict
