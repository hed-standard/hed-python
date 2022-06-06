import os
import json
from hed.tools.bids.bids_dataset import BidsDataset
from hed.tools.analysis.summary_util import breakout_tags, extract_dict_values
from hed.models.definition_dict import add_group_to_dict
from hed.models import DefinitionDict

DEFAULT_BREAKOUT_LIST = [
    "Sensory-event", "Agent-action", "Event", "Action", "Task-event-role", "Task-action-type",
    "Task-stimulus-role", "Agent-task-role", "Item", "Sensory-presentation", "Organizational-property",
    "Informational-property", "Sensory-property", "Property", "Relation"
  ]


class TagSummary:
    """ A HED tag summary for a BID file group.

    Attributes:
        file_group (BidsFileGroup):  The BIDS file group to be summarized.
        schema (HedSchema or Hed
        all_tags_dict (dict):        The keys are all of the unique tags in the file group.
            The values are dictionaries of the unique values that these tags take on.
        breakout_list (list):   The tag nodes that are to be specially summarized.
        breakout_dict (dict):   The keys are the breakout nodes. The values are dictionaries of the
                                child nodes and the nodes themselves that appear in the dataset.
        task_dict (dict):       The keys are definition names and the values are dictionaries with info.
        cond_dict (dict):       The keys are definition names and the values are dictionaries with info.

    """

    def __init__(self, file_group, schema, breakout_list=None):
        """ Constructor for TagSummary.

        Args:
            file_group (BidsFileGroup):  Container holding the files with a particular suffix.
            schema (HedSchema or HedSchemaGroup):  The HED schema(s) used in the summary.
            breakout_list (list or None):   Used to arrange the tags in specified groupings.

        """

        self.file_group = file_group
        self.schema = schema
        self.all_tags_dict = {}
        self._set_all_tags()
        self.breakout_list = breakout_list
        if not breakout_list:
            self.breakout_list = DEFAULT_BREAKOUT_LIST
        self.breakout_dict = breakout_tags(self.schema, self.all_tags_dict, breakout_list)
        self.task_dict = self.extract_summary_info(self.all_defs_dict, 'Task')
        self.cond_dict = self.extract_summary_info(self.all_defs_dict, 'Condition-variable')

    def _set_all_tags(self):
        def_dict = DefinitionDict()
        self.all_defs_dict = def_dict.defs
        for bids_sidecar in self.file_group.sidecar_dict.values():
            sidecar = bids_sidecar.contents
            for hed_string_obj, _, _ in sidecar.hed_string_iter([self.schema, def_dict]):
                add_group_to_dict(hed_string_obj, self.all_tags_dict)

    def get_design_matrices(self):
        """ Return information about the condition variables.

        Returns:
            tuple:
                - dict: Dictionary with condition variable levels corresponding to a design matrix.
                - list: List with the other condition variables that aren't associated with levels.
                - list: List of errors.

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
        """ Extract the summary of tag in this entry.

        Args:
            entry_dict (dict):  Keys are individual tag node names.
            tag_name (str):     Name of an individual node.

        Returns:
            dict: A dictionary of the extracted tag information.

        """
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
    bids = BidsDataset(root_path)
    event_group = bids.get_tabular_group(obj_type="events")
    summary = TagSummary(event_group, schema=bids.schema, breakout_list=breakouts)
    designs, others, errors = summary.get_design_matrices()

    print("to here")
