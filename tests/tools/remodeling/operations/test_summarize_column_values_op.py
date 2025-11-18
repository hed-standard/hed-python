import json
import os
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_column_values_op import ColumnValueSummary, SummarizeColumnValuesOp


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
        base_parameters = {
            "summary_name": "test summary",
            "summary_filename": "column_values_summary",
            "skip_columns": [],
            "value_columns": ["onset", "response_time"],
        }

        cls.json_parms = json.dumps(base_parameters)
        cls.data_root = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests")
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op, name, dispatch):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(dispatch, dispatch.prep_data(df), name)
        return df, dispatch.post_proc_data(df_new)

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnValuesOp(parms)
        self.assertIsInstance(sum_op, SummarizeColumnValuesOp, "constructor creates an object of the correct type")

    def test_do_ops(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnValuesOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        self.get_dfs(sum_op, "name1", dispatch)
        context1 = dispatch.summary_dicts.get(parms["summary_name"], None)
        summary1 = context1.summary_dict["name1"]
        cat_len = len(summary1.categorical_info)
        self.assertEqual(
            cat_len,
            len(self.sample_columns) - 2,
            "do_ops if all columns are categorical summary has same number of columns as df",
        )
        self.get_dfs(sum_op, "name2", dispatch)
        self.assertEqual(
            cat_len, len(self.sample_columns) - 2, "do_ops updating does not change number of categorical columns."
        )
        context = dispatch.summary_dicts["test summary"]
        text_sum = context.get_text_summary()
        self.assertIsInstance(text_sum, dict)
        self.assertEqual(len(context.summary_dict), 2)

    def test_get_summary(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnValuesOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        self.get_dfs(sum_op, "name1", dispatch)

        cont = dispatch.summary_dicts
        context = cont.get("test summary", None)
        self.assertIsInstance(context, ColumnValueSummary, "get_summary testing ColumnValueSummary")
        summary1a = context.get_summary()
        self.assertIsInstance(summary1a, dict)
        self.assertIsInstance(summary1a["Dataset"], dict)
        text_summary1 = context.get_text_summary(individual_summaries=None)
        self.assertIsInstance(text_summary1, dict)
        self.assertIsInstance(text_summary1["Dataset"], str)
        text_summary1a = context.get_text_summary(individual_summaries="separate")
        self.assertIsInstance(text_summary1a, dict)
        self.get_dfs(sum_op, "name2", dispatch)
        self.get_dfs(sum_op, "name3", dispatch)
        context2 = dispatch.summary_dicts.get(parms["summary_name"], None)
        summary2 = context2.get_summary()
        self.assertIsInstance(summary2, dict)
        text_summary2 = context2.get_text_summary(individual_summaries="consolidated")
        self.assertIsInstance(text_summary2, dict)

    def test_summary_op(self):
        events = os.path.realpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_excerpt_events.tsv"
            )
        )
        column_summary_path = os.path.realpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_summary_all_rmdl.json"
            )
        )
        with open(column_summary_path, "r") as fp:
            parms = json.load(fp)
        parsed_commands = Dispatcher.parse_operations(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df = dispatch.get_data_file(events)
        old_len = len(df)
        sum_op = parsed_commands[1]
        df = sum_op.do_op(dispatch, dispatch.prep_data(df), os.path.basename(events))
        self.assertEqual(len(df), old_len)
        context_dict = dispatch.summary_dicts
        for _key, item in context_dict.items():
            text_value = item.get_text_summary()
            self.assertTrue(text_value)
            json_value = item.get_summary()
            self.assertTrue(json_value)


if __name__ == "__main__":
    unittest.main()
