import os
import io
import shutil
import unittest
from unittest.mock import patch
import zipfile
from hed.errors import HedFileError
from hed.tools.remodeling.backup_manager import BackupManager
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        file_list = ["top_level.tsv", "sub1/sub1_events.tsv", "sub2/sub2_events.tsv", "sub2/sub2_next_events.tsv"]
        cls.file_list = file_list
        cls.extract_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/remodel_tests"))
        test_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/remodel_tests/test_root"))
        cls.test_root = test_root
        cls.test_paths = [os.path.join(test_root, file) for file in file_list]
        cls.test_zip = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/remodel_tests/test_root.zip"))

        test_root_back1 = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/remodel_tests/test_root_back1"))
        cls.test_root_back1 = test_root_back1
        cls.test_paths_back1 = [os.path.join(test_root_back1, file) for file in file_list]
        cls.test_zip_back1 = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../data/remodel_tests/test_root_back1.zip")
        )

        test_root_bad = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/remodel_tests/test_root_bad"))
        cls.test_root_bad = test_root_bad
        cls.test_root_bad_backups = os.path.join(test_root_bad, BackupManager.RELATIVE_BACKUP_LOCATION)
        cls.test_paths_bad = [os.path.join(test_root_bad, file) for file in file_list]
        cls.test_zip_bad = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../data/remodel_tests/test_root_bad.zip")
        )

    def setUp(self):
        with zipfile.ZipFile(self.test_zip, "r") as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_back1, "r") as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.test_zip_bad, "r") as zip_ref:
            zip_ref.extractall(self.extract_path)

    def tearDown(self):
        shutil.rmtree(self.test_root)
        shutil.rmtree(self.test_root_back1)
        shutil.rmtree(self.test_root_bad)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_constructor(self):
        back1_man = BackupManager(self.test_root_back1)
        self.assertIsInstance(back1_man, BackupManager, "constructor creates a BackupManager if no backups")
        self.assertTrue(back1_man.backups_dict)

    def test_constructor_alternative_location(self):
        alt_path = os.path.realpath(os.path.join(self.extract_path, "temp_backs"))
        back1_man = BackupManager(self.test_root_back1, backups_root=alt_path)
        self.assertIsInstance(back1_man, BackupManager, "constructor creates a BackupManager if no backups")
        self.assertFalse(back1_man.backups_dict)
        file_list = get_file_list(
            self.test_root_back1, name_suffix="events", exclude_dirs=["derivatives"], extensions=[".tsv"]
        )
        self.assertEqual(len(file_list), 3)
        back1_man.create_backup(file_list, backup_name="my_back")
        self.assertTrue(back1_man.backups_dict)
        backup = back1_man.backups_dict["my_back"]
        self.assertEqual(len(backup), len(file_list))
        if os.path.exists(alt_path):
            shutil.rmtree(alt_path)

    def test_bad_data_root(self):
        with self.assertRaises(HedFileError) as context:
            BackupManager("/baloney/Junk")
        self.assertEqual(context.exception.args[0], "NonExistentData")

    def test_constructor_missing_backup(self):
        remove_list = ["back2_miss_json", "back3_miss_back", "back4_miss_file"]
        remove_dirs = [os.path.join(self.test_root_bad_backups, file) for file in remove_list]
        for remove_dir in remove_dirs:
            shutil.rmtree(remove_dir)
        with self.assertRaises(HedFileError) as context:
            BackupManager(self.test_root_bad)
        self.assertEqual(context.exception.code, "MissingBackupFile")

    def test_constructor_missing_json(self):
        remove_list = ["back1_extra", "back3_miss_back", "back4_miss_file"]
        remove_dirs = [os.path.realpath(os.path.join(self.test_root_bad_backups, file)) for file in remove_list]
        for remove_dir in remove_dirs:
            shutil.rmtree(remove_dir)
        with self.assertRaises(HedFileError) as context:
            BackupManager(self.test_root_bad)
        self.assertEqual(context.exception.code, "BadBackupFormat")

    def test_constructor_extra_backup_file(self):
        remove_list = ["back1_extra", "back2_miss_json", "back4_miss_file"]
        remove_dirs = [os.path.realpath(os.path.join(self.test_root_bad_backups, file)) for file in remove_list]
        for remove_dir in remove_dirs:
            shutil.rmtree(remove_dir)
        with self.assertRaises(HedFileError) as context:
            BackupManager(self.test_root_bad)
        self.assertEqual(context.exception.code, "BadBackupFormat")

    def test_create_backup(self):
        test_man = BackupManager(self.test_root)
        file_list = get_file_list(self.test_root)
        self.assertFalse(test_man.get_backup("test_back1"), "create_backup doesn't have the backup before creation")
        return_val1 = test_man.create_backup(file_list, backup_name="test_back1", verbose=False)
        self.assertTrue(return_val1, "create_backup returns true when it has created a backup.")
        backup1 = test_man.get_backup("test_back1")
        self.assertIsInstance(backup1, dict, "create_backup creates a dictionary")
        return_val2 = test_man.create_backup(file_list, backup_name="test_back1", verbose=False)
        self.assertFalse(return_val2, "create_backup returns true when it has created a backup.")

    def test_create_backup_no_name(self):
        test_man = BackupManager(self.test_root)
        self.assertFalse(test_man.backups_dict)
        file_list = get_file_list(self.test_root)
        with patch("sys.stdout", new=io.StringIO()) as fp1:
            return_val1 = test_man.create_backup(file_list, verbose=False)
            self.assertFalse(fp1.getvalue())
        self.assertTrue(return_val1, "create_backup returns true when it has created a backup.")
        backup1 = test_man.get_backup("test_back1")
        self.assertFalse(backup1)
        back = test_man.get_backup(BackupManager.DEFAULT_BACKUP_NAME)
        self.assertIsInstance(back, dict, "create_backup creates a dictionary")
        self.assertTrue(back)
        return_val2 = test_man.create_backup(file_list, backup_name="test_back1", verbose=False)
        self.assertTrue(return_val2, "create_backup returns true when it has created a backup.")

    def test_get_task(self):
        task1 = BackupManager.get_task(["abc", "def"], "temp/myabc.txt")
        self.assertFalse(task1)
        task2 = BackupManager.get_task([], "temp/myabc.txt")
        self.assertFalse(task2)
        task3 = BackupManager.get_task(["abc", "def"], "temp/alpha_key_task_abc.txt")
        self.assertEqual(task3, "abc")


if __name__ == "__main__":
    unittest.main()
