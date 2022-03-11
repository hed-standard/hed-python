import os
from pandas import DataFrame
import unittest
from hed.tools.bids.bids_tsv_file import BidsTsvFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tsv_path = \
            os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         '../../data/bids/eeg_ds003654s_hed/sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv')

    def test_bids_tsv_file_constructor(self):
        tsv_file = BidsTsvFile(Test.tsv_path)
        self.assertEqual(tsv_file.suffix, 'events', "BidsTsvFile should have correct events suffix")
        self.assertEqual(tsv_file.ext, '.tsv', "BidsTsvFile should have a .tsv extension")
        self.assertEqual(len(tsv_file.entities), 3, "BidsTsvFile should have right number of entities")

    def test_bids_tsv_file_str(self):
        tsv_file1 = BidsTsvFile(Test.tsv_path)
        self.assertTrue(str(tsv_file1), "BidsTsvFile should have a string representation")
        tsv_file2 = BidsTsvFile(Test.tsv_path, set_contents=True)
        self.assertTrue(str(tsv_file2), "BidsTsvFile should have a string representation")
        self.assertGreater(len(str(tsv_file2)), len(str(tsv_file1)),
                           "BidsTsvFile with contents should have a longer string representation than without")

    def test_bids_tsv_file_set_contents(self):
        tsv_file = BidsTsvFile(Test.tsv_path)
        self.assertFalse(tsv_file.contents, "BidsTsvFile should have no contents until set")
        tsv_file.set_contents()
        self.assertIsInstance(tsv_file.contents, DataFrame,
                              "BidsTsvFile should have DataFrame contents after setting")
        tsv_file.clear_contents()
        self.assertFalse(tsv_file.contents, "BidsTsvFile should have no contents after clearing")


if __name__ == '__main__':
    unittest.main()
