import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.util.io_util import check_filename, extract_suffix_path, generate_filename, get_dir_dictionary, get_file_list, \
    get_path_components

from hed.util.io_util import parse_bids_filename, _split_entity


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/bids/eeg_ds003654s_hed')
        stern_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "sub-001_task-AuditoryVisualShiftHed2_run-01_events.tsv")

    def test_check_filename(self):
        name1 = "/user/local/task_baloney.gz_events.nii"
        check1a = check_filename(name1, extensions=[".txt", ".nii"])
        self.assertTrue(check1a, "check_filename should return true if has required extension")
        check1b = check_filename(name1, name_prefix="apple", extensions=[".txt", ".nii"])
        self.assertFalse(check1b, "check_filename should return false if right extension but wrong prefix")
        check1c = check_filename(name1, name_suffix='_events')
        self.assertTrue(check1c, "check_filename should return true if has a default extension and correct suffix")
        name2 = "/user/local/task_baloney.gz_events.nii.gz"
        check2a = check_filename(name2, extensions=[".txt", ".nii"])
        self.assertFalse(check2a, "check_filename should return false if extension does not match")
        check2b = check_filename(name2, extensions=[".txt", ".nii.gz"])
        self.assertTrue(check2b, "check_filename should return true if extension with gz matches")
        check2c = check_filename(name2, name_suffix="_events", extensions=[".txt", ".nii.gz"])
        self.assertTrue(check2c, "check_filename should return true if suffix after extension matches")
        name3 = "Changes"
        check3a = check_filename(name3, name_suffix="_events", extensions=None)
        print("to here")

    def test_extract_suffix_path(self):
        suffix_path = extract_suffix_path('c:/myroot/temp.tsv', 'c:')
        self.assertTrue(suffix_path.endswith('temp.tsv'), "extract_suffix_path has the right path")

    def test_generate_file_name(self):
        file1 = generate_filename('mybase')
        self.assertEqual(file1, "mybase", "generate_file_name should return the base when other arguments not set")
        file2 = generate_filename('mybase', name_prefix="prefix")
        self.assertEqual(file2, "prefixmybase", "generate_file_name should return correct name when prefix set")
        file3 = generate_filename('mybase', name_prefix="prefix", extension=".json")
        self.assertEqual(file3, "prefixmybase.json", "generate_file_name should return correct name for extension")
        file4 = generate_filename('mybase', name_suffix="suffix")
        self.assertEqual(file4, "mybasesuffix", "generate_file_name should return correct name when suffix set")
        file5 = generate_filename('mybase', name_suffix="suffix", extension=".json")
        self.assertEqual(file5, "mybasesuffix.json", "generate_file_name should return correct name for extension")
        file6 = generate_filename('mybase', name_prefix="prefix", name_suffix="suffix", extension=".json")
        self.assertEqual(file6, "prefixmybasesuffix.json",
                         "generate_file_name should return correct name for all set")
        filename = generate_filename(None, name_prefix=None, name_suffix=None, extension=None)
        self.assertEqual('', filename, "Return empty when all arguments are none")
        filename = generate_filename(None, name_prefix=None, name_suffix=None, extension='.txt')
        self.assertEqual('', filename,
                         "Return empty when base_name, prefix, and suffix are None, but extension is not")
        filename = generate_filename('c:/temp.json', name_prefix=None, name_suffix=None, extension='.txt')
        self.assertEqual('c_temp.txt', filename,
                         "Returns stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename('temp.json', name_prefix='prefix_', name_suffix='_suffix', extension='.txt')
        self.assertEqual('prefix_temp_suffix.txt', filename,
                         "Return stripped base_name + extension when prefix, and suffix are None")
        filename = generate_filename(None, name_prefix='prefix_', name_suffix='suffix', extension='.txt')
        self.assertEqual('prefix_suffix.txt', filename,
                         "Returns correct string when no base_name")
        filename = generate_filename('event-strategy-v3_task-matchingpennies_events.json',
                                     name_suffix='_blech', extension='.txt')
        self.assertEqual('event-strategy-v3_task-matchingpennies_events_blech.txt', filename,
                         "Returns correct string when base_name with hyphens")
        filename = generate_filename('HED7.2.0.xml', name_suffix='_blech', extension='.txt')
        self.assertEqual('HED7.2.0_blech.txt', filename, "Returns correct string when base_name has periods")

    def test_get_dir_dictionary(self):
        dir_dict = get_dir_dictionary(self.bids_dir, name_suffix="_events")
        self.assertTrue(isinstance(dir_dict, dict), "get_dir_dictionary returns a dictionary")
        self.assertEqual(len(dir_dict), 3, "get_dir_dictionary returns a dictionary of the correct length")

    def test_get_file_list_files(self):
        dir_pairs = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/schema_test_data/prologue_tests')
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

    def test_get_get_file_list_suffix(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data')
        file_list = get_file_list(dir_data, extensions=[".json", ".tsv"])
        for item in file_list:
            if item.endswith(".json") or item.endswith(".tsv"):
                continue
            raise HedFileError("BadFileType", "get_event_files expected only .html or .js files", "")

    def test_get_file_list_prefix(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, name_prefix='sternberg', extensions=[".tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_file_list_case(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, name_prefix='STERNBerg', extensions=[".Tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_file_list_exclude_dir(self):
        dir_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/bids/eeg_ds003654s_hed')
        file_list1 = get_file_list(dir_data, extensions=[".bmp"])
        self.assertEqual(345, len(file_list1), 'get_file_list has the right number of files when no exclude')
        file_list2 = get_file_list(dir_data, extensions=[".bmp"], exclude_dirs=[])
        self.assertEqual(len(file_list1), len(file_list2), 'get_file_list should not change when exclude_dir is empty')
        file_list3 = get_file_list(dir_data, extensions=[".bmp"], exclude_dirs=['stimuli'])
        self.assertFalse(file_list3, 'get_file_list should return an empty list when all are excluded')

    def test_get_path_components(self):
        base_path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
        file_path1 = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s/sub-01/ses-1/eeg/temp_events.tsv'
        comps1 = get_path_components(file_path1, base_path)
        self.assertEqual(comps1[0], os.path.realpath(base_path),
                         "get_path_components base_path is is the first component")
        self.assertEqual(len(comps1), 4, "get_path_components has correct number of components")
        comps2 = get_path_components(base_path, base_path)
        self.assertEqual(comps2[0], os.path.realpath(base_path), "get_path_components base_path is its own base_path")
        self.assertEqual(len(comps2), 1, "get_path_components base_path has no additional components")
        file_path3 = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s/temp_events.tsv'
        comps3 = get_path_components(file_path3, base_path)
        self.assertEqual(comps3[0], os.path.realpath(base_path), "get_path_components base_path is its own base_path")
        self.assertEqual(len(comps2), 1, "get_path_components file in base_path has no additional components")

    def test_parse_bids_filename_full(self):
        the_path1 = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        suffix1, ext1, entity_dict1 = parse_bids_filename(the_path1)
        self.assertEqual(suffix1, 'bold', "parse_bids_filename should correctly parse name_suffix for full path")
        self.assertEqual(ext1, '.json', "parse_bids_filename should correctly parse ext for full path")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict1['sub'], '01', "parse_bids_filename should have a sub entity")
        self.assertEqual(entity_dict1['ses'], 'test', "parse_bids_filename should have a ses entity")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(entity_dict1['run'], '2', "parse_bids_filename should have a run entity")
        self.assertEqual(len(entity_dict1), 4, "parse_bids_filename should 4 entity_dict in the dictionary")

        the_path2 = 'sub-01.json'
        suffix2, ext2, entity_dict2 = parse_bids_filename(the_path2)
        self.assertFalse(suffix2, "parse_bids_filename should not return a suffix if no suffix")
        self.assertTrue(entity_dict2, "parse_bids_filename should have entity dictionary if suffix missing")

    def test_parse_bids_filename_partial(self):
        path1 = 'task-overt_bold.json'
        suffix1, ext1, entity_dict1 = parse_bids_filename(path1)
        self.assertEqual(ext1, '.json', "parse_bids_filename should correctly parse ext for name")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should 1 entity_dict in the dictionary")
        path2 = 'task-overt_bold'
        suffix2, ext2, entity_dict2 = parse_bids_filename(path2)
        self.assertEqual(suffix2, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext2, '', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict2['task'], 'overt', "parse_bids_filename should have a task entity")
        path3 = 'bold'
        suffix3, ext3, entity_dict3 = parse_bids_filename(path3)
        self.assertEqual(suffix3, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext3, '', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict3, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(len(entity_dict3), 0, "parse_bids_filename should return empty dictionary when no entity_dict")

    def test_parse_bids_filename_unmatched(self):
        path1 = 'dataset_description.json'
        try:
            suffix1, ext1, entity_dict1 = parse_bids_filename(path1)
        except HedFileError:
            pass
        except Exception:
            self.fail("parse_bids_filename threw the wrong exception when filename invalid")
        else:
            self.fail("parse_bids_filename should have thrown a HedFileError when duplicate key")

    def test_parse_bids_filename_invalid(self):
        path1 = 'task_sub-01_description.json'
        try:
            suffix1, ext1, entity_dict1 = parse_bids_filename(path1)
        except HedFileError:
            pass
        except Exception:
            self.fail("parse_bids_filename threw the wrong exception when missing value in name-value")
        else:
            self.fail("parse_bids_filename should have thrown a HedFileError when missing value in name-value")


    def test_split_entity(self):
        ent_dict1 = _split_entity("apple")
        self.assertEqual("apple", ent_dict1["suffix"], "_split_entity returns the suffix of the entire piece")
        ent_dict2 = _split_entity("task-plenty")
        self.assertEqual("plenty", ent_dict2["value"], "_split_entity has the correct value")
        self.assertEqual("task", ent_dict2["key"], "_split_entity dictionary has a key key")
        self.assertFalse("suffix" in ent_dict2, "_split_entity has a key-value but no suffix")
        ent_dict3 = _split_entity("task-plenty-oops")
        self.assertEqual(1, len(ent_dict3), "_split_entity is returns a dictionary with 1 entry if invalid")
        self.assertTrue("bad" in ent_dict3, "_split_entity should have a bad component if invalid")
        ent_dict4 = _split_entity("    ")
        self.assertEqual(1, len(ent_dict4), "_split_entity is returns a dictionary with 1 entry if invalid")
        self.assertTrue("bad" in ent_dict4, "_split_entity should have a bad component if invalid")
        self.assertFalse(ent_dict4["bad"], "_split_entity bad value should be empty if blank piece")

if __name__ == '__main__':
    unittest.main()
