import os
import unittest
from werkzeug.utils import secure_filename
from hed.errors.exceptions import HedFileError
from hed.tools.io_util import get_file_list, get_path_components


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
        dir_pairs = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/hed_pairs/prologue_tests')
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

    def test_get_file_list_case(self):
        dir_data = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        file_list = get_file_list(dir_data, name_prefix='STERNBerg', extensions=[".Tsv"])
        for item in file_list:
            filename = os.path.basename(item)
            self.assertTrue(filename.startswith('sternberg'))

    def test_get_path_components(self):
        base_path = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s'
        file_path1 = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s/sub-01/ses-1/eeg/temp_events.tsv'
        comps1 = get_path_components(file_path1, base_path)
        self.assertEqual(comps1[0], os.path.abspath(base_path),
                         "get_path_components base_path is is the first component")
        self.assertEqual(len(comps1), 4, "get_path_components has correct number of components")
        comps2 = get_path_components(base_path, base_path)
        self.assertEqual(comps2[0], os.path.abspath(base_path), "get_path_components base_path is its own base_path")
        self.assertEqual(len(comps2), 1, "get_path_components base_path has no additional components")
        file_path3 = 'D:/Research/HED/hed-examples/datasets/eeg_ds003654s/temp_events.tsv'
        comps3 = get_path_components(file_path3, base_path)
        self.assertEqual(comps3[0], os.path.abspath(base_path), "get_path_components base_path is its own base_path")
        self.assertEqual(len(comps2), 1, "get_path_components file in base_path has no additional components")


if __name__ == '__main__':
    unittest.main()
