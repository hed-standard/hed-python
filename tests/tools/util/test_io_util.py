import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.tools.util.io_util import check_filename, extract_suffix_path, clean_filename, \
    get_alphanumeric_path, get_file_list, get_path_components, get_task_from_file, \
    parse_bids_filename, get_allowed, get_filtered_by_element, get_full_extension, group_by_suffix


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_dir = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                     '../../data/bids_tests/eeg_ds003645s_hed'))
        stern_base_dir = os.path.join(os.path.dirname(__file__), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(__file__), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.realpath(os.path.join(stern_base_dir, "sternberg_test_events.tsv"))
        cls.stern_test2_path = os.path.realpath(os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv"))
        cls.stern_test3_path = os.path.realpath(os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv"))
        cls.attention_shift_path = os.path.realpath(os.path.join(att_base_dir,
                                                                 "sub-001_task-AuditoryVisualShift_run-01_events.tsv"))

    def test_check_filename(self):
        name1 = "/user/local/task_baloney.gz_events.nii"
        check1a = check_filename(name1, extensions=[".txt", ".nii"])
        self.assertTrue(check1a, "check_filename should return True if has required extension")
        check1b = check_filename(name1, name_prefix="apple", extensions=[".txt", ".nii"])
        self.assertFalse(check1b, "check_filename should return False if right extension but wrong prefix")
        check1c = check_filename(name1, name_suffix='_events')
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
        suffix_path = extract_suffix_path('c:/myroot/temp.tsv', 'c:')
        self.assertTrue(suffix_path.endswith('temp.tsv'), "extract_suffix_path has the right path")

    def test_clean_file_name(self):
        file1 = clean_filename('mybase')
        self.assertEqual(file1, "mybase", "generate_file_name should return the base when other arguments not set")
        filename = clean_filename("")
        self.assertEqual('', filename, "Return empty when all arguments are none")
        filename = clean_filename(None)
        self.assertEqual('', filename,
                         "Return empty when base_name, prefix, and suffix are None, but extension is not")
        filename = clean_filename('c:/temp.json')
        self.assertEqual('c_temp.json', filename,
                         "Returns stripped base_name + extension when prefix, and suffix are None")

    def test_get_allowed(self):
        test_value = 'events.tsv'
        value = get_allowed(test_value, 'events')
        self.assertEqual(value, 'events', "get_allowed matches starts with when string")
        value = get_allowed(test_value, None)
        self.assertEqual(value, test_value, "get_allowed if None is passed for allowed, no requirement is set.")
        test_value1 = "EventsApples.tsv"
        value1 = get_allowed(test_value1, ["events", "annotations"])
        self.assertEqual(value1, "events", "get_allowed is case insensitive")
        value2 = get_allowed(test_value1, [])
        self.assertEqual(value2, test_value1)

    def test_get_alphanumeric_path(self):
        mypath1 = 'g:\\String1%_-sTring2\n//string3\\\\string4.pnG'
        repath1 = get_alphanumeric_path(mypath1)
        self.assertEqual('g_String1_sTring2_string3_string4_pnG', repath1)
        repath2 = get_alphanumeric_path(mypath1, '$')
        self.assertEqual('g$String1$sTring2$string3$string4$pnG', repath2)

    def test_get_file_list_case(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, name_prefix='STERNBerg', extensions=[".Tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_file_list_exclude_dir(self):
        dir_data = os.path.realpath(os.path.join(os.path.dirname(__file__), '../../data/bids_tests/eeg_ds003645s_hed'))
        file_list1 = get_file_list(dir_data, extensions=[".bmp"])
        self.assertEqual(3, len(file_list1), 'get_file_list has the right number of files when no exclude')
        file_list2 = get_file_list(dir_data, extensions=[".bmp"], exclude_dirs=[])
        self.assertEqual(len(file_list1), len(file_list2), 'get_file_list should not change when exclude_dir is empty')
        file_list3 = get_file_list(dir_data, extensions=[".bmp"], exclude_dirs=['stimuli'])
        self.assertFalse(file_list3, 'get_file_list should return an empty list when all are excluded')

    def test_get_file_list_files(self):
        dir_pairs = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 '../../data/schema_tests/prologue_tests')
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
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, name_prefix='sternberg', extensions=[".tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_file_list_suffix(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data')
        file_list = get_file_list(dir_data, extensions=[".json", ".tsv"])
        for item in file_list:
            if item.endswith(".json") or item.endswith(".tsv"):
                continue
            raise HedFileError("BadFileType", "get_event_files expected only .html or .js files", "")

    def test_get_filtered_by_element(self):
        file_list1 = ['D:\\big\\subj-01_task-stop_events.tsv', 'D:\\big\\subj-01_task-rest_events.tsv',
                      'D:\\big\\subj-01_events.tsv', 'D:\\big\\subj-01_task-stop_task-go_events.tsv']
        new_list1 = get_filtered_by_element(file_list1, ['task-stop'])
        self.assertEqual(len(new_list1), 2, "It should have the right length when one element filtered")
        new_list2 = get_filtered_by_element(file_list1, ['task-stop', 'task-go'])
        self.assertEqual(len(new_list2), 2, "It should have the right length when meets multiple criteria")
        new_list3 = get_filtered_by_element(file_list1, [])
        self.assertFalse(len(new_list3))
        new_list3 = get_filtered_by_element(file_list1, [])
        self.assertFalse(len(new_list3))
        new_list4 = get_filtered_by_element([], ['task-go'])
        self.assertFalse(len(new_list4))

    def test_get_path_components(self):
        base_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../../data/bids_test/eeg_ds003645s'))
        file_path1 = os.path.realpath(os.path.join(base_path, 'sub-002/eeg/sub-002_FacePerception_run-1_events.tsv'))
        comps1 = get_path_components(base_path, file_path1)
        self.assertEqual(len(comps1), 2, "get_path_components has correct number of components")
        comps2 = get_path_components(base_path, base_path)
        self.assertIsInstance(comps2, list)
        self.assertFalse(comps2, "get_path_components base_path is its own base_path")
        file_path3 = os.path.join(base_path, 'temp_events.tsv')
        comps3 = get_path_components(base_path, file_path3)
        self.assertFalse(comps3, "get_path_components files directly in base_path don't have components ")

    def test_get_task_from_file(self):
        task1 = get_task_from_file("H:/alpha/base_task-blech.tsv")
        self.assertEqual("blech", task1)
        task2 = get_task_from_file("task-blech")
        self.assertEqual("blech", task2)



class TestGetFullExtension(unittest.TestCase):
    def test_single_extension(self):
        self.assertEqual(get_full_extension("file.txt"), ("file", ".txt"),
                         "Should work with single extensions.")

    def test_multiple_extensions(self):
        self.assertEqual(get_full_extension("archive.tar.gz"), ("archive", ".tar.gz"),
                         "Should work with multiple extensions.")

    def test_no_extension(self):
        self.assertEqual(get_full_extension("filename"), ("filename", ""),
                         "Should work with no extension.")

    def test_hidden_file_no_extension(self):
        self.assertEqual(get_full_extension(".gitignore"), (".gitignore", ""),
                        "Should work with hidden files without extensions.")

    def test_hidden_file_with_extension(self):
        self.assertEqual(get_full_extension(".config.json"), (".config", ".json"),
                         "Should work with hidden files with extensions.")

    def test_nested_directory(self):
        self.assertEqual(get_full_extension("path/to/archive.tar.gz"), ("path/to/archive", ".tar.gz"),
                         "")


class TestGroupBySuffixes(unittest.TestCase):
    def test_basic_grouping(self):
        file_list = [
            "/path/to/file_abc.json",
            "/path/to/another_def.json",
            "/path/to/something_xyz.tsv"
        ]
        expected_groups = {
            "abc": ["/path/to/file_abc.json"],
            "def": ["/path/to/another_def.json"],
            "xyz": ["/path/to/something_xyz.tsv"]
        }

        result = group_by_suffix(file_list)
        self.assertEqual(result, expected_groups, "Basic grouping should work correctly")

    def test_files_without_underscore(self):
        file_list = [
            "/path/to/filename.json",  # No underscore
            "/path/to/anotherfile.tsv",
            "/path/to/ignore_me.txt"
        ]
        expected1 = {
            "filename": ["/path/to/filename.json"],
            "anotherfile": ["/path/to/anotherfile.tsv"],
            "me": ["/path/to/ignore_me.txt"]
        }

        result1 = group_by_suffix(file_list)
        self.assertEqual(result1, expected1, "valid_groups")

    def test_files_with_multiple_underscores(self):
        file_list = [
            "/path/to/project_file_abc.json",
            "/path/to/another_long_name_def.json",
            "/path/to/another_def.json",
        ]
        expected = {
            "abc": ["/path/to/project_file_abc.json"],
            "def": ["/path/to/another_long_name_def.json", "/path/to/another_def.json"]
        }
        result = group_by_suffix(file_list)
        self.assertEqual(result, expected, "It should parse with multiple underscores")  # Should be empty since len(split) > 2

    def test_empty_file_list(self):
        result1 = group_by_suffix([])
        self.assertEqual(result1, {})  # Should return an empty dict


class TestParseBidsFilename(unittest.TestCase):

    def test_standard_bids_filename(self):
        self.assertEqual(
            parse_bids_filename("sub-01_task-rest_bold.nii.gz"),
            {
                "basename": "sub-01_task-rest_bold",
                "suffix": "bold",
                "prefix": None,
                "ext": ".nii.gz",
                "bad": [],
                "entities": {"sub": "01", "task": "rest"}
            }
        )

    def test_filename_without_entities(self):
        self.assertEqual(
            parse_bids_filename("dataset_description.json"),
            {
                "basename": "dataset_description",
                "suffix": "description",
                "prefix": "dataset",
                "ext": ".json",
                "bad": [],
                "entities": {}
            }
        )

    def test_filename_with_multiple_entities(self):
        self.assertEqual(
            parse_bids_filename("sub-02_ses-1_task-memory_run-2_bold.nii.gz"),
            {
                "basename": "sub-02_ses-1_task-memory_run-2_bold",
                "suffix": "bold",
                "prefix": None,
                "ext": ".nii.gz",
                "bad": [],
                "entities": {"sub": "02", "ses": "1", "task": "memory", "run": "2"}
            }
        )

    def test_invalid_filename_without_underscore_before_suffix(self):
        self.assertEqual(
            parse_bids_filename("sub-03task-memorybold.nii.gz"),
            {
                "basename": "sub-03task-memorybold",
                "suffix": None,
                "prefix": None,
                "ext": ".nii.gz",
                "bad": ["sub-03task-memorybold"],
                "entities": {}
            }
        )

    def test_empty_filename(self):
        self.assertEqual(
            parse_bids_filename(""),
            {
                "basename": "",
                "suffix": None,
                "prefix": None,
                "ext": "",
                "bad": [],
                "entities": {}
            }
        )

    def test_filename_with_missing_entity_values(self):
        self.assertEqual(
            parse_bids_filename("sub-_task-_bold.nii.gz"),
            {
                "basename": "sub-_task-_bold",
                "suffix": "bold",
                "prefix": None,
                "ext": ".nii.gz",
                "bad": ["sub-", "task-"],
                "entities": {}
            }
        )

    def test_filename_with_missing_suffix(self):
        self.assertEqual(
            parse_bids_filename("sub-04_ses-2_task-motor.nii.gz"),
            {
                "basename": "sub-04_ses-2_task-motor",
                "suffix": None,
                "prefix": None,
                "ext": ".nii.gz",
                "bad": [],
                "entities": {"sub": "04", "ses": "2", "task": "motor"}
            }
        )

    def test_filename_with_unknown_format(self):
        self.assertEqual(
            parse_bids_filename("invalidfileformat"),
            {
                "basename": "invalidfileformat",
                "suffix": "invalidfileformat",
                "prefix": None,
                "ext": "",
                "bad": [],
                "entities": {}
            }
        )

    def test_parse_bids_filename_full(self):
        the_path1 = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        name_dict = parse_bids_filename(the_path1)
        self.assertEqual(name_dict["suffix"], 'bold',
                         "parse_bids_filename should correctly parse name_suffix for full path")
        self.assertEqual(name_dict["ext"], '.json', "parse_bids_filename should correctly parse ext for full path")
        entity_dict = name_dict["entities"]
        self.assertIsInstance(entity_dict, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict['sub'], '01', "parse_bids_filename should have a sub entity")
        self.assertEqual(entity_dict['ses'], 'test', "parse_bids_filename should have a ses entity")
        self.assertEqual(entity_dict['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(entity_dict['run'], '2', "parse_bids_filename should have a run entity")
        self.assertEqual(len(entity_dict), 4, "parse_bids_filename should 4 entity_dict in the dictionary")

        the_path2 = 'sub-01.json'
        name_dict2 = parse_bids_filename(the_path2)
        self.assertFalse(name_dict2["suffix"], "parse_bids_filename should not return a suffix if no suffix")
        self.assertEqual(len(name_dict2["entities"]), 1,
                         "parse_bids_filename should have entity dictionary if suffix missing")

    def test_parse_bids_filename_partial(self):
        path1 = 'task-overt_bold.json'
        name_dict1 = parse_bids_filename(path1)
        self.assertEqual(name_dict1["ext"], '.json', "parse_bids_filename should correctly parse ext for name")
        entity_dict1 = name_dict1["entities"]
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should 1 entity_dict in the dictionary")

        path2 = 'task-overt_bold'
        name_dict2 = parse_bids_filename(path2)
        self.assertEqual(name_dict2["suffix"], 'bold',
                         "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(name_dict2["ext"], '', "parse_bids_filename should return empty extension when only name")
        entity_dict2 = name_dict2["entities"]
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict2['task'], 'overt', "parse_bids_filename should have a task entity")

        path3 = 'bold'
        name_dict3 = parse_bids_filename(path3)
        self.assertEqual(name_dict3["suffix"], 'bold',
                         "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(name_dict3["ext"], '', "parse_bids_filename should return empty extension when only name")
        entity_dict3 = name_dict3["entities"]
        self.assertEqual(len(entity_dict3), 0, "parse_bids_filename should not have a task entity")

    def test_parse_bids_filename_unmatched(self):
        path1 = 'dataset_description.json'
        name_dict1 = parse_bids_filename(path1)
        self.assertEqual(name_dict1["suffix"], "description")
        self.assertEqual(name_dict1["ext"], '.json', "parse_bids_filename should correctly parse ext for name")
        entity_dict1 = name_dict1["entities"]
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(len(entity_dict1), 0, "parse_bids_filename should 1 entity_dict in the dictionary")
        self.assertEqual(name_dict1["prefix"], "dataset",
                         "parse_bids_filename should have entity dictionary if suffix missing")

    def test_parse_bids_filename_invalid(self):
        path1 = 'task--x_sub-01_description.json'
        name_dict1 = parse_bids_filename(path1)
        self.assertEqual(name_dict1["suffix"], "description")
        self.assertEqual(name_dict1["ext"], '.json', "parse_bids_filename should correctly parse ext for name")
        self.assertEqual(name_dict1['bad'], ['task--x'], "parse_bids_filename should have a task entity")
        entity_dict1 = name_dict1["entities"]
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should 1 entity_dict in the dictionary")


if __name__ == "__main__":
    unittest.main()
