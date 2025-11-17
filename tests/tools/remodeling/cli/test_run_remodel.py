import os
import io
import shutil
import unittest
from unittest.mock import patch
import zipfile
from hed.errors import HedFileError
from hed.tools.remodeling.cli.run_remodel import parse_arguments, parse_tasks, main


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_zip = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../../data/bids_tests/eeg_ds003645s_hed_remodel.zip")
        )
        cls.extract_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../../data/remodel_tests"))
        cls.data_root = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../../data/remodel_tests/eeg_ds003645s_hed_remodel")
        )
        cls.model_path = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "../../../data/remodel_tests/eeg_ds003645s_hed_remodel",
                "derivatives/remodel/remodeling_files/remove_extra_rmdl.json",
            )
        )
        cls.sidecar_path = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "../../../data/remodel_tests/eeg_ds003645s_hed_remodel",
                "task-FacePerception_events.json",
            )
        )
        cls.summary_model_path = os.path.realpath(
            os.path.join(
                os.path.dirname(__file__),
                "../../../data/remodel_tests/eeg_ds003645s_hed_remodel",
                "derivatives/remodel/remodeling_files",
                "summarize_hed_types_rmdl.json",
            )
        )
        cls.bad_model_path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../../data/remodel_tests/bad_rename_rmdl.json")
        )
        cls.files = [
            "/datasets/fmri_ds002790s_hed_aomic/sub-0001/func/sub-0001_task-stopsignal_acq-seq_events.tsv",
            "/datasets/fmri_ds002790s_hed_aomic/sub-0001/func/sub-0001_task-workingmemory_acq-seq_events.tsv",
            "/datasets/fmri_ds002790s_hed_aomic/sub-0002/func/sub-0002_task-emomatching_acq-seq_events.tsv",
            "/datasets/fmri_ds002790s_hed_aomic/sub-0002/func/sub-0002_task-stopsignal_acq-seq_events.tsv",
            "/datasets/fmri_ds002790s_hed_aomic/sub-0002/func/sub-0002_task-workingmemory_acq-seq_events.tsv",
        ]

    def setUp(self):
        with zipfile.ZipFile(self.data_zip, "r") as zip_ref:
            zip_ref.extractall(self.extract_path)

    def tearDown(self):
        shutil.rmtree(self.data_root)
        work_path = os.path.realpath(os.path.join(self.extract_path, "temp"))
        if os.path.exists(work_path):
            shutil.rmtree(work_path)

    @classmethod
    def tearDownClass(cls):
        pass

    def test_parse_arguments(self):
        # Test no verbose
        arg_list1 = [self.data_root, self.model_path, "-x", "derivatives", "-bn", "back1"]
        with patch("sys.stdout", new=io.StringIO()) as fp1:
            args1, operations1 = parse_arguments(arg_list1)
            self.assertFalse(fp1.getvalue())
        self.assertTrue(args1)
        self.assertEqual(len(operations1), 1)
        self.assertEqual(args1.suffixes, ["events"])

        # Test * for extensions and suffix as well as verbose
        arg_list2 = [self.data_root, self.model_path, "-x", "derivatives", "-bn", "back1", "-f", "*", "-v"]
        with patch("sys.stdout", new=io.StringIO()) as fp2:
            args2, operations2 = parse_arguments(arg_list2)
            self.assertTrue(fp2.getvalue())
        self.assertTrue(args2)
        self.assertEqual(len(operations2), 1)
        self.assertIsNone(args2.suffixes)

        # Test not able to parse
        arg_list3 = [self.data_root, self.bad_model_path, "-x", "derivatives"]
        with self.assertRaises(ValueError) as context3:
            parse_arguments(arg_list3)
        self.assertEqual(context3.exception.args[0], "UnableToFullyParseOperations")

    def test_parse_tasks(self):
        tasks1 = parse_tasks(self.files, "*")
        self.assertIn("stopsignal", tasks1)
        self.assertEqual(3, len(tasks1))
        self.assertEqual(2, len(tasks1["workingmemory"]))
        tasks2 = parse_tasks(self.files, ["workingmemory"])
        self.assertEqual(1, len(tasks2))
        files2 = ["task-.tsv", "/base/"]
        tasks3 = parse_tasks(files2, "*")
        self.assertFalse(tasks3)

    def test_main_bids(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "stimuli", "-b", "-hv", "8.3.0"]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_bids_alt_path(self):
        work_path = os.path.realpath(os.path.join(self.extract_path, "temp"))
        arg_list = [
            self.data_root,
            self.summary_model_path,
            "-x",
            "derivatives",
            "stimuli",
            "-hv",
            "8.3.0",
            "-j",
            self.sidecar_path,
            "-w",
            work_path,
        ]

        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_bids_verbose_bad_task(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "stimuli", "-b", "-t", "junk", "-v"]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertTrue(fp.getvalue())

    def test_main_bids_verbose(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "stimuli", "-b", "-v"]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertTrue(fp.getvalue())

    def test_main_bids_no_sidecar(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "stimuli", "-b"]
        os.remove(self.sidecar_path)
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_bids_no_sidecar_with_hed(self):
        arg_list = [self.data_root, self.summary_model_path, "-x", "derivatives", "stimuli", "-b"]
        os.remove(self.sidecar_path)
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_direct_no_sidecar(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "stimuli"]
        os.remove(self.sidecar_path)
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_direct_no_sidecar_with_hed(self):
        arg_list = [self.data_root, self.summary_model_path, "-x", "derivatives", "stimuli", "-hv", "8.3.0"]
        os.remove(self.sidecar_path)
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_direct_sidecar_with_hed_bad_task(self):
        arg_list = [
            self.data_root,
            self.summary_model_path,
            "-x",
            "derivatives",
            "stimuli",
            "-hv",
            "8.3.0",
            "-j",
            self.sidecar_path,
            "-t",
            "junk",
        ]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_direct_sidecar_with_hed(self):
        arg_list = [
            self.data_root,
            self.summary_model_path,
            "-x",
            "derivatives",
            "stimuli",
            "-hv",
            "8.4.0",
            "-j",
            self.sidecar_path,
            "-v",
        ]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertTrue(fp.getvalue())

    def test_main_bids_no_sidecar_with_hed_task(self):
        arg_list = [
            self.data_root,
            self.summary_model_path,
            "-x",
            "derivatives",
            "stimuli",
            "-t",
            "FacePerception",
            "-hv",
            "8.3.0",
        ]
        os.remove(self.sidecar_path)
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())

    def test_main_errors(self):
        # Test bad data directory
        arg_list = ["junk/junk", self.model_path, "-x", "derivatives", "-bn", "back1"]
        with self.assertRaises(HedFileError) as context:
            main(arg_list=arg_list)
        self.assertEqual(context.exception.args[0], "DataDirectoryDoesNotExist")

        # Test no backup
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "-bn", "back1"]
        with self.assertRaises(HedFileError) as context:
            main(arg_list=arg_list)
        self.assertEqual(context.exception.args[0], "BackupDoesNotExist")

    def test_main_verbose(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives", "-v"]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertTrue(fp.getvalue())

    def test_run_bids_ops_verbose(self):
        arg_list = [self.data_root, self.model_path, "-x", "derivatives"]
        with patch("sys.stdout", new=io.StringIO()) as fp:
            main(arg_list)
            self.assertFalse(fp.getvalue())


if __name__ == "__main__":
    unittest.main()
