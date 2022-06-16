import os
import unittest
from hed.errors import HedFileError
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

    def test_schema_from_hed_version(self):
        ver1 = "8.0.0"
        schemas1 = BidsDataset.schema_from_hed_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "schema_from_hed_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version, "8.0.0", "schema_from_hed_version has the right version")
        self.assertEqual(schemas1.library, None, "schema_from_hed_version standard schema has no library")
        ver2 = "base:8.0.0"
        schemas2 = BidsDataset.schema_from_hed_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "schema_from_hed_version returns HedSchema version+prefix")
        self.assertEqual(schemas2.version, "8.0.0", "schema_from_hed_version has the right version with prefix")
        self.assertEqual(schemas2._schema_prefix, "base:", "schema_from_hed_version has the right version with prefix")
        ver3 = ["base:8.0.0"]
        schemas3 = BidsDataset.schema_from_hed_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "schema_from_hed_version returns HedSchema version+prefix")
        self.assertEqual(schemas3.version, "8.0.0", "schema_from_hed_version has the right version with prefix")
        self.assertEqual(schemas3._schema_prefix, "base:", "schema_from_hed_version has the right version with prefix")

    def test_schema_from_hed_version_libraries(self):
        ver1 = "score_0.0.1"
        schemas1 = BidsDataset.schema_from_hed_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "schema_from_hed_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version, "0.0.1", "schema_from_hed_version has the right version")
        self.assertEqual(schemas1.library, "score", "schema_from_hed_version works with single library no prefix")
        ver2 = "base:score_0.0.1"
        schemas2 = BidsDataset.schema_from_hed_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "schema_from_hed_version returns HedSchema version+prefix")
        self.assertEqual(schemas2.version, "0.0.1", "schema_from_hed_version has the right version with prefix")
        self.assertEqual(schemas2._schema_prefix, "base:", "schema_from_hed_version has the right version with prefix")
        ver3 = ["8.0.0", "sc:score_0.0.1"]
        schemas3 = BidsDataset.schema_from_hed_version(ver3)
        self.assertIsInstance(schemas3, HedSchemaGroup, "schema_from_hed_version returns HedSchema version+prefix")
        self.assertIsInstance(schemas3._schemas, dict, "schema_from_hed_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas3._schemas), 2, "schema_from_hed_version group dictionary is right length")
        s = schemas3._schemas[""]
        self.assertEqual(s.version, "8.0.0", "schema_from_hed_version has the right version with prefix")

    def test_schema_from_hed_version_empty(self):
        schemas1 = BidsDataset.schema_from_hed_version("")
        self.assertIsInstance(schemas1, HedSchema, "schema_from_hed_version for empty string returns latest version")
        self.assertTrue(schemas1.version, "schema_from_hed_version for empty string has a version")
        self.assertFalse(schemas1.library, "schema_from_hed_version for empty string is not a library")
        schemas2 = BidsDataset.schema_from_hed_version(None)
        self.assertEqual(schemas2, None, "schema_from_hed_version None returns None")
        schemas3 = BidsDataset.schema_from_hed_version([""])
        self.assertIsInstance(schemas3, HedSchema, "schema_from_hed_version empty list returns None")
        self.assertTrue(schemas3.version, "schema_from_hed_version for empty string has a version")
        self.assertFalse(schemas3.library, "schema_from_hed_version for empty string is not a library")

    def test_schema_from_hed_version_invalid(self):
        try:
            dict1 = BidsDataset.schema_from_hed_version("x.0.1")
        except HedFileError:
            pass
        except Exception as ex:
            self.fail("schema_from_hed_version threw the wrong exception when bad version")
        else:
            self.fail("schema_from_hed_version should have thrown a HedFileError for bad version")

        try:
            BidsDataset.schema_from_hed_version("base:score_x.0.1")
        except HedFileError:
            pass
        except Exception as ex:
            self.fail("schema_from_hed_version threw the wrong exception when bad library version")
        else:
            self.fail("schema_from_hed_version should have thrown a HedFileError for bad library version")

        try:
            BidsDataset.schema_from_hed_version([])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail("schema_from_hed_version threw the wrong exception empty version list")
        else:
            self.fail("schema_from_hed_version should have thrown a HedFileError for empty version list")

        try:
            BidsDataset.schema_from_hed_version([None])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail("schema_from_hed_version threw the wrong exception for None version list")
        else:
            self.fail("schema_from_hed_version should have thrown a HedFileError for None version list")

        try:
            BidsDataset.schema_from_hed_version(["8.0.0", "score_0.0.1)"])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail("schema_from_hed_version threw the wrong exception for two no prefix")
        else:
            self.fail("schema_from_hed_version should have thrown a HedFileError two with no prefix")

        try:
            BidsDataset.schema_from_hed_version(["sc:8.0.0", "sc:score_0.0.1)"])
        except HedFileError:
            pass
        except Exception as ex:
            self.fail("schema_from_hed_version threw the wrong exception for two with same prefix")
        else:
            self.fail("schema_from_hed_version should have thrown a HedFileError two with same prefix")

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
