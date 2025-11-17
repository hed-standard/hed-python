import os
import unittest
from hed.tools.remodeling.operations.factor_hed_type_op import FactorHedTypeOp
from hed.tools.remodeling.dispatcher import Dispatcher


class Test(unittest.TestCase):
    """

    TODO: Test when no factor names and values are given.

    """

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/"))
        data_path = os.path.realpath(os.path.join(path, "sub-002_task-FacePerception_run-1_events.tsv"))
        cls.json_path = os.path.realpath(os.path.join(path, "task-FacePerception_events.json"))
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        cls.df_test = dispatch.prep_data(dispatch.get_data_file(data_path))
        cls.dispatch = dispatch

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.base_parameters = {"type_tag": "Condition-variable", "type_values": []}

    def test_valid(self):
        # Test correct when all valid and no unwanted information
        op = FactorHedTypeOp(self.base_parameters)
        df_new = op.do_op(self.dispatch, self.df_test, "subj2_run1", sidecar=self.json_path)
        self.assertEqual(len(df_new), 200, "factor_hed_type_op length is correct")
        self.assertEqual(len(df_new.columns), 17, "factor_hed_type_op has correct number of columns")

    def test_valid_specific_column(self):
        parms = self.base_parameters
        parms["type_values"] = ["key-assignment"]
        op = FactorHedTypeOp(parms)
        df_new = op.do_op(self.dispatch, self.df_test, "run-01", sidecar=self.json_path)
        df_new = self.dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), 200, "factor_hed_type_op length is correct when type_values specified")
        self.assertEqual(
            len(df_new.columns), 11, "factor_hed_type_op has correct number of columns when type_values specified"
        )


if __name__ == "__main__":
    unittest.main()
