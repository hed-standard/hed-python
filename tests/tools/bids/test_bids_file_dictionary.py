import unittest
import os

from hed.errors.exceptions import HedFileError
from hed.tools.bids.bids_file_dictionary import BidsFileDictionary
from hed.tools.bids.bids_file import BidsFile
from hed.tools.util.io_util import get_file_list


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bids_base_dir = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                      '../../data/bids_tests/eeg_ds003645s_hed'))
        cls.bids_base_dir = bids_base_dir
        cls.file_list = get_file_list(bids_base_dir, name_suffix="_events",
                                      extensions=['.tsv'], exclude_dirs=['stimuli'])

    def test_constructor_valid(self):
        dict1 = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        self.assertEqual(6, len(dict1.key_list),
                         "BidsFileDictionary should have correct number of entries when key okay")
        file1 = dict1.get_file_path('sub-002_run-1')
        self.assertIsInstance(file1, str)
        file2 = dict1.get_file_path('junk')
        self.assertIsNone(file2)

    def test_constructor_invalid(self):
        with self.assertRaises(HedFileError) as context:
            BidsFileDictionary("My name", self.file_list, entities=('sub', 'task'))
        self.assertEqual(context.exception.args[0], "NonUniqueFileKeys")

    def test_iter(self):
        dict1 = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        for key, file in dict1.iter_files():
            self.assertIsInstance(key, str)
            self.assertIsInstance(file, BidsFile)

    def test_make_dict(self):
        bids_dict = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        dict1 = bids_dict.make_dict(self.file_list, ('sub', 'run'))
        self.assertIsInstance(dict1, dict, "make_dict creates a dictionary.")
        self.assertEqual(len(dict1), 6, "make_dict should return a dictionary of the right size.")
        for file in dict1.values():
            self.assertIsInstance(file, BidsFile, "make_dict dictionary values should be BidsFile")

    def test_make_dict_bad_input(self):
        bids_dict = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        with self.assertRaises(HedFileError) as context:
            bids_dict.make_dict("data", ('sub', 'run'))
        self.assertEqual(context.exception.args[0], "BadArgument")

    def test_make_query(self):
        dict1 = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        results1 = dict1.make_query(query_dict={'sub': '*', 'run': '*'})
        self.assertEqual(len(results1), len(dict1._file_dict), "make_query should return all of the entries when *.")
        results2 = dict1.make_query(query_dict={'sub': '*', 'run': ['1']})
        self.assertEqual(len(results2), 2, "make_query should return the right number of entries.")
        results3 = dict1.make_query(query_dict={'sub': '*', 'run': ['*']})
        self.assertFalse(results3, "make_query should return an empty dictionary when * is used in a list. ")
        results4 = dict1.make_query(query_dict={'sub': '*', 'run': ['*', '1']})
        self.assertEqual(len(results4), 2, "make_query should ignore the * in a list.")
        results5 = dict1.make_query(query_dict={'sub': '*', 'run': []})
        self.assertFalse(len(results5), "make_query be empty if the list for one of the entities is empty.")
        results6 = dict1.make_query(query_dict={'sub': '*'})
        self.assertEqual(len(results6), len(dict1._file_dict), "make_query should return all of the entries when *.")

    def test_match_query(self):
        entity_dict = {'sub': '01', 'task': 'tempTask', 'run': '2'}
        query_dict1 = {'sub': ['01', '03']}
        result1 = BidsFileDictionary.match_query(query_dict1, entity_dict)
        self.assertTrue(result1, "match_query should return true when entity in the dictionary")
        query_dict2 = {'sub': ['02', '03']}
        result2 = BidsFileDictionary.match_query(query_dict2, entity_dict)
        self.assertFalse(result2, "match_query should return False when entity not in the dictionary")
        query_dict3 = {'sub': ['01', '03'], 'run': ['1', '2']}
        result3 = BidsFileDictionary.match_query(query_dict3, entity_dict)
        self.assertTrue(result3, "match_query should return True when entity in the dictionary")
        query_dict4 = {'sub': ['01', '03'], 'run': ['3', '2']}
        result4 = BidsFileDictionary.match_query(query_dict4, entity_dict)
        self.assertTrue(result4, "match_query should return False when entity not in the dictionary")

    def test_match_query_bad(self):
        entity_dict = {'sub': '01', 'task': 'tempTask', 'run': '2'}
        query_dict1 = {'sess': ['01', '03']}
        self.assertFalse(BidsFileDictionary.match_query(query_dict1, entity_dict))
        query_dict2 = {'sub': '01'}
        self.assertFalse(BidsFileDictionary.match_query(query_dict2, entity_dict))

    def test_split_by_entity(self):
        dict1 = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        split_dict, leftovers = dict1.split_by_entity('sub')

        self.assertIsInstance(split_dict, dict, "split_by_entity returns a dictionary")
        self.assertEqual(2, len(split_dict), 'split_by_entity should return the correct number of items')
        for value in split_dict.values():
            self.assertIsInstance(value, BidsFileDictionary,
                                  'split_by_entity dictionary values should be BidsFileDictionary objects')
        self.assertFalse(leftovers, "split_by_entity leftovers should be empty")

    def test_split_by_entity_non_empty_leftovers(self):
        dict1 = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        split_dict, leftovers = dict1.split_by_entity('ses')
        self.assertFalse(split_dict)
        self.assertIsInstance(leftovers, BidsFileDictionary)

    def test_split_dict_by_entity(self):
        dict1 = BidsFileDictionary("My name", self.file_list, entities=('sub', 'run'))
        dist1_split, leftovers = BidsFileDictionary._split_dict_by_entity(dict1._file_dict, 'run')
        self.assertIsInstance(dist1_split, dict, "split_by_entity returns a dictionary")
        self.assertEqual(3, len(dist1_split), 'split_by_entity should return the correct number of items')
        for value in dist1_split.values():
            self.assertIsInstance(value, dict, 'split_by_entity dictionary values should be dictionaries')
        self.assertFalse(leftovers, "split_by_entity leftovers should be empty")

    def test_correct_file(self):
        with self.assertRaises(HedFileError) as context:
            BidsFileDictionary._correct_file(["junk.tsv"])
        self.assertEqual(context.exception.args[0], "BadBidsFileArgument")


if __name__ == '__main__':
    unittest.main()
