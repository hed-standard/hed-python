import os
import unittest
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.map_utils import get_new_dataframe, get_columns_info, get_file_list, get_key_hash, get_row_hash,\
    make_dataframe, reorder_columns, remove_quotes, separate_columns


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")

    def test_extract_dataframe(self):
        df_new = get_new_dataframe(self.stern_map_path)
        self.assertIsInstance(df_new, pd.DataFrame)
        self.assertEqual(len(df_new), 87, "get_new_dataframe should return correct number of rows")
        self.assertEqual(len(df_new.columns), 4, "get_new_dataframe should return correct number of rows")
        df_new1 = get_new_dataframe(self.stern_map_path)
        self.assertIsInstance(df_new1, pd.DataFrame)
        self.assertEqual(len(df_new1), 87, "get_new_dataframe should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 4, "get_new_dataframe should return correct number of rows")
        df_new.iloc[0]['type'] = 'Pear'
        self.assertNotEqual(df_new.iloc[0]['type'], df_new1.iloc[0]['type'],
                            "get_new_dataframe returns a new dataframe")

    def test_get_columns_info(self):
        df = get_new_dataframe(self.stern_test2_path)
        col_info = get_columns_info(df)
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(col_info.keys()), len(df.columns),
                         "get_columns_info should return a dictionary with a key for each column")

    def test_get_columns_info_skip_columns(self):
        df = get_new_dataframe(self.stern_test2_path)
        col_info = get_columns_info(df, ['latency'])
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertEqual(len(col_info.keys()), len(df.columns) - 1,
                         "get_columns_info should return a dictionary with a key for each column included")
        col_info = get_columns_info(df, list(df.columns.values))
        self.assertIsInstance(col_info, dict, "get_columns_info should return a dictionary")
        self.assertFalse(col_info, "get_columns_info should return a dictionary with a key for each column included")

    def test_get_event_files(self):
        dir_pairs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/hed_pairs')
        test_files = [name for name in os.listdir(dir_pairs) if os.path.isfile(os.path.join(dir_pairs, name))]
        file_list1 = get_file_list(dir_pairs)
        for file in file_list1:
            if os.path.basename(file) in test_files:
                continue
            raise HedFileError("FileNotFound", f"get_event_files should have found file {file}", "")

        for file in test_files:
            if os.path.join(dir_pairs, file) in file_list1:
                continue
            raise HedFileError("FileShouldNotBeFound", f"get_event_files should have not have found file {file}", "")

    def test_get_event_files_suffix(self):
        dir_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')
        file_list = get_file_list(dir_data, types=[".json", ".tsv"])
        for item in file_list:
            if item.endswith(".json") or item.endswith(".tsv"):
                continue
            raise HedFileError("BadFileType", "get_event_files expected only .html or .js files", "")

    def test_get_event_files_prefix(self):
        dir_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, prefix='sternberg', types=[".tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_key_hash(self):
        test_list = ['a', 1, 'c']
        key_hash1 = get_key_hash(test_list)
        key_hash2 = get_key_hash(tuple(test_list))
        self.assertEqual(key_hash1, key_hash2, "get_key_hash should return same hash for list or tuple")
        t_hash1 = get_key_hash([])
        self.assertTrue(t_hash1, "get_key_hash should return a hash for empty list")
        t_hash2 = get_key_hash(())
        self.assertTrue(t_hash2, "get_key_hash should return a hash for empty tuple")
        self.assertEqual(t_hash1, t_hash2, "get_key_hash should return same hash for empty list and empty tuple")

    def test_get_row_hash(self):
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        key_columns = ['type', 'event_type']
        my_map = {}
        for index, row in stern_df.iterrows():
            key = get_row_hash(row, key_columns)
            my_map[key] = index
        self.assertEqual(len(my_map.keys()), len(stern_df),
                         "get_row_hash should uniquely hash all of the keys in stern map")

    def test_make_dataframe(self):
        col_dict = {"a": {"b": 10, "c": 13, "d": 4}, "e": {"n/a": 10000}}
        df1 = make_dataframe(col_dict, "a")
        self.assertIsInstance(df1, pd.DataFrame, "make_dataframe should create a dataframe if column in col_dict")
        self.assertEqual(len(df1), 3, "make_dataframe should the right number of rows.")
        df2 = make_dataframe(col_dict, "Baloney")
        self.assertFalse(df2, "make_frame should return None if column name invalid")

    def test_remove_quotes(self):
        df1 = get_new_dataframe(self.stern_test2_path)
        remove_quotes(df1)
        df2 = get_new_dataframe(self.stern_test3_path)
        self.assertEqual(df1.loc[0, 'stimulus'], df2.loc[0, 'stimulus'], "remove_quotes should have quotes removed")

    def test_reorder_columns(self):
        df = get_new_dataframe(self.stern_map_path)
        df_new = reorder_columns(df, ['event_type', 'type'])
        self.assertEqual(len(df_new), 87, "reorder_columns should return correct number of rows")
        self.assertEqual(len(df_new.columns), 2, "reorder_columns should return correct number of rows")
        self.assertEqual(len(df), 87, "reorder_columns should return correct number of rows")
        self.assertEqual(len(df.columns), 4, "reorder_columns should return correct number of rows")
        df_new1 = reorder_columns(df, ['event_type', 'type', 'baloney'])
        self.assertEqual(len(df_new1), 87, "reorder_columns should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 2, "reorder_columns should return correct number of rows")

    def test_reorder_columns_no_skip(self):
        try:
            reorder_columns(self.stern_map_path, ['event_type', 'type', 'baloney'], skip_missing=False)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'reorder_columns threw the wrong exception {str(ex)} when missing column')
        else:
            self.fail('reorder_columns should have thrown a HedFileError exception when missing')

    def test_separate_columns(self):
        base_cols = ['a', 'b', 'c', 'd']
        present, missing = separate_columns(base_cols, [])
        self.assertFalse(present, "separate_columns should have empty present when no target columns")
        self.assertFalse(missing, "separate_columns should have empty missing when no target columns")
        present, missing = separate_columns(base_cols, ['b', 'd'])
        self.assertEqual(len(present), len(['b', 'd']),
                         "separate_columns should have target columns present when target columns subset of base")
        self.assertFalse(missing, "separate_columns should no missing columns when target columns subset of base")
        present, missing = separate_columns(base_cols, base_cols)
        self.assertEqual(len(present), len(base_cols),
                         "separate_columns should have target columns present when target columns equals base")
        self.assertFalse(missing, "separate_columns should no missing columns when target columns equals base")
        present, missing = separate_columns(base_cols, ['g', 'h'])
        self.assertFalse(present, "separate_columns should have empty present when target columns do not overlap base")
        self.assertEqual(len(missing), 2, "separate_columns should have all target columns missing")


if __name__ == '__main__':
    unittest.main()
