import json
import os
import unittest
from hed.tools.analysis.column_name_summary import ColumnNameSummary
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_column_names_op import ColumnNameSummaryContext, SummarizeColumnNamesOp


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data'))
        cls.sample_columns1 = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time']
        cls.sample_columns2 = ['trial_type', 'onset', 'duration', 'stop_signal_delay', 'response_time']
        cls.data1 = [[3.0, 0.5, 'go', 0.2, 1.3], [5.0, 0.5, 'go', 0.2, 1.3]]
        base_parameters = {
            "summary_name": "columns",
            "summary_filename": "column_name_summary"
        }
        cls.json_parms = json.dumps(base_parameters)
        cls.events_path = \
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodel_tests/aomic_sub-0013_excerpt_events.tsv'))
        cls.sidecar_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                         '../../../data/remodel_tests/aomic_sub-0013_events.json'))
        cls.model_path = \
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodel_tests/aomic_sub-0013_summary_all_rmdl.json'))

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnNamesOp(parms)
        self.assertIsInstance(sum_op, SummarizeColumnNamesOp, "constructor creates an object of the correct type")

    def test_summary_op(self):
        with open(self.model_path, 'r') as fp:
            parms = json.load(fp)
        parsed_commands, errors = Dispatcher.parse_operations(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions='8.1.0')
        df = dispatch.get_data_file(self.events_path)
        df = dispatch.prep_events(df)

        old_len = len(df)
        sum_op = parsed_commands[0]
        df = sum_op.do_op(dispatch, df, 'run-02')
        df = sum_op.do_op(dispatch, df, 'run-01')
        self.assertEqual(len(df), old_len)
        df1 = df.drop(labels='onset', axis=1)
        sum_op.do_op(dispatch, df1, 'run-03')
        this_context = dispatch.context_dict[sum_op.summary_name]
        for key, item in this_context.summary_dict.items():
            summary = item.get_summary()
            self.assertIsInstance(summary, dict)
            json_value = item.get_summary(as_json=True)
            self.assertIsInstance(json_value, str)
            new_summary = json.loads(json_value)
            self.assertIsInstance(new_summary, dict)
        merged1 = this_context._merge_all()
        self.assertIsInstance(merged1, ColumnNameSummary)
        self.assertEqual(len(merged1.file_dict), 3)
        self.assertEqual(len(merged1.unique_headers), 2)
        with self.assertRaises(ValueError) as except_context:
            sum_op.do_op(dispatch, df, 'run-03')
        self.assertEqual(except_context.exception.args[0], 'FileHasChangedColumnNames')


if __name__ == '__main__':
    unittest.main()
