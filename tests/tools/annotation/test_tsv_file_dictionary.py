import unittest
import os

from hed.errors.exceptions import HedFileError
from hed.tools import TsvFileDictionary
from hed.util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bids_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed')

    def test_event_file_dictionary_constructor_valid(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        dict1 = TsvFileDictionary(file_list)
        self.assertEqual(6, len(dict1.key_list), "FileDictionary should have correct number of entries when key okay")

    def test_constructor_invalid(self):
        file_list = get_file_list(self.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])
        try:
            dict1 = TsvFileDictionary(file_list, name_indices=(0, 1))
        except HedFileError:
            pass
        except Exception:
            self.fail("EventFileDictionary threw the wrong exception when duplicate key")
        else:
            self.fail("FileDictionary should have thrown a HedFileError when duplicate key")


if __name__ == '__main__':
    unittest.main()
