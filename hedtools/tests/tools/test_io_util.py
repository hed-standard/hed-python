import os
import unittest
from hed.errors.exceptions import HedFileError
from hed.tools.io_util import generate_filename, get_dir_dictionary, get_file_list, get_path_components


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bids_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/bids_old')
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")

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
