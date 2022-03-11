import unittest
import os

from hed.errors.exceptions import HedFileError
from hed.tools import BidsFileDictionary
from hed.util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bids_base_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                         '../../data/bids/eeg_ds003654s_hed')
        cls.file_list = get_file_list(cls.bids_base_dir, name_suffix="_events",
                                  extensions=['.tsv'], exclude_dirs=['stimuli'])

    def test_constructor_valid(self):
        dict1 = BidsFileDictionary(self.file_list, entities=('sub', 'run'))
        self.assertEqual(6, len(dict1.key_list),
                         "BidsFileDictionary should have correct number of entries when key okay")

    def test_constructor_invalid(self):
        try:
            dict1 = BidsFileDictionary(self.file_list, entities=('sub', 'task'))
        except HedFileError:
            pass
        except Exception:
            self.fail("BidsFileDictionary threw the wrong exception when duplicate key")
        else:
            self.fail("BidsFileDictionary should have thrown a HedFileError when duplicate key")

    def test_match_query(self):
        entity_dict = {'sub':'01', 'task': 'tempTask', 'run':'2'}
        query_dict1 = {'sub':['01', '03']}
        result1 = BidsFileDictionary.match_query(query_dict1, entity_dict)
        self.assertTrue(result1, "match_query should return true when entity in the dictionary")
        query_dict2 = {'sub':['02', '03']}
        result2 = BidsFileDictionary.match_query(query_dict2, entity_dict)
        self.assertFalse(result2, "match_query should return False when entity not in the dictionary")
        query_dict3 = {'sub': ['01', '03'], 'run':['1', '2']}
        result3 = BidsFileDictionary.match_query(query_dict3, entity_dict)
        self.assertTrue(result3, "match_query should return True when entity in the dictionary")
        query_dict4 = {'sub': ['01', '03'], 'run': ['3', '2']}
        result4 = BidsFileDictionary.match_query(query_dict4, entity_dict)
        self.assertTrue(result4, "match_query should return False when entity not in the dictionary")

    def test_make_query(self):
        dict1 = BidsFileDictionary(self.file_list, entities=('sub', 'run'))
        results1 = dict1.make_query(query_dict={'sub': '*', 'run': '*'})
        self.assertEqual(len(results1), len(dict1.file_dict), "make_query should return all of the entries when *")
        results2 = dict1.make_query(query_dict={'sub': '*', 'run': ['1']})
        self.assertEqual(len(results2), 2, "make_query should return the right number of entries ")


if __name__ == '__main__':
    unittest.main()
