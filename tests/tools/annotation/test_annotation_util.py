import os
import json
import unittest
from pandas import DataFrame
from hed.tools import df_to_hed, extract_tag, generate_sidecar_entry, hed_to_df, merge_hed_dict
from hed.tools.annotation.annotation_util import _flatten_cat_col, _flatten_val_col


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        json_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 '../../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json'))
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

    def test_df_to_hed(self):
        df1 = hed_to_df(self.sidecar1a, col_names=None)
        hed1 = df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed1), 1, "df_to_hed ")
        df2 = hed_to_df(self.sidecar2b, col_names=None)
        hed2 = df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed2), 1, "df_to_hed ")

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

    def test_hed_to_def(self):
        df1a = hed_to_df(self.sidecar1a, col_names=None)
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 1)
        df1a = hed_to_df(self.sidecar1a, col_names=["a"])
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 0)
        df2a = hed_to_df(self.sidecar2a)
        self.assertIsInstance(df2a, DataFrame)
        self.assertEqual(len(df2a), 2)

    def test_merge_hed_dict(self):
        df1a = hed_to_df(self.sidecar1a, col_names=None)
        hed1a = df_to_hed(df1a)
        self.assertEqual(len(df1a), 1, "merge_hed_dict should have the right length before merge")
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length before merge")
        merge_hed_dict(self.sidecar1a, hed1a)
        self.assertEqual(len(self.sidecar1a), 2, "merge_hed_dict should have the right length after merge")

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



if __name__ == '__main__':
    unittest.main()
