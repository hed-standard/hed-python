import json
import numpy as np
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.reorder_columns_op import ReorderColumnsOp


class Test(unittest.TestCase):
    """

    TODO:
        - extras, no keep, no ignore
        - no extras, keep, ignore
        - no extras, no keep, ignore
        - no extras, keep, no ignore
        - no extras, no keep, ignore

    """

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
        cls.reordered = [
            [0.0776, 0.5083, 0.565, "go"],
            [5.5774, 0.5083, 0.49, "unsuccesful_stop"],
            [9.5856, 0.5084, 0.45, "go"],
            [13.5939, 0.5083, "n/a", "succesful_stop"],
            [17.1021, 0.5083, 0.633, "unsuccesful_stop"],
            [21.6103, 0.5083, 0.443, "go"],
        ]

        base_parameters = {
            "column_order": ["onset", "duration", "response_time", "trial_type"],
            "ignore_missing": True,
            "keep_others": False,
        }
        cls.reordered_columns = ["onset", "duration", "response_time", "trial_type"]
        cls.reordered_keep_columns = [
            "onset",
            "duration",
            "response_time",
            "trial_type",
            "stop_signal_delay",
            "response_accuracy",
            "response_hand",
            "sex",
        ]
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, self.dispatch.prep_data(df), "run-01")
        return df, self.dispatch.post_proc_data(df_new)

    def test_valid_no_keep_others_ignore_missing(self):
        # Test no extras no keep and ignore missing
        parms = json.loads(self.json_parms)
        op = ReorderColumnsOp(parms)
        df, df_new = self.get_dfs(op)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        self.assertTrue(
            self.reordered_columns == list(df_new.columns),
            "reorder_columns resulting df should have correct columns when no extras, no keep, and ignore",
        )
        self.assertEqual(
            len(df), len(df_new), "reorder_columns should not change the number of events when no extras, no keep, and ignore"
        )
        df_reordered = pd.DataFrame(self.reordered, columns=self.reordered_columns)
        self.assertTrue(
            np.array_equal(df_new.to_numpy(), df_reordered.to_numpy()),
            "reorder_column should have expected values when no extras, no keep, and ignore",
        )

        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns),
            "reorder_columns should not change the input df columns when no extras, no keep, and ignore",
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()),
            "reorder_columns should not change the input df values when no extras, no keep, and ignore",
        )

    def test_valid_extras_no_keep_others_ignore_missing(self):
        # Test when extras, no keep and ignore missing
        parms = json.loads(self.json_parms)
        parms["column_order"] = ["onset", "duration", "response_time", "apples", "trial_type"]
        op = ReorderColumnsOp(parms)
        df, df_new = self.get_dfs(op)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        num_test_rows = len(df1)
        self.assertTrue(
            self.reordered_columns == list(df_new.columns),
            "reorder_columns resulting df should have correct columns when extras, no keep, and ignore",
        )
        self.assertEqual(
            num_test_rows,
            len(df_new),
            "reorder_columns should not change the number of events when extras, no keep, and ignore",
        )
        df_reordered = pd.DataFrame(self.reordered, columns=self.reordered_columns)
        self.assertTrue(
            np.array_equal(df_new.to_numpy(), df_reordered.to_numpy()),
            "reorder_columns should have expected values when extras, no keep, and ignore",
        )

        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns),
            "reorder_columns should not change the input df columns when extras, no keep, and ignore",
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()),
            "reorder_columns should not change the input df values when extras, no keep, and ignore",
        )

    def test_invalid_extras_no_keep_others_no_ignore_missing(self):
        # Test when extras, no keep and no ignore
        parms = json.loads(self.json_parms)
        parms["column_order"] = ["onset", "duration", "response_time", "apples", "trial_type"]
        parms["ignore_missing"] = False
        op = ReorderColumnsOp(parms)
        with self.assertRaises(ValueError) as context:
            self.get_dfs(op)
        self.assertEqual(context.exception.args[0], "MissingReorderedColumns")

    def test_valid_keep_others_ignore_missing(self):
        # Test extras, keep, ignore
        parms = json.loads(self.json_parms)
        parms["column_order"] = ["onset", "duration", "response_time", "apples", "trial_type"]
        parms["keep_others"] = True
        op = ReorderColumnsOp(parms)
        df, df_new = self.get_dfs(op)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        self.assertTrue(
            self.reordered_keep_columns == list(df_new.columns),
            "reorder_columns resulting df should have correct columns when extras, keep, and ignore",
        )
        self.assertEqual(
            len(df), len(df_new), "reorder_columns should not change the number of events when extras, keep, and ignore"
        )

        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns),
            "reorder_columns should not change the input df columns when extras, keep, and ignore",
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()),
            "reorder_columns should not change the input df values when extras, keep, and ignore",
        )


if __name__ == "__main__":
    unittest.main()
