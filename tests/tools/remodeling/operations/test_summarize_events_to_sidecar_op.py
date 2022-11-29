import os
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_events_to_sidecar_op import EventsToSidecarSummary, \
    SummarizeEventsToSidecarOp


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
        cls.base_parameters = {
            "summary_name": "extracted_json",
            "summary_filename": "extracted_json",
            "skip_columns": ["onset", "duration"],
            "value_columns": ["response_time", "stop_signal_delay"],
        }

        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                      '../../../data/remodel_tests'))

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        sum_op = SummarizeEventsToSidecarOp(self.base_parameters)
        self.assertIsInstance(sum_op, SummarizeEventsToSidecarOp, "constructor creates an object of the correct type")

    def test_do_ops(self):
        sum_op = SummarizeEventsToSidecarOp(self.base_parameters)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df1a = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        sum_op.do_op(dispatch, dispatch.prep_events(df1), 'name1')
        context1 = dispatch.context_dict.get(self.base_parameters['summary_name'], None)
        summary = context1.summary
        cat_len = len(summary.categorical_info)
        cat_base = len(self.sample_columns) - len(self.base_parameters["skip_columns"]) -  \
            len(self.base_parameters["value_columns"])
        self.assertEqual(cat_len, cat_base, 'do_ops has right number of categorical columns')
        sum_op.do_op(dispatch, dispatch.prep_events(df1a), 'name1')
        self.assertEqual(len(df1.columns), len(self.sample_columns), "do_ops updating does not change number columns.")
        sum_op.do_op(dispatch, dispatch.prep_events(df1a), 'name2')

    def test_get_summary(self):
        sum_op = SummarizeEventsToSidecarOp(self.base_parameters)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        sum_op.do_op(dispatch, dispatch.prep_events(df1), 'name1')
        context1 = dispatch.context_dict.get(self.base_parameters['summary_name'], None)
        self.assertIsInstance(context1, EventsToSidecarSummary, "get_summary testing EventsToSidecarSummary")
        summary1 = context1.get_summary()
        self.assertIsInstance(summary1, dict, "get_summary returns a dictionary by default")
        summary1_contents = summary1["summary"]
        self.assertIsInstance(summary1_contents, dict, "The summary contents is a dictionary")
        self.assertEqual(len(summary1_contents), len(self.sample_columns) - len(self.base_parameters["skip_columns"]))
        summary2 = context1.get_summary(as_json=True)
        self.assertIsInstance(summary2, str, "get_summary returns a dictionary if json requested")
        summary3 = context1.get_text_summary(include_individual=True)
        self.assertIsInstance(summary3, str, "get_text_summary returns a str if verbose is False")
        summary4 = context1.get_text_summary()
        self.assertIsInstance(summary4, str, "get_text_summary returns a str by default")
        summary5 = context1.get_text_summary(include_individual=True)
        self.assertIsInstance(summary5, str, "get_text_summary returns a str with verbose True")


if __name__ == '__main__':
    unittest.main()
