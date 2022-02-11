import os
import json
import unittest
from pandas import DataFrame
from hed.tools import df_to_hed, hed_to_df, merge_hed_dict


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        json_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                 '../data/bids/eeg_ds003654s_hed/task-FacePerception_events.json'))
        cls.sidecar1 = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                        "b": {"HED": "Purple"}}
        cls.sidecar2 = {"a": {"c": {"c1": "blech3", "c2": "blech3a"}, "d": "blech4", "e": "blech5"},
                        "b": {"HED": {"b2": "Purple", "b3": "Red"}}}
        with open(json_path) as fp:
            cls.sidecar3 = json.load(fp)

    def test_hed_to_def(self):
        df1 = hed_to_df(self.sidecar1, col_names=None)
        self.assertIsInstance(df1, DataFrame)
        self.assertEqual(len(df1), 1)
        df1a = hed_to_df(self.sidecar1, col_names=["a"])
        self.assertIsInstance(df1a, DataFrame)
        self.assertEqual(len(df1a), 0)
        df2 = hed_to_df(self.sidecar2)
        self.assertIsInstance(df2, DataFrame)
        self.assertEqual(len(df2), 2)
        print("To here1")

    def test_df_to_hed(self):
        df1 = hed_to_df(self.sidecar1, col_names=None)
        hed1 = df_to_hed(df1)
        self.assertIsInstance(hed1, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed1), 1, "df_to_hed ")
        df2 = hed_to_df(self.sidecar2, col_names=None)
        hed2 = df_to_hed(df2)
        self.assertIsInstance(hed2, dict, "df_to_hed should produce a dictionary")
        self.assertEqual(len(hed2), 1, "df_to_hed ")
        print("To here")

    def test_merge_hed_dict(self):
        df1 = hed_to_df(self.sidecar1, col_names=None)
        hed1 = df_to_hed(df1)
        self.assertEqual(len(self.sidecar1), 2, "merge_hed_dict should have the right length before merge")
        merge_hed_dict(self.sidecar1, hed1)
        self.assertEqual(len(self.sidecar1), 2, "merge_hed_dict should have the right length after merge")
        print("Here3")


if __name__ == '__main__':
    unittest.main()
