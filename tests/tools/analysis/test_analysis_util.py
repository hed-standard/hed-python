import os
import io
import json
import unittest
from pandas import DataFrame
from hed import schema as hedschema
from hed.models import Sidecar, TabularInput, HedStringComb
from hed.tools import assemble_hed, get_assembled_strings, search_tabular


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        schema_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       '../../data/schema_test_data/HED8.0.0.xml'))
        cls.bids_root_path = bids_root_path
        json_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        events_path = os.path.realpath(os.path.join(bids_root_path,
                                                    'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

        cls.hed_schema = hedschema.load_schema(schema_path)
        cls.sidecar = Sidecar(json_path, name='face_sub1_json')
        cls.input_data = TabularInput(events_path, sidecar=cls.sidecar, name="face_sub1_events")

    def test_get_assembled_strings_no_schema(self):
        hed_list1 = get_assembled_strings(self.input_data, expand_defs=False)
        self.assertIsInstance(hed_list1, list, "get_assembled_groups should return a list when expand defs is False")
        self.assertIsInstance(hed_list1[0], HedStringComb)
        hed_strings1 = [str(hed) for hed in hed_list1]
        self.assertIsInstance(hed_strings1[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings1, list)
        hed_strings_joined1 = (",").join(hed_strings1)
        self.assertEqual(hed_strings_joined1.find("Def-expand/"), -1,
                          "get_assembled_strings should not have Def-expand when expand_defs is False" )
        self.assertNotEqual(hed_strings_joined1.find("Def/"), -1,
                          "get_assembled_strings should have Def/ when expand_defs is False")
        hed_list2 = get_assembled_strings(self.input_data, expand_defs=True)
        self.assertIsInstance(hed_list2, list, "get_assembled_groups should return a list")
        self.assertIsInstance(hed_list2[0], HedStringComb)
        hed_strings2 = [str(hed) for hed in hed_list2]
        self.assertIsInstance(hed_strings2[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings2, list, "get_assembled")
        hed_strings_joined2 = (",").join(hed_strings2)
        self.assertNotEqual(hed_strings_joined2.find("Def-expand/"), -1,
                          "get_assembled_strings should have Def-expand when expand_defs is True" )
        self.assertEqual(hed_strings_joined2.find("Def/"), -1,
                          "get_assembled_strings should not have Def/ when expand_defs is True")

    def test_get_assembled_strings_with_schema(self):
        hed_list1 = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=False)
        self.assertIsInstance(hed_list1, list,
                              "get_assembled_groups should return a list when expand defs is False")
        self.assertIsInstance(hed_list1[0], HedStringComb)
        hed_strings1 = [str(hed) for hed in hed_list1]
        self.assertIsInstance(hed_strings1[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings1, list)
        hed_strings_joined1 = (",").join(hed_strings1)
        self.assertEqual(hed_strings_joined1.find("Def-expand/"), -1,
                         "get_assembled_strings should not have Def-expand when expand_defs is False")
        self.assertNotEqual(hed_strings_joined1.find("Def/"), -1,
                            "get_assembled_strings should have Def/ when expand_defs is False")
        hed_list2 = get_assembled_strings(self.input_data, hed_schema=self.hed_schema, expand_defs=True)
        self.assertIsInstance(hed_list2, list, "get_assembled_groups should return a list")
        self.assertIsInstance(hed_list2[0], HedStringComb)
        hed_strings2 = [str(hed) for hed in hed_list2]
        self.assertIsInstance(hed_strings2[0], str, "get_assembled_strings can be converted.")
        self.assertIsInstance(hed_strings2, list, "get_assembled")
        hed_strings_joined2 = (",").join(hed_strings2)
        self.assertNotEqual(hed_strings_joined2.find("Def-expand/"), -1,
                            "get_assembled_strings should have Def-expand when expand_defs is True")
        self.assertEqual(hed_strings_joined2.find("Def/"), -1,
                         "get_assembled_strings should not have Def/ when expand_defs is True")

    def test_assemble_hed(self):
        df1 = assemble_hed(self.input_data, columns_included=["onset", "duration", "event_type"], expand_defs=False)
        self.assertIsInstance(df1, DataFrame, "hed_assemble should return a dataframe when columns are included")
        columns1 = list(df1.columns)
        self.assertEqual(len(columns1), 4,
                         "assemble_hed should return the correct number of columns when columns are included ")
        first_str1 = df1.iloc[0]['HED']
        self.assertNotEqual(first_str1.find('Def/'), -1, "assemble_hed with no def expand has Def tags")
        self.assertEqual(first_str1.find('Def-expand'), -1,
                         "assemble_hed with no def expand does not have Def-expand tags")
        df2 = assemble_hed(self.input_data, columns_included=["onset", "duration", "event_type"], expand_defs=True)
        first_str2 = df2.iloc[0]['HED']
        self.assertEqual(first_str2.find('Def/'), -1, "assemble_hed with def expand has no Def tag")
        self.assertNotEqual(first_str2.find('Def-expand/'), -1, "assemble_hed with def expand has Def-expand tags")

        df3 = assemble_hed(self.input_data,
                           columns_included=["onset", "baloney", "duration", "event_type"], expand_defs=False)
        columns3 = list(df3.columns)
        self.assertEqual(len(columns3), 4,
                         "assemble_hed should return the correct number of columns when bad columns are included ")

    def test_search_tabular(self):
        query1 = "sensory-event"
        df1 = search_tabular(self.input_data, self.hed_schema, query1, columns_included=None)
        self.assertIsInstance(df1, DataFrame, "search_tabular returns a dataframe when the query is satisfied.")
        self.assertEqual(len(df1.columns), 2, "search_tabular has the right number of columns when query okay")
        self.assertEqual(len(df1.index), 438, "search_tabular has right number of rows when query okay")
        query2 = 'data-feature'
        df2 = search_tabular(self.input_data, self.hed_schema, query2, columns_included=None)
        self.assertFalse(df2, "search_tabular returns None when query is not satisfied.")

        query3 = "sensory-event"
        df3 = search_tabular(self.input_data, self.hed_schema, query3, columns_included=['event_type', 'rep_status'])
        self.assertIsInstance(df3, DataFrame, "search_tabular returns a DataFrame when extra columns")
        self.assertEqual(len(df3.columns), 4, "search_tabular returns right number of columns when extra columns")
        self.assertEqual(len(df3.index), 438, "search_tabular has right number of rows when query okay")


if __name__ == '__main__':
    unittest.main()
