""" Creates a summary from a list containing HedTags and HedGroups but no definitions """
import os
import json
from hed.models.model_constants import DefTagNames
from hed.tools.bids.bids_dataset import BidsDataset
from hed.tools.summaries.summary_entry import SummaryEntry
from hed.tools.summaries.summary_util import add_tag_list_to_dict, breakout_tags
from hed.models.def_dict import add_group_to_dict_new
from hed.models import DefDict


DEFAULT_BREAKOUT_LIST = [
    "Sensory-event", "Agent-action", "Event", "Action", "Task-event-role", "Task-action-type",
    "Task-stimulus-role", "Agent-task-role", "Item", "Sensory-presentation", "Organizational-property",
    "Informational-property", "Sensory-property", "Property", "Relation"
  ]


class TagSummary:
    def __init__(self, dataset, breakout_list=None):
        self.dataset = dataset
        self.all_tags_dict = {}
        self.all_defs_dict = {}
        self._set_all_tags()
        self.breakout_list = breakout_list
        if not breakout_list:
            self.breakout_list = DEFAULT_BREAKOUT_LIST
        self.breakout_dict = breakout_tags(self.dataset.schemas, self.all_tags_dict, breakout_list)
        self.task_dict = SummaryEntry.extract_summary_info(self.all_defs_dict, 'Task')
        self.cond_dict = SummaryEntry.extract_summary_info(self.all_defs_dict, 'Condition-variable')

        # ======= NEW ========
        self.all_tags_dict_new = {}
        self.all_defs_dict_new = {}
        self._set_all_tags_new()
        self.task_dict_new = SummaryEntry.extract_summary_info(self.all_defs_dict_new, 'Task')
        self.cond_dict_new = SummaryEntry.extract_summary_info(self.all_defs_dict_new, 'Condition-variable')
        # END NEW

        # todo: This block to be removed
        if self.cond_dict_new != self.cond_dict:
            raise ValueError("Cond dict!")
        if self.task_dict_new != self.task_dict:
            raise ValueError("Task dict!")
        if self.all_tags_dict != self.all_tags_dict_new:
            raise ValueError("tags dict!")
        if len(self.all_defs_dict) != len(self.all_defs_dict_new):
            raise ValueError("Defs!")

    def _set_all_tags_new(self):
        self.all_tags_dict_new = {}
        schema = self.dataset.schemas
        def_dict = DefDict()
        self.all_defs_dict_new = def_dict.defs
        for bids_sidecar in self.dataset.event_files.sidecar_dict.values():
            sidecar = bids_sidecar.contents
            for hed_string_obj, _, _ in sidecar.hed_string_iter([schema, def_dict]):
                add_group_to_dict_new(hed_string_obj, self.all_tags_dict_new)

    # Todo: This function to be removed
    def _set_all_tags(self):
        self.all_tags_dict = {}
        self.all_defs_dict = {}
        schema = self.dataset.schemas
        for bids_sidecar in self.dataset.event_files.sidecar_dict.values():
            sidecar = bids_sidecar.contents
            tag_list = []
            for column in sidecar:
                for hed, key in column._hed_iter():
                    hed.convert_to_canonical_forms(schema)
                    tag_list.append(hed)
                    SummaryEntry.separate_anchored_groups(hed, self.all_defs_dict, DefTagNames.DEFINITION_KEY)
            add_tag_list_to_dict(tag_list, self.all_tags_dict, hed_schema=schema)

    def get_design_matrices(self):
        cond_dict = self.cond_dict
        design_dict = {}
        other_list = []
        error_list = []
        for key, item in cond_dict.items():
            level_info = {'cond': key, 'level': key, 'description': item['description'], 'tags': item['tags']}
            cond_variables = item['tag_values']
            if not cond_variables:
                other_list.append(level_info)
            elif len(cond_variables) == 1:
                cond = cond_variables[0]
                level_info['cond'] = cond
                info_list = design_dict.get(cond, [])
                info_list.append(level_info)
                design_dict[cond] = info_list
            else:
                level_info['cond'] = cond_variables
                error_list.append(level_info)
        return design_dict, other_list, error_list


if __name__ == '__main__':
    root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             '../../../tests/data/bids/eeg_ds003654s_hed')

    json_path = "../../../tests/data/summaries/tag_summary_template.json5"
    with open(json_path) as fp:
        rules = json.load(fp)
    breakout_list = rules["Tag-categories"]

    summary = TagSummary(BidsDataset(root_path), breakout_list)
    design_dict, other_list, error_list = summary.get_design_matrices()


