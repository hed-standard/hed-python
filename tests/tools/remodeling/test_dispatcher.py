import os
import json
import shutil
import unittest
import pandas as pd
import numpy as np
import zipfile
from hed.errors.exceptions import HedFileError
from hed.tools.remodeling.dispatcher import Dispatcher
from hed.tools.remodeling.operations.base_op import BaseOp
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        data_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/remodel_tests"))
        cls.sample_data = [
            [0.0776, 0.5083, "go", "n/a", 0.565, "correct", "right", "female"],
            [5.5774, 0.5083, "unsuccesful_stop", 0.2, 0.49, "correct", "right", "female"],
            [9.5856, 0.5084, "go", "n/a", 0.45, "correct", "right", "female"],
            [13.5939, 0.5083, "succesful_stop", 0.2, "n/a", "n/a", "n/a", "female"],
            [17.1021, 0.5083, "unsuccesful_stop", 0.25, 0.633, "correct", "left", "male"],
            [21.6103, 0.5083, "go", "n/a", 0.443, "correct", "left", "male"],
        ]
        cls.sample_columns = [
            "onset",
            "duration",
            "trial_type",
            "stop_signal_delay",
            "response_time",
            "response_accuracy",
            "response_hand",
            "sex",
        ]
        cls.data_path = data_path
        cls.file_path = os.path.realpath(os.path.join(data_path, "aomic_sub-0013_excerpt_events.tsv"))
        cls.test_zip_back1 = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../../data/remodel_tests/test_root_back1.zip"
        )
        cls.test_root_back1 = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../../data/remodel_tests/test_root_back1"
        )
        cls.summarize_model = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../../data/remodel_tests/test_root1_summarize_column_value_rmdl.json"
        )
        cls.summarize_excerpt = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "../../data/remodel_tests/aomic_sub-0013_before_after_reorder_rmdl.json",
        )

    def setUp(self):
        with zipfile.ZipFile(self.test_zip_back1, "r") as zip_ref:
            zip_ref.extractall(self.data_path)

    def tearDown(self):
        if os.path.exists(self.test_root_back1):
            shutil.rmtree(self.test_root_back1)

    def test_dispatcher_constructor(self):
        model_path1 = os.path.join(self.data_path, "simple_reorder_rmdl.json")
        with open(model_path1) as fp:
            model1 = json.load(fp)
        dispatch = Dispatcher(model1)
        self.assertEqual(
            len(dispatch.parsed_ops), len(model1), "dispatcher operation list should have one item for each operation"
        )

    def test_constructor_empty_operations(self):
        disp = Dispatcher([], data_root=None, backup_name=None, hed_versions=["8.1.0"])
        self.assertIsInstance(disp, Dispatcher, "")
        self.assertFalse(disp.parsed_ops, "constructor empty operations list has empty parsed ops")

    def test_get_data_file(self):
        model_path1 = os.path.join(self.data_path, "simple_reorder_rmdl.json")
        with open(model_path1) as fp:
            model1 = json.load(fp)
        sidecar_file = os.path.realpath(os.path.join(self.data_path, "task-FacePerception_events.json"))
        dispatch = Dispatcher(model1)
        with self.assertRaises(HedFileError) as context:
            dispatch.get_data_file(sidecar_file)
        self.assertEqual(context.exception.code, "BadDataFile")

    def test_get_summary_save_dir(self):
        model_path1 = os.path.join(self.data_path, "simple_reorder_rmdl.json")
        with open(model_path1) as fp:
            model1 = json.load(fp)
        dispatch1 = Dispatcher(model1, data_root=self.test_root_back1, backup_name="back1")
        summary_path = dispatch1.get_summary_save_dir()
        self.assertEqual(
            summary_path,
            os.path.realpath(os.path.join(self.test_root_back1, "derivatives", Dispatcher.REMODELING_SUMMARY_PATH)),
        )
        dispatch2 = Dispatcher(model1)
        with self.assertRaises(HedFileError) as context:
            dispatch2.get_summary_save_dir()
        self.assertEqual(context.exception.code, "NoDataRoot")

    def test_parse_operation_list(self):
        test = [
            {
                "operation": "remove_rows",
                "parameters": {"column_name": "trial_type", "remove_values": ["succesful_stop", "unsuccesful_stop"]},
            },
            {"operation": "remove_rows", "parameters": {"column_name": "response_time", "remove_values": ["n/a"]}},
        ]
        dispatch = Dispatcher(test)
        parsed_ops = dispatch.parsed_ops
        self.assertEqual(len(parsed_ops), len(test), "dispatch has a operation for each item in operation list")
        for item in parsed_ops:
            self.assertIsInstance(item, BaseOp)

    def test_run_operations(self):
        model_path1 = os.path.join(self.data_path, "simple_reorder_rmdl.json")
        with open(model_path1) as fp:
            model1 = json.load(fp)
        dispatch = Dispatcher(model1)
        df_test = pd.DataFrame(self.sample_data, columns=self.sample_columns)
        num_test_rows = len(df_test)
        df_test_values = df_test.to_numpy()
        df_new = dispatch.run_operations(self.file_path)
        reordered_columns = ["onset", "duration", "trial_type", "response_time"]
        self.assertTrue(reordered_columns == list(df_new.columns), "run_operations resulting df should have correct columns")
        self.assertTrue(list(df_test.columns) == self.sample_columns, "run_operations did not change the input df columns")
        self.assertEqual(len(df_test), num_test_rows, "run_operations did not change the input df rows")
        self.assertFalse(
            np.array_equal(df_test_values, df_test.to_numpy), "run_operations does not change the values in the input df"
        )
        self.assertEqual(len(df_new), num_test_rows, "run_operations did not change the number of output rows")
        self.assertEqual(
            len(dispatch.parsed_ops), len(model1), "dispatcher operation list should have one item for each operation"
        )

    def test_run_operations_hed(self):
        events_path = os.path.realpath(os.path.join(self.data_path, "sub-002_task-FacePerception_run-1_events.tsv"))
        sidecar_path = os.path.realpath(os.path.join(self.data_path, "task-FacePerception_events.json"))
        op_list = [
            {
                "operation": "factor_hed_type",
                "description": "Test run",
                "parameters": {"type_tag": "Condition-variable", "type_values": []},
            }
        ]
        dispatch = Dispatcher(op_list, hed_versions=["8.1.0"])
        df = dispatch.run_operations(events_path, sidecar=sidecar_path, verbose=False)
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 200)
        self.assertEqual(len(df.columns), 17)
        self.assertIn("key-assignment.right-sym-cond", df.columns)

    def test_save_summaries(self):
        with open(self.summarize_model) as fp:
            model1 = json.load(fp)
        dispatch1 = Dispatcher(model1, data_root=self.test_root_back1, backup_name="back1")
        file_list = get_file_list(
            self.test_root_back1, name_suffix="events", extensions=[".tsv"], exclude_dirs=["derivatives"]
        )
        for file in file_list:
            dispatch1.run_operations(file)
        summary_path = dispatch1.get_summary_save_dir()
        self.assertFalse(os.path.exists(summary_path))
        dispatch1.save_summaries()
        self.assertTrue(os.path.exists(summary_path))
        file_list1 = os.listdir(summary_path)
        self.assertEqual(2, len(file_list1), "save_summaries creates correct number of summary files when run.")
        dispatch1.save_summaries(save_formats=[])
        dir_list2 = os.listdir(summary_path)
        self.assertEqual(2, len(dir_list2), "save both summaries")
        path_before = os.path.realpath(os.path.join(summary_path, "test summary_values_before"))
        file_list2 = [f for f in os.listdir(path_before) if os.path.isfile(os.path.join(path_before, f))]
        self.assertEqual(2, len(file_list2))
        dispatch1.save_summaries(task_name="task-blech")
        file_list3 = [f for f in os.listdir(path_before) if os.path.isfile(os.path.join(path_before, f))]
        self.assertEqual(4, len(file_list3), "saving with task has different name than without")

    def test_get_summaries(self):
        with open(self.summarize_excerpt) as fp:
            model1 = json.load(fp)
        dispatch = Dispatcher(model1)
        df_new = dispatch.run_operations(self.file_path)
        self.assertIsInstance(df_new, pd.DataFrame)
        summaries = dispatch.get_summaries(file_formats=[".txt", ".json", ".tsv"])
        self.assertIsInstance(summaries, list)
        # self.assertEqual(len(summaries), 4)


if __name__ == "__main__":
    unittest.main()
