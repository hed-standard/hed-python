import os
import json
import pandas as pd
import numpy as np
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.split_event_op import SplitEventOp


class Test(unittest.TestCase):

    """

    TODO: only the anchor column existing has been tested so far.
        - test new anchor column
        - test not adding trial numbers
        - test deleting parent events

    """
    @classmethod
    def setUpClass(cls):
        cls.events_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                        '../../../data/remodel_tests/sub-0013_task-stopsignal_acq-seq_events.tsv'))
        cls.model1_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                        '../../../data/remodel_tests/only_splitevents_rmdl.json'))
        cls.sample_data = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                           [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                           [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                           [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                           [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]

        cls.split = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
                     [0.6426, 0, 'response', 'n/a', 'n/a', 'correct', 'right', 'female'],
                     [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                     [5.7774, 0.5, 'stop_signal', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'],
                     [6.0674, 0, 'response', 'n/a', 'n/a', 'correct', 'right', 'female'],
                     [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                     [10.0356, 0, 'response', 'n/a', 'n/a', 'correct', 'right', 'female'],
                     [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                     [13.7939, 0.5, 'stop_signal', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'],
                     [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                     [17.3521, 0.5, 'stop_signal', 'n/a', 'n/a', 'n/a', 'n/a', 'n/a'],
                     [17.7351, 0, 'response', 'n/a', 'n/a', 'correct', 'left', 'male'],
                     [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male'],
                     [22.0533, 0, 'response', 'n/a', 'n/a', 'correct', 'left', 'male']]
        cls.sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                              'response_accuracy', 'response_hand', 'sex']
        cls.split_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                             'response_accuracy', 'response_hand', 'sex']
        base_parameters = {
            "anchor_column": "trial_type",
            "new_events": {
                "response": {
                    "onset_source": ["response_time"],
                    "duration": [0],
                    "copy_columns": ["response_accuracy", "response_hand", "sex"]
                },
                "stop_signal": {
                    "onset_source": ["stop_signal_delay"],
                    "duration": [0.5],
                    "copy_columns": []
                }
            },
            "remove_parent_event": False
        }
        cls.json_parms = json.dumps(base_parameters)
        cls.dispatch = Dispatcher([])

    @classmethod
    def tearDownClass(cls):
        pass

    def test_split_event_valid_existing_column(self):
        # Test when existing column is used as anchor event
        parms = json.loads(self.json_parms)
        op = SplitEventOp(parms)
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_check = pd.DataFrame(self.split, columns=self.split_columns)
        df_test = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(self.dispatch, df_test, name="sample_data")
        df_new = df_new.fillna('n/a')

        # Test that df_new has the right values
        self.assertEqual(len(df_check), len(df_new),
                         "split_event should have expected number of rows when existing column anchor")
        self.assertEqual(len(df_new.columns), len(self.split_columns),
                         "split_event should have expected number of columns when existing column anchor")
        self.assertTrue(list(df_new.columns) == list(self.split_columns),
                        "split_event should have the expected columns when existing column anchor")

        # Must check individual columns because of round-off on the numeric columns
        for col in list(df_new.columns):
            new = df_new[col].to_numpy()
            check = df_check[col].to_numpy()
            if np.array_equal(new, check):
                continue
            self.assertTrue(np.allclose(new, check, equal_nan=True))

        # Test that df has not been changed by the op
        self.assertTrue(list(df.columns) == list(df_test.columns),
                        "split_event should not change the input df columns when existing column anchor")
        self.assertTrue(np.array_equal(df.to_numpy(), df_test.to_numpy()),
                        "split_event should not change the input df values when existing column anchor")

    def test_split_event_from_files(self):
        # Test when existing column is used as anchor event
        df = pd.read_csv(self.events_path, delimiter='\t', header=0, dtype=str, keep_default_na=False, na_values=None)
        with open(self.model1_path) as fp:
            operation_list = json.load(fp)
        operations, errors = Dispatcher.parse_operations(operation_list)
        self.assertFalse(errors, 'split_event should not give errors if operation is correct')
        dispatch = Dispatcher(operation_list)
        df = dispatch.prep_events(df)
        for operation in dispatch.parsed_ops:
            df_new = operation.do_op(dispatch, df, "Name")
        df_new = df_new.fillna('n/a')
        df_check = pd.read_csv(self.events_path, delimiter='\t', header=0, dtype=str,
                               keep_default_na=False, na_values=None)
        # parms = json.loads(self.json_parms)
        # op = SplitEventOp(parms)
        # df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        # df_check = pd.DataFrame(self.split, columns=self.split_columns)
        # df_test = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        # df_new = op.do_op(self.dispatch, df_test, name="sample_data")
        # df_new = df_new.fillna('n/a')
        #
        # Test that this
        self.assertEqual(len(df_check), len(df),
                         "split_event should not change the length of the original dataframe")
        self.assertEqual(len(df_check.columns), len(df.columns),
                         "split_event should change the number of columns of the original dataframe")

if __name__ == '__main__':
    unittest.main()
