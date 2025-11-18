import os
import json
import unittest
from hed.tools.remodeling.operations.factor_hed_tags_op import FactorHedTagsOp
from hed.tools.remodeling.dispatcher import Dispatcher


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/"))
        cls.data_path = os.path.realpath(os.path.join(path, "sub-002_task-FacePerception_run-1_events.tsv"))
        cls.json_path = os.path.realpath(os.path.join(path, "task-FacePerception_events.json"))
        base_parameters = {
            "queries": ["sensory-event", "agent-action"],
            "query_names": [],
            "remove_types": [],
            "expand_context": False,
            "replace_defs": True,
        }
        cls.json_params = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_valid_no_query_names(self):
        # Test correct when all valid and no unwanted information
        params = json.loads(self.json_params)
        op = FactorHedTagsOp(params)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        df_new = dispatch.get_data_file(self.data_path)
        pre_columns = len(list(df_new.columns))
        df_new = op.do_op(dispatch, dispatch.prep_data(df_new), "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), 200, "factor_hed_tags_op length is correct")
        self.assertEqual(len(df_new.columns), pre_columns + 2, "factor_hed_tags_op has correct number of columns")
        self.assertIn("query_0", list(df_new.columns))
        self.assertIn("query_1", list(df_new.columns))

    def test_valid_with_query_names(self):
        # Test correct when all valid and no unwanted information
        params = json.loads(self.json_params)
        params["query_names"] = ["apple", "banana"]
        op = FactorHedTagsOp(params)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        df_new = dispatch.get_data_file(self.data_path)
        pre_columns = len(list(df_new.columns))
        df_new = op.do_op(dispatch, dispatch.prep_data(df_new), "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), 200, "factor_hed_tags_op length is correct")
        self.assertEqual(len(df_new.columns), pre_columns + 2, "factor_hed_tags_op has correct number of columns")
        self.assertIn("apple", list(df_new.columns))
        self.assertIn("banana", list(df_new.columns))

    def test_invalid_query_names(self):
        # Duplicate query names
        params = json.loads(self.json_params)
        params["query_names"] = ["apple", "apple"]
        with self.assertRaises(ValueError) as context:
            FactorHedTagsOp(params)
        self.assertEqual(context.exception.args[0], "FactorHedTagInvalidQueries")

        # Query names have wrong length
        params = json.loads(self.json_params)
        params["query_names"] = ["apple", "banana", "pear"]
        with self.assertRaises(ValueError) as context:
            FactorHedTagsOp(params)
        self.assertEqual(context.exception.args[0], "FactorHedTagInvalidQueries")

        # Query name already a column name
        params = json.loads(self.json_params)
        params["query_names"] = ["face_type", "bananas"]
        op = FactorHedTagsOp(params)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        df_new = dispatch.get_data_file(self.data_path)
        with self.assertRaises(ValueError) as context:
            op.do_op(dispatch, dispatch.prep_data(df_new), "run-01", sidecar=self.json_path)
        self.assertEqual(context.exception.args[0], "QueryNameAlreadyColumn")

    def test_no_expand_context(self):
        # Setup for testing remove types
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        params = json.loads(self.json_params)
        params["expand_context"] = False
        params["queries"] = ["Def/Famous-face-cond", "Def/Right-sym-cond", "Def/Initialize-recording"]
        df = dispatch.get_data_file(self.data_path)
        df = dispatch.prep_data(df)
        df_columns = len(list(df.columns))
        total_famous = (df["face_type"] == "famous_face").sum()

        # If Defs are replaced and Condition-variable not removed, should not find Def/Famous-face-cond
        params["replace_defs"] = True
        params["remove_types"] = []
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertFalse(df_new["query_0"].sum())
        self.assertFalse(df_new["query_1"].sum())
        self.assertFalse(df_new["query_2"].sum())

        # If Defs are not replaced and Condition-variable not removed, should find Def/Famous-face-cond
        params["replace_defs"] = False
        params["remove_types"] = []
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertEqual(df_new["query_0"].sum(), total_famous)
        self.assertEqual(df_new["query_1"].sum(), 1)
        self.assertEqual(df_new["query_2"].sum(), 1)

        # If Defs are not replaced and Condition-variable is removed, should not find Def/Famous-face-cond
        params["replace_defs"] = False
        params["remove_types"] = ["Condition-variable", "Task"]
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertFalse(df_new["query_0"].sum())
        self.assertFalse(df_new["query_1"].sum())
        self.assertEqual(df_new["query_2"].sum(), 1)

        # If Defs are not replaced and Condition-variable is removed, should not find Def/Famous-face-cond
        params["replace_defs"] = True
        params["remove_types"] = ["Condition-variable", "Task"]
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertFalse(df_new["query_0"].sum())
        self.assertFalse(df_new["query_1"].sum())
        self.assertFalse(df_new["query_2"].sum())

    def test_expand_context(self):
        # Setup for testing remove types
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions="8.1.0")
        params = json.loads(self.json_params)
        params["expand_context"] = True
        params["queries"] = ["Def/Famous-face-cond", "Def/Right-sym-cond", "Def/Initialize-recording"]
        df = dispatch.get_data_file(self.data_path)
        df = dispatch.prep_data(df)
        df_columns = len(list(df.columns))
        total_famous = (df["face_type"] == "famous_face").sum()

        # If Defs are replaced and Condition-variable not removed, should not find Def/Famous-face-cond
        params["replace_defs"] = True
        params["remove_types"] = []
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertFalse(df_new["query_0"].sum())
        self.assertFalse(df_new["query_1"].sum())
        self.assertFalse(df_new["query_2"].sum())

        # If Defs are not replaced and Condition-variable not removed, should find Def/Famous-face-cond
        params["replace_defs"] = False
        params["remove_types"] = []
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertEqual(df_new["query_0"].sum(), total_famous)
        self.assertEqual(df_new["query_1"].sum(), len(df))
        self.assertEqual(df_new["query_2"].sum(), len(df))

        # If Defs are not replaced and Condition-variable is removed, should not find Def/Famous-face-cond
        params["replace_defs"] = False
        params["remove_types"] = ["Condition-variable", "Task"]
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertFalse(df_new["query_0"].sum())
        self.assertFalse(df_new["query_1"].sum())
        self.assertEqual(df_new["query_2"].sum(), len(df))

        # If Defs are not replaced and Condition-variable is removed, should not find Def/Famous-face-cond
        params["replace_defs"] = True
        params["remove_types"] = ["Condition-variable", "Task"]
        op = FactorHedTagsOp(params)
        df_new = op.do_op(dispatch, df, "run-01", sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), len(df))
        self.assertEqual(len(df_new.columns), df_columns + 3)
        self.assertFalse(df_new["query_0"].sum())
        self.assertFalse(df_new["query_1"].sum())
        self.assertFalse(df_new["query_2"].sum())


if __name__ == "__main__":
    unittest.main()
