import os
import unittest
from unittest.mock import patch
from hed.errors.exceptions import HedFileError
from hed.tools.util.io_util import (
    check_filename,
    extract_suffix_path,
    clean_filename,
    get_alphanumeric_path,
    get_file_list,
    get_path_components,
    get_task_from_file,
    get_allowed,
    get_filtered_by_element,
    get_full_extension,
)


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/bids_tests/eeg_ds003645s_hed"))
        stern_base_dir = os.path.join(os.path.dirname(__file__), "../data/sternberg")
        att_base_dir = os.path.join(os.path.dirname(__file__), "../data/attention_shift")
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.realpath(os.path.join(stern_base_dir, "sternberg_test_events.tsv"))
        cls.stern_test2_path = os.path.realpath(os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv"))
        cls.stern_test3_path = os.path.realpath(os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv"))
        cls.attention_shift_path = os.path.realpath(
            os.path.join(att_base_dir, "sub-001_task-AuditoryVisualShift_run-01_events.tsv")
        )

    def test_check_filename(self):
        name1 = "/user/local/task_baloney.gz_events.nii"
        check1a = check_filename(name1, extensions=[".txt", ".nii"])
        self.assertTrue(check1a, "check_filename should return True if has required extension")
        check1b = check_filename(name1, name_prefix="apple", extensions=[".txt", ".nii"])
        self.assertFalse(check1b, "check_filename should return False if right extension but wrong prefix")
        check1c = check_filename(name1, name_suffix="_events")
        self.assertTrue(check1c, "check_filename should return True if has a default extension and correct suffix")
        name2 = "/user/local/task_baloney.gz_events.nii.gz"
        check2a = check_filename(name2, extensions=[".txt", ".nii"])
        self.assertFalse(check2a, "check_filename should return False if extension does not match")
        check2b = check_filename(name2, extensions=[".txt", ".nii.gz"])
        self.assertTrue(check2b, "check_filename should return True if extension with gz matches")
        check2c = check_filename(name2, name_suffix="events", extensions=[".txt", ".nii.gz"])
        self.assertTrue(check2c, "check_filename should return True if suffix after extension matches")
        name3 = "Changes"
        check3a = check_filename(name3, name_suffix="events", extensions=None)
        self.assertFalse(check3a, "check_filename should be False if it doesn't match with no extension")
        check3b = check_filename(name3, name_suffix="es", extensions=None)
        self.assertTrue(check3b, "check_filename should be True if match with no extension.")

    def test_extract_suffix_path(self):
        suffix_path = extract_suffix_path("c:/myroot/temp.tsv", "c:")
        self.assertTrue(suffix_path.endswith("temp.tsv"), "extract_suffix_path has the right path")

    def test_clean_file_name(self):
        file1 = clean_filename("mybase")
        self.assertEqual(file1, "mybase", "generate_file_name should return the base when other arguments not set")
        filename = clean_filename("")
        self.assertEqual("", filename, "Return empty when all arguments are none")
        filename = clean_filename(None)
        self.assertEqual("", filename, "Return empty when base_name, prefix, and suffix are None, but extension is not")
        filename = clean_filename("c:/temp.json")
        self.assertEqual("c_temp.json", filename, "Returns stripped base_name + extension when prefix, and suffix are None")

    def test_get_allowed(self):
        test_value = "events.tsv"
        value = get_allowed(test_value, "events")
        self.assertEqual(value, "events", "get_allowed matches starts with when string")
        value = get_allowed(test_value, None)
        self.assertEqual(value, test_value, "get_allowed if None is passed for allowed, no requirement is set.")
        test_value1 = "EventsApples.tsv"
        value1 = get_allowed(test_value1, ["events", "annotations"])
        self.assertEqual(value1, "events", "get_allowed is case insensitive")
        value2 = get_allowed(test_value1, [])
        self.assertEqual(value2, test_value1)

    def test_get_alphanumeric_path(self):
        mypath1 = "g:\\String1%_-sTring2\n//string3\\\\string4.pnG"
        repath1 = get_alphanumeric_path(mypath1)
        self.assertEqual("g_String1_sTring2_string3_string4_pnG", repath1)
        repath2 = get_alphanumeric_path(mypath1, "$")
        self.assertEqual("g$String1$sTring2$string3$string4$pnG", repath2)

    def test_get_file_list_case(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/sternberg")
        file_list = get_file_list(dir_data, name_prefix="STERNBerg", extensions=[".Tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith("sternberg"))

    def test_get_file_list_exclude_dir(self):
        dir_data = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/bids_tests/eeg_ds003645s_hed"))
        file_list1 = get_file_list(dir_data, extensions=[".bmp"])
        self.assertEqual(3, len(file_list1), "get_file_list has the right number of files when no exclude")
        file_list2 = get_file_list(dir_data, extensions=[".bmp"], exclude_dirs=[])
        self.assertEqual(len(file_list1), len(file_list2), "get_file_list should not change when exclude_dir is empty")
        file_list3 = get_file_list(dir_data, extensions=[".bmp"], exclude_dirs=["stimuli"])
        self.assertFalse(file_list3, "get_file_list should return an empty list when all are excluded")

    def test_get_file_list_files(self):
        dir_pairs = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/schema_tests/prologue_tests")
        dir_pairs = os.path.realpath(dir_pairs)
        test_files = [name for name in os.listdir(dir_pairs) if os.path.isfile(os.path.join(dir_pairs, name))]
        file_list1 = get_file_list(dir_pairs)
        for file in file_list1:
            if os.path.basename(file) in test_files:
                continue
            raise HedFileError("FileNotFound", f"get_file_list should have found file {file}", "")

        for file in test_files:
            if os.path.join(dir_pairs, file) in file_list1:
                continue
            raise HedFileError("FileShouldNotBeFound", f"get_event_files should have not have found file {file}", "")

    def test_get_file_list_prefix(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/sternberg")
        file_list = get_file_list(dir_data, name_prefix="sternberg", extensions=[".tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith("sternberg"))

    def test_get_file_list_suffix(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data")
        file_list = get_file_list(dir_data, extensions=[".json", ".tsv"])
        for item in file_list:
            if item.endswith(".json") or item.endswith(".tsv"):
                continue
            raise HedFileError("BadFileType", "get_event_files expected only .html or .js files", "")

    def test_get_filtered_by_element(self):
        file_list1 = [
            "D:\\big\\subj-01_task-stop_events.tsv",
            "D:\\big\\subj-01_task-rest_events.tsv",
            "D:\\big\\subj-01_events.tsv",
            "D:\\big\\subj-01_task-stop_task-go_events.tsv",
        ]
        new_list1 = get_filtered_by_element(file_list1, ["task-stop"])
        self.assertEqual(len(new_list1), 2, "It should have the right length when one element filtered")
        new_list2 = get_filtered_by_element(file_list1, ["task-stop", "task-go"])
        self.assertEqual(len(new_list2), 2, "It should have the right length when meets multiple criteria")
        new_list3 = get_filtered_by_element(file_list1, [])
        self.assertFalse(len(new_list3))
        new_list3 = get_filtered_by_element(file_list1, [])
        self.assertFalse(len(new_list3))
        new_list4 = get_filtered_by_element([], ["task-go"])
        self.assertFalse(len(new_list4))

    def test_get_path_components(self):
        base_path = os.path.realpath(os.path.join(os.path.dirname(__file__), "../../data/bids_test/eeg_ds003645s"))
        file_path1 = os.path.realpath(os.path.join(base_path, "sub-002/eeg/sub-002_FacePerception_run-1_events.tsv"))
        comps1 = get_path_components(base_path, file_path1)
        self.assertEqual(len(comps1), 2, "get_path_components has correct number of components")
        comps2 = get_path_components(base_path, base_path)
        self.assertIsInstance(comps2, list)
        self.assertFalse(comps2, "get_path_components base_path is its own base_path")
        file_path3 = os.path.join(base_path, "temp_events.tsv")
        comps3 = get_path_components(base_path, file_path3)
        self.assertFalse(comps3, "get_path_components files directly in base_path don't have components ")

    def test_get_task_from_file(self):
        task1 = get_task_from_file("H:/alpha/base_task-blech.tsv")
        self.assertEqual("blech", task1)
        task2 = get_task_from_file("task-blech")
        self.assertEqual("blech", task2)


class TestGetFullExtension(unittest.TestCase):
    def test_single_extension(self):
        self.assertEqual(get_full_extension("file.txt"), ("file", ".txt"), "Should work with single extensions.")

    def test_multiple_extensions(self):
        self.assertEqual(get_full_extension("archive.tar.gz"), ("archive", ".tar.gz"), "Should work with multiple extensions.")

    def test_no_extension(self):
        self.assertEqual(get_full_extension("filename"), ("filename", ""), "Should work with no extension.")

    def test_hidden_file_no_extension(self):
        self.assertEqual(
            get_full_extension(".gitignore"), (".gitignore", ""), "Should work with hidden files without extensions."
        )

    def test_hidden_file_with_extension(self):
        self.assertEqual(
            get_full_extension(".config.json"), (".config", ".json"), "Should work with hidden files with extensions."
        )

    def test_nested_directory(self):
        self.assertEqual(get_full_extension("path/to/archive.tar.gz"), ("path/to/archive", ".tar.gz"), "")


class TestSeparateByExt(unittest.TestCase):

    @patch("hed.tools.util.io_util.get_full_extension")  # Replace 'your_module' with the actual module name
    def test_separate_by_ext(self, mock_get_full_extension):
        file_paths = ["file1.tsv", "file2.json", "file3.tsv", "file4.txt", "file5.json"]

        # Define the return values for the mocked function
        mock_get_full_extension.side_effect = [
            ("file1", ".tsv"),
            ("file2", ".json"),
            ("file3", ".tsv"),
            ("file4", ".txt"),
            ("file5", ".json"),
        ]

        expected_result = {
            ".tsv": ["file1.tsv", "file3.tsv"],
            ".json": ["file2.json", "file5.json"],
            ".txt": ["file4.txt"],
        }

        from hed.tools.util.io_util import separate_by_ext  # Import inside to avoid circular dependencies

        result = separate_by_ext(file_paths)

        self.assertEqual(result, expected_result)

    @patch("hed.tools.util.io_util.get_full_extension")
    def test_separate_by_ext_empty_list(self, mock_get_full_extension):
        mock_get_full_extension.return_value = None  # No calls expected for an empty list

        from hed.tools.util.io_util import separate_by_ext

        result = separate_by_ext([])

        self.assertEqual(result, {})

    @patch("hed.tools.util.io_util.get_full_extension")
    def test_separate_by_ext_mixed_extensions(self, mock_get_full_extension):
        file_paths = ["file1.log", "file2.json", "file3.log", "file4.json"]

        mock_get_full_extension.side_effect = [
            ("file1", ".log"),
            ("file2", ".json"),
            ("file3", ".log"),
            ("file4", ".json"),
        ]

        expected_result = {
            ".log": ["file1.log", "file3.log"],
            ".json": ["file2.json", "file4.json"],
        }

        from hed.tools.util.io_util import separate_by_ext

        result = separate_by_ext(file_paths)

        self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
