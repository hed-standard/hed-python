import json
import os
import unittest
from hed.models import Sidecar
from hed.schema import load_schema_version
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_hed_type_op import SummarizeHedTypeOp, HedTypeSummary
from hed.tools import HedVariableSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodel_tests/'))
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

    def test_summary_op(self):
        events =  os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                '../../../data/remodel_tests/aomic_sub-0013_excerpt_events.tsv'))
        sidecar_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                     '../../../data/remodel_tests/aomic_sub-0013_events.json'))
        hed_schema = load_schema_version('8.1.0')
        sidecar = Sidecar(sidecar_path, 'aomic_sidecar', hed_schema=hed_schema)
        column_summary_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                '../../../data/remodel_tests/aomic_sub-0013_summary_all_rmdl.json'))
        with open(column_summary_path, 'r') as fp:
            parms = json.load(fp)
        parsed_commands, errors = Dispatcher.parse_operations(parms)
        self.assertFalse(errors)
        dispatch = Dispatcher([], data_root=None, hed_versions=['8.1.0'])
        df = dispatch.get_data_file(events)
        sum_op =  parsed_commands[2]
        df = sum_op.do_op(dispatch, df, os.path.basename(events), sidecar=sidecar)
        context_dict = dispatch.context_dict
        for key, item in context_dict.items():
            text_value = item.get_text_summary()
            self.assertTrue(text_value)
            json_value = item.get_summary(as_json=True)
            self.assertTrue(json_value)
        context1 = dispatch.context_dict['AOMIC_condition_variables']
        self.assertIsInstance(context1, HedTypeSummary)
        summary = context1.summary
        self.assertIsInstance(summary, HedVariableSummary)
        self.assertEqual(context1.variable_type, 'condition-variable')


if __name__ == '__main__':
    unittest.main()
