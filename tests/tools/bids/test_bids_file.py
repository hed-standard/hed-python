import os
import unittest
from hed.tools.bids.bids_file import BidsFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                      '../../data/bids_old/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../data/bids_old/task-FacePerception_events.json')

    def test_bids_file_constructor(self):
        bids1 = BidsFile(Test.event_path)
        self.assertEqual(bids1.suffix, 'events', "BidsFile should have correct events suffix")
        self.assertEqual(bids1.ext, '.tsv', "BidsFile should have a .tsv extension")
        self.assertEqual(len(bids1.entity_dict), 3, "BidsFile should have right number of entity_dict")

        bids2 = BidsFile(Test.sidecar_path)
        self.assertEqual(bids2.suffix, 'events', "BidsFile should have correct events suffix")
        self.assertEqual(bids2.ext, '.json', "BidsFile should have a .json extension")
        self.assertEqual(len(bids2.entity_dict), 1, "BidsFile should have right number of entity_dict")

    def test_bids_file_str(self):
        bids = BidsFile(Test.sidecar_path)
        my_str1 = str(bids)
        self.assertIsInstance(my_str1, str, "BidsFile convert to string should return a string")
        self.assertGreater(len(my_str1), 0, "BidsFile convert to string should return a non-empty string")
        my_str2 = bids.__str__()
        self.assertIsInstance(my_str2, str, "BidsFile __str__ method should return a string")
        self.assertGreater(len(my_str2), 0, "BidsFile __str__ method should return a non-empty string")


if __name__ == '__main__':
    unittest.main()
