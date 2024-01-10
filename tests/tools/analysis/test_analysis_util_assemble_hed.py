import os
import unittest
from pandas import DataFrame
from hed import schema as hedschema
from hed.models import Sidecar, TabularInput, DefinitionDict
from hed.models import df_util
from hed.tools.analysis.analysis_util import assemble_hed, search_strings


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
        cls.schema = schema
        sidecar1 = Sidecar(json_path, name='face_sub1_json')
        cls.sidecar1 = sidecar1
        cls.input_data = TabularInput(events_path, sidecar=sidecar1, name="face_sub1_events")
        cls.input_data_no_sidecar = TabularInput(events_path, name="face_sub1_events_no_sidecar")

    def test_assemble_hed_included_no_expand(self):
        df1, dict1 = assemble_hed(self.input_data, self.sidecar1, self.schema, expand_defs=False,
                                  columns_included=["onset", "duration", "event_type"])
        self.assertIsInstance(df1, DataFrame, "hed_assemble should return a dataframe when columns are included")
        columns1 = list(df1.columns)
        self.assertEqual(len(columns1), 4,
                         "assemble_hed should return the correct number of columns when columns are included ")
        first_str1 = df1.iloc[0]['HED_assembled']
        self.assertNotEqual(first_str1.find('Def/'), -1, "assemble_hed with no def expand has Def tags")
        self.assertEqual(first_str1.find('Def-expand'), -1,
                         "assemble_hed with no def expand does not have Def-expand tags")
        self.assertIsInstance(dict1.defs, dict, "hed_assemble returns a dictionary of definitions")
        self.assertEqual(len(dict1.defs), 17, "hed_assemble definition dictionary has the right number of elements.")

    def test_assemble_hed_included_expand(self):
        df2, dict2 = assemble_hed(self.input_data, self.sidecar1, self.schema, expand_defs=True,
                                  columns_included=["onset", "duration", "event_type"])
        first_str2 = df2.iloc[0]['HED_assembled']
        self.assertEqual(first_str2.find('Def/'), -1, "assemble_hed with def expand has no Def tag")
        self.assertNotEqual(first_str2.find('Def-expand/'), -1, "assemble_hed with def expand has Def-expand tags")

    def test_assemble_hed_included_no_expand_bad_column(self):
        df3, dict3 = assemble_hed(self.input_data, self.sidecar1, self.schema, expand_defs=True,
                                  columns_included=["onset", "baloney", "duration", "event_type"])
        columns3 = list(df3.columns)
        self.assertEqual(len(columns3), 4,
                         "assemble_hed should return the correct number of columns when bad columns are included ")

    def test_assemble_hed_included_expand_bad_column(self):
        df3, dict3 = assemble_hed(self.input_data, self.sidecar1, self.schema, expand_defs=True,
                                  columns_included=["onset", "baloney", "duration", "event_type"])
        columns3 = list(df3.columns)
        self.assertEqual(len(columns3), 4,
                         "assemble_hed should return the correct number of columns when bad columns are included ")

    def test_assemble_hed_no_included_no_expand(self):
        df1, dict1 = assemble_hed(self.input_data, self.sidecar1, self.schema,
                                  columns_included=None, expand_defs=False)
        self.assertIsInstance(df1, DataFrame, "hed_assemble returns a dataframe when no columns are included")
        columns1 = list(df1.columns)
        self.assertEqual(len(columns1), 1,
                         "assemble_hed returns only assembled strings when no columns include. ")
        first_str1 = df1.iloc[0]['HED_assembled']
        self.assertNotEqual(first_str1.find('Def/'), -1, "assemble_hed with no def expand has Def tags")
        self.assertEqual(first_str1.find('Def-expand'), -1,
                         "assemble_hed with no def expand does not have Def-expand tags")
        self.assertIsInstance(dict1, DefinitionDict, "hed_assemble returns a dictionary of definitions")
        self.assertEqual(len(dict1.defs), 17, "hed_assemble definition dictionary has the right number of elements.")

    def test_assemble_hed_no_included_expand(self):
        df2, dict2 = assemble_hed(self.input_data, self.sidecar1, self.schema,
                                  columns_included=None, expand_defs=True)
        first_str2 = df2.iloc[0]['HED_assembled']
        self.assertEqual(first_str2.find('Def/'), -1, "assemble_hed with def expand has no Def tag")
        self.assertNotEqual(first_str2.find('Def-expand/'), -1, "assemble_hed with def expand has Def-expand tags")

    def test_assemble_hed_bad_column_no_expand(self):
        df3, dict3 = assemble_hed(self.input_data, self.sidecar1, self.schema,
                                  columns_included=["onset", "baloney", "duration", "event_type"], expand_defs=False)
        columns3 = list(df3.columns)
        self.assertEqual(len(columns3), 4,
                         "assemble_hed returns the correct number of columns when bad columns are included ")
        first_str2 = df3.iloc[0]['HED_assembled']
        self.assertNotEqual(first_str2.find('Def/'), -1, "assemble_hed with def expand has no Def tag")
        self.assertEqual(first_str2.find('Def-expand/'), -1, "assemble_hed with def expand has Def-expand tags")

    def test_search_strings(self):
        hed_strings, dict1 = df_util.get_assembled(self.input_data, self.sidecar1, self.schema, extra_def_dicts=None,
                                                   join_columns=True, shrink_defs=False, expand_defs=True)
        queries1 = ["sensory-event"]
        query_names1 = ["sensory"]
        df1 = search_strings(hed_strings, queries1, query_names1)
        self.assertIsInstance(df1, DataFrame, "search_tabular returns a dataframe when the query is satisfied.")
        self.assertEqual(len(df1.columns), 1, "search_tabular has the right number of columns when query okay")
        self.assertEqual(len(df1.index), 200, "search_tabular has right number of rows when query okay")
        queries2 = ['data-feature', "sensory-event"]
        query_names2 = ['data', 'sensory']
        df2 = search_strings(hed_strings, queries2, query_names2)
        self.assertEqual(len(df2.columns), 2, "search_tabular has the right number of columns when query okay")
        self.assertEqual(len(df2.index), 200, "search_tabular has right number of rows when query okay")
        totals = df2.sum(axis=0)
        self.assertFalse(totals.loc['data'])
        self.assertEqual(totals.loc['sensory'], 155)
        queries3 = ['image', "sensory-event", "face"]
        query_names3 = ['image', 'sensory', "faced"]
        df3 = search_strings(hed_strings, queries3, query_names3)
        self.assertIsInstance(df3, DataFrame, "search_tabular returns a DataFrame when extra columns")
        self.assertEqual(len(df3.columns), 3, "search_tabular returns right number of columns when extra columns")
        self.assertEqual(len(df3.index), 200, "search_tabular has right number of rows when query okay")


if __name__ == '__main__':
    unittest.main()
