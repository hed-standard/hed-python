import json
import os
import unittest
import pandas as pd
from hed.models import Sidecar
from hed.schema import load_schema_version
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_hed_type_op import SummarizeHedTypeOp, HedTypeSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/"))
        cls.data_path = os.path.realpath(os.path.join(path, "sub-002_task-FacePerception_run-1_events.tsv"))
        cls.json_path = os.path.realpath(os.path.join(path, "task-FacePerception_events.json"))
        base_parameters = {
            "summary_name": "get summary conditions",
            "summary_filename": "summarize_condition_variable_type",
            "type_tag": "condition-variable",
        }
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

        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        cls.events = os.path.realpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_excerpt_events.tsv"
            )
        )
        cls.sidecar_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_events.json")
        )
        cls.hed_schema = load_schema_version("8.1.0")
        cls.summary_path = os.path.realpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/aomic_sub-0013_summary_all_rmdl.json"
            )
        )
        rel_path = "../../../data/remodel_tests/sub-002_task-FacePerception_run-1_events.tsv"
        cls.events_wh = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), rel_path))
        rel_side = "../../../data/remodel_tests/task-FacePerception_events.json"
        cls.sidecar_path_wh = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), rel_side))

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTypeOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedTypeOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")
        df_new = sum_op.do_op(self.dispatch, df, "subj2_run1", sidecar=self.json_path)
        self.assertEqual(200, len(df_new), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(list(df_new.columns)), "summarize_hed_type_op has correct number of columns")

    def test_summary(self):
        with open(self.summary_path, "r") as fp:
            parms = json.load(fp)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df = dispatch.get_data_file(self.events)
        parsed_commands = Dispatcher.parse_operations(parms)
        sum_op = parsed_commands[2]
        sum_op.do_op(dispatch, dispatch.prep_data(df), "run-01", sidecar=self.sidecar_path)
        context1 = dispatch.summary_dicts["AOMIC_condition_variables"]
        summary1 = context1.get_summary()
        self.assertIn("run-01", summary1["Individual files"])
        self.assertEqual(len(summary1["Individual files"]), 1)
        summary1a = context1.get_summary()
        self.assertIsInstance(summary1a["Dataset"], dict)
        sum_op.do_op(dispatch, dispatch.prep_data(df), "run-02", sidecar=self.sidecar_path)
        context2 = dispatch.summary_dicts["AOMIC_condition_variables"]
        summary2 = context2.get_summary(individual_summaries="separate")
        self.assertEqual(summary2["Dataset"]["Overall summary"]["Files"][0], "run-01")
        self.assertEqual(len(summary2["Dataset"]["Overall summary"]["Files"]), 2)
        summary2a = context2.get_summary(individual_summaries="separate")
        self.assertIsInstance(summary2a["Individual files"]["run-02"], dict)

    def test_text_summary_with_levels(self):
        with open(self.summary_path, "r") as fp:
            parms = json.load(fp)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df = dispatch.get_data_file(self.events_wh)
        parsed_commands = Dispatcher.parse_operations(parms)
        sum_op = parsed_commands[2]
        sum_op.do_op(dispatch, dispatch.prep_data(df), "run-01", sidecar=self.sidecar_path_wh)
        context1 = dispatch.summary_dicts["AOMIC_condition_variables"]
        text_summary1 = context1.get_text_summary()
        self.assertIsInstance(text_summary1, dict)

    def test_text_summary(self):
        sidecar = Sidecar(self.sidecar_path, name="aomic_sidecar")

        with open(self.summary_path, "r") as fp:
            parms = json.load(fp)
        parsed_commands = Dispatcher.parse_operations(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df = dispatch.get_data_file(self.events)
        old_len = len(df)
        sum_op = parsed_commands[2]
        df = sum_op.do_op(dispatch, dispatch.prep_data(df), os.path.basename(self.events), sidecar=sidecar)
        self.assertEqual(len(df), old_len)
        context_dict = dispatch.summary_dicts
        self.assertIsInstance(context_dict, dict)
        context1 = dispatch.summary_dicts["AOMIC_condition_variables"]
        self.assertIsInstance(context1, HedTypeSummary)
        text_summary1 = context1.get_text_summary()
        self.assertIsInstance(text_summary1, dict)
        sum_op.do_op(dispatch, dispatch.prep_data(df), "new_events", sidecar=sidecar)
        context2 = dispatch.summary_dicts["AOMIC_condition_variables"]
        text_summary2 = context2.get_text_summary()
        self.assertIsInstance(text_summary2, dict)
        self.assertEqual(len(text_summary1["Individual files"]), 1)
        self.assertEqual(len(text_summary2["Individual files"]), 2)


if __name__ == "__main__":
    unittest.main()
