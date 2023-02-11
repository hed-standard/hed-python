import os
import unittest
from pandas import DataFrame
from hed import schema as hedschema
from hed.models import Sidecar, TabularInput, HedString, HedTag
from hed.tools import assemble_hed
from hed.tools.analysis.hed_tag_counts import HedTagCount, HedTagCounts


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.0.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

        cls.hed_schema = hedschema.load_schema(schema_path)
        sidecar1 = Sidecar(json_path, name='face_sub1_json')
        input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        input_df, def_dict = assemble_hed(input_data, expand_defs=False)
        cls.input_df = input_df
        cls.def_dict = def_dict

    def test_constructor(self):
        counts = HedTagCounts('Base_name')
        self.assertIsInstance(counts, HedTagCounts)
        self.assertFalse(counts.tag_dict)
        for k in range(6):
            counts.update_event_counts(HedString(self.input_df.iloc[k]['HED_assembled'], self.hed_schema),
                                       file_name='Base_name')
        self.assertIsInstance(counts.tag_dict, dict)
        self.assertEqual(len(counts.tag_dict), 15)

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
        self.assertEqual(len(counts1.tag_dict), 15)
        self.assertEqual(len(counts2.tag_dict), 15)
        self.assertEqual(len(counts3.tag_dict), 15)
        self.assertEqual(counts3.tag_dict['experiment-structure'].events, 2)

    def test_hed_tag_count(self):
        name = 'Base_name1'
        counts1 = HedTagCounts(name, 0)
        counts1.update_event_counts(HedString(self.input_df.iloc[0]['HED_assembled'], self.hed_schema), 
                                    file_name=name)
        self.assertIsInstance(counts1, HedTagCounts)


if __name__ == '__main__':
    unittest.main()
