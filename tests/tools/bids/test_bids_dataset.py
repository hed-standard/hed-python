import os
import unittest
from hed.schema.hed_schema_io import load_schema, load_schema_version
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_dataset import BidsDataset
from hed.tools.bids.bids_file_group import BidsFileGroup


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/bids/eeg_ds003654s_hed')
        cls.library_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                            '../../data/bids/eeg_ds003654s_hed_library'))

    def test_constructor(self):
        bids = BidsDataset(Test.root_path)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        parts = bids.get_tabular_group("participants")
        self.assertIsInstance(parts, BidsFileGroup, "BidsDataset participants should be a BidsFileGroup")
        self.assertEqual(len(parts.sidecar_dict), 1, "BidsDataset should have one participants.json file")
        self.assertEqual(len(parts.datafile_dict), 1, "BidsDataset should have one participants.tsv file")
        self.assertIsInstance(bids.dataset_description, dict, "BidsDataset dataset_description should be a dict")
        for group in bids.tabular_files.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset event files should be in a BidsFileGroup")
        self.assertTrue(bids.schema, "BidsDataset constructor extracts a schema from the dataset.")
        self.assertIsInstance(bids.schema, HedSchema, "BidsDataset schema should be HedSchema")

    def test_constructor_libraries(self):
        bids = BidsDataset(self.library_path)
        self.assertIsInstance(bids, BidsDataset,
                              "BidsDataset with libraries should create a valid object from valid dataset")
        parts = bids.get_tabular_group("participants")
        self.assertIsInstance(parts, BidsFileGroup, "BidsDataset participants should be a BidsFileGroup")
        self.assertEqual(len(parts.sidecar_dict), 1, "BidsDataset should have one participants.json file")
        self.assertEqual(len(parts.datafile_dict), 1, "BidsDataset should have one participants.tsv file")
        self.assertIsInstance(bids.dataset_description, dict, "BidsDataset dataset_description should be a dict")
        for group in bids.tabular_files.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset event files should be in a BidsFileGroup")
        self.assertTrue(bids.schema, "BidsDataset constructor extracts a schema from the dataset.")
        self.assertIsInstance(bids.schema, HedSchemaGroup, "BidsDataset schema should be HedSchemaGroup")

    def test_constructor_tabular(self):
        bids = BidsDataset(self.library_path, tabular_types=["channels"])
        self.assertIsInstance(bids, BidsDataset,
                              "BidsDataset with libraries should create a valid object from valid dataset")
        parts = bids.get_tabular_group("participants")
        self.assertIsInstance(parts, BidsFileGroup, "BidsDataset participants should be a BidsFileGroup")
        self.assertEqual(len(parts.sidecar_dict), 1, "BidsDataset should have one participants.json file")
        self.assertEqual(len(parts.datafile_dict), 1, "BidsDataset should have one participants.tsv file")
        self.assertIsInstance(bids.dataset_description, dict, "BidsDataset dataset_description should be a dict")
        for group in bids.tabular_files.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset event files should be in a BidsFileGroup")
        events = bids.get_tabular_group("events")
        self.assertFalse(events, "BidsDataset should not have events if tabular_files do not include them.")
        channels = bids.get_tabular_group("channels")
        self.assertTrue(channels, "BidsDataset should the type of tabular file specified in constructor.")
        self.assertTrue(bids.schema, "BidsDataset constructor extracts a schema from the dataset.")
        self.assertIsInstance(bids.schema, HedSchemaGroup, "BidsDataset schema should be HedSchemaGroup")

    def test_validator(self):
        bids = BidsDataset(self.root_path)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        issues = bids.validate()
        self.assertTrue(issues, "BidsDataset validate should return issues when the default check_for_warnings is used")
        issues = bids.validate(check_for_warnings=True)
        self.assertTrue(issues, "BidsDataset validate should return issues when check_for_warnings is True")
        issues = bids.validate(check_for_warnings=False)
        self.assertFalse(issues, "BidsDataset validate should return no issues when check_for_warnings is False")

    def test_validator_libraries(self):
        bids = BidsDataset(self.library_path)
        issues = bids.validate(check_for_warnings=False)
        self.assertFalse(issues, "BidsDataset with libraries should validate")

    def test_validator_types(self):
        bids = BidsDataset(self.root_path, tabular_types=None)
        issues = bids.validate(check_for_warnings=False)
        self.assertFalse(issues, "BidsDataset with participants and events validates")

    def test_with_schema_group(self):
        base_version = '8.0.0'
        library1_url = "https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/" + \
                       "library_schemas/score/hedxml/HED_score_0.0.1.xml"
        library2_url = "https://raw.githubusercontent.com/hed-standard/hed-schema-library/main/" + \
                       "library_schemas/testlib/hedxml/HED_testlib_1.0.2.xml"
        schema_list = [load_schema_version(xml_version=base_version)]
        schema_list.append(load_schema(library1_url, schema_prefix="sc"))
        schema_list.append(load_schema(library2_url, schema_prefix="test"))
        x = HedSchemaGroup(schema_list)
        bids = BidsDataset(self.library_path, schema=x)
        self.assertIsInstance(bids, BidsDataset,
                              "BidsDataset with libraries should create a valid object from valid dataset")
        parts = bids.get_tabular_group("participants")
        self.assertIsInstance(parts, BidsFileGroup, "BidsDataset participants should be a BidsFileGroup")

        self.assertIsInstance(bids.dataset_description, dict,
                              "BidsDataset with libraries dataset_description should be a dict")
        for group in bids.tabular_files.values():
            self.assertIsInstance(group, BidsFileGroup,
                                  "BidsDataset with libraries event_files should be  BidsFileGroup")
        self.assertIsInstance(bids.schema, HedSchemaGroup,
                              "BidsDataset with libraries should have schema that is a HedSchemaGroup")
        issues = bids.validate(check_for_warnings=True)
        self.assertTrue(issues, "BidsDataset validate should return issues when check_for_warnings is True")

    def test_get_summary(self):
        bids1 = BidsDataset(self.root_path)
        summary1 = bids1.get_summary()
        self.assertIsInstance(summary1, dict, "BidsDataset summary is a dictionary")
        self.assertTrue("hed_schema_versions" in summary1, "BidsDataset summary has a hed_schema_versions key")
        self.assertIsInstance(summary1["hed_schema_versions"], list,
                              "BidsDataset summary hed_schema_versions is a list")
        self.assertTrue("dataset" in summary1)
        self.assertEqual(len(summary1["hed_schema_versions"]), 1,
                         "BidsDataset summary hed_schema_versions entry has one schema")
        bids2 = BidsDataset(self.library_path)
        summary2 = bids2.get_summary()
        self.assertIsInstance(summary2, dict, "BidsDataset with libraries has a summary that is a dictionary")
        self.assertTrue("hed_schema_versions" in summary2,
                        "BidsDataset with libraries has a summary with a hed_schema_versions key")
        self.assertIsInstance(summary2["hed_schema_versions"], list,
                              "BidsDataset with libraries hed_schema_versions in summary is a list")
        self.assertEqual(len(summary2["hed_schema_versions"]), 3,
                         "BidsDataset with libraries summary hed_schema_versions list has 3 schema")
        self.assertTrue("dataset" in summary2)


if __name__ == '__main__':
    unittest.main()
