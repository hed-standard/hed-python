import json
import os
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_hed_type_op import SummarizeHedTypeOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodeling/'))
        cls.data_path = os.path.realpath(os.path.join(path, 'sub-002_task-FacePerception_run-1_events.tsv'))
        cls.json_path = os.path.realpath(os.path.join(path, 'task-FacePerception_events.json'))
        base_parameters = {
            "summary_name": 'summarize conditions',
            "summary_filename": 'summarize_condition_variable_type',
            "type_tag": "condition-variable"
        }
        cls.sample_data = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                           [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                           [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                           [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                           [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        cls.sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                              'response_accuracy', 'response_hand', 'sex']

        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], hed_versions=['8.1.0'])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTypeOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedTypeOp, "constructor creates an object of the correct type")
        df_new = sum_op.do_op(self.dispatch, self.data_path, 'subj2_run1', sidecar=self.json_path)
        self.assertEqual(200, len(df_new), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new.columns), "summarize_hed_type_op has correct number of columns")

    # def test_do_ops(self):
    #     # TODO
    #     parms = json.loads(self.json_parms)
    #     sum_op = SummarizeColumnValuesOp(parms)
    #     dispatch = Dispatcher([], data_root=self.data_root)
    #     df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
    #     df1a = pd.DataFrame(self.sample_data, columns=self.sample_columns)
    #     sum_op.do_op(dispatch, df1, 'name1')
    #     context1 = dispatch.context_dict.get(parms['summary_name'], None)
    #     summary = context1.summary
    #     cat_len = len(summary.categorical_info)
    #     self.assertEqual(cat_len, len(self.sample_columns),
    #                      'do_ops if all columns are categorical summary has same number of columns as df')
    #     sum_op.do_op(dispatch, df1a, 'name1')
    #     self.assertEqual(len(context1.summary.categorical_info), len(self.sample_columns),
    #                      "do_ops updating does not change number of categorical columns.")
    #     sum_op.do_op(dispatch, df1a, 'name2')
    #
    # def test_get_summary(self):
    #     # TODO implement these tests
    #     parms = json.loads(self.json_parms)
    #     sum_op = SummarizeColumnValuesOp(parms)
    #     dispatch = Dispatcher([], data_root=self.data_root)
    #     df1 = pd.DataFrame(self.sample_data, columns=self.sample_columns)
    #     sum_op.do_op(dispatch, df1, 'name1')
    #     sum_op.do_op(dispatch, df1, 'name2')
    #     sum_op.do_op(dispatch, df1, 'name3')
    #     context1 = dispatch.context_dict.get(parms['summary_name'], None)
    #     self.assertIsInstance(context1, ColumnValueSummary, "get_summary testing ColumnValueSummary")
    #     summary1 = context1.get_summary()
    #     self.assertIsInstance(summary1, dict, "get_summary returns a dictionary by default")
    #     summary2 = context1.get_summary(as_json=True)
    #     self.assertIsInstance(summary2, str, "get_summary returns a dictionary if json requested")
    #     summary3 = context1.get_text_summary(verbose=False)
    #     self.assertIsInstance(summary3, str, "get_text_summary returns a str if verbose is False")
    #     summary4 = context1.get_text_summary()
    #     self.assertIsInstance(summary4, str, "get_text_summary returns a str by default")
    #     summary5 = context1.get_text_summary(verbose=True)
    #     self.assertIsInstance(summary5, str, "get_text_summary returns a str with verbose True")


if __name__ == '__main__':
    unittest.main()
