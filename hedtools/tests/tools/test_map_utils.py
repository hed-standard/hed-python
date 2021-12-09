import os
import unittest
import pandas as pd
from hed.tools.map_utils import get_columns_info
from hed.tools.data_utils import get_key_hash, get_row_hash
from hed.tools.data_utils import get_new_dataframe


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


if __name__ == '__main__':
    unittest.main()
