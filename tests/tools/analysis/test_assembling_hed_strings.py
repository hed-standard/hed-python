import os
import unittest
import pandas as pd
from hed import schema as hedschema
from hed.models.tabular_input import TabularInput
from hed.models.df_util import expand_defs, shrink_defs


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids_tests/eeg_ds003645s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.2.0.xml'))
        bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                       'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        hed_schema = hedschema.load_schema(schema_path)
        cls.hed_schema = hed_schema
        # sidecar1 = Sidecar(self.json_path, name='face_sub1_json')
        # cls.sidecar_path = sidecar1
        # cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        # cls.input_data_no_sidecar = TabularInput(events_path, name="face_sub1_events_no_sidecar")
        input_data = TabularInput(events_path, sidecar=json_path, name="face_sub1_events")
        definitions = input_data.get_def_dict(hed_schema)
        cls.input_data = input_data
        cls.definitions = definitions

    def test_get_assembled_strings_no_def_expand(self):
        df = pd.DataFrame({"HED_assembled": self.input_data.series_a})
        # Results don't contain Def-expand/ when definitions aren't expanded but there are Defs in the string.
        combined_string = ', '.join(df['HED_assembled'])
        self.assertEqual(combined_string.find("Def-expand/"), -1)
        self.assertGreater(combined_string.find("Def/"), 0)

    def test_get_assembled_strings_def_expand(self):
        df = pd.DataFrame({"HED_assembled": self.input_data.series_a})
        expand_defs(df, self.hed_schema, self.definitions)
        combined_string = ', '.join(df['HED_assembled'])
        self.assertEqual(combined_string.find("Def/"), -1)
        self.assertGreater(combined_string.find("Def-expand/"), 0)
        shrink_defs(df, self.hed_schema)
        shrunk_string = ', '.join(df['HED_assembled'])
        self.assertEqual(shrunk_string.find("Def-expand/"), -1)
        self.assertGreater(shrunk_string.find("Def/"), 0)


if __name__ == '__main__':
    unittest.main()
