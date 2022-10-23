import unittest
import os

from hed.errors.exceptions import HedFileError
from hed.tools.analysis.file_dictionary import FileDictionary
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bids_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../data/bids_tests/eeg_ds003654s_hed')

    def test_constructor_valid(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        dict1 = FileDictionary("My name", file_list)
        self.assertEqual(6, len(dict1.key_list), "FileDictionary should have correct number of entries when key okay")

    def test_constructor_invalid(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        with self.assertRaises(HedFileError) as context:
            FileDictionary("My name", file_list, key_indices=(0, 1))
        self.assertEqual(context.exception.args[0], 'NonUniqueFileKeys')

    def test_file_list(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        dict1 = FileDictionary("My name", file_list)
        internal_list = dict1.file_list
        self.assertIsInstance(internal_list, list)
        self.assertEqual(6, len(internal_list))

    def test_get_file_path(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        dict1 = FileDictionary("My name", file_list)
        new_path = dict1.get_file_path('sub-002_run-1')
        self.assertTrue(new_path)
        bad_path = dict1.get_file_path('junk')
        self.assertFalse(bad_path)

    def test_iter_files(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        dict1 = FileDictionary("My name", file_list)
        new_list = [next_file for key, next_file in dict1.iter_files()]
        self.assertIsInstance(new_list, list)
        self.assertEqual(len(new_list), len(file_list))

    def test_key_diffs(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        dict1 = FileDictionary("My name", file_list)
        dict2 = FileDictionary("Your name", file_list, key_indices=(0, 1, 2))
        diffs1 = dict1.key_diffs(dict2)
        diffs2 = dict2.key_diffs(dict1)
        self.assertEqual(len(diffs1), 2*len(file_list))
        self.assertIsInstance(diffs1, list)
        self.assertIsInstance(diffs2, list)
        diffs3 = dict1.key_diffs(dict1)
        self.assertIsInstance(diffs3, list)
        self.assertFalse(diffs3)


if __name__ == '__main__':
    unittest.main()
