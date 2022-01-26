""" SidecarSummary: Holds a summary of Json Sidecar """

from hed.errors.error_reporter import get_printable_issue_string
from hed.models.model_constants import DefTagNames
from hed.models.hed_group import HedGroup
from hed.models.hed_tag import HedTag
from hed.models.model_constants import DefTagNames
from hed.models.sidecar import Sidecar
from hed.schema.hed_schema_io import load_schema
from hed.tools.summaries.summary_util import tag_list_to_dict


class DefinitionEntry:
    def __init__(self, name, contents):
        """Contains info for a single definition tag

        Parameters
        ----------
        name : str
            The label portion of this name (not including Definition/)
        contents: HedGroup or None
            The contents of this definition
        """
        self.name = name
        self.group = contents
        self.tag_dict = None

    def set_tag_dict(self, hed_schema=None):
        self.tag_dict = tag_list_to_dict([self.group], hed_schema)


# class DefinitionSummary():
#
#     def __init__(self):
#         """ Construct a summary of the definitions in the dataset
#
#         """
#
#         self.definitions = {}
#
#     def __str__(self):
#         return "Has summary"
#
#     def separate_defs(self, hed_string_obj):
#         groups = hed_string_obj.groups()
#         tags_no_def = hed_string_obj.tags()
#         for group in groups:
#             def_entry = extract_anchored_group(group)
#             if def_entry:
#                 self.definitions[def_entry.name] = def_entry
#             else:
#                 tags_no_def.append(group)
#         return tags_no_def
#
#     def set_tag_dictionaries(self, hed_schema):
#         for entry in self.definitions.values():
#             entry.set_tag_dict(hed_schema)


def set_definition_dictionaries(tag_dict, hed_schema):
    for entry in tag_dict.values():
        entry.set_tag_dict(hed_schema)


def separate_defs(definition_dict, hed_string_obj):
    groups = hed_string_obj.groups()
    tags_no_def = hed_string_obj.tags()
    for group in groups:
        def_entry = extract_anchored_group(group)
        if def_entry:
            definition_dict[def_entry.name] = def_entry
        else:
            tags_no_def.append(group)
    return tags_no_def


def extract_anchored_group(group, anchor_name=DefTagNames.DEFINITION_KEY):
    tags = group.tags()
    if len(tags) != 1:
        return None

    index = tags[0].short_tag.lower().find(anchor_name)
    if index == -1:
        return None
    tag_name = tags[0].short_tag[(index + len(anchor_name) + 1):]
    groups = group.groups()
    return DefinitionEntry(tag_name, groups[0])


if __name__ == '__main__':
    the_path = '../../../tests/data/bids/eeg_ds003654s_hed/task-FacePerception_events.json'
    sidecar = Sidecar(the_path)
    schema = \
        load_schema('https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml')
    # def_sum = DefinitionSummary()
    # tag_dict = {}
    # no_defs_list = []
    # the_list = []
    # for column in sidecar:
    #     for hed, key in column._hed_iter():
    #         the_list.append(hed)
    #         no_defs_list += def_sum.separate_defs(hed)

    # def_sum = DefinitionSummary()
    tag_dict = {}
    no_defs_list = []
    def_dict = {}
    for column in sidecar:
        for hed, key in column._hed_iter():
            no_defs_list += separate_defs(def_dict, hed)

    set_definition_dictionaries(def_dict, schema)
    tag_dict = tag_list_to_dict(no_defs_list, schema)

    hed_list = []
    for column in sidecar:
        for hed, key in column._hed_iter():
            hed_list.append(hed)

    only_dict = tag_list_to_dict(hed_list, schema)
    print(only_dict.keys())

    # for hed_string_obj, column_info, issues in sidecar.hed_string_iter():
    #     leftovers = def_sum.separate_defs(hed_string_obj)
    #     column_name = column_info[0]
    #     tag_dict[column_name] = leftovers
    #     if issues:
    #         print(get_printable_issue_string(issues, title=column_name))

    print("whew")
