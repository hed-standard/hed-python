import json
import math
import numpy as np
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.merge_consecutive_op import MergeConsecutiveOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [[0.0776, 0.5083, 'go', 'n/a', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 'right', 'female'],
                           [9.5856, 0.5083, 'go', 'n/a', 'right', 'female'],
                           [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'female'],
                           [14.2, 0.5083, 'succesful_stop', 0.2,  'n/a', 'female'],
                           [15.3, 0.7083, 'succesful_stop', 0.2,  'n/a', 'female'],
                           [17.3, 0.5083, 'succesful_stop', 0.25,  'n/a', 'female'],
                           [19.0, 0.5083, 'succesful_stop', 0.25, 'n/a', 'female'],
                           [21.1021, 0.5083, 'unsuccesful_stop', 0.25, 'left', 'male'],
                           [22.6103, 0.5083, 'go', 'n/a', 'left', 'male']]
        cls.sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay',  'response_hand', 'sex']

        cls.result_data = [[0.0776, 0.5083, 'go', 'n/a', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 'right', 'female'],
                           [9.5856, 0.5083, 'go', 'n/a', 'right', 'female'],
                           [13.5939, 2.4144, 'succesful_stop', 0.2, 'n/a', 'female'],
                           [17.3, 2.2083, 'succesful_stop', 0.25,  'n/a', 'female'],
                           [21.1021, 0.5083, 'unsuccesful_stop', 0.25, 'left', 'male'],
                           [22.6103, 0.5083, 'go', 'n/a', 'left', 'male']]

        base_parameters = {
                "column_name": "trial_type",
                "event_code": "succesful_stop",
                "match_columns": ['stop_signal_delay', 'response_hand', 'sex'],
                "set_durations": True,
                "ignore_missing": True
            }
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_valid(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        op = MergeConsecutiveOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df = df.replace('n/a', np.NaN)
        df_test = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_test = df_test.replace('n/a', np.NaN)
        df_new = op.do_op(self.dispatch, df_test, 'sample_data')
        self.assertTrue(list(df_new.columns) == list(df.columns),
                        "merge_consecutive should not change the number of columns")
        df_results = pd.DataFrame(self.result_data, columns=self.sample_columns)
        df_results = df_results.replace('n/a', np.NaN)
        self.assertTrue(list(df_new.columns) == list(df_results.columns),
                        "merge_consecutive should has correct number of columns after merge")
        for index, row in df_new.iterrows():
            if not math.isclose(df_new.loc[index, "onset"], df_results.loc[index, "onset"]):
                self.fail(f"merge_consecutive result has wrong onset at {index}: {df_new.loc[index, 'onset']} " +
                          "instead of{df_results.loc[index, 'onset']}")
            if not math.isclose(df_new.loc[index, "duration"], df_results.loc[index, "duration"]):
                self.fail(f"merge_consecutive result has wrong duration at {index}: {df_new.loc[index, 'duration']} " +
                          f"instead of {df_results.loc[index, 'duration']}")

        # Test that df has not been changed by the op
        self.assertTrue(list(df.columns) == list(df_test.columns),
                        "merge_consecutive should not change the input df columns when no extras and not ignored")
        for index, row in df.iterrows():
            if not math.isclose(df.loc[index, "onset"], df_test.loc[index, "onset"]):
                self.fail(f"merge_consecutive should not change onset after op, but onset does not agree at" +
                          f"at {index}: {df.loc[index, 'onset']} instead of {df_test.loc[index, 'onset']}")
            if not math.isclose(df.loc[index, "duration"], df_test.loc[index, "duration"]):
                self.fail(f"merge_consecutive should not change duration after op, but duration does not agree at" +
                          f"at {index}: {df.loc[index, 'duration']} instead of {df_test.loc[index, 'duration']}")

    def test_get_remove_groups(self):
        match_df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        match_df = match_df.replace('n/a', np.NaN)
        match_df1 = match_df.loc[:, ['duration', 'stop_signal_delay',  'response_hand', 'sex']]
        code_mask1 = pd.Series([False, False, False, True, True, True, True, True, False, False])
        remove_groups1 = MergeConsecutiveOp._get_remove_groups(match_df1, code_mask1)
        self.assertEqual(max(remove_groups1), 3, "_get_remove_groups has three groups when duration is included")
        self.assertEqual(remove_groups1[4], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups1[7], 3, "_get_remove_groups has correct second group")
        match_df2 = match_df.loc[:, ['stop_signal_delay', 'response_hand', 'sex']]
        remove_groups2 = MergeConsecutiveOp._get_remove_groups(match_df2, code_mask1)
        self.assertEqual(max(remove_groups2), 2, "_get_remove_groups has 2 groups when duration not included")
        self.assertEqual(remove_groups2[4], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups2[5], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups2[7], 2, "_get_remove_groups has correct second group")
        match_df3 = match_df.loc[:, ['trial_type']]
        remove_groups3 = MergeConsecutiveOp._get_remove_groups(match_df3, code_mask1)
        self.assertEqual(max(remove_groups3), 1, "_get_remove_groups has 2 groups when duration not included")
        self.assertEqual(remove_groups3[4], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups3[5], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups3[7], 1, "_get_remove_groups has correct second group")

    # def test_valid_missing(self):
    #     # Test when no extras but ignored.
    #     parms = json.loads(self.json_parms)
    #     before_len = len(parms["map_list"])
    #     parms["map_list"] = parms["map_list"][:-1]
    #     after_len = len(parms["map_list"])
    #     self.assertEqual(after_len + 1, before_len)
    #     op = RemapColumnsOp(parms)
    #     df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
    #     df_test = pd.DataFrame(self.sample_data, columns=self.sample_columns)
    #     df_new = op.do_op(df_test)
    #     self.assertNotIn("response_type", df.columns, "remap_columns before does not have response_type column")
    #     self.assertIn("response_type", df_new.columns, "remap_columns after has response_type column")
    #
    # def test_invalid_missing(self):
    #     # Test when no extras but ignored.
    #     parms = json.loads(self.json_parms)
    #     before_len = len(parms["map_list"])
    #     parms["map_list"] = parms["map_list"][:-1]
    #     parms["ignore_missing"] = False
    #     after_len = len(parms["map_list"])
    #     self.assertEqual(after_len + 1, before_len)
    #     op = RemapColumnsOp(parms)
    #     df_test = pd.DataFrame(self.sample_data, columns=self.sample_columns)
    #     with self.assertRaises(ValueError):
    #         df_new = op.do_op(df_test)


if __name__ == '__main__':
    unittest.main()
