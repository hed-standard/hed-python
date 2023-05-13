import os
import shutil
import unittest
from hed.tools.remodeling.operations.base_context import BaseContext


class TestContext(BaseContext):

    def __init__(self):
        super().__init__("TestContext", "test", "test_context")
        self.summary_dict["data1"] = "test data 1"
        self.summary_dict["data2"] = "test data 2"

    def get_details_dict(self, include_individual=True):
        summary = {"name": self.context_name}
        if include_individual:
            summary["more"] = "more stuff"
        return summary

    def merge_all_info(self):
        return {"merged": self.context_name}

    def update_context(self, context_dict):
        pass


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        summary_dir = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                    '../../../data/remodel_tests/temp'))    
        cls.summary_dir = summary_dir

    def test_constructor(self):
        with self.assertRaises(TypeError) as context:
            BaseContext('apple', 'banana', 'pear')
        self.assertTrue(context.exception.args[0])

        test = TestContext()
        self.assertIsInstance(test, TestContext)

    def test_get_text_summary(self):
        test = TestContext()
        out1 = test.get_text_summary(individual_summaries="none")
        self.assertIsInstance(out1, dict)
        self.assertTrue(out1["Dataset"])
        self.assertEqual(len(out1), 1)
        out2 = test.get_text_summary(individual_summaries="consolidated")
        self.assertIsInstance(out2, dict)
        self.assertIn('Dataset', out2)
        self.assertNotIn('Individual files', out2)
        self.assertLess(len(out1['Dataset']), len(out2['Dataset']))
        out3 = test.get_text_summary(individual_summaries="separate")
        self.assertIsInstance(out3, dict)
        self.assertIn('Dataset', out3)
        self.assertIn('Individual files', out3)
        self.assertEqual(out1['Dataset'], out3['Dataset'])
        self.assertIn('data1', out3['Individual files'])

    def test_save_no_ind(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)
        os.makedirs(self.summary_dir)
        test1 = TestContext()
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        test1.save(self.summary_dir, individual_summaries="none")
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/'))
        file_list2 = os.listdir(dir_full)
        self.assertEqual(len(file_list2), 1)
        basename = os.path.basename(file_list2[0])
        self.assertTrue(basename.startswith('test_context'))
        self.assertEqual(os.path.splitext(basename)[1], '.txt')
        shutil.rmtree(self.summary_dir)

    def test_save_consolidated(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)
        os.makedirs(self.summary_dir)
        test1 = TestContext()
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        dir_ind = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/',
                                                "individual_summaries/"))
        self.assertFalse(os.path.isdir(dir_ind))
        test1.save(self.summary_dir, file_formats=['.json', '.tsv'], individual_summaries="consolidated")
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/'))
        file_list2 = os.listdir(dir_full)
        self.assertEqual(len(file_list2), 1)
        basename = os.path.basename(file_list2[0])
        self.assertTrue(basename.startswith('test_context'))
        self.assertEqual(os.path.splitext(basename)[1], '.json')
        shutil.rmtree(self.summary_dir)
        
    def test_save_separate(self):
        if os.path.isdir(self.summary_dir):
            shutil.rmtree(self.summary_dir)
        os.makedirs(self.summary_dir)
        test1 = TestContext()
        file_list1 = os.listdir(self.summary_dir)
        self.assertFalse(file_list1)
        test1.save(self.summary_dir, file_formats=['.json', '.tsv'], individual_summaries="separate")
        dir_ind = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/',
                                                "individual_summaries/"))
        dir_full = os.path.realpath(os.path.join(self.summary_dir, test1.context_name + '/'))
        self.assertTrue(os.path.isdir(dir_ind))
        file_list4 = os.listdir(dir_full)
        self.assertEqual(len(file_list4), 2)
        file_list5 = os.listdir(dir_ind)
        self.assertEqual(len(file_list5), 2)
        shutil.rmtree(self.summary_dir)


if __name__ == '__main__':
    unittest.main()
