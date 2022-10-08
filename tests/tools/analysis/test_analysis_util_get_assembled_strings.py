import os
import unittest
from hed import schema as hedschema
from hed.models.hed_string import HedString
from hed.models.tabular_input import TabularInput
from hed.tools.analysis.analysis_util import get_assembled_strings


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../data/schema_tests/HED8.0.0.xml'))
        cls.bids_root_path = bids_root_path
        cls.json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.events_path = os.path.realpath(os.path.join(bids_root_path,
                                           'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        cls.hed_schema = hedschema.load_schema(schema_path)
        # sidecar1 = Sidecar(self.json_path, name='face_sub1_json')
        # cls.sidecar_path = sidecar1
        # cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        # cls.input_data_no_sidecar = TabularInput(events_path, name="face_sub1_events_no_sidecar")

    def test_get_assembled_strings_no_schema(self):
        input_data = TabularInput(self.events_path, sidecar=self.json_path, name="face_sub1_events")
        hed_list1 = get_assembled_strings(input_data, expand_defs=False)
        self.assertIsInstance(hed_list1, list, "get_assembled_groups should return a list when expand defs is False")
        self.assertIsInstance(hed_list1[0], HedString)
        hed_strings1 = [str(hed) for hed in hed_list1]
        self.assertIsInstance(hed_strings1[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings1, list)
        hed_strings_joined1 = ",".join(hed_strings1)
        self.assertEqual(hed_strings_joined1.find("Def-expand/"), -1,
                         "get_assembled_strings should not have Def-expand when expand_defs is False")
        self.assertNotEqual(hed_strings_joined1.find("Def/"), -1,
                            "get_assembled_strings should have Def/ when expand_defs is False")
        hed_list2 = get_assembled_strings(input_data, expand_defs=True)
        self.assertIsInstance(hed_list2, list, "get_assembled_groups should return a list")
        self.assertIsInstance(hed_list2[0], HedString)
        hed_strings2 = [str(hed) for hed in hed_list2]
        self.assertIsInstance(hed_strings2[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings2, list, "get_assembled")
        hed_strings_joined2 = ",".join(hed_strings2)
        self.assertNotEqual(hed_strings_joined2.find("Def-expand/"), -1,
                            "get_assembled_strings should have Def-expand when expand_defs is True")
        self.assertEqual(hed_strings_joined2.find("Def/"), -1,
                         "get_assembled_strings should not have Def/ when expand_defs is True")

    def test_get_assembled_strings_with_schema(self):
        input_data = TabularInput(self.events_path, sidecar=self.json_path, name="face_sub1_events")
        hed_list1 = get_assembled_strings(input_data, hed_schema=self.hed_schema, expand_defs=False)
        self.assertIsInstance(hed_list1, list,
                              "get_assembled_groups should return a list when expand defs is False")
        self.assertIsInstance(hed_list1[0], HedString)
        hed_strings1 = [str(hed) for hed in hed_list1]
        self.assertIsInstance(hed_strings1[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings1, list)
        hed_strings_joined1 = ",".join(hed_strings1)
        self.assertEqual(hed_strings_joined1.find("Def-expand/"), -1,
                         "get_assembled_strings should not have Def-expand when expand_defs is False")
        self.assertNotEqual(hed_strings_joined1.find("Def/"), -1,
                            "get_assembled_strings should have Def/ when expand_defs is False")
        hed_list2 = get_assembled_strings(input_data, hed_schema=self.hed_schema, expand_defs=True)
        self.assertIsInstance(hed_list2, list, "get_assembled_groups should return a list")
        self.assertIsInstance(hed_list2[0], HedString)
        hed_strings2 = [str(hed) for hed in hed_list2]
        self.assertIsInstance(hed_strings2[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings2, list, "get_assembled")
        hed_strings_joined2 = ",".join(hed_strings2)
        self.assertNotEqual(hed_strings_joined2.find("Def-expand/"), -1,
                            "get_assembled_strings should have Def-expand when expand_defs is True")
        self.assertEqual(hed_strings_joined2.find("Def/"), -1,
                         "get_assembled_strings should not have Def/ when expand_defs is True")

    def test_get_assembled_strings_no_hed(self):
        input_data_no_sidecar = TabularInput(self.events_path, name="face_sub1_events")
        hed_list1 = get_assembled_strings(input_data_no_sidecar, expand_defs=False)
        self.assertEqual(len(hed_list1), 200,
                         "get_assembled_strings should have right number of entries when no sidecar")
        self.assertIsInstance(hed_list1[0], HedString,
                              "get_assembled_string should return an HedString when no sidecar")
        self.assertFalse(hed_list1[0].children, "get_assembled_string returned HedString is empty when no sidecar")

        input_data_no_sidecar_with_schema = TabularInput(self.events_path, hed_schema=self.hed_schema,
                                                         name="face_sub1_events")
        hed_list2 = get_assembled_strings(input_data_no_sidecar_with_schema, expand_defs=False)
        self.assertEqual(len(hed_list2), 200,
                         "get_assembled_strings should have right number of entries when no sidecar")
        self.assertIsInstance(hed_list2[0], HedString,
                              "get_assembled_string should return an HedString when no sidecar")
        self.assertFalse(hed_list1[0].children, "get_assembled_string returned HedString is empty when no sidecar")


if __name__ == '__main__':
    unittest.main()
