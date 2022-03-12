import unittest
import os

from hed.errors.exceptions import HedFileError
from hed.tools import BidsTsvDictionary
from hed.util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bids_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed')
        cls.file_list = get_file_list(cls.bids_base_dir, name_suffix="_events",
                                      extensions=['.tsv'], exclude_dirs=['stimuli'])

    def test_bids_tsv_dictionary_constructor_valid(self):
        dict1 = BidsTsvDictionary(self.file_list, entities=('sub', 'run'))
        self.assertEqual(6, len(dict1.key_list),
                         "BidsTsvDictionary should have correct number of entries when key okay")

    def test_bids_tsv_dictionary_constructor_invalid(self):
        try:
            dict1 = BidsTsvDictionary(self.file_list, entities=('sub'))
        except HedFileError:
            pass
        except Exception:
            self.fail("BidsTsvDictionary threw the wrong exception when duplicate key")
        else:
            self.fail("FileDictionary should have thrown a HedFileError when duplicate key")

    def test_create_split_dict(self):
        dict1 = BidsTsvDictionary(self.file_list, entities=('sub', 'run'))
        dist1_split, leftovers = dict1.create_split_dict('run')
        self.assertIsInstance(dist1_split, dict, "create_split_dict returns a dictionary")
        self.assertEqual(3, len(dist1_split), 'create_split_dict should return the correct number of items')
        for value in dist1_split.values():
            self.assertIsInstance(value, BidsTsvDictionary, "create_split_dict dict has BidsTsvDictionary objects")
        self.assertFalse(leftovers, "create_split_dict leftovers should be empty")


if __name__ == '__main__':
    unittest.main()
