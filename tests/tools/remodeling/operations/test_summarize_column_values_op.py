import json
import os
import pandas as pd
import unittest
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_column_values_op import \
    ColumnValueSummaryContext, SummarizeColumnValuesOp
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sample_data = [[0.0776, 0.5083, 'go', 'n/a', 0.565, 'correct', 'right', 'female'],
                           [5.5774, 0.5083, 'unsuccesful_stop', 0.2, 0.49, 'correct', 'right', 'female'],
                           [9.5856, 0.5084, 'go', 'n/a', 0.45, 'correct', 'right', 'female'],
                           [13.5939, 0.5083, 'succesful_stop', 0.2, 'n/a', 'n/a', 'n/a', 'female'],
                           [17.1021, 0.5083, 'unsuccesful_stop', 0.25, 0.633, 'correct', 'left', 'male'],
                           [21.6103, 0.5083, 'go', 'n/a', 0.443, 'correct', 'left', 'male']]
        cls.sample_columns = ['onset', 'duration', 'trial_type', 'stop_signal_delay', 'response_time',
                              'response_accuracy', 'response_hand', 'sex']
        base_parameters = {
            "summary_name": "test summary",
            "summary_filename": "column_values_summary",
            "skip_columns": [],
            "value_columns": ['onset', 'response_time']
        }

        cls.json_parms = json.dumps(base_parameters)
        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                      '../../../data/remodel_tests'))

    @classmethod
    def tearDownClass(cls):
        pass

    def get_dfs(self, op, name, dispatch):
        df = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        df_new = op.do_op(dispatch, dispatch.prep_data(df), name)
        return df, dispatch.post_proc_data(df_new)

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnValuesOp(parms)
        self.assertIsInstance(sum_op, SummarizeColumnValuesOp, "constructor creates an object of the correct type")

    def test_do_ops(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnValuesOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions='8.1.0')
        self.get_dfs(sum_op, 'name1', dispatch)
        context1 = dispatch.context_dict.get(parms['summary_name'], None)
        summary1 = context1.summary_dict['name1']
        cat_len = len(summary1.categorical_info)
        self.assertEqual(cat_len, len(self.sample_columns) - 2,
                         'do_ops if all columns are categorical summary has same number of columns as df')
        self.get_dfs(sum_op, 'name2', dispatch)
        self.assertEqual(cat_len, len(self.sample_columns) - 2,
                         "do_ops updating does not change number of categorical columns.")
        context = dispatch.context_dict['test summary']
        self.assertEqual(len(context.summary_dict), 2)

    def test_get_summary(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnValuesOp(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions='8.1.0')
        self.get_dfs(sum_op, 'name1', dispatch)

        cont = dispatch.context_dict
        context1 = cont.get("test_summary", None)
        # print("to here")
        # self.assertIsInstance(context1, ColumnValueSummaryContext, "get_summary testing ColumnValueSummary")
        # summary1 = context1.get_summary()
        # self.assertIsInstance(summary1, dict, "get_summary returns a dictionary by default")
        # summary1a = context1.get_summary(as_json=True)
        # self.assertIsInstance(summary1a, str, "get_summary returns a dictionary if json requested")
        # text_summary = context1.get_text_summary(include_individual=True)
        # print(text_summary)
        # self.assertIsInstance(text_summary, str)
        # self.get_dfs(sum_op, 'name2', dispatch)
        # self.get_dfs(sum_op, 'name3', dispatch)
        # context2 = dispatch.context_dict.get(parms['summary_name'], None)
        # summary2 = context2.get_summary()
        # self.assertIsInstance(summary2, dict)
        # text_summary2 = context2.get_text_summary(include_individual=True)
        # self.assertIsInstance(text_summary2, str)

    def test_summary_op(self):
        events = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                               '../../../data/remodel_tests/aomic_sub-0013_excerpt_events.tsv'))
        column_summary_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                               '../../../data/remodel_tests/aomic_sub-0013_summary_all_rmdl.json'))
        with open(column_summary_path, 'r') as fp:
            parms = json.load(fp)
        parsed_commands, errors = Dispatcher.parse_operations(parms)
        dispatch = Dispatcher([], data_root=None, backup_name=None, hed_versions=['8.1.0'])
        df = dispatch.get_data_file(events)
        old_len = len(df)
        sum_op = parsed_commands[1]
        df = sum_op.do_op(dispatch, dispatch.prep_data(df), os.path.basename(events))
        self.assertEqual(len(df), old_len)
        context_dict = dispatch.context_dict
        for key, item in context_dict.items():
            text_value = item.get_text_summary()
            self.assertTrue(text_value)
            json_value = item.get_summary(as_json=True)
            self.assertTrue(json_value)

    # def test_temp(self):
    #     data_path = 'H:/HEDExamples/hed-examples/datasets/eeg_ds003654s_hed'
    #     json_path = os.path.realpath(os.path.join(data_path, 'task-FacePerception_events.json'))
    #     remodel_list = [{
    #         "operation": "summarize_column_values",
    #         "description": "Summarize column values.",
    #         "parameters": {
    #             "summary_name": "column_values_summary",
    #             "summary_filename": "column_values_summary",
    #             "skip_columns": ["onset", "duration", "sample"],
    #             "value_columns": ["trial", "stim_file"]
    #         }
    #     }]
    #     file_list = get_file_list(data_path, name_suffix='events', extensions=['.tsv'], exclude_dirs=['stimuli'])
    #     dispatch = Dispatcher(remodel_list, data_root=None, backup_name=None, hed_versions=['8.1.0'])
    #     for file in file_list:
    #         dispatch.run_operations(file)
    #     context_dict = dispatch.context_dict.get("column_values_summary")
    #     text_summary = context_dict.get_text_summary()
    #     #print(text_summary)
    #     summary = context_dict.get_summary(as_json=True)
    #     print(summary)


if __name__ == '__main__':
    unittest.main()
