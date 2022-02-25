import unittest
import os
from unittest import mock
import pandas as pd
from hed.errors.exceptions import HedFileError
from hed.tools import ColumnSummary
from hed.util import get_file_list, get_new_dataframe, make_file_dict


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/attention_shift')
        cls.bids_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids/eeg_ds003654s_hed')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")
        cls.wh_events_path = \
            os.path.abspath(os.path.join(cls.bids_base_dir, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))

    def test_constructor(self):
        dict1 = ColumnSummary()
        self.assertIsInstance(dict1, ColumnSummary, "ColumnSummary constructor is allowed to have no arguments")
        self.assertFalse(dict1.value_info)

        dict2 = ColumnSummary(value_cols=['a', 'b', 'c'], name='baloney')
        self.assertIsInstance(dict2, ColumnSummary, "ColumnSummary: multiple values are okay in constructor")
        self.assertEqual(len(dict2.value_info.keys()), 3, "ColumnSummary should have keys for each value column")

    def test_get_number_unique_values(self):
        dict1 = ColumnSummary()
        wh_df = pd.read_csv(self.wh_events_path, delimiter='\t', header=0)
        dict1.update(wh_df)
        self.assertEqual(len(dict1.value_info.keys()), 0, "ColumnSummary value_info should be empty if no value columns")
        self.assertEqual(len(dict1.categorical_info.keys()), len(wh_df.columns),
                         "ColumnSummary categorical_info should have all the columns if no restrictions")
        count_dict = dict1.get_number_unique_values()
        self.assertEqual(len(count_dict), 10, "get_number_unique_values should have the correct number of entries")
        self.assertEqual(count_dict['onset'], 551, "get_number_unique_values should have the right number of unique")

    def test_print(self):
        from io import StringIO
        t_map = ColumnSummary()
        t_map.update(self.stern_map_path)
        df = get_new_dataframe(self.stern_map_path)
        t_map.update(self.stern_map_path)
        self.assertEqual(len(t_map.categorical_info.keys()), len(df.columns),
                         "ColumnSummary should have all columns as categorical if no value or skip are given")
        with mock.patch('sys.stdout', new=StringIO()):
            t_map.print()
            print("This should be eaten by the StringIO")

    def test_update(self):
        dict1 = ColumnSummary()
        stern_df = pd.read_csv(self.stern_map_path, delimiter='\t', header=0)
        dict1.update(stern_df)
        self.assertEqual(len(dict1.value_info.keys()), 0, "ColumnSummary value_info should be empty if no value columns")
        self.assertEqual(len(dict1.categorical_info.keys()), len(stern_df.columns),
                         "ColumnSummary categorical_info should have all the columns if no restrictions")

        dict2 = ColumnSummary(value_cols=['letter'], skip_cols=['event_type'])
        dict2.update(stern_df)
        self.assertEqual(len(dict2.value_info.keys()), 1, "ColumnSummary value_info should have letter value column")
        self.assertEqual(dict2.value_info['letter'], len(stern_df), "ColumnSummary value counts should length of column")
        self.assertEqual(len(dict2.skip_cols), 1, "ColumnSummary should have one skip column")
        self.assertEqual(len(dict2.categorical_info.keys()), len(stern_df.columns) - 2,
                         "ColumnSummary categorical_info should have all the columns except value and skip columns")
        dict2.update(stern_df)
        self.assertEqual(len(dict2.value_info.keys()), 1, "ColumnSummary value_info should have letter value column")
        self.assertEqual(dict2.value_info['letter'], 2*len(stern_df),
                         "ColumnSummary value counts should update by column length each time update is called")

    def test_update_dict(self):
        dict1 = ColumnSummary()
        dict2 = ColumnSummary()
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
        dict1 = ColumnSummary(value_cols=['latency'])
        dict1.update(stern_df_test3)
        dict2 = ColumnSummary(value_cols=['latency'])
        dict2.update(stern_df_test1)
        dict2.update_dict(dict1)
        dict1.update(stern_df_test1)
        value_keys = dict1.value_info.keys()
        for col in value_keys:
            self.assertEqual(dict1.value_info[col], dict2.value_info[col], "update_dict should update values correctly")

    def test_update_dict_with_bad_value_cols(self):
        stern_df_test1 = pd.read_csv(self.stern_test1_path, delimiter='\t', header=0)
        stern_df_test3 = pd.read_csv(self.stern_test3_path, delimiter='\t', header=0)
        dict1 = ColumnSummary(value_cols=['latency'])
        dict1.update(stern_df_test3)
        dict3 = ColumnSummary()
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
        dict1 = ColumnSummary(skip_cols=['latency'])
        dict1.update(stern_test3)
        dict2 = ColumnSummary(value_cols=['latency'])
        dict2.update(stern_test3)
        try:
            dict2.update_dict(dict1)
        except HedFileError:
            pass
        except Exception as ex:
            self.fail(f'update_dict threw the wrong exception {ex} when value columns should be categorical')
        else:
            self.fail('update_dict should have thrown a HedFileError when value columns should be categorical')

    def test_make_combined_dicts(self):
        files_bids = get_file_list(self.bids_base_dir, extensions=[".tsv"], name_suffix="_events")
        file_dict = make_file_dict(files_bids)
        dicts_all1, dicts1 = ColumnSummary.make_combined_dicts(file_dict)
        self.assertTrue(isinstance(dicts_all1, ColumnSummary), "make_combined_dicts should return a ColumnSummary")
        self.assertTrue(isinstance(dicts1, dict), "make_combined_dicts should also return a dictionary of file names")
        self.assertEqual(6, len(dicts1), "make_combined_dicts should return correct number of file names")
        self.assertEqual(10, len(dicts_all1.categorical_info),
                         "make_combined_dicts should return right number of entries")
        dicts_all2, dicts2 = ColumnSummary.make_combined_dicts(file_dict, skip_cols=["onset", "duration", "sample"])
        self.assertTrue(isinstance(dicts_all2, ColumnSummary), "make_combined_dicts should return a ColumnSummary")
        self.assertTrue(isinstance(dicts2, dict), "make_combined_dicts should also return a dictionary of file names")
        self.assertEqual( 6, len(dicts2), "make_combined_dicts should return correct number of file names")
        self.assertEqual(len(dicts_all2.categorical_info), 7,
                         "make_combined_dicts should return right number of entries")


if __name__ == '__main__':
    unittest.main()
