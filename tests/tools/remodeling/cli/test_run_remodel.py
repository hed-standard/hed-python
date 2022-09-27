import os
import shutil
import unittest
import zipfile
from hed.tools.remodeling.backup_manager import BackupManager
import hed.tools.remodeling.cli.run_remodel as cli_remodel
from hed.tools.util.data_util import get_new_dataframe


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        file_list = ['top_level.tsv', 'sub1/sub1_events.tsv', 'sub2/sub2_events.tsv', 'sub2/sub2_next_events.tsv']
        cls.file_list = file_list
        cls.extract_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../data/remodeling')
        test_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../data/remodeling/test_root')
        cls.test_root = test_root
        cls.test_paths = [os.path.join(test_root, file) for file in file_list]
        cls.test_zip = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                    '../../../data/remodeling/test_root.zip')

        test_root_back1 = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                       '../../../data/remodeling/test_root_back1')
        cls.test_root_back1 = test_root_back1
        cls.test_paths_back1 = [os.path.join(test_root_back1, file) for file in file_list]
        cls.test_zip_back1 = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodeling/test_root_back1.zip')

        test_root_bad = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                     '../../../data/remodeling/test_root_bad')
        cls.test_root_bad = test_root_bad
        cls.test_root_bad_backups = os.path.join(test_root_bad, BackupManager.RELATIVE_BACKUP_LOCATION)
        cls.test_paths_bad = [os.path.join(test_root_bad, file) for file in file_list]
        cls.test_zip_bad = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../../data/remodeling/test_root_bad.zip')
        cls.model_rename_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodeling/test_root1_rename_rmdl.json')
        cls.model_summary_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                              '../../../data/remodeling/test_root1_summarize_column_value_rmdl.json')

    def setUp(self):
        with zipfile.ZipFile(self.test_zip, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_back1, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_bad, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)

    def tearDown(self):
        shutil.rmtree(self.test_root)
        shutil.rmtree(self.test_root_back1)
        shutil.rmtree(self.test_root_bad)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_main_rename_columns(self):
        derv_path = os.path.realpath(os.path.join(self.test_root_back1,
                                                  BackupManager.RELATIVE_BACKUP_LOCATION, 'back1'))
        self.assertTrue(os.path.exists(derv_path), 'run_model backup exists before model can be run')
        arg_list = [self.test_root_back1, self.model_rename_path, '-n', 'back1', '-x', 'derivatives',
                    '-f', 'events', '-e', '.tsv']
        test_file1 = os.path.realpath(os.path.join(self.test_root_back1, 'sub1', 'sub1_events.tsv'))
        back_file1 = os.path.realpath(os.path.join(derv_path, 'backup_root', 'sub1', 'sub1_events.tsv'))
        df_orig_before = get_new_dataframe(test_file1)
        df_back_before = get_new_dataframe(back_file1)
        self.assertTrue('stuff' in df_orig_before.columns, "run_remodel before remodeling original has not been remodelled")
        self.assertFalse('value' in df_orig_before.columns, "run_remodel before remodeling original has not been remodelled")
        self.assertTrue('stuff' in df_back_before.columns, "run_remodel before remodeling backup has not been remodelled")
        self.assertFalse('value' in df_back_before.columns, "run_remodel before remodeling backup has not been remodelled")
        cli_remodel.main(arg_list)
        df_orig_after = get_new_dataframe(test_file1)
        df_back_after = get_new_dataframe(back_file1)
        self.assertFalse('stuff' in df_orig_after.columns, "run_remodel after remodeling original is remodelled")
        self.assertTrue('value' in df_orig_after.columns, "run_remodel after remodeling original is remodelled")
        self.assertTrue('stuff' in df_back_after.columns, "run_remodel after remodeling backup is not changed")
        self.assertFalse('value' in df_back_after.columns, "run_remodel after remodeling backup is not changed")

    def test_main_summarize(self):
        arg_list = [self.test_root_back1, self.model_summary_path, '-n', 'back1', '-x', 'derivatives',
                    '-f', 'events', '-e', '.tsv']
        summary_path = os.path.realpath(os.path.join(self.test_root_back1, 'derivatives', 'remodel', 'summaries'))
        self.assertFalse(os.path.exists(summary_path), "run_remodel does not have a summaries directory before")
        cli_remodel.main(arg_list)
        file_list1 = os.listdir(summary_path)
        self.assertEqual(len(file_list1), 4, "run_remodel creates correct number of summary files when run.")


if __name__ == '__main__':
    unittest.main()
