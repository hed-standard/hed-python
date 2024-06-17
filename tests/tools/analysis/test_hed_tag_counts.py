import os
import unittest
from hed import schema as hedschema
from hed.models import Sidecar, TabularInput, HedString
from hed.models.df_util import expand_defs
from hed.tools.analysis.hed_tag_counts import HedTagCounts
import pandas as pd


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../../data/bids_tests/eeg_ds003645s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.2.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

        schema = hedschema.load_schema(schema_path)
        cls.hed_schema = schema
        sidecar1 = Sidecar(json_path, name='face_sub1_json')
        input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.input_data = input_data
        cls.sidecar1 = sidecar1
        cls.input_df = pd.DataFrame(input_data.series_a, columns=["HED_assembled"])
        cls.def_dict = input_data.get_def_dict(schema)
        cls.tag_template = {
            "Sensory events": ["Sensory-event", "Sensory-presentation", "Sensory-attribute",
                               "Experimental-stimulus", "Task-stimulus-role",
                               "Task-attentional-demand", "Incidental", "Instructional", "Warning"],
            "Agent actions": ["Agent-action", "Agent", "Action", "Agent-task-role",
                              "Task-action-type", "Participant-response"],
            "Objects": ["Item"],
            "Other events": ["Event", "Task-event-role", "Mishap"]
        }

    def test_constructor(self):
        counts = HedTagCounts('Base_name')
        self.assertIsInstance(counts, HedTagCounts)
        self.assertFalse(counts.tag_dict)
        for k in range(6):
            counts.update_event_counts(HedString(self.input_df.iloc[k]['HED_assembled'], self.hed_schema),
                                       file_name='Base_name')
        self.assertIsInstance(counts.tag_dict, dict)
        self.assertEqual(14, len(counts.tag_dict))

    def test_merge_tag_dicts(self):
        counts1 = HedTagCounts('Base_name1', 50)
        counts2 = HedTagCounts('Base_name2', 100)
        for k in range(6):
            counts1.update_event_counts(HedString(self.input_df.iloc[k]['HED_assembled'], self.hed_schema),
                                        file_name='Base_name1')
            counts2.update_event_counts(HedString(self.input_df.iloc[k]['HED_assembled'], self.hed_schema),
                                        file_name='Base_name2')
        counts3 = HedTagCounts("All", 0)
        counts3.merge_tag_dicts(counts1.tag_dict)
        counts3.merge_tag_dicts(counts2.tag_dict)
        self.assertEqual(14, len(counts1.tag_dict))
        self.assertEqual(14, len(counts2.tag_dict))
        self.assertEqual(14, len(counts3.tag_dict))
        self.assertEqual(2, counts3.tag_dict['experiment-structure'].events)

    def test_hed_tag_count(self):
        name = 'Base_name1'
        counts1 = HedTagCounts(name, 0)
        counts1.update_event_counts(HedString(self.input_df.iloc[0]['HED_assembled'], self.hed_schema),
                                    file_name=name)
        self.assertIsInstance(counts1, HedTagCounts)

    def test_organize_tags(self):
        counts = HedTagCounts('Base_name')
        definitions = self.input_data.get_def_dict(self.hed_schema)
        df = pd.DataFrame({"HED_assembled": self.input_data.series_a})
        expand_defs(df, self.hed_schema, definitions)

        # type_defs = input_data.get_definitions().gathered_defs
        for hed in df["HED_assembled"]:
            counts.update_event_counts(HedString(hed, self.hed_schema), 'run-1')
        self.assertIsInstance(counts.tag_dict, dict)
        self.assertEqual(46, len(counts.tag_dict))
        org_tags, leftovers = counts.organize_tags(self.tag_template)
        self.assertEqual(19, len(org_tags))
        self.assertEqual(21, len(leftovers))


if __name__ == '__main__':
    unittest.main()
