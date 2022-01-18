import os
import unittest
import pandas as pd
from hed.tools.bids.bids_dataset import BidsDataset, BidsEventFiles


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids/eeg_ds003654s_hed')

    def test_bids_constructor(self):
        bids = BidsDataset(Test.root_path)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        self.assertIsInstance(bids.participants, pd.DataFrame, "BidsDataset participants should be a DataFrame")
        self.assertIsInstance(bids.dataset_description, dict, "BidsDataset dataset_description should be a dict")
        self.assertIsInstance(bids.event_files, BidsEventFiles, "BidsDataset event_files should be  BidsEventFiles")

    def test_bids_validator(self):
        bids = BidsDataset(Test.root_path)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        issues = bids.validate()
        self.assertTrue(issues, "It should return issues when the default check_for_warnings is used")
        issues = bids.validate(check_for_warnings=True)
        self.assertTrue(issues, "It should return issues when check_for_warnings is explicitly set to True")
        issues = bids.validate(check_for_warnings=False)
        self.assertFalse(issues, "It should return no issues when check_for_warnings is explicitly set to False")


if __name__ == '__main__':
    unittest.main()
