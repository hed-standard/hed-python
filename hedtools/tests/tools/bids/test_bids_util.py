import os
import unittest
from hed.tools.bids.bids_util import parse_bids_filename


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        stern_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/sternberg')
        att_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/attention_shift')
        cls.stern_map_path = os.path.join(stern_base_dir, "sternberg_map.tsv")
        cls.stern_test1_path = os.path.join(stern_base_dir, "sternberg_test_events.tsv")
        cls.stern_test2_path = os.path.join(stern_base_dir, "sternberg_with_quotes_events.tsv")
        cls.stern_test3_path = os.path.join(stern_base_dir, "sternberg_no_quotes_events.tsv")
        cls.attention_shift_path = os.path.join(att_base_dir, "auditory_visual_shift_events.tsv")

    def test_parse_bids_filename_full(self):
        the_path1 = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        suffix1, ext1, entity_dict1, unmatched1 = parse_bids_filename(the_path1)
        self.assertEqual(suffix1, 'bold', "parse_bids_filename should correctly parse name_suffix for full path")
        self.assertEqual(ext1, '.json', "parse_bids_filename should correctly parse ext for full path")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(entity_dict1['sub'], '01', "parse_bids_filename should have a sub entity")
        self.assertEqual(entity_dict1['ses'], 'test', "parse_bids_filename should have a ses entity")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(entity_dict1['run'], '2', "parse_bids_filename should have a run entity")
        self.assertEqual(len(entity_dict1), 4, "parse_bids_filename should 4 entities in the dictionary")
        self.assertEqual(len(unmatched1), 0, "parse_bids_filename should not have unmatched items")

    def test_parse_bids_filename_partial(self):
        path1 = 'task-overt_bold.json'
        suffix1, ext1, entity_dict1, unmatched1 = parse_bids_filename(path1)
        self.assertEqual(suffix1, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext1, '.json', "parse_bids_filename should correctly parse ext for name")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should 1 entities in the dictionary")
        path2 = 'task-overt_bold'
        suffix2, ext2, entity_dict2, unmatched2 = parse_bids_filename(path2)
        self.assertEqual(suffix2, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext2, '', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(entity_dict2['task'], 'overt', "parse_bids_filename should have a task entity")
        path3 = 'bold'
        suffix3, ext3, entity_dict3, unmatched3 = parse_bids_filename(path3)
        self.assertEqual(suffix3, 'bold', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext3, '', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict3, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(len(entity_dict3), 0, "parse_bids_filename should return empty dictionary when no entities")

    def test_parse_bids_filename_unmatched(self):
        path1 = 'dataset_description.json'
        suffix1, ext1, entity_dict1, unmatched1 = parse_bids_filename(path1)
        self.assertEqual(suffix1, 'dataset_description', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext1, '.json', "parse_bids_filename should return empty extension when only name")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(len(entity_dict1), 0, "parse_bids_filename should handle names with no entities")
        self.assertEqual(unmatched1, [],
                         "parse_bids_filename a name with no entities should be unmatched")

        path2 = 'participants.json'
        suffix2, ext2, entity_dict2, unmatched2 = parse_bids_filename(path2)
        self.assertEqual(suffix2, 'participants', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext2, '.json', "parse_bids_filename should return correct extension when only suffix")
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(len(entity_dict2), 0, "parse_bids_filename should handle names with no entities")
        self.assertFalse(unmatched2, "parse_bids_filename a name with only suffix should have no unmatched")

    def test_parse_bids_filename_invalid(self):
        path1 = 'task_sub-01_description.json'
        suffix1, ext1, entity_dict1, unmatched1 = parse_bids_filename(path1)
        self.assertEqual(suffix1, 'description', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext1, '.json', "parse_bids_filename correctly return extension when unmatched entity")
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should handle names with no entities")
        self.assertEqual(len(unmatched1), 1,
                         "parse_bids_filename unmatched list should have correct length when unmatched entity")
        self.assertEqual(unmatched1[0], 'task',
                         "parse_bids_filename unmatched list should have correct values when unmatched entity")
        path2 = 'sub-01.json'
        suffix2, ext2, entity_dict2, unmatched2 = parse_bids_filename(path2)
        self.assertEqual(suffix2, '', "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(ext2, '.json', "parse_bids_filename correctly return extension when unmatched entity")
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entities as a dictionary")
        self.assertEqual(len(entity_dict2), 0, "parse_bids_filename should handle names with no suffix")
        self.assertEqual(len(unmatched2), 1,
                         "parse_bids_filename unmatched list should have correct length when no suffix")
        self.assertEqual(unmatched2[0], 'sub-01',
                         "parse_bids_filename unmatched list should have correct values when unmatched entity")


if __name__ == '__main__':
    unittest.main()
