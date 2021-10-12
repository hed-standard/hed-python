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
        cls.att_sub_001 = os.path.join(att_base_dir, "sub-001_run-01_events.tsv")
        cls.att_sub_001_temp = os.path.join(att_base_dir, "sub-001_run-01_events_temp.tsv")

    def test_base (self):
        df_eeg = get_new_dataframe(self.att_sub_001_temp)
        df_eeg.drop(['sample_offset', 'latency', 'urevent', 'usertags'], axis=1, inplace=True)
        df_eeg['new_col'] = df_eeg['cond_code'].map(str) + df_eeg['event_code'].map(str)
        trial_col = df_eeg['cond_code'].map(str) != '0'

        comp_col = df_eeg['new_col'].map(str) != df_eeg["type"].map(str)
        x = comp_col & trial_col
        y = sum(comp_col & trial_col)
        for index, value in x.iteritems():
            if value:
                row = df_eeg.loc[index]
                print(f"{index}: event_code:{row['event_code']} type:{row['type']} cond_code:{row['cond_code']}")
        z = sum(trial_col)
        print("To here")


if __name__ == '__main__':
    unittest.main()
