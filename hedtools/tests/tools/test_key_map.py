import unittest
import os
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools import KeyMap
from hed.tools.map_utils import get_file_list, get_row_hash


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")
        cls.key_cols = ['type']
        cls.target_cols = ['event_type', 'task_role', 'letter']
        cls.count_col = ['counts']

    def test_lookup_cols(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update(stern_df)
        t_col = t_map.col_map
        for index, row in stern_df.iterrows():
            key = get_row_hash(row, self.key_cols)
            key_value = t_map.map_dict[key]
            self.assertEqual(t_col.iloc[key_value]['type'], row['type'], "The key should be looked up for same map")

        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        for index, row in stern_test1.iterrows():
            key = get_row_hash(row, self.key_cols)
            key_value = t_map.map_dict[key]
            self.assertEqual(t_col.iloc[key_value]['type'], row['type'], "The key should be looked up for other file")

    def test_constructor(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        self.assertIsInstance(t_map, KeyMap)
        df = t_map.col_map
        self.assertIsInstance(df, pd.DataFrame)
        try:
            KeyMap(None, ['a'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'KeyMap threw the wrong exception {ex} when no key columns')
        else:
            self.fail('KeyMap should have thrown a HedFileError exception when no key columns')

        try:
            KeyMap(['a', 'b', 'c'], ['b', 'c', 'd'])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'KeyMap threw the wrong exception {ex} when key and target columns overlap')
        else:
            self.fail('KeyMap should have thrown a HedFileError exception when key and target columns overlap')

        emap1 = KeyMap(['a'], [])
        self.assertIsInstance(emap1, KeyMap, "KeyMap: target columns can be empty")
        self.assertEqual(len(emap1.col_map.columns), 1,
                         "The column map should have only key columns when no target")

    def test_remap(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update(stern_df)
        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        df_new, missing = t_map.remap(stern_test1)
        self.assertFalse(missing, "remap should return empty missing when all keys are accounted for")
        self.assertEqual(len(stern_test1), len(df_new), "remap should not change number rows in file")
        self.assertEqual(df_new.iloc[3]["event_type"], 'show_letter',
                         "remap should not change number rows in file")

    def test_remap_missing(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        t_map.update(stern_df)
        stern_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        stern_test1.at[3, 'type'] = 'baloney'
        stern_test1.at[10, 'type'] = 'special'
        df_new, missing = t_map.remap(stern_test1)
        self.assertTrue(missing, "remap should return return nonempty missing when when keys missing")
        self.assertEqual(len(stern_test1), len(df_new), "remap should not change number rows in file")
        self.assertEqual(df_new.iloc[3]["event_type"], 'n/a',
                         "remap should have n/a in the targets when key is missing")

    def test_remap_a(self):
        key_cols = ['type']
        target_cols = ['event_type', 'task_role', 'letter']
        key_map = KeyMap(key_cols, target_cols, 'my_name')
        key_map.update(self.stern_map_path)
        event_file_list = get_file_list(self.data_dir, types=[".tsv"], prefix='sternberg', suffix="_events")
        for file in event_file_list:
            df_new, missing = key_map.remap(file)
            self.assertFalse(missing)

    def test_update_map(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        duplicates = t_map.update(stern_df)
        df_map = t_map.col_map
        df_dict = t_map.map_dict
        self.assertEqual(len(df_map), len(stern_df), "update map should contain all the entries")
        self.assertEqual(len(df_dict.keys()), len(stern_df),
                         "update dictionary should contain all the entries")
        self.assertFalse(duplicates, "update should not have any duplicates for stern map")

    def test_update_map_missing_key(self):
        keys = self.key_cols + ['another']
        t_map = KeyMap(keys, self.target_cols)
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        try:
            t_map.update(stern_df)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'update threw the wrong exception {ex} when key column missing')
        else:
            self.fail('update should have thrown a HedFileError exception when key column was missing')

    def test_update_map_duplicate_keys(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_test2_path, delimiter='\t', header=0)
        duplicates = t_map.update(stern_df)
        self.assertTrue(duplicates, "update should return a list of duplicates if repeated keys")

    def test_update_map_not_unique(self):
        t_map = KeyMap(self.key_cols, self.target_cols)
        stern_df = pd.read_csv(self.stern_test2_path, delimiter='\t', header=0)
        duplicates = t_map.update(stern_df)
        self.assertEqual(len(t_map.col_map.columns), 4, "update should produce correct number of columns")
        self.assertEqual(len(t_map.col_map), len(stern_df) - len(duplicates),
                         "update should produce the correct number of rows")
        self.assertTrue(duplicates, "update using event file has duplicates")


if __name__ == '__main__':
    unittest.main()
