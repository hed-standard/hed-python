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
        with self.assertRaises(HedFileError):
            dict1 = FileDictionary("My name", file_list, key_indices=(0, 1))


if __name__ == '__main__':
    unittest.main()
