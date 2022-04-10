import os
import unittest
from hed.tools import BidsDatasetSummary


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/bids/eeg_ds003654s_hed')
        cls.library_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed_library')

    def test_bids_constructor(self):
        bids1 = BidsDatasetSummary(self.root_path)
        self.assertIsInstance(bids1, BidsDatasetSummary,
                              "BidsDatasetSummary should create a valid object from valid dataset")


if __name__ == '__main__':
    unittest.main()
