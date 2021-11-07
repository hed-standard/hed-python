import unittest
import os
from unittest import mock
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools.col_dict import ColumnDict
from hed.tools import get_new_dataframe


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

    def test_constructor(self):
        dict1 = ColumnDict()
        self.assertIsInstance(dict1, ColumnDict, "ColumnDict constructor is allowed to have no arguments")
        self.assertFalse(dict1.value_info)

        dict2 = ColumnDict(value_cols=['a', 'b', 'c'], name='baloney')
        self.assertIsInstance(dict2, ColumnDict, "ColumnDict: multiple values are okay in constructor")
        self.assertEqual(len(dict2.value_info.keys()), 3, "ColumnDict should have keys for each value column")

    def test_get_flattened(self):
        t_map = ColumnDict()
        t_map.update(self.stern_map_path)
        df1 = t_map.get_flattened()
        self.assertEqual(len(df1), 137, "Flattening should produce same number of items whether or not value used")
        self.assertEqual(len(df1.columns), 2, "A flattened map should have 2 columns")
        t_map2 = ColumnDict(value_cols=['letter'], skip_cols=['type'])
        t_map2.update(self.stern_map_path)
        df2 = t_map2.get_flattened()
        self.assertGreater(len(df1), len(df2), "Flattening of few columns produces smaller flattened array")
        self.assertEqual(len(df2.columns), 2, "Flattening should produce 2 columns when value and skip columns")

    def test_print(self):
        from io import StringIO
        t_map = ColumnDict()
        t_map.update(self.stern_map_path)
        df = get_new_dataframe(self.stern_map_path)
        t_map.update(self.stern_map_path)
        self.assertEqual(len(t_map.categorical_info.keys()), len(df.columns),
                         "ColumnDict should have all columns as categorical if no value or skip are given")
        with mock.patch('sys.stdout', new=StringIO()):
            t_map.print()
            print("This should be eaten by the StringIO")

    def test_update(self):
        dict1 = ColumnDict()
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        dict1.update(stern_df)
        self.assertEqual(len(dict1.value_info.keys()), 0, "ColumnDict value_info should be empty if no value columns")
        self.assertEqual(len(dict1.categorical_info.keys()), len(stern_df.columns),
                         "ColumnDict categorical_info should have all the columns if no restrictions")

        dict2 = ColumnDict(value_cols=['letter'], skip_cols=['event_type'])
        dict2.update(stern_df)
        self.assertEqual(len(dict2.value_info.keys()), 1, "ColumnDict value_info should have letter value column")
        self.assertEqual(dict2.value_info['letter'], len(stern_df), "ColumnDict value counts should length of column")
        self.assertEqual(len(dict2.skip_cols), 1, "ColumnDict should have one skip column")
        self.assertEqual(len(dict2.categorical_info.keys()), len(stern_df.columns) - 2,
                         "ColumnDict categorical_info should have all the columns except value and skip columns")
        dict2.update(stern_df)
        self.assertEqual(len(dict2.value_info.keys()), 1, "ColumnDict value_info should have letter value column")
        self.assertEqual(dict2.value_info['letter'], 2*len(stern_df),
                         "ColumnDict value counts should update by column length each time update is called")

    def test_update_dict(self):
        dict1 = ColumnDict()
        dict2 = ColumnDict()
        stern_df_map = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        dict1.update(stern_df_map)
        dict2.update_dict(dict1)
        dict2.update_dict(dict1)
        dict1.update(stern_df_map)
        cat_keys = dict1.categorical_info.keys()
        for col in cat_keys:
            self.assertTrue(col in dict2.categorical_info.keys())
            key_dict1 = dict1.categorical_info[col]
            key_dict2 = dict2.categorical_info[col]
            for key, value in key_dict1.items():
                self.assertEqual(value, key_dict2[key], "update_dict should give same values as update")

    def test_update_dict_with_value_cols(self):
        stern_df_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        stern_df_test3 = pd.read_csv(self.stern_test3_path, delimiter='\t', header=0)
        dict1 = ColumnDict(value_cols=['latency'])
        dict1.update(stern_df_test3)
        dict2 = ColumnDict(value_cols=['latency'])
        dict2.update(stern_df_test1)
        dict2.update_dict(dict1)
        dict1.update(stern_df_test1)
        value_keys = dict1.value_info.keys()
        for col in value_keys:
            self.assertEqual(dict1.value_info[col], dict2.value_info[col], "update_dict should update values correctly")

    def test_update_dict_with_bad_value_cols(self):
        stern_df_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        stern_df_test3 = pd.read_csv(self.stern_test3_path, delimiter='\t', header=0)
        dict1 = ColumnDict(value_cols=['latency'])
        dict1.update(stern_df_test3)
        dict3 = ColumnDict()
        dict3.update(stern_df_test1)
        try:
            dict1.update_dict(dict3)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'update_dict threw the wrong exception {ex} when value columns should be categorical')
        else:
            self.fail('update_dict should have thrown a HedFileError when value columns should be categorical')

    def test_update_dict_bad_skip_col(self):
        stern_test3 = pd.read_csv(self.stern_test3_path, delimiter='\t', header=0)
        dict1 = ColumnDict(skip_cols=['latency'])
        dict1.update(stern_test3)
        dict2 = ColumnDict(value_cols=['latency'])
        dict2.update(stern_test3)
        try:
            dict2.update_dict(dict1)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'update_dict threw the wrong exception {ex} when value columns should be categorical')
        else:
            self.fail('update_dict should have thrown a HedFileError when value columns should be categorical')


if __name__ == '__main__':
    unittest.main()
