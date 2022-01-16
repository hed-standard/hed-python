import os
import unittest
import pandas as pd
from hed.tools.bids.bids_dataset import BidsDataset, BidsEventFiles


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids')

    def test_bids_constructor(self):
        bids = BidsDataset(Test.root_path)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        self.assertIsInstance(bids.participants, pd.DataFrame, "BidsDataset participants should be a DataFrame")
        self.assertIsInstance(bids.dataset_description, dict, "BidsDataset dataset_description should be a dict")
        self.assertIsInstance(bids.event_files, BidsEventFiles, "BidsDataset event_files should be  BidsEventFiles")


if __name__ == '__main__':
    unittest.main()
