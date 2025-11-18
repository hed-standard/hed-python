import json
import numpy as np
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.remove_columns_op import RemoveColumnsOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [
            [0.0776, 0.5083, "go", "n/a", 0.565, "correct", "right", "female"],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, 0.49, "correct", "right", "female"],
            [9.5856, 0.5084, "go", "n/a", 0.45, "correct", "right", "female"],
            [13.5939, 0.5083, "succesful_stop", 0.2, "n/a", "n/a", "n/a", "female"],
            [17.1021, 0.5083, "unsuccesful_stop", 0.25, 0.633, "correct", "left", "male"],
            [21.6103, 0.5083, "go", "n/a", 0.443, "correct", "left", "male"],
        ]
        cls.sample_columns = [
            "onset",
            "duration",
            "trial_type",
            "stop_signal_delay",
            "response_time",
            "response_accuracy",
            "response_hand",
            "sex",
        ]

        base_parameters = {"column_names": ["stop_signal_delay", "response_accuracy"], "ignore_missing": True}
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, self.dispatch.prep_data(df), "run-01")
        return df, self.dispatch.post_proc_data(df_new)

    def test_valid_no_extras_ignore_missing(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        op = RemoveColumnsOp(parms)
        df, df_new = self.get_dfs(op)
        remaining_columns = ["onset", "duration", "trial_type", "response_time", "response_hand", "sex"]
        self.assertTrue(remaining_columns == list(df_new.columns), "remove_columns resulting df should have correct columns")
        self.assertEqual(
            len(df), len(df_new), "remove_columns should not change the number of events when no extras and ignored"
        )

        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df.columns),
            "remove_columns should not change the input df columns when no extras and ignore missing",
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df.to_numpy()),
            "remove_columns should not change the input df values when no extras and ignore missing",
        )

    def test_valid_extras_ignore_missing(self):
        # Test when extras, but ignored
        parms = json.loads(self.json_parms)
        parms["column_names"].append("face")
        op = RemoveColumnsOp(parms)
        df, df_new = self.get_dfs(op)
        remaining_columns = ["onset", "duration", "trial_type", "response_time", "response_hand", "sex"]
        self.assertTrue(
            remaining_columns == list(df_new.columns),
            "remove_columns resulting df should have correct columns when extras ignored",
        )
        self.assertEqual(len(df), len(df_new), "remove_columns should not change the number of events when extras but ignored")

        # Test that df has not been changed by the op
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        self.assertTrue(
            list(df1.columns) == list(df.columns),
            "remove_columns should not change the input df columns when extras and ignore missing",
        )
        self.assertTrue(
            np.array_equal(df1.to_numpy(), df.to_numpy()),
            "remove_columns should not change the input df values when extras and ignore missing",
        )

    def test_valid_no_extras_no_ignore(self):
        # Test when no extras but not ignored.
        parms = json.loads(self.json_parms)
        parms["ignore_missing"] = False
        op = RemoveColumnsOp(parms)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df, df_new = self.get_dfs(op)
        remaining_columns = ["onset", "duration", "trial_type", "response_time", "response_hand", "sex"]
        self.assertTrue(
            remaining_columns == list(df_new.columns),
            "remove_columns resulting df should have correct columns when no extras but not ignored",
        )
        self.assertEqual(
            len(df), len(df_new), "remove_columns should not change the number of events when no extras but not ignored"
        )

        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns),
            "remove_columns should not change the input df columns when no extras and not ignored",
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()),
            "remove_columns should not change the input df values when no extras and not ignored",
        )

    def test_invalid_extras_no_ignore(self):
        # Test when extras and not ignored.
        parms = json.loads(self.json_parms)
        parms["column_names"].append("face")
        parms["ignore_missing"] = False
        op = RemoveColumnsOp(parms)
        with self.assertRaises(KeyError) as context:
            self.get_dfs(op)
        self.assertEqual(context.exception.args[0], "MissingColumnCannotBeRemoved")


if __name__ == "__main__":
    unittest.main()
