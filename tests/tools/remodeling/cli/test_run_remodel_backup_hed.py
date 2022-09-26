import os
import json
import shutil
import unittest
import zipfile

from hed.tools.remodeling.backup_manager import BackupManager
import hed.tools.remodeling.cli.run_remodel_backup as cli_backup
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.extract_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../data/remodeling')
        cls.test_zip_ds002790 = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 '../../../data/remodeling/test_ds002790s_hed.zip'))
        cls.test_root_ds002790 = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                               '../../../data/remodeling/test_ds002790s_hed'))
        cls.test_zip_ds003654 = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                 '../../../data/remodeling/test_ds003654s_hed.zip'))
        cls.test_root_ds003654 = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                               '../../../data/remodeling/test_ds003654s_hed'))

    def setUp(self):
        with zipfile.ZipFile(self.test_zip_ds002790, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_ds003654, 'r') as zip_ref:
            zip_ref.extractall(self.extract_path)

    def tearDown(self):
        shutil.rmtree(self.test_root_ds002790)
        shutil.rmtree(self.test_root_ds003654)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_main_events(self):
        derv_path = os.path.realpath(os.path.join(self.test_root_ds002790, BackupManager.RELATIVE_BACKUP_LOCATION))
        self.assertFalse(os.path.exists(derv_path), 'backup directory does not exist before creation')
        arg_list = [self.test_root_ds002790, '-n', BackupManager.DEFAULT_BACKUP_NAME, '-x', 'derivatives',
                    '-f', 'events', '-e', '.tsv']
        cli_backup.main(arg_list)
        self.assertTrue(os.path.exists(derv_path), 'backup directory exists before creation')
        json_path = os.path.realpath(os.path.join(derv_path, BackupManager.DEFAULT_BACKUP_NAME,
                                                  BackupManager.BACKUP_DICTIONARY))
        with open(json_path, 'r') as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 5, "The backup of events.tsv does not include top_level.tsv")
        file_list = get_file_list(derv_path, name_suffix='events', extensions=['.tsv'])
        self.assertEqual(len(file_list), 5, "The backup of events.tsv has the right number of files")

    def test_main_events_with_task(self):
        derv_path = os.path.realpath(os.path.join(self.test_root_ds002790, BackupManager.RELATIVE_BACKUP_LOCATION))
        self.assertFalse(os.path.exists(derv_path), 'backup directory does not exist before creation')
        arg_list = [self.test_root_ds002790, '-n', BackupManager.DEFAULT_BACKUP_NAME,
                    '-x', 'derivatives', '-f', 'events', '-e', '.tsv', '-t', 'stopsignal']
        cli_backup.main(arg_list)
        self.assertTrue(os.path.exists(derv_path), 'backup directory exists before creation')
        json_path = os.path.realpath(os.path.join(derv_path, BackupManager.DEFAULT_BACKUP_NAME,
                                                  BackupManager.BACKUP_DICTIONARY))
        with open(json_path, 'r') as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 2, "The backup of events.tsv does not include top_level.tsv")
        file_list = get_file_list(derv_path, name_suffix='events', extensions=['.tsv'])
        self.assertEqual(len(file_list), 2, "The backup of events.tsv has the right number of files")

    def test_main_wh(self):
        derv_path = os.path.realpath(os.path.join(self.test_root_ds003654, BackupManager.RELATIVE_BACKUP_LOCATION))
        self.assertFalse(os.path.exists(derv_path), 'backup directory does not exist before creation')
        arg_list = [self.test_root_ds003654, '-n', BackupManager.DEFAULT_BACKUP_NAME,
                    '-x', 'derivatives', 'stimuli', '-f', 'events', '-e', '.tsv']
        cli_backup.main(arg_list)
        self.assertTrue(os.path.exists(derv_path), 'backup directory exists before creation')
        json_path = os.path.realpath(os.path.join(derv_path, BackupManager.DEFAULT_BACKUP_NAME,
                                                  BackupManager.BACKUP_DICTIONARY))
        with open(json_path, 'r') as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 6, "The backup of events.tsv does not include top_level.tsv")
        file_list = get_file_list(derv_path, name_suffix='events', extensions=['.tsv'])
        self.assertEqual(len(file_list), 6, "The backup of events.tsv has the right number of files")


if __name__ == '__main__':
    unittest.main()
