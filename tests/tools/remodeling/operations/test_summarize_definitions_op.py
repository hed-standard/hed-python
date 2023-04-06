import json
import os
import unittest
import pandas as pd
from hed.models.df_util import get_assembled
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_definitions_op import SummarizeDefinitionsOp, DefinitionSummaryContext


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodel_tests/'))
        cls.data_path = os.path.realpath(os.path.join(path, 'sub-002_task-FacePerception_run-1_events.tsv'))
        cls.json_path = os.path.realpath(os.path.join(path, 'task-FacePerception_events.json'))
        base_parameters = {
            "summary_name": 'get_definition_summary',
            "summary_filename": 'summarize_definitions'
        }
        cls.json_parms = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op1 = SummarizeDefinitionsOp(parms)
        self.assertIsInstance(sum_op1, SummarizeDefinitionsOp, "constructor creates an object of the correct type")
        parms["expand_context"] = ""
        with self.assertRaises(KeyError) as context:
            SummarizeDefinitionsOp(parms)
        self.assertEqual(context.exception.args[0], "BadParameter")
        parms2 = json.loads(self.json_parms)
        parms2["mystery"] = True
        with self.assertRaises(KeyError) as context:
            SummarizeDefinitionsOp(parms2)
        self.assertEqual(context.exception.args[0], "BadParameter")

    def test_do_op(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeDefinitionsOp(parms)
        self.assertIsInstance(sum_op, SummarizeDefinitionsOp, "constructor creates an object of the correct type")
        df = pd.read_csv(self.data_path, delimiter='\t', header=0, keep_default_na=False, na_values=",null")
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run1', sidecar=self.json_path)
        self.assertEqual(200, len(df_new), "summarize_hed_type_op dataframe length is correct")
        self.assertEqual(10, len(df_new.columns), "summarize_hed_type_op has correct number of columns")
        self.assertIn(sum_op.summary_name, dispatch.context_dict)
        self.assertIsInstance(dispatch.context_dict[sum_op.summary_name], DefinitionSummaryContext)
        # x = dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run1']
        # self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run1'].tag_dict), 47)
        # df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), 'subj2_run2', sidecar=self.json_path)
        # self.assertEqual(len(dispatch.context_dict[sum_op.summary_name].summary_dict['subj2_run2'].tag_dict), 47)


if __name__ == '__main__':
    unittest.main()
