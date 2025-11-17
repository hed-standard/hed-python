import json
import os
import pandas as pd
import unittest

# from hed.tools.analysis.column_name_summary import ColumnNameSummary
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_column_names_op import SummarizeColumnNamesOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data"))
        cls.sample_columns1 = ["onset", "duration", "trial_type", "stop_signal_delay", "response_time"]
        cls.sample_columns2 = ["trial_type", "onset", "duration", "stop_signal_delay", "response_time"]
        cls.data1 = [[3.0, 0.5, "go", 0.2, 1.3], [5.0, 0.5, "go", 0.2, 1.3]]
        base_parameters = {"summary_name": "columns", "summary_filename": "column_name_summary"}
        cls.json_parms = json.dumps(base_parameters)

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
        cls.events_path = os.path.realpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_excerpt_events.tsv"
            )
        )
        cls.sidecar_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_events.json")
        )
        cls.model_path = os.path.realpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_summary_all_rmdl.json"
            )
        )
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op, name, dispatch):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(dispatch, dispatch.prep_data(df), name)
        return df, dispatch.post_proc_data(df_new)

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnNamesOp(parms)
        self.assertIsInstance(sum_op, SummarizeColumnNamesOp, "constructor creates an object of the correct type")

    def test_summary_op(self):
        with open(self.model_path, "r") as fp:
            parms = json.load(fp)
        parsed_commands = Dispatcher.parse_operations(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        df = dispatch.get_data_file(self.events_path)
        df = dispatch.prep_data(df)

        old_len = len(df)
        sum_op = parsed_commands[0]
        df = sum_op.do_op(dispatch, df, "run-02")
        df = sum_op.do_op(dispatch, df, "run-01")
        self.assertEqual(len(df), old_len)
        df1 = df.drop(labels="onset", axis=1)
        sum_op.do_op(dispatch, df1, "run-03")
        this_context = dispatch.summary_dicts[sum_op.summary_name]
        for _key, item in this_context.summary_dict.items():
            summary = item.get_summary()
            self.assertIsInstance(summary, dict)
            json_value = item.get_summary(as_json=True)
            self.assertIsInstance(json_value, str)
            new_summary = json.loads(json_value)
            self.assertIsInstance(new_summary, dict)
        merged1 = this_context.merge_all_info()
        # self.assertIsInstance(merged1, ColumnNameSummary)
        self.assertEqual(len(merged1.file_dict), 3)
        self.assertEqual(len(merged1.unique_headers), 2)
        with self.assertRaises(ValueError) as except_context:
            sum_op.do_op(dispatch, df, "run-03")
        self.assertEqual(except_context.exception.args[0], "FileHasChangedColumnNames")

    def test_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        parms = json.loads(self.json_parms)
        op = SummarizeColumnNamesOp(parms)
        df, df_new = self.get_dfs(op, "run-01", dispatch)
        self.assertEqual(len(df), len(df_new))
        context_dict = dispatch.summary_dicts
        self.assertIsInstance(context_dict, dict)
        self.get_dfs(op, "run-02", dispatch)
        context = dispatch.summary_dicts["columns"]
        summary = context.get_summary()
        dataset_sum = summary["Dataset"]
        json_str = json.dumps(dataset_sum)
        json_obj = json.loads(json_str)
        columns = json_obj["Overall summary"]["Specifics"]["Columns"]
        self.assertEqual(len(columns), 1)
        self.assertEqual(len(columns[0]["Files"]), 2)
        ind_sum = summary["Individual files"]
        self.assertEqual(len(ind_sum), 2)

    def test_text_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        parms = json.loads(self.json_parms)
        op = SummarizeColumnNamesOp(parms)
        self.get_dfs(op, "run-01", dispatch)
        self.get_dfs(op, "run-02", dispatch)
        context = dispatch.summary_dicts["columns"]
        # self.assertIsInstance(context, ColumnNameSummary)
        text_summary1 = context.get_text_summary()
        self.assertIsInstance(text_summary1, dict)

    def test_multiple(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        parms = json.loads(self.json_parms)
        op = SummarizeColumnNamesOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        op.do_op(dispatch, dispatch.prep_data(df), "run-01")
        df1 = pd.DataFrame(self.data1, columns=self.sample_columns1)
        op.do_op(dispatch, dispatch.prep_data(df1), "run-02")
        op.do_op(dispatch, dispatch.prep_data(df1), "run-03")
        df2 = pd.DataFrame(self.data1, columns=self.sample_columns2)
        op.do_op(dispatch, dispatch.prep_data(df2), "run-05")
        context = dispatch.summary_dicts["columns"]
        summary = context.get_summary()
        text_summary1 = context.get_text_summary()
        self.assertEqual(len(summary), 2)
        self.assertIsInstance(text_summary1, dict)
        self.assertEqual(len(text_summary1), 2)
        self.assertEqual(len(text_summary1["Individual files"]), 4)


if __name__ == "__main__":
    unittest.main()
