import os
import shutil
import unittest
from hed.tools.remodeling.operations.base_context import BaseContext


class TestContext(BaseContext):

    def __init__(self):
        super().__init__("TestContext", "test", "test_context")
        self.summary_dict["data1"] = "test data 1"
        self.summary_dict["data2"] = "test data 2"

    def _get_summary_details(self, include_individual=True):
        summary = {"name": self.context_name}
        if include_individual:
            summary["more"] = "more stuff"
        return summary

    def _merge_all(self):
        return {"merged": self.context_name}

    def update_context(self, context_dict):
        pass


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        summary_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../../data/remodel_tests/temp'))
        os.makedirs(summary_dir, exist_ok=True)
        cls.summary_dir = summary_dir

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.summary_dir)

    def test_constructor(self):
        with self.assertRaises(TypeError) as context:
            BaseContext('apple', 'banana', 'pear')
        self.assertTrue(context.exception.args[0])

        test = TestContext()
        self.assertIsInstance(test, TestContext)

    def test_get_text_summary(self):
        test = TestContext()
        out1 = test.get_text_summary(separate_files=False, include_individual=False)
        self.assertIsInstance(out1, dict)
        self.assertTrue(out1["Dataset"])
        self.assertEqual(len(out1), 1)
        out2 = test.get_text_summary(include_individual=False, separate_files=True)
        self.assertIsInstance(out2, dict)
        self.assertIn('Dataset', out2)
        self.assertNotIn('Individual files', out2)
        self.assertEqual(out1['Dataset'], out2['Dataset'])
        out3 = test.get_text_summary(include_individual=True)
        self.assertIsInstance(out3, dict)
        self.assertIn('Dataset', out3)
        self.assertIn('Individual files', out3)
        self.assertEqual(out1['Dataset'], out3['Dataset'])
        self.assertIn('data1', out3['Individual files'])

    def test_save(self):
        test1 = TestContext()
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        test1.save(self.summary_dir, include_individual=True, separate_files=True)
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/'))
        file_list2 = os.listdir(dir_full)
        self.assertEqual(len(file_list2), 2)
        dir_ind = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/',
                                                "individual_summaries/"))
        file_list3 = os.listdir(dir_ind)
        self.assertEqual(len(file_list3), 2)
        test1.save(self.summary_dir, file_formats=['.json', '.tsv'], include_individual=False, separate_files=True)
        file_list4 = os.listdir(dir_full)
        self.assertEqual(len(file_list4), len(file_list2) + 1)
        file_list5 = os.listdir(dir_ind)
        self.assertEqual(len(file_list3), len(file_list5))
        test1.save(self.summary_dir, file_formats=['.json', '.tsv'], include_individual=True, separate_files=True)
        file_list6 = os.listdir(dir_full)
        self.assertEqual(len(file_list6), len(file_list4) + 1)
        file_list7 = os.listdir(dir_ind)
        self.assertEqual(len(file_list7), len(file_list5) + 2)


if __name__ == '__main__':
    unittest.main()
