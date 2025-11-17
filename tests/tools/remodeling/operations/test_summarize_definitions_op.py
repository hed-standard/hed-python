import json
import os
import unittest
import pandas as pd
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_definitions_op import SummarizeDefinitionsOp, DefinitionSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/"))
        cls.data_path = os.path.realpath(os.path.join(path, "sub-002_task-FacePerception_run-1_events.tsv"))
        cls.json_path = os.path.realpath(os.path.join(path, "task-FacePerception_events.json"))
        base_parameters = {"summary_name": "get_definition_summary", "summary_filename": "summarize_definitions"}
        cls.json_parms = json.dumps(base_parameters)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_do_op(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeDefinitionsOp(parms)
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")
        df_new = sum_op.do_op(dispatch, df, "subj2_run1", sidecar=self.json_path)
        self.assertEqual(200, len(df_new), " dataframe length is correct")
        self.assertEqual(10, len(df_new.columns), " has correct number of columns")
        self.assertIn(sum_op.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op.summary_name], DefinitionSummary)

    def test_summary(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeDefinitionsOp(parms)
        df = pd.read_csv(self.data_path, delimiter="\t", header=0, keep_default_na=False, na_values=",null")
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertEqual(200, len(df_new), " dataframe length is correct")
        self.assertEqual(10, len(df_new.columns), " has correct number of columns")
        self.assertIn(sum_op.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op.summary_name], DefinitionSummary)
        # print(str(dispatch.summary_dicts[sum_op.summary_name].get_text_summary()['Dataset']))

        cont = dispatch.summary_dicts
        context = cont.get("get_definition_summary", None)
        self.assertIsInstance(context, DefinitionSummary, "get_summary testing DefinitionSummary")
        summary1a = context.get_summary()
        self.assertIsInstance(summary1a, dict)
        self.assertIsInstance(summary1a["Dataset"], dict)
        text_summary1 = context.get_text_summary(individual_summaries=None)
        self.assertIsInstance(text_summary1, dict)
        self.assertIsInstance(text_summary1["Dataset"], str)

    def test_summary_errors(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeDefinitionsOp(parms)
        df = pd.DataFrame(
            {
                "HED": [
                    "(Def-expand/A1/1, (Action/1, Acceleration/5, Item-count/2))",
                    "(Def-expand/B2/3, (Action/3, Collection/animals, Acceleration/3))",
                    "(Def-expand/C3/5, (Action/5, Acceleration/5, Item-count/5))",
                    "(Def-expand/D4/7, (Action/7, Acceleration/7, Item-count/8))",
                    "(Def-expand/D5/7, (Action/7, Acceleration/7, Item-count/8, Event))",
                    "(Def-expand/A1/2, (Action/2, Age/5, Item-count/2))",
                    "(Def-expand/A1/3, (Action/3, Age/4, Item-count/3))",
                    # This could be identified, but fails due to the above raising errors
                    "(Def-expand/A1/4, (Action/4, Age/5, Item-count/2))",
                ]
            }
        )
        df_new = sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertIsInstance(df_new, pd.DataFrame)
        self.assertIn(sum_op.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op.summary_name], DefinitionSummary)
        # print(str(dispatch.summary_dicts[sum_op.summary_name].get_text_summary()['Dataset']))

    def test_ambiguous_def_errors(self):
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        parms = json.loads(self.json_parms)
        sum_op = SummarizeDefinitionsOp(parms)
        df = pd.DataFrame(
            {
                "HED": [
                    "(Def-expand/B2/3, (Action/3, Collection/animals, Acceleration/3))",
                ]
            }
        )
        sum_op.do_op(dispatch, dispatch.prep_data(df), "subj2_run1", sidecar=self.json_path)
        self.assertIn(sum_op.summary_name, dispatch.summary_dicts)
        self.assertIsInstance(dispatch.summary_dicts[sum_op.summary_name], DefinitionSummary)
        # print(str(dispatch.summary_dicts[sum_op.summary_name].get_text_summary()['Dataset']))
        cont = dispatch.summary_dicts
        context = cont.get("get_definition_summary", None)
        self.assertIsInstance(context, DefinitionSummary, "get_summary testing DefinitionSummary")
        summary1a = context.get_summary()
        self.assertIsInstance(summary1a, dict)


if __name__ == "__main__":
    unittest.main()
