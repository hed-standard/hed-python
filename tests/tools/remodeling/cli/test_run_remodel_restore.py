import os
import shutil
import unittest
import zipfile
from hed.tools.remodeling.backup_manager import BackupManager
import hed.tools.remodeling.cli.run_remodel_restore as cli_restore
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

    def test_main_restore(self):
        files1 = get_file_list(self.test_root_back1, exclude_dirs=['derivatives'])
        self.assertEqual(len(files1), 4, "run_restore starts with the right number of files.")
        shutil.rmtree(os.path.realpath(os.path.join(self.test_root_back1, 'sub1')))
        shutil.rmtree(os.path.realpath(os.path.join(self.test_root_back1, 'sub2')))
        os.remove(os.path.realpath(os.path.join(self.test_root_back1, 'top_level.tsv')))
        files2 = get_file_list(self.test_root_back1, exclude_dirs=['derivatives'])
        self.assertFalse(files2, "run_restore starts with the right number of files.")
        arg_list = [self.test_root_back1, '-n', 'back1']
        cli_restore.main(arg_list)
        files3 = get_file_list(self.test_root_back1, exclude_dirs=['derivatives'])
        overlap = set(files1).intersection(set(files3))
        self.assertEqual(len(overlap), len(files1), "run_restore restores all the files after")


if __name__ == '__main__':
    unittest.main()
