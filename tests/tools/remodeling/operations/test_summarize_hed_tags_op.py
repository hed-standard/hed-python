import json
import os
import unittest
import pandas as pd
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_hed_tags_op import SummarizeHedTagsOp, HedTagSummaryContext


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodel_tests/'))
        cls.data_path = os.path.realpath(os.path.join(path, 'sub-002_task-FacePerception_run-1_events.tsv'))
        cls.json_path = os.path.realpath(os.path.join(path, 'task-FacePerception_events.json'))
        base_parameters = {
            "summary_name": 'get_summary hed tags',
            "summary_filename": 'summarize_hed_tags',
            "tags": {
                "Sensory events": ["Sensory-event", "Sensory-presentation", "Task-stimulus-role",
                                   "Experimental-stimulus"],
                "Agent actions": ["Agent-action", "Agent", "Action", "Agent-task-role", "Task-action-type",
                                  "Participant-response"],
                "Task properties": ["Task-property"],
                "Objects": ["Item"],
                "Properties": ["Property"]
            },
            "expand_context": False,
        }
        cls.json_parms = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op1 = SummarizeHedTagsOp(parms)
        self.assertIsInstance(sum_op1, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        parms["expand_context"] = ""
        with self.assertRaises(TypeError) as context:
            SummarizeHedTagsOp(parms)
        self.assertEqual(context.exception.args[0], "BadType")
        parms2 = json.loads(self.json_parms)
        parms2["mystery"] = True
        with self.assertRaises(KeyError) as context:
            SummarizeHedTagsOp(parms2)
        self.assertEqual(context.exception.args[0], "BadParameter")

    def test_do_op(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run1', sidecar=self.json_path)
        self.assertEqual(200, len(df_new), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new.columns), "summarize_hed_type_op has correct number of columns")
        self.assertIn(sum_op.summary_name, dispatch.context_dict)
        self.assertIsInstance(dispatch.context_dict[sum_op.summary_name], HedTagSummaryContext)
        self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run1'].tag_dict), 18)
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run2', sidecar=self.json_path)
        self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run2'].tag_dict), 18)

    def test_get_summary_details(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        self.assertIsInstance(sum_op, SummarizeHedTagsOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run1', sidecar=self.json_path)
        self.assertIn(sum_op.summary_name, dispatch.context_dict)
        sum_context = dispatch.context_dict[sum_op.summary_name]
        self.assertIsInstance(sum_context, HedTagSummaryContext)
        sum_obj1 = sum_context.get_summary_details()
        self.assertIsInstance(sum_obj1, dict)
        json_str1 = json.dumps(sum_obj1, indent=4)
        self.assertIsInstance(json_str1, str)
        json_obj1 = json.loads(json_str1)
        self.assertIsInstance(json_obj1, dict)
        sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run2', sidecar=self.json_path)
        sum_context2 = dispatch.context_dict[sum_op.summary_name]
        sum_obj2 = sum_context2.get_summary_details()
        json_str2 = json.dumps(sum_obj2, indent=4)
        self.assertIsInstance(json_str2, str)
        sum_obj3 = sum_context2.get_summary_details(include_individual=False)
        self.assertFalse(sum_obj3['Individual files'])

    def test_get_summary_details_verbose(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        df = dispatch.prep_data(dispatch.get_data_file(self.data_path))
        sum_op.do_op(dispatch, df, 'subj2_run1', sidecar=self.json_path)
        sum_op.do_op(dispatch, df, 'subj2_run2', sidecar=self.json_path)
        sum_context1 = dispatch.context_dict[sum_op.summary_name]
        sum_obj1 = sum_context1.get_summary_details(include_individual=True)
        json_str1 = json.dumps(sum_obj1, indent=4)
        self.assertIsInstance(json_str1, str)

    def test_get_summary_text_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        df = dispatch.prep_data(df)
        sum_op.do_op(dispatch, df, 'subj2_run1', sidecar=self.json_path)

        sum_op.do_op(dispatch, df, 'subj2_run2', sidecar=self.json_path)
        sum_context1 = dispatch.context_dict[sum_op.summary_name]
        text_sum1 = sum_context1.get_text_summary(include_individual=True, separate_files=False)
        text_sum1t = sum_context1.get_text_summary(include_individual=True, separate_files=True)
        text_sum1no = sum_context1.get_text_summary(include_individual=False, separate_files=False)
        self.assertGreater(len(text_sum1['Dataset']), len(text_sum1t['Dataset']))
        self.assertGreater(len(text_sum1['Dataset']), len(text_sum1no['Dataset']))

    def test_sample_example(self):
        remodel_list = [{
            "operation": "summarize_hed_tags",
            "description": "Produce a summary of HED tags.",
            "parameters": {
                "summary_name": "summarize_hed_tags",
                "summary_filename": "summarize_hed_tags",
                "tags": {
                    "Sensory events": ["Sensory-event", "Sensory-presentation", "Task-stimulus-role",
                                       "Experimental-stimulus"],
                    "Agent actions": ["Agent-action", "Agent", "Action", "Agent-task-role", "Task-action-type",
                                      "Participant-response"],
                    "Objects": ["Item"]
                },
                "expand_context": False
            }}]

        sample_data = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
                       [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                       [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                       [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                       [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                       [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                          'response_accuracy', 'response_hand', 'sex']

        sidecar_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                     '../../../data/remodel_tests/aomic_sub-0013_events.json'))

        dispatch = Dispatcher(remodel_list, data_root=None, backup_name=None, hed_versions=['8.1.0'])
        df = pd.DataFrame(sample_data, columns=sample_columns)
        df = dispatch.prep_data(df)
        for operation in dispatch.parsed_ops:
            df = operation.do_op(dispatch, df, "sample", sidecar=sidecar_path)
        context_dict = dispatch.context_dict.get("summarize_hed_tags")
        text_summary = context_dict.get_text_summary()
        self.assertIsInstance(text_summary["Dataset"], str)


if __name__ == '__main__':
    unittest.main()
