import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.tools.io_utils import get_file_list, parse_bids_filename, get_path_components


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")

    def test_get_file_list_files(self):
        dir_pairs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/hed_pairs')
        test_files = [name for name in os.listdir(dir_pairs) if os.path.isfile(os.path.join(dir_pairs, name))]
        file_list1 = get_file_list(dir_pairs)
        for file in file_list1:
            if os.path.basename(file) in test_files:
                continue
            raise HedFileError("FileNotFound", f"get_event_files should have found file {file}", "")

        for file in test_files:
            if os.path.join(dir_pairs, file) in file_list1:
                continue
            raise HedFileError("FileShouldNotBeFound", f"get_event_files should have not have found file {file}", "")

    def test_get_get_file_list_suffix(self):
        dir_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data')
        file_list = get_file_list(dir_data, extensions=[".json", ".tsv"])
        for item in file_list:
            if item.endswith(".json") or item.endswith(".tsv"):
                continue
            raise HedFileError("BadFileType", "get_event_files expected only .html or .js files", "")

    def test_get_file_list_prefix(self):
        dir_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, name_prefix='sternberg', extensions=[".tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_path_components(self):
        base_path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
        file_path1 = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s/sub-01/ses-1/eeg/temp_events.tsv'
        comps1 = get_path_components(file_path1, base_path)
        self.assertEqual(comps1[0], os.path.abspath(base_path), "get_path_components base_path is is the first component")
        self.assertEqual(len(comps1), 4, "get_path_components has correct number of components")
        comps2 = get_path_components(base_path, base_path)
        self.assertEqual(comps2[0], os.path.abspath(base_path), "get_path_components base_path is its own base_path")
        self.assertEqual(len(comps2), 1, "get_path_components base_path has no additional components")
        file_path3 = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s/temp_events.tsv'
        comps3 = get_path_components(file_path3, base_path)
        self.assertEqual(comps3[0], os.path.abspath(base_path), "get_path_components base_path is its own base_path")
        self.assertEqual(len(comps2), 1, "get_path_components file in base_path has no additional components")

    def test_parse_bids_filename(self):
        the_path = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        suffix, ext, entity_dict = parse_bids_filename(the_path)
        self.assertEqual(suffix, 'bold', "parse_bids_filename should correctly parse name_suffix for full path")
        self.assertEqual(ext, '.json', "parse_bids_filename should correctly parse ext for full path")
        self.assertIsInstance(entity_dict, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(entity_dict['sub'], '01', "parse_bids_filename should have a sub entity")
        self.assertEqual(entity_dict['ses'], 'test', "parse_bids_filename should have a ses entity")
        self.assertEqual(entity_dict['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(entity_dict['run'], '2', "parse_bids_filename should have a run entity")
        self.assertEqual(len(entity_dict), 4, "parse_bids_filename should 4 entities in the dictionary")

    def test_parse_bids_filename_partial(self):
        path = 'task-overt_bold.json'
        suffix, ext, entity_dict = parse_bids_filename(path)
        self.assertEqual(suffix, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext, '.json', "parse_bids_filename should correctly parse ext for name")
        self.assertIsInstance(entity_dict, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(entity_dict['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(len(entity_dict), 1, "parse_bids_filename should 1 entities in the dictionary")
        path1 = 'task-overt_bold'
        suffix1, ext1, entity_dict1 = parse_bids_filename(path1)
        self.assertEqual(suffix1, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext1, '', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        path2 = 'bold'
        suffix2, ext2, entity_dict2 = parse_bids_filename(path2)
        self.assertEqual(suffix2, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext2, '', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(len(entity_dict2), 0, "parse_bids_filename should return empty dictionary when no entities")

if __name__ == '__main__':
    unittest.main()
