import os
import json
from hed.tools.bids.bids_dataset import BidsDataset
from hed.tools.annotation.summary_util import breakout_tags, extract_dict_values
from hed.models.def_dict import add_group_to_dict
from hed.models import DefDict

DEFAULT_BREAKOUT_LIST = [
    "Sensory-event", "Agent-action", "Event", "Action", "Task-event-role", "Task-action-type",
    "Task-stimulus-role", "Agent-task-role", "Item", "Sensory-presentation", "Organizational-property",
    "Informational-property", "Sensory-property", "Property", "Relation"
  ]


class TagSummary:
    """ Creates a HED tag summary for a BIDS dataset.

    Args:
        dataset (BidsDataset)        Contains the information for a BIDS dataset.
        breakout_list (list, None):  List of the tags to be explicitly broken out.

    """
    def __init__(self, dataset, breakout_list=None):
        self.dataset = dataset
        self.all_tags_dict = {}
        self._set_all_tags()
        self.breakout_list = breakout_list
        if not breakout_list:
            self.breakout_list = DEFAULT_BREAKOUT_LIST
        self.breakout_dict = breakout_tags(self.dataset.schemas, self.all_tags_dict, breakout_list)
        self.task_dict = self.extract_summary_info(self.all_defs_dict, 'Task')
        self.cond_dict = self.extract_summary_info(self.all_defs_dict, 'Condition-variable')

    def _set_all_tags(self):
        schema = self.dataset.schemas
        def_dict = DefDict()
        self.all_defs_dict = def_dict.defs
        for bids_sidecar in self.dataset.event_files.sidecar_dict.values():
            sidecar = bids_sidecar.contents
            for hed_string_obj, _, _ in sidecar.hed_string_iter([schema, def_dict]):
                add_group_to_dict(hed_string_obj, self.all_tags_dict)

    def get_design_matrices(self):
        """ Returns a dictionary with condition variables.

        Returns: (dict, list, list)
            Dictionary with condition variable levels corresponding to a design matrix.
            List with the other condition variables that aren't associated with levels.
            List of errors.

        """
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

    @staticmethod
    def extract_summary_info(entry_dict, tag_name):
        dict_info = {}
        for key, entry in entry_dict.items():
            tags = list(entry.tag_dict.keys())
            tag_names, tag_present = extract_dict_values(entry.tag_dict, tag_name, tags)
            if not tag_present:
                continue
            descriptions, tag_present = extract_dict_values(entry.tag_dict, 'Description', tags)
            dict_info[entry.name] = {'tag_name': tag_name, 'def_name': entry.name, 'tags': tags,
                                     'description': ' '.join(descriptions), 'tag_values': tag_names}
        return dict_info


if __name__ == '__main__':
    root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../../../tests/data/bids/eeg_ds003654s_hed')

    json_path = "../../../tests/data/curation/tag_summary_template.json5"
    with open(json_path) as fp:
        rules = json.load(fp)
    breakouts = rules["Tag-categories"]

    summary = TagSummary(BidsDataset(root_path), breakouts)
    designs, others, errors = summary.get_design_matrices()
    print("to here")
