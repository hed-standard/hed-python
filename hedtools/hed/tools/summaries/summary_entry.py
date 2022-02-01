""" SidecarSummary: Holds a summary of Json Sidecar """
import json
from hed.models.hed_group import HedGroup
from hed.models.model_constants import DefTagNames
from hed.models.sidecar import Sidecar
from hed.schema.hed_schema_io import load_schema_version
from hed.tools.summaries.summary_util import add_tag_list_to_dict, breakout_tags, extract_dict_values


class SummaryEntry:
    def __init__(self, name, contents, anchor_name=None):
        """Contains info for a HedGroup

        Parameters
        ----------
        name : str
            The label for this entry
        contents: HedGroup or None
            The contents of this group
       anchor_tag: str
             Lowercase version of tag that anchars this group

        For Definition groups, the label portion of the Definition tag not including the Definition/ is the name
        and the group is the contents of the Definition.
        """
        self.name = name
        self.anchor_name = anchor_name
        self.group = contents
        self.tag_dict = {}
        add_tag_list_to_dict([self.group], self.tag_dict)

    @staticmethod
    def extract_anchored_group(group, anchor_name=DefTagNames.DEFINITION_KEY):
        """ Extract a list of non-anchored groups and return a SummaryEntry for the extracted group

        Parameters:
            group: HedGroup
                Group from which to extract the summary entry
            anchor_name: str
                Short tag name (without value) of the anchor tag
        Returns:
            SummaryEntry

        This assumes that the canonical forms have already been set.
        """

        tags = group.tags()
        if len(tags) != 1 or not anchor_name:
            return None
        index = tags[0].short_tag.lower().find(anchor_name.lower())
        if index == -1:
            return None
        tag_name = tags[0].short_tag[(index + len(anchor_name) + 1):]
        groups = group.groups()
        return SummaryEntry(tag_name, groups[0], anchor_name)

    @staticmethod
    def extract_summary_info(summary_entry_dict, tag_name):
        dict_info = {}
        for key, entry in summary_entry_dict.items():
            tags = list(entry.tag_dict.keys())
            tag_names, tag_present =  extract_dict_values(entry.tag_dict, tag_name, tags)
            if not tag_present:
                continue
            descriptions, tag_present = extract_dict_values(entry.tag_dict, 'Description', tags)
            dict_info[entry.name] = {'tag_name': tag_name, 'def_name': entry.name, 'tags': tags,
                                     'description': ' '.join(descriptions), 'tag_values': tag_names}
        return dict_info

    @staticmethod
    def separate_anchored_groups(hed_string_obj, entry_dict, anchor_name=DefTagNames.DEFINITION_KEY):
        """ Removes the anchored groups from a HedString and puts them in a separate dictionary

        Parameters:
            hed_string_obj:  HedString
                HedString object whose children have their canonical forms already set
            entry_dict: dict
                dictionary of information for anchored tag groups
            anchor_name: str
                Short tag name (without value) of the anchor tag

        Returns:
            list:  a list of direct children of HedString with the anchor groups removed

        """
        groups = hed_string_obj.groups()
        tags_no_anchor = hed_string_obj.tags()
        for group in groups:
            def_entry = SummaryEntry.extract_anchored_group(group, anchor_name=anchor_name)
            if def_entry:
                entry_dict[def_entry.name] = def_entry
            else:
                tags_no_anchor.append(group)
        return tags_no_anchor


if __name__ == '__main__':
    the_path = '../../../tests/data/bids/eeg_ds003654s_hed/task-FacePerception_events.json'
    sidecar = Sidecar(the_path)
    schema = load_schema_version(xml_version='8.0.0')

    tag_dict = {}
    no_defs_list = []
    def_dict = {}
    for column in sidecar:
        for hed, key in column._hed_iter():
            hed.convert_to_canonical_forms(schema)
            no_defs_list += SummaryEntry.separate_anchored_groups(hed, def_dict, DefTagNames.DEFINITION_KEY)
    add_tag_list_to_dict(no_defs_list, tag_dict)

    hed_list = []
    for column in sidecar:
        for hed, key in column._hed_iter():
            hed.convert_to_canonical_forms(schema)
            hed_list.append(hed)

    only_dict = {}
    add_tag_list_to_dict(hed_list, only_dict )
    print(only_dict.keys())

    json_path = "../../../tests/data/summaries/tag_summary_template.json5"
    with open(json_path) as fp:
        rules = json.load(fp)
    breakout_list = rules["Tag-categories"]
    breakout_dict = breakout_tags(schema, only_dict.keys(), breakout_list)
    with open('d:/temp1.json', "w") as fp:
        json.dump(breakout_dict, fp, indent=4)



