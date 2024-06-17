import os
import unittest
import numpy as np

from pandas import DataFrame, Categorical
from hed.errors.exceptions import HedFileError
from hed.tools.util.data_util import add_columns, check_match, delete_columns, delete_rows_by_column, \
    get_key_hash, get_new_dataframe, get_row_hash, get_value_dict, \
    make_info_dataframe, reorder_columns, replace_na, replace_values, separate_values


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        curation_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/remodel_tests')
        cls.stern_map_path = os.path.join(curation_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(curation_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(curation_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(curation_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(curation_base_dir, "sub-001_task-AuditoryVisualShift_run-01_events.tsv")
        cls.sampling_rate_path = os.path.join(curation_base_dir, "bcit_baseline_driving_samplingRates.tsv")

    def test_add_column(self):
        data = {'Name': ['n/a', '', 'tom', 'alice', 0, 1],
                'Age': [np.nan, 10, '', 'n/a', '0', '10']}
        df1 = DataFrame(data)
        self.assertEqual(len(list(df1)), 2, "Dataframe has 2 columns initially")
        add_columns(df1, ["Address", "Age", "State"], value='n/a')
        self.assertEqual(len(list(df1)), 4, "Dataframe has 4 columns after adding")

    def test_check_match(self):
        data1 = {'Name': ['n/a', '', 'tom', 'alice', 0, 1],
                 'Age': [np.nan, 10, '', 'n/a', '0', '10']}
        data2 = {'Blame': ['n/a', '', 'tom', 'alice', 0, 1],
                 'Rage': [np.nan, 10, '', 'n/a', '0', '10']}
        df1 = DataFrame(data1)
        df2 = DataFrame(data2)
        errors = check_match(df1['Name'], df2['Blame'])
        self.assertFalse(errors, "There should not be errors if the items are compared as strings")
        errors = check_match(df1['Age'], df2['Rage'], numeric=True)
        self.assertFalse(errors, "There should not be errors if the items are compared as strings")
        data3 = {'Blame': ['n/a', '', 'tom', 'alice', 0, 1],
                 'Rage': [np.nan, 10, '', '1', '0', 30]}
        df3 = DataFrame(data3)
        errors = check_match(df1['Age'], df3['Rage'], numeric=True)
        self.assertTrue(errors, "There should be errors")

    def test_delete_columns(self):
        df = get_new_dataframe(self.stern_map_path)
        col_list = ['banana', 'event_type', 'letter', 'apple', 'orange']
        self.assertEqual(len(list(df)), 4, "stern_map should have 4 columns before deletion")
        delete_columns(df, col_list)
        self.assertEqual(len(list(df)), 2, "stern_map should have 2 columns after deletion")

    def test_delete_rows_by_column(self):
        data = {'Name': ['n/a', '', 'tom', 'alice', 0, 1],
                'Age': [np.nan, 10, '', 'n/a', '0', '10']}
        df1 = DataFrame(data)
        self.assertEqual(len(df1.index), 6, "The data frame should have 6 rows to start")
        delete_rows_by_column(df1, '')
        self.assertEqual(len(df1.index), 4, "The data frame should have 4 rows after deletion")

    def test_get_new_dataframe(self):
        df_new = get_new_dataframe(self.stern_map_path)
        self.assertIsInstance(df_new, DataFrame)
        self.assertEqual(len(df_new), 87, "get_new_dataframe should return correct number of rows")
        self.assertEqual(len(df_new.columns), 4, "get_new_dataframe should return correct number of rows")
        df_new1 = get_new_dataframe(self.stern_map_path)
        self.assertIsInstance(df_new1, DataFrame)
        self.assertEqual(len(df_new1), 87, "get_new_dataframe should return correct number of rows")
        self.assertEqual(len(df_new1.columns), 4, "get_new_dataframe should return correct number of rows")
        df_new.loc[0, 'type'] = 'Pear'
        self.assertNotEqual(df_new.iloc[0]['type'], df_new1.iloc[0]['type'],
                            "get_new_dataframe returns a new dataframe")

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
        stern_df = get_new_dataframe(self.stern_map_path)
        key_columns = ['type', 'event_type']
        my_map = {}
        for index, row in stern_df.iterrows():
            key = get_row_hash(row, key_columns)
            my_map[key] = index
        self.assertEqual(len(my_map.keys()), len(stern_df),
                         "get_row_hash should uniquely hash all of the keys in stern map")

    def test_get_value_dict(self):
        conv_dict = get_value_dict(self.sampling_rate_path)
        self.assertIsInstance(conv_dict, dict, "get_value_dict should return a dictionary")
        self.assertEqual(17, len(conv_dict), "get_value_dict should return a dictionary of the correct length")

    def test_make_info_dataframe(self):
        col_dict = {"a": {"b": 10, "c": 13, "d": 4}, "e": {"n/a": 10000}}
        df1 = make_info_dataframe(col_dict, "a")
        self.assertIsInstance(df1, DataFrame, "make_info_dataframe should create a dataframe if column in col_dict")
        self.assertEqual(len(df1), 3, "make_info_dataframe should the right number of rows.")
        df2 = make_info_dataframe(col_dict, "Baloney")
        self.assertFalse(df2, "make_frame should return None if column name invalid")

    def test_replace_na(self):
        # With categorical column containing n/a's
        df = DataFrame({
            'A': Categorical(['apple', 'n/a', 'cherry']),
            'B': ['n/a', 'pear', 'banana']
        })
        replace_na(df)
        self.assertTrue(df['A'].isnull().any())
        self.assertTrue(df['B'].isnull().any())

        # With categorical column not containing n/a's
        df = DataFrame({
            'A': Categorical(['apple', 'orange', 'cherry']),
            'B': ['pear', 'melon', 'banana']
        })
        replace_na(df)
        self.assertFalse(df['A'].isnull().any())
        self.assertFalse(df['B'].isnull().any())

        # preserving other values
        df = DataFrame({
            'A': Categorical(['apple', 'n/a', 'cherry']),
            'B': ['n/a', 'pear', 'banana'],
            'C': [1, 2, 3]
        })
        replace_na(df)
        self.assertEqual(list(df['C']), [1, 2, 3])

        # Non-categorical n/a replacement
        df = DataFrame({
            'A': ['apple', 'n/a', 'cherry'],
            'B': ['n/a', 'pear', 'banana']
        })
        replace_na(df)
        self.assertTrue(df['A'].isnull().any())
        self.assertTrue(df['B'].isnull().any())

    def test_replace_values(self):
        data = {'Name': ['n/a', '', 'tom', 'alice', 0, 1],
                'Age': [np.nan, 10, '', 'n/a', '0', '10']}
        df1 = DataFrame(data)
        self.assertFalse(df1.loc[1, 'Name'], "replace_values before replacement value is empty")
        num_replaced1 = replace_values(df1, values=['', 0])
        self.assertEqual(df1.loc[1, 'Name'], 'n/a', "replace_values should replace the empty string with n/a")
        self.assertEqual(4, num_replaced1, "replace_values should replace the correct number of values")
        df2 = DataFrame(data)
        num_replaced2 = replace_values(df2, replace_value='Baloney', column_list=['Name'])
        self.assertEqual(df2.loc[1, 'Name'], 'Baloney',
                         "replace_values should replace the empty string with specified value in correct columns")
        self.assertEqual(1, num_replaced2,
                         "replace_values should replace the correct number of values when columns are specified")

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
        with self.assertRaises(HedFileError) as context:
            reorder_columns(self.stern_map_path, ['event_type', 'type', 'baloney'], skip_missing=False)
        self.assertEqual(context.exception.args[0], 'MissingKeys')

    def test_separate_columns(self):
        base_cols = ['a', 'b', 'c', 'd']
        present, missing = separate_values(base_cols, [])
        self.assertFalse(present, "separate_values should have empty present when no target columns")
        self.assertFalse(missing, "separate_values should have empty missing when no target columns")
        present, missing = separate_values(base_cols, ['b', 'd'])
        self.assertEqual(len(present), len(['b', 'd']),
                         "separate_values should have target columns present when target columns subset of base")
        self.assertFalse(missing, "separate_values should no missing columns when target columns subset of base")
        present, missing = separate_values(base_cols, base_cols)
        self.assertEqual(len(present), len(base_cols),
                         "separate_values should have target columns present when target columns equals base")
        self.assertFalse(missing, "separate_values should no missing columns when target columns equals base")
        present, missing = separate_values(base_cols, ['g', 'h'])
        self.assertFalse(present, "separate_values should have empty present when target columns do not overlap base")
        self.assertEqual(len(missing), 2, "separate_values should have all target columns missing")


if __name__ == '__main__':
    unittest.main()
