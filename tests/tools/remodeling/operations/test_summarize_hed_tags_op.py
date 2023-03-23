import json
import os
import unittest
import pandas as pd
from hed.models.df_util import get_assembled
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
        x = dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run1']
        self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run1'].tag_dict), 47)
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run2', sidecar=self.json_path)
        self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run2'].tag_dict), 47)

    def test_quick_test(self):
        from hed.models.hed_tag import HedTag
        from hed.schema import load_schema_version
        my_tag = "Description/This is a test"
        tag = HedTag(my_tag)
        x = tag.tag_terms
        # print(x)
        my_schema = load_schema_version('8.1.0')
        tag1 = HedTag(my_tag, hed_schema=my_schema)
        x1 = tag1.tag_terms
        # print(x1)

    def test_quick3(self):
        from hed.models import TabularInput, Sidecar
        from hed.schema import load_schema_version
        from hed.tools.analysis.hed_tag_counts import HedTagCounts
        from io import StringIO
        my_schema = load_schema_version('8.1.0')
        my_json = {
                    "code": {
                        "HED": {
                            "code1": "((Def/Blech1, Green), Blue)",
                            "code2": "((Def/Blech3, Description/Help me), Blue)"
                        }
                    },
                    "defs": {
                        "HED": {
                            "def1": "(Definition/Blech1, (Condition-variable/Cat, Description/this is hard))"
                        }
                    }
                  }
        my_json_str = json.dumps(my_json)
        my_sidecar = Sidecar(StringIO(my_json_str))
        data = [[0.5, 0, 'code1', 'Description/This is a test, Label/Temp, (Def/Blech1, Green)'],
                [0.6, 0, 'code2', 'Sensory-event, ((Description/Animal, Condition-variable/Blech))']]
        df = pd.DataFrame(data, columns=['onset', 'duration', 'code', 'HED'])
        input_data = TabularInput(df, sidecar=my_sidecar)
        counts = HedTagCounts('myName', 2)
        summary_dict = {}
        hed_strings, definitions = get_assembled(input_data, my_sidecar, my_schema, extra_def_dicts=None, join_columns=True,
                                    shrink_defs=False, expand_defs=True)
        for hed in hed_strings:
            counts.update_event_counts(hed, 'myName')
        summary_dict['myName'] = counts

    def test_quick4(self):
        from hed.models import TabularInput, Sidecar
        from hed.schema import load_schema_version
        from hed.tools.analysis.hed_tag_counts import HedTagCounts
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodel_tests/'))
        data_path = os.path.realpath(os.path.join(path, 'sub-002_task-FacePerception_run-1_events.tsv'))
        json_path = os.path.realpath(os.path.join(path, 'task-FacePerception_events.json'))
        my_schema = load_schema_version('8.1.0')
        sidecar = Sidecar(json_path,)
        input_data = TabularInput(data_path, sidecar=sidecar)
        counts = HedTagCounts('myName', 2)
        summary_dict = {}
        hed_strings, definitions = get_assembled(input_data, sidecar, my_schema, 
                                                 extra_def_dicts=None, join_columns=True,
                                                 shrink_defs=False, expand_defs=True)
        for hed in hed_strings:
            counts.update_event_counts(hed, 'myName')
        summary_dict['myName'] = counts

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

    def test_get_summary_text_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeHedTagsOp(parms)
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        df = dispatch.prep_data(df)
        sum_op.do_op(dispatch, df, 'subj2_run1', sidecar=self.json_path)
        sum_op.do_op(dispatch, df, 'subj2_run2', sidecar=self.json_path)
        sum_context1 = dispatch.context_dict[sum_op.summary_name]
        text_sum_none = sum_context1.get_text_summary(individual_summaries="none")
        self.assertIn('Dataset', text_sum_none)
        self.assertIsInstance(text_sum_none['Dataset'], str)
        self.assertFalse(text_sum_none.get("Individual files", {}))
        
        text_sum_consolidated = sum_context1.get_text_summary(individual_summaries="consolidated")
        self.assertIn('Dataset', text_sum_consolidated)
        self.assertIsInstance(text_sum_consolidated['Dataset'], str)
        self.assertFalse(text_sum_consolidated.get("Individual files", {}))
        self.assertGreater(len(text_sum_consolidated['Dataset']), len(text_sum_none['Dataset']))
        
        text_sum_separate = sum_context1.get_text_summary(individual_summaries="separate")
        self.assertIn('Dataset', text_sum_separate)
        self.assertIsInstance(text_sum_separate['Dataset'], str)
        self.assertIn("Individual files", text_sum_separate)
        self.assertIsInstance(text_sum_separate["Individual files"], dict)
        self.assertEqual(len(text_sum_separate["Individual files"]), 2)

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
