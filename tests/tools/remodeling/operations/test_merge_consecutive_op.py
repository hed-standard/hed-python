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
        cls.sample_data = [
            [0.0776, 0.5083, "go", "n/a", "right", "female"],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, "right", "female"],
            [9.5856, 0.5083, "go", "n/a", "right", "female"],
            [13.5939, 0.5083, "succesful_stop", 0.2, "n/a", "female"],
            [14.2, 0.5083, "succesful_stop", 0.2, "n/a", "female"],
            [15.3, 0.7083, "succesful_stop", 0.2, "n/a", "female"],
            [17.3, 0.5083, "succesful_stop", 0.25, "n/a", "female"],
            [19.0, 0.5083, "succesful_stop", 0.25, "n/a", "female"],
            [21.1021, 0.5083, "unsuccesful_stop", 0.25, "left", "male"],
            [22.6103, 0.5083, "go", "n/a", "left", "male"],
        ]
        cls.sample_columns = ["onset", "duration", "trial_type", "stop_signal_delay", "response_hand", "sex"]

        cls.result_data = [
            [0.0776, 0.5083, "go", "n/a", "right", "female"],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, "right", "female"],
            [9.5856, 0.5083, "go", "n/a", "right", "female"],
            [13.5939, 2.4144, "succesful_stop", 0.2, "n/a", "female"],
            [17.3, 2.2083, "succesful_stop", 0.25, "n/a", "female"],
            [21.1021, 0.5083, "unsuccesful_stop", 0.25, "left", "male"],
            [22.6103, 0.5083, "go", "n/a", "left", "male"],
        ]

        base_parameters = {
            "column_name": "trial_type",
            "event_code": "succesful_stop",
            "match_columns": ["stop_signal_delay", "response_hand", "sex"],
            "set_durations": True,
            "ignore_missing": True,
        }
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, self.dispatch.prep_data(df), "run-01")
        return df, self.dispatch.post_proc_data(df_new)

    def test_do_op_valid(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        op = MergeConsecutiveOp(parms)
        df_test, df_new = self.get_dfs(op)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        self.assertTrue(list(df_new.columns) == list(df.columns), "merge_consecutive should not change the number of columns")
        for index, _row in df_new.iterrows():
            if not math.isclose(df_new.loc[index, "onset"], df_new.loc[index, "onset"]):
                self.fail(
                    f"merge_consecutive result has wrong onset at {index}: {df_new.loc[index, 'onset']} "
                    + "instead of{df_results.loc[index, 'onset']}"
                )
            if not math.isclose(df_new.loc[index, "duration"], df_new.loc[index, "duration"]):
                self.fail(
                    f"merge_consecutive result has wrong duration at {index}: {df_new.loc[index, 'duration']} "
                    + f"instead of {df_new.loc[index, 'duration']}"
                )

        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df_test.columns),
            "merge_consecutive should not change the input df columns when no extras and not ignored",
        )
        for index, _row in df.iterrows():
            if not math.isclose(df.loc[index, "onset"], df_test.loc[index, "onset"]):
                self.fail(
                    "merge_consecutive should not change onset after op, but onset does not agree at"
                    + f"at {index}: {df.loc[index, 'onset']} instead of {df_test.loc[index, 'onset']}"
                )
            if not math.isclose(df.loc[index, "duration"], df_test.loc[index, "duration"]):
                self.fail(
                    "merge_consecutive should not change duration after op, but duration does not agree at"
                    + f"at {index}: {df.loc[index, 'duration']} instead of {df_test.loc[index, 'duration']}"
                )

    def test_do_op_no_set_durations(self):
        # Test when no set duration.
        parms1 = json.loads(self.json_parms)
        parms1["set_durations"] = False
        op1 = MergeConsecutiveOp(parms1)
        df_test, df_new1 = self.get_dfs(op1)
        parms2 = json.loads(self.json_parms)
        parms2["set_durations"] = True
        op2 = MergeConsecutiveOp(parms2)
        df_test2, df_new2 = self.get_dfs(op2)
        self.assertTrue(list(df_new1.columns) == list(df_new2.columns))
        code_mask = df_new1["duration"] != df_new2["duration"]
        self.assertEqual(sum(code_mask.astype(int)), 2)

    def test_do_op_valid_no_change(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        parms["event_code"] = "baloney"
        op = MergeConsecutiveOp(parms)
        df, df_new = self.get_dfs(op)
        self.assertEqual(len(df), len(df_new))

    def test_get_remove_groups(self):
        match_df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        match_df = match_df.replace("n/a", np.nan)
        match_df1 = match_df.loc[:, ["duration", "stop_signal_delay", "response_hand", "sex"]]
        code_mask1 = pd.Series([False, False, False, True, True, True, True, True, False, False])
        remove_groups1 = MergeConsecutiveOp._get_remove_groups(match_df1, code_mask1)
        self.assertEqual(max(remove_groups1), 3, "_get_remove_groups has three groups when duration is included")
        self.assertEqual(remove_groups1[4], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups1[7], 3, "_get_remove_groups has correct second group")
        match_df2 = match_df.loc[:, ["stop_signal_delay", "response_hand", "sex"]]
        remove_groups2 = MergeConsecutiveOp._get_remove_groups(match_df2, code_mask1)
        self.assertEqual(max(remove_groups2), 2, "_get_remove_groups has 2 groups when duration not included")
        self.assertEqual(remove_groups2[4], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups2[5], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups2[7], 2, "_get_remove_groups has correct second group")
        match_df3 = match_df.loc[:, ["trial_type"]]
        remove_groups3 = MergeConsecutiveOp._get_remove_groups(match_df3, code_mask1)
        self.assertEqual(max(remove_groups3), 1, "_get_remove_groups has 2 groups when duration not included")
        self.assertEqual(remove_groups3[4], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups3[5], 1, "_get_remove_groups has correct first group")
        self.assertEqual(remove_groups3[7], 1, "_get_remove_groups has correct second group")

    def test_invalid_missing_column(self):
        parms = json.loads(self.json_parms)
        parms["column_name"] = "baloney"
        parms["ignore_missing"] = False
        op = MergeConsecutiveOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df = df.replace("n/a", np.nan)
        with self.assertRaises(ValueError) as context:
            op.do_op(self.dispatch, df, "sample_data")
        self.assertEqual(context.exception.args[0], "ColumnMissing")

    def test_do_op_missing_onset(self):
        parms = json.loads(self.json_parms)
        parms["ignore_missing"] = False
        op = MergeConsecutiveOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df = df.replace("n/a", np.nan)
        df_new = df.drop("onset", axis=1)
        self.assertEqual(len(df.columns), len(df_new.columns) + 1)
        with self.assertRaises(ValueError) as context:
            op.do_op(self.dispatch, df_new, "sample_data")
        self.assertEqual(context.exception.args[0], "MissingOnsetColumn")

    def test_do_op_missing_duration(self):
        parms = json.loads(self.json_parms)
        parms["set_durations"] = True
        op = MergeConsecutiveOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df = df.replace("n/a", np.nan)
        df_new = df.drop("duration", axis=1)
        self.assertEqual(len(df.columns), len(df_new.columns) + 1)
        with self.assertRaises(ValueError) as context:
            op.do_op(self.dispatch, df_new, "sample_data")
        self.assertEqual(context.exception.args[0], "MissingDurationColumn")

    def test_do_op_missing_match(self):
        parms = json.loads(self.json_parms)
        parms["match_columns"] = ["stop_signal_delay", "response_hand", "sex", "baloney"]
        parms["ignore_missing"] = False
        op = MergeConsecutiveOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df = df.replace("n/a", np.nan)
        with self.assertRaises(ValueError) as context:
            op.do_op(self.dispatch, df, "sample_data")
        self.assertEqual(context.exception.args[0], "MissingMatchColumns")


if __name__ == "__main__":
    unittest.main()
