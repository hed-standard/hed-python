import json
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.remap_columns_op import RemapColumnsOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [
            [0.0776, 0.5083, 1, "go", "n/a", 0.565, "correct", "right", "female"],
            [5.5774, 0.5083, 2, "unsuccesful_stop", 0.2, 0.49, "correct", "right", "female"],
            [9.5856, 0.5084, "n/a", "go", "n/a", 0.45, "correct", "right", "female"],
            [13.5939, 0.5083, 3, "succesful_stop", 0.2, "n/a", "n/a", "n/a", "female"],
            [17.1021, 0.5083, 4, "unsuccesful_stop", 0.25, 0.633, "correct", "left", "male"],
            [21.6103, 0.5083, 5, "go", "n/a", 0.443, "correct", "left", "male"],
        ]
        cls.sample_columns = [
            "onset",
            "duration",
            "test",
            "trial_type",
            "stop_signal_delay",
            "response_time",
            "response_accuracy",
            "response_hand",
            "sex",
        ]

        base_parameters = {
            "source_columns": ["response_accuracy", "response_hand"],
            "destination_columns": ["response_type"],
            "map_list": [
                ["correct", "left", "correct_left"],
                ["correct", "right", "correct_right"],
                ["incorrect", "left", "incorrect_left"],
                ["incorrect", "right", "incorrect_left"],
                ["n/a", "n/a", "n/a"],
            ],
            "ignore_missing": True,
        }
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=None)

        base_parameters1 = {
            "source_columns": ["test"],
            "destination_columns": ["new_duration", "new_hand"],
            "map_list": [[1, 1, "correct_left"], [2, 2, "correct_right"]],
            "ignore_missing": True,
            "integer_sources": ["test"],
        }
        cls.json_parms1 = json.dumps(base_parameters1)

        base_parameters2 = {
            "source_columns": ["test", "response_accuracy", "response_hand"],
            "destination_columns": ["response_type"],
            "map_list": [
                [1, "correct", "left", "correct_left"],
                [2, "correct", "right", "correct_right"],
                [3, "incorrect", "left", "incorrect_left"],
                [4, "incorrect", "right", "incorrect_left"],
                [5, "n/a", "n/a", "n/a"],
            ],
            "ignore_missing": True,
            "integer_sources": ["test"],
        }
        cls.json_parms2 = json.dumps(base_parameters2)

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op, df=None):
        if df is None:
            df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, self.dispatch.prep_data(df), "run-01")
        return df, self.dispatch.post_proc_data(df_new)

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
        self.assertEqual(context.exception.args[0], "MapSourceValueMissing")

    def test_numeric_keys(self):
        parms = {
            "source_columns": ["duration"],
            "destination_columns": ["new_duration"],
            "map_list": [[0.5083, 0.6], [0.5084, 0.7]],
            "ignore_missing": True,
        }
        op = RemapColumnsOp(parms)
        df, df_test = self.get_dfs(op)
        self.assertNotIn("new_duration", df.columns.values)
        self.assertIn("new_duration", df_test.columns.values)

    def test_numeric_keys_cascade(self):
        # Test when no extras but ignored.
        op_list = [
            {
                "operation": "remap_columns",
                "description": "This is first operation in sequence",
                "parameters": {
                    "source_columns": ["duration"],
                    "destination_columns": ["new_duration"],
                    "map_list": [[5, 6], [3, 2]],
                    "ignore_missing": True,
                    "integer_sources": ["duration"],
                },
            },
            {
                "operation": "remap_columns",
                "description": "This is first operation in sequence",
                "parameters": {
                    "source_columns": ["new_duration"],
                    "destination_columns": ["new_value"],
                    "map_list": [[3, 0.5], [2, 0.4]],
                    "ignore_missing": True,
                    "integer_sources": ["new_duration"],
                },
            },
        ]
        dispatcher = Dispatcher(op_list, data_root=None, backup_name=None, hed_versions=[])

        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_test = dispatcher.run_operations(df, verbose=False, sidecar=None)
        self.assertIn("new_duration", df_test.columns.values)
        self.assertIn("new_value", df_test.columns.values)

    def test_scratch(self):
        pass
        # import os
        # from hed.tools.util.io_util import get_file_list
        # from hed.tools.util.data_util import get_new_dataframe
        # event_path = os.path.realpath('D:/monique/test_events.tsv')
        # save_path = os.path.realpath('D:/monique/output')
        # json_dir = os.path.realpath('D:/monique/json')
        # json_list = get_file_list(json_dir, extensions=['.json'])
        # for json_file in json_list:
        #     event_out = os.path.basename(json_file)
        #     event_out = f"events_{os.path.splitext(event_out)[0]}.tsv"
        #     with open(json_file, 'r') as fp:
        #         op_list = json.load(fp)
        #     df = get_new_dataframe(event_path)
        #     dispatcher = Dispatcher(op_list, data_root=None, backup_name=None, hed_versions=[])
        #     df_test = dispatcher.run_operations(df, verbose=False, sidecar=None)
        #     new_path = os.path.realpath(os.path.join(save_path, event_out))
        #     df_test.to_csv(new_path, sep='\t', index=False, header=True)
        #     break


if __name__ == "__main__":
    unittest.main()
