import os
import json
import unittest
import pandas as pd
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_dataset import BidsDataset
from hed.tools.bids.bids_event_files import BidsEventFiles


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../data/bids/eeg_ds003654s_hed')
        cls.library_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        '../../data/bids/eeg_ds003654s_hed_library')

    def test_bids_constructor(self):
        bids1 = BidsDataset(Test.root_path)
        self.assertIsInstance(bids1, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        self.assertIsInstance(bids1.participants, pd.DataFrame, "BidsDataset participants should be a DataFrame")
        self.assertIsInstance(bids1.dataset_description, dict, "BidsDataset dataset_description should be a dict")
        self.assertIsInstance(bids1.event_files, BidsEventFiles, "BidsDataset event_files should be  BidsEventFiles")
        self.assertIsInstance(bids1.schemas, HedSchemaGroup, "BidsDataset schemas should be HedSchemaGroup")

        bids2 = BidsDataset(Test.library_path)
        self.assertIsInstance(bids2, BidsDataset,
                              "BidsDataset with libraries should create a valid object from valid dataset")
        self.assertIsInstance(bids2.participants, pd.DataFrame,
                              "BidsDataset with libraries should have a participants that is a DataFrame")
        self.assertIsInstance(bids2.dataset_description, dict,
                              "BidsDataset with libraries dataset_description should be a dict")
        self.assertIsInstance(bids2.event_files, BidsEventFiles,
                              "BidsDataset with libraries event_files should be  BidsEventFiles")
        self.assertIsInstance(bids2.schemas, HedSchemaGroup,
                              "BidsDataset with libraries should have schemas that is a HedSchemaGroup")

    def test_bids_validator(self):
        bids1 = BidsDataset(Test.root_path)
        self.assertIsInstance(bids1, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        issues = bids1.validate()
        self.assertTrue(issues, "BidsDataset validate should return issues when the default check_for_warnings is used")
        issues = bids1.validate(check_for_warnings=True)
        self.assertTrue(issues,
                        "BidsDataset validate should return issues when check_for_warnings is True")
        issues = bids1.validate(check_for_warnings=False)
        self.assertFalse(issues,
                         "BidsDataset validate should return no issues when check_for_warnings is False")

        bids2 = BidsDataset(Test.library_path)
        self.assertIsInstance(bids2, BidsDataset,
                              "BidsDataset with libraries should create a valid object from valid dataset")
        issues = bids2.validate()
        self.assertTrue(issues,
                        "BidsDataset with libraries should return issues when the default check_for_warnings is used")
        issues = bids2.validate(check_for_warnings=True)
        self.assertTrue(issues,
                        "BidsDataset with libraries should return issues when check_for_warnings is True")
        issues = bids2.validate(check_for_warnings=False)
        self.assertFalse(issues,
                         "BidsDataset with libraries should return no issues when check_for_warnings is False")

    def test_get_summary(self):
        bids1 = BidsDataset(Test.root_path)
        summary1 = bids1.get_summary()
        self.assertIsInstance(summary1, dict, "BidsDataset summary is a dictionary")
        self.assertTrue("hed_schema_versions" in summary1, "BidsDataset summary has a hed_schema_versions key")
        self.assertIsInstance(summary1["hed_schema_versions"], list,
                              "BidsDataset summary hed_schema_versions is a list")
        self.assertEqual(len(summary1["hed_schema_versions"]), 1,
                         "BidsDataset summary hed_schema_versions entry has one schema")
        bids2 = BidsDataset(Test.library_path)
        summary2 = bids2.get_summary()
        self.assertIsInstance(summary2, dict, "BidsDataset with libraries has a summary that is a dictionary")
        self.assertTrue("hed_schema_versions" in summary2,
                        "BidsDataset with libraries has a summary with a hed_schema_versions key")
        self.assertIsInstance(summary2["hed_schema_versions"], list,
                              "BidsDataset with libraries hed_schema_versions in summary is a list")
        self.assertEqual(len(summary2["hed_schema_versions"]), 3,
                         "BidsDataset with libraries summary hed_schema_versions list has 3 schemas")


if __name__ == '__main__':
    unittest.main()
