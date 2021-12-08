import os
import unittest
import numpy as np
from pandas import DataFrame
from hed.tools.data_utils import get_new_dataframe
from hed.tools.event_utils import add_columns, check_match, delete_columns, delete_rows_by_column, \
    replace_values


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

    def test_replace_values(self):
        data = {'Name': ['n/a', '', 'tom', 'alice', 0, 1],
                'Age': [np.nan, 10, '', 'n/a', '0', '10']}
        df1 = DataFrame(data)
        replace_values(df1, values=['', 0])
        self.assertEqual(df1.loc[0, 'Name'], 'n/a', "The empty string should be replaced")


if __name__ == '__main__':
    unittest.main()
