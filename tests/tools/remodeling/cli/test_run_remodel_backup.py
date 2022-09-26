import os
import json
import shutil
import unittest
import zipfile
import collections
from hed.errors import HedFileError
from hed.tools.remodeling.backup_manager import BackupManager
import hed.tools.remodeling.cli.run_remodel_backup as cli_backup
from hed.tools.util.io_util import get_file_list


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

    def test_main_events(self):
        derv_path = os.path.realpath(os.path.join(self.test_root, BackupManager.RELATIVE_BACKUP_LOCATION))
        self.assertFalse(os.path.exists(derv_path), 'backup directory does not exist before creation')
        arg_list = [self.test_root, '-n', BackupManager.DEFAULT_BACKUP_NAME, '-x', 'derivatives',
                   '-f', 'events', '-e', '.tsv']
        cli_backup.main(arg_list)
        self.assertTrue(os.path.exists(derv_path), 'backup directory exists before creation')
        json_path = os.path.realpath(os.path.join(derv_path, BackupManager.DEFAULT_BACKUP_NAME,
                                                  BackupManager.BACKUP_DICTIONARY))
        with open(json_path, 'r') as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 3, "The backup of events.tsv does not include top_level.tsv")
        file_list = get_file_list(derv_path, name_suffix='events', extensions=['.tsv'])
        self.assertEqual(len(file_list), 3, "The backup of events.tsv has the right number of files")

    def test_main_all(self):
        arg_list = [self.test_root, '-n', BackupManager.DEFAULT_BACKUP_NAME, '-x', 'derivatives',
                    '-f', '*', '-e', '*']
        derv_path = os.path.realpath(os.path.join(self.test_root, BackupManager.RELATIVE_BACKUP_LOCATION))
        self.assertFalse(os.path.exists(derv_path), 'backup directory does not exist before creation')
        cli_backup.main(arg_list)
        self.assertTrue(os.path.exists(derv_path), 'backup directory exists before creation')
        json_path = os.path.realpath(os.path.join(derv_path, BackupManager.DEFAULT_BACKUP_NAME,
                                                  BackupManager.BACKUP_DICTIONARY))
        with open(json_path, 'r') as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 4, "The backup of events.tsv does not include top_level.tsv")
        back_path = os.path.realpath(os.path.join(derv_path, BackupManager.DEFAULT_BACKUP_NAME, 'backup_root'))
        file_list = get_file_list(back_path)
        self.assertEqual(len(file_list), 4, "The backup of events.tsv has the right number of files")


if __name__ == '__main__':
    unittest.main()
