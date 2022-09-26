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
        cls.extract_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../data/remodeling')
        cls.model_rename_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                             '../../../data/remodeling/test_ds002790_rename_rmdl.json')
        cls.model_summary_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                              '../../../data/remodeling/test_root1_summarize_column_value_rmdl.json')
        cls.hed_model_summary_path = \
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodeling/test_ds003654_summarize_condition_variable_rmdl.json'))
        cls.test_root_ds002790 = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                               '../../../data/remodeling/test_ds002790s_hed'))
        cls.test_zip_ds002790 = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                              '../../../data/remodeling/test_ds002790s_hed.zip'))
        cls.test_root_ds002790_backed = \
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodeling/test_ds002790s_hed_backed'))
        cls.test_zip_ds002790_backed = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                        '../../../data/remodeling/test_ds002790s_hed_backed.zip'))
        cls.test_root_ds003654_backed = \
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodeling/test_ds003654s_hed_backed'))
        cls.test_zip_ds003654_backed = \
            os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                          '../../../data/remodeling/test_ds003654s_hed_backed.zip'))

    def setUp(self):
        with zipfile.ZipFile(self.test_zip_ds002790, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_ds002790_backed, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_ds003654_backed, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)

    def tearDown(self):
        shutil.rmtree(self.test_root_ds002790)
        shutil.rmtree(self.test_root_ds002790_backed)
        shutil.rmtree(self.test_root_ds003654_backed)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_main_rename_columns(self):
        derv_path = os.path.realpath(os.path.join(self.test_root_ds002790_backed,
                                                  BackupManager.RELATIVE_BACKUP_LOCATION,
                                                  BackupManager.DEFAULT_BACKUP_NAME))
        self.assertTrue(os.path.exists(derv_path), 'run_model backup exists before model can be run')
        arg_list = [self.test_root_ds002790_backed, '-n', BackupManager.DEFAULT_BACKUP_NAME, '-x', 'derivatives',
                    '-f', 'events', '-e', '.tsv', '-m', self.model_rename_path, '-b']
        test_file1 = os.path.realpath(os.path.join(self.test_root_ds002790_backed, 'sub-0001', 'func',
                                                   'sub-0001_task-stopsignal_acq-seq_events.tsv'))
        back_file1 = os.path.realpath(os.path.join(derv_path, 'backup_root', 'sub-0001', 'func',
                                                   'sub-0001_task-stopsignal_acq-seq_events.tsv'))
        df_orig_before = get_new_dataframe(test_file1)
        df_back_before = get_new_dataframe(back_file1)
        self.assertTrue('sex' in df_orig_before.columns,
                        "run_remodel before remodeling original has not been remodelled")
        self.assertFalse('face_sex' in df_orig_before.columns,
                         "run_remodel before remodeling original has not been remodelled")
        self.assertTrue('sex' in df_back_before.columns,
                        "run_remodel before remodeling backup has not been remodelled")
        self.assertFalse('face_sex' in df_back_before.columns,
                         "run_remodel before remodeling backup has not been remodelled")
        cli_remodel.main(arg_list)
        df_orig_after = get_new_dataframe(test_file1)
        df_back_after = get_new_dataframe(back_file1)
        self.assertFalse('sex' in df_orig_after.columns, "run_remodel after remodeling original is remodelled")
        self.assertTrue('face_sex' in df_orig_after.columns, "run_remodel after remodeling original is remodelled")
        self.assertTrue('sex' in df_back_after.columns, "run_remodel after remodeling backup is not changed")
        self.assertFalse('face_sex' in df_back_after.columns, "run_remodel after remodeling backup is not changed")

    def test_main_summarize(self):
        print(self.hed_model_summary_path)
        arg_list = [self.test_root_ds003654_backed, '-n', BackupManager.DEFAULT_BACKUP_NAME,
                    '-x', 'derivatives', 'stimuli'
                    '-f', 'events', '-e', '.tsv', '-m', self.hed_model_summary_path, '-b']
        summary_path = os.path.realpath(os.path.join(self.test_root_ds003654_backed, 'derivatives',
                                                     'remodel', 'summaries'))
        self.assertFalse(os.path.exists(summary_path), "run_remodel does not have a summaries directory before")
        cli_remodel.main(arg_list)
        file_list1 = os.listdir(summary_path)
        self.assertEqual(len(file_list1), 2, "run_remodel creates correct number of summary files when run.")


if __name__ == '__main__':
    unittest.main()
