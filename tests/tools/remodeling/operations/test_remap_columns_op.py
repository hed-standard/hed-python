import json
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.remap_columns_op import RemapColumnsOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                           [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                           [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                           [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                           [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        cls.sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                              'response_accuracy', 'response_hand', 'sex']

        base_parameters = {
                "source_columns": ["response_accuracy", "response_hand"],
                "destination_columns": ["response_type"],
                "map_list": [["correct", "left", "correct_left"],
                             ["correct", "right", "correct_right"],
                             ["incorrect", "left", "incorrect_left"],
                             ["incorrect", "right", "incorrect_left"],
                             ["n/a", "n/a", "n/a"]],
                "ignore_missing": True
            }
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=None)

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, self.dispatch.prep_events(df), 'run-01')
        return df, self.dispatch.post_prep_events(df_new)

    def test_valid(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        op = RemapColumnsOp(parms)
        df, df_test = self.get_dfs(op)
        self.assertNotIn("response_type", df.columns, "remap_columns before does not have response_type column")
        self.assertIn("response_type", df_test.columns, "remap_columns after has response_type column")

    def test_invalid_params(self):
        parms1 = json.loads(self.json_parms)
        parms1["source_columns"] = []
        with self.assertRaises(ValueError) as context1:
            RemapColumnsOp(parms1)
        self.assertEqual(context1.exception.args[0], "EmptySourceColumns")

        parms2 = json.loads(self.json_parms)
        parms2["destination_columns"] = []
        with self.assertRaises(ValueError) as context2:
            RemapColumnsOp(parms2)
        self.assertEqual(context2.exception.args[0], "EmptyDestinationColumns")

        parms3 = json.loads(self.json_parms)
        parms3["map_list"][1] = ["right", "correct_right"],
        with self.assertRaises(ValueError) as context3:
            RemapColumnsOp(parms3)
        self.assertEqual(context3.exception.args[0], "BadColumnMapEntry")

    def test_valid_missing(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        before_len = len(parms["map_list"])
        parms["map_list"] = parms["map_list"][:-1]
        after_len = len(parms["map_list"])
        self.assertEqual(after_len + 1, before_len)
        op = RemapColumnsOp(parms)
        df, df_test = self.get_dfs(op)
        self.assertNotIn("response_type", df.columns, "remap_columns before does not have response_type column")
        self.assertIn("response_type", df_test.columns, "remap_columns after has response_type column")

    def test_invalid_missing(self):
        # Test when no extras but ignored.
        parms = json.loads(self.json_parms)
        before_len = len(parms["map_list"])
        parms["map_list"] = parms["map_list"][:-1]
        parms["ignore_missing"] = False
        after_len = len(parms["map_list"])
        self.assertEqual(after_len + 1, before_len)
        op = RemapColumnsOp(parms)
        with self.assertRaises(ValueError) as context:
            self.get_dfs(op)
        self.assertEqual(context.exception.args[0], 'MapSourceValueMissing')


if __name__ == '__main__':
    unittest.main()
