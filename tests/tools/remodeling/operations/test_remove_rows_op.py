import json
import numpy as np
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.remove_rows_op import RemoveRowsOp


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

        cls.result_data = [
            [0.0776, 0.5083, "go", "n/a", 0.565, "correct", "right", "female"],
            [9.5856, 0.5084, "go", "n/a", 0.45, "correct", "right", "female"],
            [21.6103, 0.5083, "go", "n/a", 0.443, "correct", "left", "male"],
        ]

        base_parameters = {"column_name": "trial_type", "remove_values": ["succesful_stop", "unsuccesful_stop"]}
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, self.dispatch.prep_data(df), "run-01")
        return df, self.dispatch.post_proc_data(df_new)

    def test_valid(self):
        # Test when errors.
        parms = json.loads(self.json_parms)
        op = RemoveRowsOp(parms)
        df, df_new = self.get_dfs(op)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        self.assertTrue(
            list(df.columns) == list(df_new.columns), "remove_rows does not change the number of columns when all valid"
        )
        df_result = pd.DataFrame(self.result_data, columns=self.sample_columns)
        self.assertTrue(
            np.array_equal(df_result.to_numpy(), df_new.to_numpy()), "remove_rows should have the right values after removal"
        )
        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns), "remove_rows should not change the input df columns when all valid"
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()), "remove_rows should not change the input df values when all valid"
        )

    def test_bad_values(self):
        # Test when bad values included
        parms = json.loads(self.json_parms)
        parms["remove_values"] = ["succesful_stop", "unsuccesful_stop", "baloney"]
        op = RemoveRowsOp(parms)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df, df_new = self.get_dfs(op)
        self.assertTrue(
            list(df.columns) == list(df_new.columns),
            "remove_rows does not change the number of columns when bad values included",
        )
        df_result = pd.DataFrame(self.result_data, columns=self.sample_columns)
        self.assertTrue(
            np.array_equal(df_result.to_numpy(), df_new.to_numpy()),
            "remove_rows should have the right values after removal when bad values",
        )
        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns), "remove_rows should not change the input df columns when bad values"
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()), "remove_rows should not change the input df values when bad values"
        )

    def test_bad_column_name(self):
        # A bad column name should result in no change to df.
        parms = json.loads(self.json_parms)
        parms["column_name"] = "baloney"
        op = RemoveRowsOp(parms)
        df, df_new = self.get_dfs(op)
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        self.assertTrue(
            list(df.columns) == list(df_new.columns), "remove_rows does not change the number of columns when bad column"
        )

        self.assertTrue(
            np.array_equal(df.to_numpy(), df_new.to_numpy()),
            "remove_rows should have the right values after removal when bad column",
        )
        # Test that df has not been changed by the op
        self.assertTrue(
            list(df.columns) == list(df1.columns), "remove_rows should not change the input df columns when bad column"
        )
        self.assertTrue(
            np.array_equal(df.to_numpy(), df1.to_numpy()), "remove_rows should not change the input df values when bad column"
        )


if __name__ == "__main__":
    unittest.main()
