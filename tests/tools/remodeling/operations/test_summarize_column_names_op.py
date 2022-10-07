import json
import os
import pandas as pd
import unittest
from hed.models import Sidecar
from hed.schema import load_schema_version
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.summarize_column_names_op import ColumnNameSummary, SummarizeColumnNamesOp


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

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnNamesOp(parms)
        self.assertEqual(sum_op.summary_type, "column_names", "constructor creates summary of right type")
        self.assertIsInstance(sum_op, SummarizeColumnNamesOp, "constructor creates an object of the correct type")

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
        dispatch = Dispatcher([], data_root=None, hed_versions=['8.1.0'])
        df = dispatch.get_data_file(events)
        sum_op = parsed_commands[0]
        df = sum_op.do_op(dispatch, df, os.path.basename(events), sidecar=sidecar)
        context_dict = dispatch.context_dict
        for key, item in context_dict.items():
            text_value = item.get_text_summary()
            self.assertTrue(text_value)
            json_value = item.get_summary(as_json=True)
            self.assertTrue(json_value)
        context1 = dispatch.context_dict['AOMIC_column_names']
        self.assertIsInstance(context1, ColumnNameSummary)
        self.assertEqual(len(context1.unique_headers), 1)

    def test_do_ops(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnNamesOp(parms)
        dispatch = Dispatcher([], data_root=None)
        df1 = pd.DataFrame(self.data1, columns=self.sample_columns1)
        df1a = pd.DataFrame(self.data1, columns=self.sample_columns1)
        df2 = pd.DataFrame(self.data1, columns=self.sample_columns2)
        sum_op.do_op(dispatch, df1, 'name1')
        context1 = dispatch.context_dict.get(parms['summary_name'], None)
        self.assertEqual(len(context1.unique_headers), 1, "do_ops context has a element after adding to summary")
        self.assertIsInstance(context1, ColumnNameSummary, "do_ops adds context of correct type")
        sum_op.do_op(dispatch, df1a, 'name2')
        self.assertEqual(len(context1.unique_headers), 1, "do_ops context does not change unique names if same added")
        self.assertIsInstance(context1, ColumnNameSummary, "do_ops adds context of correct type")
        sum_op.do_op(dispatch, df2, 'name3')
        self.assertEqual(len(context1.unique_headers), 2, "do_ops context changes unique names if new added")
        self.assertEqual(context1, dispatch.context_dict.get(parms['summary_name'], None),
                         "do_ops making sure the context is in the dispatcher")
        with self.assertRaises(ValueError):
            sum_op.do_op(dispatch, df2, 'name1')

    def test_get_summary(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnNamesOp(parms)
        dispatch = Dispatcher([], data_root=None)
        df1 = pd.DataFrame(self.data1, columns=self.sample_columns1)
        df1a = pd.DataFrame(self.data1, columns=self.sample_columns1)
        df2 = pd.DataFrame(self.data1, columns=self.sample_columns2)
        sum_op.do_op(dispatch, df1, 'name1')
        sum_op.do_op(dispatch, df1a, 'name2')
        sum_op.do_op(dispatch, df2, 'name3')
        summary_obj = dispatch.context_dict["columns"]
        self.assertIsInstance(summary_obj, ColumnNameSummary, "get_summary testing ColumnNameSummary")
        summary1 = summary_obj.get_summary()
        self.assertIsInstance(summary1, dict, "get_summary returns a dictionary by default")
        summary2 = summary_obj.get_summary(as_json=True)
        self.assertIsInstance(summary2, str, "get_summary returns a dictionary if json requested")
        summary3 = summary_obj.get_text_summary(verbose=False)
        self.assertIsInstance(summary3, str, "get_text_summary returns a str if verbose is False")
        summary4 = summary_obj.get_text_summary()
        self.assertIsInstance(summary4, str, "get_text_summary returns a str by default")
        self.assertTrue(len(summary4),
                        "get_text_summary returns string at least as much information with verbose as without.")
        summary5 = summary_obj.get_text_summary(verbose=True)
        self.assertIsInstance(summary5, str, "get_text_summary returns a str with verbose True")
        self.assertEqual(summary4, summary5, "get_text_summary string is same when verbose omitted or True")

    def test_context_get_name_group(self):
        parms = json.loads(self.json_parms)
        sum_op = SummarizeColumnNamesOp(parms)
        context = ColumnNameSummary(sum_op)
        context.update_context({"name": "name1", "column_names": self.sample_columns1})
        self.assertEqual(len(context.file_dict), 1, "update_context has first item at position 0")
        self.assertEqual(context.file_dict["name1"], 0, "update_context has first item at position 0")
        self.assertEqual(len(context.unique_headers), 1, "update_context has 1 unique item after first insertion")
        context.update_context({"name": "name1a", "column_names": self.sample_columns1})
        self.assertEqual(len(context.file_dict), 2, "update_context adds new names to file dictionary")
        self.assertEqual(context.file_dict["name1a"], 0, "update_context the unique header position is correct")
        self.assertEqual(len(context.unique_headers), 1, "update_context has 1 unique item after second insertion")
        context.update_context({"name": "name2", "column_names": self.sample_columns2})
        self.assertEqual(len(context.file_dict), 3, "update_context adds new names to file dictionary ")
        self.assertEqual(context.file_dict["name2"], 1, "update_context has new columns at position 1")
        self.assertEqual(len(context.unique_headers), 2, "update_context has 2 unique items after insertion")


if __name__ == '__main__':
    unittest.main()
