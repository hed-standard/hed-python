import json
import os
import unittest
import pandas as pd
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_hed_validation_op import SummarizeHedValidationOp, \
    HedValidationSummaryContext


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodel_tests/'))
        cls.data_path = os.path.realpath(os.path.join(path, 'sub-002_task-FacePerception_run-1_events.tsv'))
        cls.json_path = os.path.realpath(os.path.join(path, 'task-FacePerception_events.json'))
        cls.bad_json_path =  os.path.realpath(os.path.join(path, 'task-FacePerceptionMissingDefs_events.json'))
        cls.sample_sidecar_path = os.path.realpath(os.path.join(path, 'task-stopsignal_acq-seq_events.json'))
        cls.sample_data = [[0.0776, 0.5083, 'baloney', 'n/a', 0.565, 'correct', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                           [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                           [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                           [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                           [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        cls.sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                              'response_accuracy', 'response_hand', 'sex']
        base_parameters = {
            "summary_name": 'summarize_hed_validation_errors',
            "summary_filename": 'summarize_hed_validation_errors',
            "check_for_warnings": True
        }
        cls.json_parms = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op1 = SummarizeHedValidationOp(parms)
        self.assertIsInstance(sum_op1, SummarizeHedValidationOp, "constructor creates an object of the correct type")

        parms2 = json.loads(self.json_parms)
        parms2["mystery"] = True
        with self.assertRaises(KeyError) as context:
            SummarizeHedValidationOp(parms2)
        self.assertEqual(context.exception.args[0], "BadParameter")

    def test_do_op(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedValidationOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedValidationOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        sum_op.do_op(dispatch, dispatch.prep_events(df), 'subj2_run1', sidecar=self.json_path)
        self.assertIn(sum_op.summary_name, dispatch.context_dict)
        self.assertIsInstance(dispatch.context_dict[sum_op.summary_name], HedValidationSummaryContext)
        sub1 = dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run1']
        self.assertEqual(len(sub1['event_issues']), 1)
        sum_op.do_op(dispatch, dispatch.prep_events(df), 'subj2_run2', sidecar=self.json_path)
        self.assertEqual(len(sub1['event_issues']), 1)
        sum_op.do_op(dispatch, dispatch.prep_events(df), 'subj2_run3', sidecar=self.bad_json_path)
        self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict), 3)
        run3 = dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run3']
        self.assertEqual(run3["total_sidecar_issues"], 2)

    def test_get_summary_details(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedValidationOp(parms)
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        sum_op.do_op(dispatch, dispatch.prep_events(df), 'subj2_run1', sidecar=self.json_path)
        sum_context = dispatch.context_dict[sum_op.summary_name]
        sum_obj1 = sum_context.get_summary_details()
        self.assertIsInstance(sum_obj1, dict)
        json_str1 = json.dumps(sum_obj1, indent=4)
        self.assertIsInstance(json_str1, str)
        json_obj1 = json.loads(json_str1)
        self.assertIsInstance(json_obj1, dict)
        sum_op.do_op(dispatch, dispatch.prep_events(df), 'subj2_run2', sidecar=self.json_path)
        sum_context2 = dispatch.context_dict[sum_op.summary_name]
        sum_obj2 = sum_context2.get_summary_details()
        json_str2 = json.dumps(sum_obj2, indent=4)
        self.assertIsInstance(json_str2, str)
        sum_obj3 = sum_context2.get_summary_details(include_individual=False)
        self.assertNotIn('Individual files', sum_obj3)
        sum_op.do_op(dispatch, dispatch.prep_events(df), 'subj2_run4', sidecar=self.bad_json_path)
        sum_obj4 = sum_context2.get_summary_details(include_individual=True)
        self.assertIsInstance(sum_obj4, dict)

    def test_get_summary_text_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedValidationOp(parms)
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        df = dispatch.prep_events(df)
        sum_op.do_op(dispatch, df, 'subj2_run1', sidecar=self.bad_json_path)

        sum_context1 = dispatch.context_dict[sum_op.summary_name]
        text_sum1 = sum_context1.get_text_summary(include_individual=True)
        print(text_sum1)
        sum_op.do_op(dispatch, df, 'subj2_run2', sidecar=self.json_path)
        sum_op.do_op(dispatch, df, 'subj2_run3', sidecar=self.bad_json_path)
        text_sum2 = sum_context1.get_text_summary(include_individual=False)
        text_sum3 = sum_context1.get_text_summary(include_individual=True)
        self.assertIsInstance(text_sum3, str)
        self.assertIsInstance(text_sum2, str)
        self.assertIsInstance(text_sum2, str)

    def test_with_sample_data(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedValidationOp(parms)
        print(self.sample_sidecar_path)
        sum_op.do_op(dispatch, df, 'sub-0013_task-stopsignal_acq-seq_events.tsv', sidecar=self.sample_sidecar_path)

        sum_context1 = dispatch.context_dict[sum_op.summary_name]
        text_sum1 = sum_context1.get_text_summary(include_individual=True)
        print(text_sum1)


if __name__ == '__main__':
    unittest.main()
