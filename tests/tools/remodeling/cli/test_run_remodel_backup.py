import os
import json
import shutil
import unittest
import zipfile
from hed.errors import HedFileError
from hed.tools.remodeling.backup_manager import BackupManager
from hed.tools.remodeling.cli.run_remodel_backup import main
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        file_list = ["top_level.tsv", "sub1/sub1_events.tsv", "sub2/sub2_events.tsv", "sub2/sub2_next_events.tsv"]
        # cls.file_list = file_list
        extract_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests")
        cls.alt_path = os.path.realpath(os.path.join(extract_path, "temp"))
        cls.extract_path = extract_path
        test_root = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/test_root")
        cls.test_root = test_root
        cls.test_paths = [os.path.join(test_root, file) for file in file_list]
        cls.test_zip = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../../data/remodel_tests/test_root.zip")
        cls.derv_path = os.path.realpath(os.path.join(test_root, BackupManager.RELATIVE_BACKUP_LOCATION))
        cls.data_zip = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../../data/bids_tests/eeg_ds003645s_hed_remodel.zip")
        )
        cls.data_root = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../../data/remodel_tests/eeg_ds003645s_hed_remodel")
        )

    def setUp(self):
        with zipfile.ZipFile(self.test_zip, "r") as zip_ref:
            zip_ref.extractall(self.extract_path)
        with zipfile.ZipFile(self.data_zip, "r") as zip_ref:
            zip_ref.extractall(self.extract_path)

    def tearDown(self):
        if os.path.exists(self.test_root):
            shutil.rmtree(self.test_root)
        if os.path.exists(self.data_root):
            shutil.rmtree(self.data_root)
        if os.path.exists(self.alt_path):
            shutil.rmtree(self.alt_path)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_main_events(self):
        self.assertFalse(os.path.exists(self.derv_path), "backup directory does not exist before creation")
        arg_list = [
            self.test_root,
            "-bn",
            BackupManager.DEFAULT_BACKUP_NAME,
            "-bd",
            self.derv_path,
            "-x",
            "derivatives",
            "-fs",
            "events",
        ]
        main(arg_list)
        self.assertTrue(os.path.exists(self.derv_path), "backup directory exists before creation")
        json_path = os.path.realpath(
            os.path.join(self.derv_path, BackupManager.DEFAULT_BACKUP_NAME, BackupManager.BACKUP_DICTIONARY)
        )
        with open(json_path, "r") as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 3, "The backup of events.tsv does not include top_level.tsv")
        file_list = get_file_list(self.derv_path, name_suffix="events")
        self.assertEqual(len(file_list), 3, "The backup of events.tsv has the right number of files")

    def test_main_all(self):
        arg_list = [
            self.test_root,
            "-bn",
            BackupManager.DEFAULT_BACKUP_NAME,
            "-bd",
            self.derv_path,
            "-x",
            "derivatives",
            "-fs",
            "*",
        ]

        self.assertFalse(os.path.exists(self.derv_path), "backup directory does not exist before creation")
        main(arg_list)
        self.assertTrue(os.path.exists(self.derv_path), "backup directory exists before creation")
        json_path = os.path.realpath(
            os.path.join(self.derv_path, BackupManager.DEFAULT_BACKUP_NAME, BackupManager.BACKUP_DICTIONARY)
        )
        with open(json_path, "r") as fp:
            key_dict = json.load(fp)
        self.assertEqual(len(key_dict), 4, "The backup of events.tsv does not include top_level.tsv")
        back_path = os.path.realpath(os.path.join(self.derv_path, BackupManager.DEFAULT_BACKUP_NAME, "backup_root"))
        file_list1 = get_file_list(back_path)
        self.assertIsInstance(file_list1, list)
        self.assertEqual(len(file_list1), 4)

    def test_main_task(self):
        der_path = os.path.realpath(os.path.join(self.data_root, "derivatives"))
        self.assertTrue(os.path.exists(der_path))
        shutil.rmtree(der_path)
        self.assertFalse(os.path.exists(der_path))
        arg_list = [
            self.data_root,
            "-bn",
            BackupManager.DEFAULT_BACKUP_NAME,
            "-x",
            "derivatives",
            "-fs",
            "events",
            "-t",
            "FacePerception",
        ]
        main(arg_list)
        self.assertTrue(os.path.exists(der_path))
        back_path = os.path.realpath(
            os.path.join(
                self.data_root, BackupManager.RELATIVE_BACKUP_LOCATION, BackupManager.DEFAULT_BACKUP_NAME, "backup_root"
            )
        )
        self.assertTrue(os.path.exists(back_path))
        backed_files = get_file_list(back_path)
        self.assertEqual(len(backed_files), 6)

    def test_main_bad_task(self):
        der_path = os.path.realpath(os.path.join(self.data_root, "derivatives"))
        self.assertTrue(os.path.exists(der_path))
        shutil.rmtree(der_path)
        self.assertFalse(os.path.exists(der_path))
        arg_list = [
            self.data_root,
            "-bn",
            BackupManager.DEFAULT_BACKUP_NAME,
            "-x",
            "derivatives",
            "-fs",
            "events",
            "-t",
            "Baloney",
        ]
        main(arg_list)
        self.assertTrue(os.path.exists(der_path))
        back_path = os.path.realpath(
            os.path.join(
                self.data_root, BackupManager.RELATIVE_BACKUP_LOCATION, BackupManager.DEFAULT_BACKUP_NAME, "backup_root"
            )
        )
        self.assertTrue(os.path.exists(back_path))
        backed_files = get_file_list(back_path)
        self.assertEqual(len(backed_files), 0)

    def test_alt_loc(self):
        if os.path.exists(self.alt_path):
            shutil.rmtree(self.alt_path)
        self.assertFalse(os.path.exists(self.alt_path))
        arg_list = [
            self.data_root,
            "-bn",
            BackupManager.DEFAULT_BACKUP_NAME,
            "-x",
            "derivatives",
            "-bd",
            self.alt_path,
            "-fs",
            "events",
        ]
        main(arg_list)
        self.assertTrue(os.path.exists(self.alt_path))
        back_path = os.path.realpath(os.path.join(self.alt_path, "default_back/backup_root"))
        self.assertTrue(os.path.exists(back_path))
        backed_files = get_file_list(back_path)
        self.assertEqual(len(backed_files), 6)

    def test_main_backup_exists(self):
        der_path = os.path.realpath(os.path.join(self.data_root, "derivatives"))
        self.assertTrue(os.path.exists(der_path))
        arg_list = [
            self.data_root,
            "-bn",
            BackupManager.DEFAULT_BACKUP_NAME,
            "-x",
            "derivatives",
            "-fs",
            "events",
            "-t",
            "Baloney",
        ]
        with self.assertRaises(HedFileError) as context:
            main(arg_list)
        self.assertEqual(context.exception.args[0], "BackupExists")


if __name__ == "__main__":
    unittest.main()
