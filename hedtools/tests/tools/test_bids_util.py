import os
import unittest
from hed.tools.bids_util import parse_bids_filename


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
