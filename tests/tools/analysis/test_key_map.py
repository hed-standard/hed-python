import unittest
import os
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.analysis.key_map import KeyMap
from hed.tools.util.data_util import get_new_dataframe
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/other_tests")
        cls.curation_base_dir = curation_base_dir
        cls.stern_map_path = os.path.join(curation_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(curation_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(curation_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(curation_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path2 = os.path.join(
            curation_base_dir, "sub-001_task-AuditoryVisualShift_run-01_events.tsv"
        )
        cls.attn_map_path = os.path.join(curation_base_dir, "attention_shift_remap_event_template_filled.tsv")
        cls.key_cols1 = ["type"]
        cls.target_cols1 = ["event_type", "task_role", "letter"]
        cls.count_col1 = ["counts"]
        cls.key_cols2 = ["event_code", "cond_code", "focus_modality"]
        cls.target_cols2 = ["event_type", "attention_status", "task_role"]

    def test_constructor(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        self.assertIsInstance(t_map, KeyMap)
        df = t_map.col_map
        self.assertIsInstance(df, pd.DataFrame)
        with self.assertRaises(ValueError) as context:
            KeyMap(None, ["a"])
        self.assertEqual(context.exception.args[0], "KEY_COLUMNS_EMPTY")

        with self.assertRaises(ValueError) as context1:
            KeyMap(["a", "b", "c"], ["b", "c", "d"])
        self.assertEqual(context1.exception.args[0], "KEY_AND_TARGET_COLUMNS_NOT_DISJOINT")

        emap1 = KeyMap(["a"], [])
        self.assertIsInstance(emap1, KeyMap, "KeyMap: target columns can be empty")
        self.assertEqual(len(emap1.col_map.columns), 1, "The column map should have only key columns when no target")

    def test_str(self):
        t_map = KeyMap(self.key_cols1)
        str1 = str(t_map)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df)
        str2 = str(t_map)
        self.assertGreater(len(str2), len(str1))
        self.assertIsInstance(str2, str)

    def test_make_template(self):
        t_map = KeyMap(self.key_cols1)
        stern_df = get_new_dataframe(self.stern_test1_path)
        t_map.update(stern_df)
        df1 = t_map.make_template(show_counts=False)
        self.assertIsInstance(df1, pd.DataFrame, "make_template should return a DataFrame")
        self.assertEqual(len(df1.columns), 1, "make_template should return 1 column single key, no additional columns")
        df2 = t_map.make_template(show_counts=True)
        self.assertEqual(len(df2.columns), 2, "make_template returns an extra column for counts")

        t_map2 = KeyMap(["event_type", "type"])
        t_map2.update(self.stern_test1_path)
        df3 = t_map2.make_template()
        self.assertIsInstance(df3, pd.DataFrame, "make_template should return a DataFrame")
        self.assertEqual(len(df3.columns), 3, "make_template should return 2 columns w 2 keys, no additional columns")
        df3 = t_map2.make_template(["bananas", "pears", "apples"])
        self.assertIsInstance(df3, pd.DataFrame, "make_template should return a DataFrame")
        self.assertEqual(len(df3.columns), 6, "make_template should return 5 columns w 2 keys, 3 additional columns")

    def test_make_template_key_overlap(self):
        t_map = KeyMap(["event_type", "type"])
        t_map.update(self.stern_map_path)
        with self.assertRaises(HedFileError) as context:
            t_map.make_template(["Bananas", "type", "Pears"])
        self.assertEqual(context.exception.args[0], "AdditionalColumnsNotDisjoint")

    def test_remap(self):
        t_map_stern = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map_stern.update(stern_df)
        stern_test1 = get_new_dataframe(self.stern_test1_path)
        df1, missing1 = t_map_stern.remap(stern_test1)
        self.assertFalse(missing1, "remap should return empty missing when all keys are accounted for")
        self.assertEqual(len(stern_test1), len(df1), "remap should not change number rows in file")
        self.assertEqual(
            df1.iloc[3]["event_type"], "show_letter", "remap should have right value when single column key"
        )

    def test_remap_multiple_keys(self):
        t_map_attn = KeyMap(self.key_cols2, self.target_cols2)
        attn_df_map = get_new_dataframe(self.attn_map_path)
        t_map_attn.update(attn_df_map)
        attn_test = get_new_dataframe(self.attention_shift_path2)
        df1, missing1 = t_map_attn.remap(attn_test)
        self.assertFalse(missing1, "remap should return empty missing when all keys are accounted for")
        self.assertEqual(len(attn_test), len(df1), "remap should not change number rows in file")
        self.assertEqual(
            df1.iloc[3]["event_type"], "button_press", "remap should have correct value when multiple keys"
        )

    def test_remap_missing(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df)
        stern_test1 = get_new_dataframe(self.stern_test1_path)
        stern_test1.at[3, "type"] = "baloney"
        stern_test1.at[10, "type"] = "special"
        df_new, missing = t_map.remap(stern_test1)
        self.assertTrue(missing, "remap should return return nonempty missing when when keys missing")
        self.assertEqual(len(stern_test1), len(df_new), "remap should not change number rows in file")
        self.assertEqual(
            df_new.iloc[3]["event_type"], "n/a", "remap should have n/a in the targets when key is missing"
        )

    def test_remap_files(self):
        key_cols = ["type"]
        target_cols = ["event_type", "task_role", "letter"]
        key_map = KeyMap(key_cols, target_cols, "my_name")
        key_map.update(self.stern_map_path)
        event_file_list = get_file_list(
            self.curation_base_dir, name_prefix="sternberg", name_suffix="events", extensions=[".tsv"]
        )
        for file in event_file_list:
            df_new, missing = key_map.remap(file)
            self.assertFalse(missing)

    def test_update_map(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df)
        df_map = t_map.col_map
        df_dict = t_map.map_dict
        self.assertEqual(len(df_map), len(stern_df), "update map should contain all the entries")
        self.assertEqual(len(df_dict.keys()), len(stern_df), "update dictionary should contain all the entries")

    def test_update_map_missing(self):
        keys = self.key_cols1 + ["another"]
        t_map = KeyMap(keys, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        try:
            t_map.update(stern_df, allow_missing=False)
        except (HedFileError, KeyError):
            pass
        except Exception as ex:
            self.fail(f"update threw the wrong exception {ex} when key column missing")
        else:
            self.fail("update should have thrown a HedFileError exception when key column was missing")

    def test_update_map_missing_allowed(self):
        keys = self.key_cols1 + ["another"]
        t_map = KeyMap(keys, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_map_path)
        t_map.update(stern_df, allow_missing=True)

    def test_update_map_not_unique(self):
        t_map = KeyMap(self.key_cols1, self.target_cols1)
        stern_df = get_new_dataframe(self.stern_test2_path)
        t_map.update(stern_df)
        self.assertEqual(len(t_map.col_map.columns), 4, "update should produce correct number of columns")
        self.assertEqual(len(t_map.col_map), len(t_map.count_dict), "update should produce the correct number of rows")

    def test_remap_numeric_keys_simple(self):
        """Test remap with simple numeric keys (pandas 3.0 compatibility)."""
        # Create a simple KeyMap with numeric keys
        key_map = KeyMap(['col1'], ['result'])
        
        # Create a mapping DataFrame with numeric keys
        map_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'result': ['one', 'two', 'three']
        })
        key_map.update(map_df)
        
        # Create test data with numeric values
        test_df = pd.DataFrame({
            'col1': [1, 2, 1, 3, 2]
        })
        
        # This should not raise ValueError on pandas 3.0.3
        df_result, missing = key_map.remap(test_df)
        
        self.assertEqual(len(df_result), 5, "remap should preserve number of rows")
        self.assertEqual(df_result.iloc[0]['result'], 'one', "remap should map 1 to 'one'")
        self.assertEqual(df_result.iloc[1]['result'], 'two', "remap should map 2 to 'two'")
        self.assertEqual(df_result.iloc[2]['result'], 'one', "remap should map 1 to 'one'")
        self.assertEqual(df_result.iloc[3]['result'], 'three', "remap should map 3 to 'three'")
        self.assertFalse(missing, "remap should not have missing keys")

    def test_remap_numeric_keys_as_strings(self):
        """Test remap with numeric keys stored as strings (common case)."""
        key_map = KeyMap(['test_code'], ['test_label'])
        
        # Create a mapping where numeric keys are stored as strings
        map_df = pd.DataFrame({
            'test_code': ['1', '2', '3', '4'],
            'test_label': ['low', 'medium', 'high', 'critical']
        })
        key_map.update(map_df)
        
        # Create test data with numeric values as strings
        test_df = pd.DataFrame({
            'test_code': ['1', '2', '3', '1', '4', '2']
        })
        
        df_result, missing = key_map.remap(test_df)
        
        self.assertEqual(len(df_result), 6, "remap should preserve number of rows")
        self.assertEqual(df_result.iloc[0]['test_label'], 'low')
        self.assertEqual(df_result.iloc[1]['test_label'], 'medium')
        self.assertEqual(df_result.iloc[2]['test_label'], 'high')
        self.assertEqual(df_result.iloc[4]['test_label'], 'critical')
        self.assertFalse(missing, "remap should not have missing keys")

    def test_remap_numeric_keys_with_na(self):
        """Test remap with numeric keys including n/a values."""
        key_map = KeyMap(['value'], ['category'])
        
        # Create mapping with numeric and string keys
        map_df = pd.DataFrame({
            'value': ['1', '2', '3'],
            'category': ['cat_a', 'cat_b', 'cat_c']
        })
        key_map.update(map_df)
        
        # Create test data with n/a values
        test_df = pd.DataFrame({
            'value': ['1', '2', 'n/a', '3', 'n/a']
        })
        
        df_result, missing = key_map.remap(test_df)
        
        self.assertEqual(len(df_result), 5, "remap should preserve number of rows")
        self.assertEqual(df_result.iloc[0]['category'], 'cat_a')
        self.assertEqual(df_result.iloc[2]['category'], 'n/a', "remap should map n/a to n/a")
        self.assertEqual(df_result.iloc[3]['category'], 'cat_c')

    def test_remap_multiple_numeric_keys_cascade(self):
        """Test remap with multiple numeric keys cascading (the pandas 3.0.3 failing case)."""
        # This is the exact scenario from pandas_fail.md that was failing
        key_map = KeyMap(['test', 'response_accuracy'], ['result'])
        
        # Create mapping for multiple key combination
        map_df = pd.DataFrame({
            'test': ['1', '2'],
            'response_accuracy': ['correct', 'correct'],
            'result': ['correct_left', 'correct_right']
        })
        key_map.update(map_df)
        
        # Create test data matching the failure scenario
        test_df = pd.DataFrame({
            'test': ['1', '2', 'n/a', '3', '4', '5'],
            'response_accuracy': ['correct', 'correct', 'correct', 'n/a', 'correct', 'correct']
        })
        
        # This was the failing line: map_series = pd.Series(self.map_dict)
        # Should work now with explicit index/data parameters
        df_result, missing = key_map.remap(test_df)
        
        self.assertEqual(len(df_result), 6, "remap should preserve number of rows")
        self.assertEqual(df_result.iloc[0]['result'], 'correct_left')
        self.assertEqual(df_result.iloc[1]['result'], 'correct_right')
        # Rows with missing key combinations should get 'n/a'
        self.assertEqual(df_result.iloc[2]['result'], 'n/a')
        self.assertEqual(df_result.iloc[3]['result'], 'n/a')

    def test_remap_large_numeric_key_dict(self):
        """Test remap with a large dictionary of numeric keys to ensure Series construction works."""
        key_map = KeyMap(['event_id'], ['event_name'])
        
        # Create a large mapping with numeric event IDs
        size = 100
        map_data = {
            'event_id': [str(i) for i in range(size)],
            'event_name': [f'event_{i}' for i in range(size)]
        }
        map_df = pd.DataFrame(map_data)
        key_map.update(map_df)
        
        # Create test data with random event IDs
        test_data = {
            'event_id': [str(i % 50) for i in range(200)]  # Use first 50 event IDs
        }
        test_df = pd.DataFrame(test_data)
        
        df_result, missing = key_map.remap(test_df)
        
        self.assertEqual(len(df_result), 200, "remap should preserve number of rows")
        # Verify some mappings
        self.assertEqual(df_result.iloc[0]['event_name'], 'event_0')
        self.assertEqual(df_result.iloc[50]['event_name'], 'event_0')  # 50 % 50 = 0
        self.assertEqual(df_result.iloc[99]['event_name'], 'event_49')  # 99 % 50 = 49


if __name__ == "__main__":
    unittest.main()
