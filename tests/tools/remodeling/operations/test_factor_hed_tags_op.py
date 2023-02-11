import os
import json
import unittest
from hed.tools.remodeling.operations.factor_hed_tags_op import FactorHedTagsOp
from hed.tools.remodeling.dispatcher import Dispatcher


class Test(unittest.TestCase):
    """

    """

    @classmethod
    def setUpClass(cls):
        path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodel_tests/'))
        cls.data_path = os.path.realpath(os.path.join(path, 'sub-002_task-FacePerception_run-1_events.tsv'))
        cls.json_path = os.path.realpath(os.path.join(path, 'task-FacePerception_events.json'))
        base_parameters = {
            "queries": ["sensory-event", "agent-action"],
            "query_names": [],
            "remove_types": [],
            "expand_context": False
        }
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_valid_no_query_names(self):
        # Test correct when all valid and no unwanted information
        parms = json.loads(self.json_parms)
        op = FactorHedTagsOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions='8.1.0')
        df_new = dispatch.get_data_file(self.data_path)
        pre_columns = len(list(df_new.columns))
        df_new = op.do_op(dispatch, dispatch.prep_data(df_new), 'run-01', sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), 200, "factor_hed_tags_op length is correct")
        self.assertEqual(len(df_new.columns), pre_columns + 2, "factor_hed_tags_op has correct number of columns")
        self.assertIn('query_0', list(df_new.columns))
        self.assertIn('query_1', list(df_new.columns))

    def test_valid_with_query_names(self):
        # Test correct when all valid and no unwanted information
        parms = json.loads(self.json_parms)
        parms["query_names"] = ["apple", "banana"]
        op = FactorHedTagsOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions='8.1.0')
        df_new = dispatch.get_data_file(self.data_path)
        pre_columns = len(list(df_new.columns))
        df_new = op.do_op(dispatch, dispatch.prep_data(df_new), 'run-01', sidecar=self.json_path)
        df_new = dispatch.post_proc_data(df_new)
        self.assertEqual(len(df_new), 200, "factor_hed_tags_op length is correct")
        self.assertEqual(len(df_new.columns), pre_columns + 2, "factor_hed_tags_op has correct number of columns")
        self.assertIn('apple', list(df_new.columns))
        self.assertIn('banana', list(df_new.columns))

    def test_invalid_query_names(self):
        # Duplicate query names
        parms = json.loads(self.json_parms)
        parms["query_names"] = ["apple", "apple"]
        with self.assertRaises(ValueError) as context:
            FactorHedTagsOp(parms)
        self.assertEqual(context.exception.args[0], 'DuplicateQueryNames')

        # Query names have wrong length
        parms = json.loads(self.json_parms)
        parms["query_names"] = ["apple", "banana", "pear"]
        with self.assertRaises(ValueError) as context:
            FactorHedTagsOp(parms)
        self.assertEqual(context.exception.args[0], 'QueryNamesLengthBad')

        # Query name already a column name
        parms = json.loads(self.json_parms)
        parms["query_names"] = ["face_type", "bananas"]
        op = FactorHedTagsOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions='8.1.0')
        df_new = dispatch.get_data_file(self.data_path)
        with self.assertRaises(ValueError) as context:
            op.do_op(dispatch, dispatch.prep_data(df_new), 'run-01', sidecar=self.json_path)
        self.assertEqual(context.exception.args[0], 'QueryNameAlreadyColumn')

    def test_sample(self):
        pass
        # sample_data = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
        #                    [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
        #                    [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
        #                    [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
        #                    [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
        #                    [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        #
        # sample_sidecar_path = os.path.realpath(os.path.join(path, 'task-stopsignal_acq-seq_events.json'))
        # sample_data = [[0.0776, 0.5083, 'baloney', 'n/a', 0.565, 'correct', 'right', 'female'],
        #                    [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
        #                    [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
        #                    [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
        #                    [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
        #                    [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        # sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
        #                       'response_accuracy', 'response_hand', 'sex']


if __name__ == '__main__':
    unittest.main()
