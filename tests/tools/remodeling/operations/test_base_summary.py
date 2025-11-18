import os
import shutil
import unittest
from hed.tools.remodeling.operations.base_summary import BaseSummary
from hed.tools.remodeling.operations.base_op import BaseOp


class TestOp(BaseOp):
    NAME = "test_op"
    PARAMS = {
        "operation": "test_summary_op",
        "required_parameters": {"summary_name": str, "summary_filename": str},
        "optional_parameters": {"append_timecode": bool},
    }

    SUMMARY_TYPE = "test_sum"

    def __init__(self, parameters):
        super().__init__(parameters)
        self.summary_name = parameters["summary_name"]
        self.summary_filename = parameters["summary_filename"]
        self.append_timecode = parameters.get("append_timecode", False)

    def do_op(self, dispatcher, df, name, sidecar=None):
        return df.copy()

    @staticmethod
    def validate_input_data(parameters):
        return []


class TestSummary(BaseSummary):

    def __init__(self, op):

        super().__init__(op)
        self.summary_dict["data1"] = "test data 1"
        self.summary_dict["data2"] = "test data 2"

    def get_details_dict(self, include_individual=True):
        summary = {"name": self.op.summary_name}
        if include_individual:
            summary["more"] = "more stuff"
        return summary

    def merge_all_info(self):
        return {"merged": self.op.summary_name}

    def update_summary(self, info_dict):
        pass


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        summary_dir = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/temp")
        )
        cls.summary_dir = summary_dir

    def test_constructor(self):
        op2 = TestOp({"summary_name": "test", "summary_filename": "test_context"})
        test = TestSummary(op2)
        self.assertIsInstance(test, TestSummary)

    def test_get_text_summary(self):
        op = TestOp({"summary_name": "test", "summary_filename": "test_context"})
        test = TestSummary(op)
        out1 = test.get_text_summary(individual_summaries="none")
        self.assertIsInstance(out1, dict)
        self.assertTrue(out1["Dataset"])
        self.assertEqual(len(out1), 1)
        out2 = test.get_text_summary(individual_summaries="consolidated")
        self.assertIsInstance(out2, dict)
        self.assertIn("Dataset", out2)
        self.assertNotIn("Individual files", out2)
        self.assertLess(len(out1["Dataset"]), len(out2["Dataset"]))
        out3 = test.get_text_summary(individual_summaries="separate")
        self.assertIsInstance(out3, dict)
        self.assertIn("Dataset", out3)
        self.assertIn("Individual files", out3)
        self.assertEqual(out1["Dataset"], out3["Dataset"])
        self.assertIn("data1", out3["Individual files"])

    def test_save_no_ind(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)
        os.makedirs(self.summary_dir)
        op = TestOp({"summary_name": "test", "summary_filename": "test_context"})
        test1 = TestSummary(op)
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        test1.save(self.summary_dir, individual_summaries="none")
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.op.summary_name + "/"))
        file_list2 = os.listdir(dir_full)
        self.assertEqual(len(file_list2), 1)
        basename = os.path.basename(file_list2[0])
        self.assertTrue(basename.startswith("test_context"))
        self.assertEqual(os.path.splitext(basename)[1], ".txt")
        shutil.rmtree(self.summary_dir)

    def test_save_consolidated(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)
        os.makedirs(self.summary_dir)
        op = TestOp({"summary_name": "test", "summary_filename": "test_context"})
        test1 = TestSummary(op)
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        dir_ind = os.path.realpath(os.path.join(self.summary_dir, test1.op.summary_name + "/", "individual_summaries/"))
        self.assertFalse(os.path.isdir(dir_ind))
        test1.save(self.summary_dir, file_formats=[".json", ".tsv"], individual_summaries="consolidated")
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.op.summary_name + "/"))
        file_list2 = os.listdir(dir_full)
        self.assertEqual(len(file_list2), 1)
        basename = os.path.basename(file_list2[0])
        self.assertTrue(basename.startswith("test_context"))
        self.assertEqual(os.path.splitext(basename)[1], ".json")
        shutil.rmtree(self.summary_dir)

    def test_save_separate(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)
        os.makedirs(self.summary_dir)
        op = TestOp({"summary_name": "test", "summary_filename": "test_context"})
        test1 = TestSummary(op)
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        test1.save(self.summary_dir, file_formats=[".json", ".tsv"], individual_summaries="separate")
        dir_ind = os.path.realpath(os.path.join(self.summary_dir, test1.op.summary_name + "/", "individual_summaries/"))
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.op.summary_name + "/"))
        self.assertTrue(os.path.isdir(dir_ind))
        file_list4 = os.listdir(dir_full)
        self.assertEqual(len(file_list4), 2)
        file_list5 = os.listdir(dir_ind)
        self.assertEqual(len(file_list5), 2)
        shutil.rmtree(self.summary_dir)


if __name__ == "__main__":
    unittest.main()
