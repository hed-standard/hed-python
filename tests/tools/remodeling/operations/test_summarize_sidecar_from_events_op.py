import os
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_sidecar_from_events_op import (
    EventsToSidecarSummary,
    SummarizeSidecarFromEventsOp,
)


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
        cls.base_parameters = {
            "summary_name": "extracted_json",
            "summary_filename": "extracted_json",
            "skip_columns": ["onset", "duration"],
            "value_columns": ["response_time", "stop_signal_delay"],
        }

        cls.data_root = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests")
        )

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        sum_op = SummarizeSidecarFromEventsOp(self.base_parameters)
        self.assertIsInstance(sum_op, SummarizeSidecarFromEventsOp, "constructor creates an object of the correct type")

    def test_do_ops(self):
        sum_op = SummarizeSidecarFromEventsOp(self.base_parameters)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df1a = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        sum_op.do_op(dispatch, dispatch.prep_data(df1), "name1")
        context1 = dispatch.summary_dicts.get(self.base_parameters["summary_name"], None)
        summary = context1.summary_dict["name1"]
        cat_len = len(summary.categorical_info)
        cat_base = (
            len(self.sample_columns) - len(self.base_parameters["skip_columns"]) - len(self.base_parameters["value_columns"])
        )
        self.assertEqual(cat_len, cat_base, "do_ops has right number of categorical columns")
        sum_op.do_op(dispatch, dispatch.prep_data(df1a), "name1")
        self.assertEqual(len(df1.columns), len(self.sample_columns), "do_ops updating does not change number columns.")
        sum_op.do_op(dispatch, dispatch.prep_data(df1a), "name2")

    def test_get_summary(self):
        sum_op = SummarizeSidecarFromEventsOp(self.base_parameters)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        sum_op.do_op(dispatch, dispatch.prep_data(df1), "name1")
        context1 = dispatch.summary_dicts.get(self.base_parameters["summary_name"], None)
        self.assertIsInstance(context1, EventsToSidecarSummary, "get_summary testing EventsToSidecarSummary")
        summary1 = context1.get_summary()
        self.assertIsInstance(summary1, dict, "get_summary returns a dictionary by default")
        self.assertIsInstance(summary1["Dataset"], dict)
        self.assertEqual(len(summary1["Individual files"]), 1)
        summary2 = context1.get_summary()
        self.assertIsInstance(summary2, dict, "get_summary returns a dictionary by default")
        self.assertIsInstance(summary2["Dataset"], dict)
        self.assertIsInstance(summary2["Individual files"]["name1"], dict)
        summary_text3 = context1.get_text_summary(individual_summaries="none")
        self.assertIsInstance(summary_text3, dict, "get_text_summary returns a str if verbose is False")
        self.assertNotIn("Individual files", summary_text3)
        summary_text4 = context1.get_text_summary(individual_summaries="consolidated")
        self.assertIsInstance(summary_text4, dict)
        summary_text5 = context1.get_text_summary(individual_summaries="separate")
        self.assertIsInstance(summary_text5, dict)
        self.assertGreater(len(summary_text4["Dataset"]), len(summary_text5["Dataset"]))
        sum_op.do_op(dispatch, dispatch.prep_data(df1), "name2")
        context2 = dispatch.summary_dicts.get(self.base_parameters["summary_name"], None)
        self.assertIsInstance(context1, EventsToSidecarSummary, "get_summary testing EventsToSidecarSummary")
        summary_text6 = context2.get_text_summary(individual_summaries="separate")
        self.assertIsInstance(summary_text6, dict)


if __name__ == "__main__":
    unittest.main()
