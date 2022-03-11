import os
import json
import unittest
from pandas import DataFrame
from hed.tools import check_df_columns, df_to_hed, extract_tag, generate_sidecar_entry, hed_to_df, merge_hed_dict, \
    EventValueSummary
from hed.tools.annotation.annotation_util import _flatten_cat_col, _flatten_val_col,  _get_value_entry, _update_cat_dict
from hed.util import get_file_list


# noinspection PyBroadException
class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../data/bids/eeg_ds003654s_hed'))
        json_path = os.path.realpath(os.path.join(cls.bids_root_path, 'task-FacePerception_events.json'))
        cls.sidecar1a = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": "Purple"}}
        cls.sidecar1b = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": "Purple", "Description": "Its a color."}}
        cls.sidecar1c = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": "Purple, Description/New purple", "Description": "Its a color."}}
        cls.sidecar2a = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": {"b2": "Purple", "b3": "Red"}}}
        cls.sidecar2b = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": {"b2": "Purple", "b3": "Red"}}}
        cls.sidecar2c = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                         "b": {"HED": {"b2": "Purple,Description/Bad purple", "b3": "Red"},
                               "Levels": {"b2": "Its purple.", "b3": "Its red."}}}
        with open(json_path) as fp:
            cls.sidecar3 = json.load(fp)

    def test_check_df_columns(self):
        df1 = hed_to_df(self.sidecar1a)
        missing1 = check_df_columns(df1)
        self.assertFalse(missing1)
        df2 = df1.drop('column_value', axis=1)
        missing2 = check_df_columns(df2, ('column_name', 'column_value'))
        self.assertTrue(missing2, "check_df_column has non-empty return if items missing")
        self.assertEqual(len(missing2), 1, "check_df_column finds correct number of missing items")

    def test_df_to_hed(self):
        df1 = hed_to_df(self.sidecar1a, col_names=None)
        hed1 = df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed1), 1, "df_to_hed ")
        df2 = hed_to_df(self.sidecar2b, col_names=None)
        hed2 = df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed2), 1, "df_to_hed ")

    def test_df_to_hed_columns_missing(self):
        df2a = hed_to_df(self.sidecar2a, col_names=None)
        df2b = hed_to_df(self.sidecar2b, col_names=None)
        df2c = hed_to_df(self.sidecar2c, col_names=None)
        hed2a = df_to_hed(df2a)
        self.assertIsInstance(hed2a, dict)
        # TODO: test of missing columns

    def test_df_to_hed_extra_col_names(self):
        df2a = hed_to_df(self.sidecar2a, col_names=None)
        df2b = hed_to_df(self.sidecar2b, col_names=None)
        df2c = hed_to_df(self.sidecar2c, col_names=None)
        hed2a = df_to_hed(df2a)
        self.assertIsInstance(hed2a, dict)
        # TODO: test of col_names

    def test_extract_tag(self):
        str1 = "Bear, Description, Junk"
        remainder1, extracted1 = extract_tag(str1, 'Description/')
        self.assertEqual(remainder1, str1, "extract_tag should return same string if no extracted tag")
        self.assertIsInstance(extracted1, list, "extract_tag should return an empty list list")
        self.assertFalse(extracted1, "extract_tag return an empty extracted list if no tag in string ")
        str2 = "Bear, Description/Pluck this leaf., Junk"
        remainder2, extracted2 = extract_tag(str2, 'Description/')
        self.assertEqual(remainder2, "Bear, Junk", "extract_tag should return the right string")
        self.assertIsInstance(extracted2, list, "extract_tag should return a list")
        self.assertEqual(len(extracted2), 1, "extract_tag should return a list of the right length")
        self.assertEqual(extracted2[0], "Pluck this leaf.", "extract_tag return right item ")
        str3 = "Bear, Description/Pluck this leaf., Junk, Description/Another description."
        remainder3, extracted3 = extract_tag(str3, 'Description/')
        self.assertEqual(remainder3, "Bear, Junk", "extract_tag should return the right string")
        self.assertIsInstance(extracted3, list, "extract_tag should return a list")
        self.assertEqual(len(extracted3), 2, "extract_tag should return a list of the right length")
        self.assertEqual(extracted3[0], "Pluck this leaf.", "extract_tag return right item ")
        self.assertEqual(extracted3[1], "Another description.", "extract_tag return right item ")

    def test_generate_sidecar_entry(self):
        entry1 = generate_sidecar_entry('event_type', column_values=['apple', 'banana', 'n/a'])
        self.assertIsInstance(entry1, dict, "generate_sidecar_entry should be a dictionary when column values")
        self.assertEqual(len(entry1), 3, "generate_sidecar_entry should have 3 entries when column values")
        self.assertIn('Description', entry1, "generate_sidecar_entry should have Description when column values")
        self.assertIn('HED', entry1,  "generate_sidecar_entry should have HED when column values")
        self.assertEqual(len(entry1['HED']), 2, "generate_sidecar_entry should not include n/a in HED")
        self.assertIn('Levels', entry1, "generate_sidecar_entry should have Levels when column values")
        self.assertEqual(len(entry1['Levels']), 2, "generate_sidecar_entry should not include n/a in Levels")
        entry2 = generate_sidecar_entry('event_type')
        self.assertIsInstance(entry2, dict, "generate_sidecar_entry should be a dictionary when no column values")
        self.assertEqual(len(entry2), 2, "generate_sidecar_entry should have 2 entries when no column values")
        self.assertIn('Description', entry2, "generate_sidecar_entry should have a Description when no column values")
        self.assertIn('HED', entry2, "generate_sidecar_entry should have a Description when no column values")
        self.assertIsInstance(entry2['HED'], str,
                              "generate_sidecar_entry HED entry should be str when no column values")

    def test_hed_to_df(self):
        df1a = hed_to_df(self.sidecar1a, col_names=None)
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 1)
        df1a = hed_to_df(self.sidecar1a, col_names=["a"])
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 0)
        df2a = hed_to_df(self.sidecar2a)
        self.assertIsInstance(df2a, DataFrame)
        self.assertEqual(len(df2a), 2)

    def test_merge_hed_dict_cat_col(self):
        df2a = hed_to_df(self.sidecar2a, col_names=None)
        df2b = hed_to_df(self.sidecar2b, col_names=None)
        df2c = hed_to_df(self.sidecar2c, col_names=None)
        hed2a = df_to_hed(df2a)
        self.assertIsInstance(hed2a, dict)
        # TODO: test of categorical columns not yet written

    def test_merge_hed_dict_value_col(self):
        df1a = hed_to_df(self.sidecar1a, col_names=None)
        df1b = hed_to_df(self.sidecar1b, col_names=None)
        hed1a = df_to_hed(df1a)
        hed1b = df_to_hed(df1b)
        self.assertEqual(len(df1a), 1, "merge_hed_dict should have the right length before merge")
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length before merge")
        merge_hed_dict(self.sidecar1a, hed1a)
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length after merge")
        self.assertIsInstance(self.sidecar1a['b']['HED'], str, "merge_hed_dict preserve a value key")
        self.assertNotIn('Description', self.sidecar1a['b'], "merge_hed_dict should not have description when n/a")
        merge_hed_dict(self.sidecar1b, hed1a)
        self.assertIsInstance(self.sidecar1b['b']['HED'], str, "merge_hed_dict preserve a value key")
        self.assertIn('Description', self.sidecar1b['b'], "merge_hed_dict should not have description when n/a")
        merge_hed_dict(self.sidecar1b, hed1b)
        self.assertIn('Description', self.sidecar1b['b'], "merge_hed_dict should not have description when n/a")

    def test_merge_hed_dict_full(self):
        exclude_dirs = ['stimuli']
        name_indices = (0, 2)
        skip_columns = ["onset", "duration", "sample", "trial", "response_time"]
        value_columns = ["rep_lag", "stim_file", "value"]
        event_files = get_file_list(self.bids_root_path, extensions=[".tsv"], name_suffix="_events",
                                    exclude_dirs=exclude_dirs)
        value_sum = EventValueSummary(value_cols=value_columns, skip_cols=skip_columns)
        value_sum.update(event_files)
        sidecar_template = value_sum.extract_sidecar_template()
        example_spreadsheet = hed_to_df(sidecar_template)
        spreadsheet_sidecar = df_to_hed(example_spreadsheet, description_tag=False)
        example_sidecar = {}
        self.assertEqual(0, len(example_sidecar), 'merge_hed_dict input is empty for this test')
        merge_hed_dict(example_sidecar, spreadsheet_sidecar)
        self.assertEqual(6, len(example_sidecar), 'merge_hed_dict merges with the correct length')

    def test_flatten_cat_col(self):
        col1 = self.sidecar2c["a"]
        col2 = self.sidecar2c["b"]
        try:
            _flatten_cat_col("a", col1)
        except KeyError:
            pass
        except Exception:
            self.fail("_flatten_cat_col threw the wrong exception when no HED key")
        else:
            self.fail("_flatten_cat_col should have thrown a KeyError exception when no HED key")

        keys2, values2, descriptions2, tags2 = _flatten_cat_col("b", col2)
        self.assertEqual(len(keys2), 2, "_flatten_cat_col should have right number of keys if HED")
        self.assertEqual(len(values2), 2, "_flatten_cat_col should have right number of values if HED")
        self.assertEqual(len(descriptions2), 2, "_flatten_cat_col should have right number of descriptions if HED")
        self.assertEqual(len(tags2), 2, "_flatten_cat_col should have right number of tags if HED")
        self.assertEqual(descriptions2[0], 'Bad purple',
                         "_flatten_cat_col should use the Description tag if available")

    def test_flatten_value_col(self):
        col1 = self.sidecar1a["a"]
        col2 = self.sidecar1b["b"]
        try:
            _flatten_val_col("a", col1)
        except KeyError:
            pass
        except Exception:
            self.fail("_flatten_value_col threw the wrong exception when no HED key")
        else:
            self.fail("_flatten_value_col should have thrown a KeyError exception when no HED key")

        keys2, values2, descriptions2, tags2 = _flatten_val_col("b", col2)
        self.assertEqual(len(keys2), 1, "_flatten_val_col should have right number of keys if HED")
        self.assertEqual(len(values2), 1, "_flatten_val_col should have right number of values if HED")
        self.assertEqual(len(descriptions2), 1, "_flatten_val_col should have right number of descriptions if HED")
        self.assertEqual(len(tags2), 1, "_flatten_cat_col should have right number of tags if HED")
        self.assertEqual(descriptions2[0], 'Its a color.',
                         "_flatten_cat_col should use the Description tag if available")
        self.assertEqual(values2[0], 'n/a', "_flatten_cat_col should a n/a value column")

    def test_get_row_tags(self):
        col1 = self.sidecar2c["a"]
        col2 = self.sidecar2c["b"]
        self.assertTrue(col1)

    def test_get_value_entry(self):
        dict1 = _get_value_entry('n/a', 'n/a')
        self.assertFalse(dict1, "_get_value_entry should return empty dict if everything n/a")
        dict2 = _get_value_entry('', '')
        self.assertFalse(dict2, "_get_value_entry should return empty dict if everything empty")
        dict3 = _get_value_entry('Red,Blue', '')
        self.assertIn('HED', dict3, "_get_value_entry should have a HED entry when tags but no description")
        self.assertNotIn('Description', dict3,
                         "_get_value_entry should not have a Description entry when tags but no description")
        dict4 = _get_value_entry('Red,Blue,Description/Too bad', '')
        self.assertIn('HED', dict4, "_get_value_entry should have a HED entry when Description tag")
        self.assertNotIn('Description', dict4,
                         "_get_value_entry should not have a Description entry when Description tag")
        dict5 = _get_value_entry('', 'This is a test')
        self.assertIn('HED', dict5, "_get_value_entry should have a HED entry when Description used")
        self.assertIn('Description', dict5,
                      "_get_value_entry should have a Description entry when Description used")
        dict6 = _get_value_entry('Red,Blue', 'This is a test')
        self.assertIn('HED', dict5, "_get_value_entry should have a HED entry when Description used")
        self.assertEqual(dict5['HED'], 'Description/This is a test',
                         "_get_value_entry should correct value when Description used for HED tags")
        self.assertIn('Description', dict5,
                      "_get_value_entry should have a Description entry when Description used")
        dict7 = _get_value_entry('Red,Blue', 'This is a test')
        self.assertIn('HED', dict7, "_get_value_entry should have a HED entry when Description used")
        self.assertIn('Description', dict7, "_get_value_entry should have a HED entry when Description used")
        dict8 = _get_value_entry('', 'This is a test', description_tag=False)
        self.assertNotIn('HED', dict8, "_get_value_entry should not have a HED entry when Description not used")
        self.assertIn('Description', dict8, "_get_value_entry should have a Description entry when Description not used")

    def test_update_cat_dict(self):
        # TODO: Improve tests
        cat_dict = self.sidecar3['event_type']
        value1 = cat_dict['HED']['show_face']
        self.assertNotEqual(cat_dict['HED']['show_face'], 'Blue,Red')
        _update_cat_dict(cat_dict, 'show_face', 'Blue,Red', 'n/a', description_tag=True)
        self.assertEqual(cat_dict['HED']['show_face'], 'Blue,Red')


if __name__ == '__main__':
    unittest.main()
