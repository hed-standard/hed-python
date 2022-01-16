import os
import unittest
from hed.tools.bids.bids_file import BidsFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                      '../../data/bids/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')
        cls.sidecar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '../../data/bids/task-FacePerception_events.json')

    def test_bids_file_constructor(self):
        bids1 = BidsFile(Test.event_path)
        self.assertEqual(bids1.suffix, 'events', "BidsFile should have correct events suffix")
        self.assertEqual(bids1.ext, '.tsv', "BidsFile should have a .tsv extension")
        self.assertEqual(len(bids1.entities), 3, "BidsFile should have right number of entities")

        bids2 = BidsFile(Test.sidecar_path)
        self.assertEqual(bids2.suffix, 'events', "BidsFile should have correct events suffix")
        self.assertEqual(bids2.ext, '.json', "BidsFile should have a .json extension")
        self.assertEqual(len(bids2.entities), 1, "BidsFile should have right number of entities")

    def test_bids_file_str(self):
        bids = BidsFile(Test.sidecar_path)
        my_str = str(bids)
        self.assertIsInstance(my_str, str, "BidsFile __str__ method should return a string")
        self.assertGreater(len(my_str), 0, "BidsFile __str__ method returns a non-empty string")


if __name__ == '__main__':
    unittest.main()
