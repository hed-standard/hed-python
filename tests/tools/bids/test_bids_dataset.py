import os
import unittest
from hed.schema.hed_schema_io import load_schema_version
from hed.schema.hed_schema import HedSchema
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.tools.bids.bids_dataset import BidsDataset
from hed.models.sidecar import Sidecar
from hed.tools.bids.bids_file_group import BidsFileGroup
from hed.tools.bids.bids_sidecar_file import BidsSidecarFile
from hed.tools.bids.bids_tabular_file import BidsTabularFile


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed")
        cls.demo_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed_demo"
        )
        cls.library_path = os.path.realpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed_library")
        )
        cls.empty_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_empty")
        cls.inherit_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../../data/bids_tests/eeg_ds003645s_hed_inheritance"
        )

    def test_basic(self):
        bids = BidsDataset(self.root_path, suffixes=["events"])
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        parts = bids.get_file_group("participants")
        self.assertFalse(parts)

    def test_basic_with_suffixes(self):
        bids = BidsDataset(self.root_path, suffixes=["participants", "events"])
        parts = bids.get_file_group("participants")
        self.assertTrue(parts)
        self.assertFalse(parts.has_hed)
        events = bids.get_file_group("events")
        self.assertIsInstance(events, BidsFileGroup, "BidsDataset events should be a BidsFileGroup")
        self.assertEqual(len(events.sidecar_dict), 1, "BidsDataset should have one participants.json file")

        for group in bids.file_groups.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset event files should be in a BidsFileGroup")
        self.assertTrue(bids.schema, "BidsDataset constructor extracts a schema from the dataset.")
        self.assertIsInstance(bids.schema, HedSchema, "BidsDataset schema should be HedSchema")
        issues = bids.validate()
        self.assertFalse(issues, "BidsDataset validate should not return issues when the default check_for_warnings is used")
        issues = bids.validate(check_for_warnings=True)
        self.assertEqual(len(issues), 6, "BidsDataset validate should return issues when check_for_warnings is True")

    def test_basic_none_suffixes(self):
        bids = BidsDataset(self.root_path, suffixes=None)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        self.assertEqual(len(bids.file_groups), 3, "BidsDataset should have one file groups")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts)
        issues = bids.validate()
        self.assertFalse(issues, "BidsDataset validate should return issues when the default check_for_warnings is used")
        issues = bids.validate(check_for_warnings=True)
        self.assertTrue(issues, "BidsDataset validate should return issues when check_for_warnings is True")
        issues = bids.validate(check_for_warnings=False)
        self.assertFalse(issues, "BidsDataset validate should return no issues when check_for_warnings is False")

        bids = BidsDataset(self.root_path, suffixes=["participants", "events"])
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts)
        events = bids.get_file_group("events")
        self.assertIsInstance(events, BidsFileGroup, "BidsDataset events should be a BidsFileGroup")
        self.assertEqual(len(events.sidecar_dict), 1, "BidsDataset should have one participants.json file")
        for group in bids.file_groups.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset event files should be in a BidsFileGroup")
        self.assertTrue(bids.schema, "BidsDataset constructor extracts a schema from the dataset.")
        self.assertIsInstance(bids.schema, HedSchema, "BidsDataset schema should be HedSchema")

    def test_unset_default_behavior(self):
        """Test that not providing suffixes/exclude_dirs uses the default values."""
        bids = BidsDataset(self.root_path)
        # Default suffixes are ['events', 'participants']
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts, "Default suffixes should include participants")
        events = bids.get_file_group("events")
        self.assertIsNotNone(events, "Default suffixes should include events")

    def test_unset_explicit_none(self):
        """Test that explicitly passing None for suffixes discovers all files."""
        bids = BidsDataset(self.root_path, suffixes=None)
        # None means discover all files
        self.assertEqual(len(bids.file_groups), 3, "suffixes=None should discover all file types")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts, "suffixes=None should include participants")

    def test_unset_empty_list(self):
        """Test that explicitly passing empty list for suffixes discovers all files."""
        bids = BidsDataset(self.demo_path, suffixes=[])
        # Empty list means discover all files (same as None)
        self.assertEqual(len(bids.file_groups), 9, "suffixes=[] should discover all file types")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts, "suffixes=[] should include participants")

    def test_unset_custom_suffixes(self):
        """Test that custom suffix list works correctly."""
        bids = BidsDataset(self.root_path, suffixes=["events"])
        # Only events suffix specified
        parts = bids.get_file_group("participants")
        self.assertIsNone(parts, "Custom suffixes=['events'] should not include participants")
        events = bids.get_file_group("events")
        self.assertIsNotNone(events, "Custom suffixes=['events'] should include events")

    def test_unset_exclude_dirs_default(self):
        """Test that not providing exclude_dirs uses the default exclusion list."""
        # Default exclude_dirs includes common directories like .git, derivatives, etc.
        bids = BidsDataset(self.root_path)
        # This should work without errors - validating the default exclude_dirs is applied
        self.assertIsInstance(bids, BidsDataset, "Default exclude_dirs should work")

    def test_unset_exclude_dirs_none(self):
        """Test that explicitly passing None for exclude_dirs discovers files in all directories."""
        bids = BidsDataset(self.root_path, exclude_dirs=None)
        # None means no directories are excluded
        self.assertIsInstance(bids, BidsDataset, "exclude_dirs=None should work")

    def test_unset_exclude_dirs_custom(self):
        """Test that custom exclude_dirs list works correctly."""
        bids = BidsDataset(self.root_path, exclude_dirs=["custom_exclude"])
        # Custom exclude list
        self.assertIsInstance(bids, BidsDataset, "Custom exclude_dirs should work")

    def test_demo_none_suffixes(self):
        bids = BidsDataset(self.demo_path, suffixes=None)
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts)
        self.assertEqual(len(parts.datafile_dict), 1, "BidsDataset should have one participants.tsv file")
        self.assertEqual(len(parts.sidecar_dict), 1, "BidsDataset should have one participants.json file")
        self.assertEqual(len(bids.file_groups), 9, "BidsDataset should have 7 file groups")
        scans = bids.get_file_group("scans")
        self.assertEqual(len(scans.datafile_dict), 4, "BidsDataset should have 3 scans.tsv file")
        self.assertEqual(len(scans.sidecar_dict), 3, "BidsDataset should have 3 scans.json file")
        motion = bids.get_file_group("motion")
        self.assertIsNone(motion)
        for key, group in bids.file_groups.items():
            self.assertEqual(len(group.bad_files), 0, f"The demo dataset should have no bad files but {key} does.")
        issues = bids.validate(check_for_warnings=True)
        self.assertEqual(len(issues), 4, "It should have warning issues")

    def test_demo_empty_suffixes(self):
        bids = BidsDataset(self.demo_path, suffixes=[])
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts)
        self.assertEqual(len(parts.datafile_dict), 1, "BidsDataset should have one participants.tsv file")
        self.assertEqual(len(parts.sidecar_dict), 1, "BidsDataset should have one participants.json file")
        self.assertEqual(len(bids.file_groups), 9, "BidsDataset should have 7 file groups")
        scans = bids.get_file_group("scans")
        self.assertEqual(len(scans.datafile_dict), 4, "BidsDataset should have 3 scans.tsv file")
        self.assertEqual(len(scans.sidecar_dict), 3, "BidsDataset should have 3 scans.json file")
        motion = bids.get_file_group("motion")
        self.assertIsNone(motion)
        for key, group in bids.file_groups.items():
            self.assertEqual(len(group.bad_files), 0, f"The demo dataset should have no bad files but {key} does.")
        issues = bids.validate(check_for_warnings=True)
        self.assertEqual(len(issues), 4, "It should have warning issues")

    def test_inheritance_no_suffixes(self):
        bids = BidsDataset(self.inherit_path, suffixes=["events"])
        self.assertIsInstance(bids, BidsDataset, "BidsDataset should create a valid object from valid dataset")
        events = bids.get_file_group("events")
        self.assertIsNotNone(events)
        self.assertEqual(len(events.datafile_dict), 6, "BidsDataset should have 6 event.tsv file")
        self.assertEqual(len(events.sidecar_dict), 3, "BidsDataset should have one participants.json file")
        self.assertEqual(len(bids.file_groups), 1, "BidsDataset should have 7 file groups")
        json1 = os.path.realpath(os.path.join(self.inherit_path, "task-FacePerception_events.json"))
        tsv1 = os.path.realpath(os.path.join(self.inherit_path, "sub-002", "sub-002_task-FacePerception_run-1_events.tsv"))
        tsv2 = os.path.realpath(
            os.path.join(self.inherit_path, "sub-003", "eeg", "sub-003_task-FacePerception_run-1_events.tsv")
        )
        sidecar1 = events.sidecar_dict.get(json1)
        self.assertIsInstance(sidecar1, BidsSidecarFile, "BidsDataset events should be a BidsFileGroup")
        self.assertIsInstance(sidecar1.contents, Sidecar, "The contents is set and should be a Sidecar")

        # Test inheritance for missing keys
        tabular1 = events.datafile_dict.get(tsv1)
        self.assertIsInstance(tabular1, BidsTabularFile, "The tabular dictionary should have a BidsTabularFile")
        tsv1_sidecar = tabular1.sidecar
        self.assertIsInstance(tsv1_sidecar, Sidecar, "BidsDataset events should be a BidsFileGroup")
        merged1 = tsv1_sidecar.loaded_dict
        self.assertIn("rep_status", merged1, "The merged sidecar should have a rep_status")
        self.assertNotIn("rep_status", sidecar1.contents.loaded_dict, "The original sidecar should not have a rep_status")

        # Test inheritance for overwritten keys
        self.assertIsInstance(sidecar1, BidsSidecarFile, "BidsDataset events should be a BidsFileGroup")
        self.assertIsInstance(sidecar1.contents, Sidecar, "The contents is set and should be a Sidecar")
        tabular2 = events.datafile_dict.get(tsv2)
        tsv2_sidecar = tabular2.sidecar
        merged2 = tsv2_sidecar.loaded_dict
        self.assertIn("rep_status", merged2, "The merged sidecar should have a rep_status")
        self.assertEqual(
            merged2["face_type"]["HED"]["famous_face"],
            "Def/Famous-face-cond, Label/Famous",
            "The merged sidecar should have a overwritten famous_face",
        )
        self.assertEqual(
            sidecar1.contents.loaded_dict["face_type"]["HED"]["famous_face"],
            "Def/Famous-face-cond",
            "The original top-level sidecar should not be overwritten famous_face",
        )

    def test_libraries(self):
        bids = BidsDataset(self.library_path, suffixes=["participants", "events"])
        self.assertIsInstance(bids, BidsDataset, "BidsDataset with libraries should create a valid object from valid dataset")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts, "BidsDataset participants should be none if no HED")

        for group in bids.file_groups.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset event files should be in a BidsFileGroup")
        self.assertTrue(bids.schema, "BidsDataset constructor extracts a schema from the dataset.")
        self.assertIsInstance(bids.schema, HedSchemaGroup, "BidsDataset schema should be HedSchemaGroup")
        issues = bids.validate(check_for_warnings=True)
        self.assertEqual(len(issues), 6, "BidsDataset with libraries have 6 warnings")

    def test_demo_empty(self):
        bids = BidsDataset(self.demo_path, suffixes=["channels"])
        self.assertIsInstance(bids, BidsDataset, "BidsDataset with libraries should create a valid object from valid dataset")
        chans = bids.get_file_group("channels")
        self.assertIsNotNone(chans, "BidsDataset channels should not be a BidsFileGroup")

    def test_empty(self):
        bids = BidsDataset(self.empty_path, suffixes=["participants", "events"])
        self.assertEqual(len(bids.file_groups), 2, "BidsDataset for dataset should have no file groups")

    def test_with_schema_group(self):
        x = load_schema_version(["score_2.0.0", "test:testlib_1.0.2"])
        bids = BidsDataset(self.library_path, schema=x, suffixes=["participants"])
        self.assertIsInstance(bids, BidsDataset, "BidsDataset with libraries should create a valid object from valid dataset")
        parts = bids.get_file_group("participants")
        self.assertIsNotNone(parts, "BidsDataset participants should be a None")

        for group in bids.file_groups.values():
            self.assertIsInstance(group, BidsFileGroup, "BidsDataset with libraries event_files should be  BidsFileGroup")
        self.assertIsInstance(
            bids.schema, HedSchemaGroup, "BidsDataset with libraries should have schema that is a HedSchemaGroup"
        )
        issues = bids.validate(check_for_warnings=True)
        self.assertFalse(issues)

    def test_get_summary(self):
        bids1 = BidsDataset(self.root_path)
        summary1 = bids1.get_summary()
        self.assertIsInstance(summary1, dict, "BidsDataset summary is a dictionary")
        self.assertTrue("hed_schema_versions" in summary1, "BidsDataset summary has a hed_schema_versions key")
        self.assertIsInstance(summary1["hed_schema_versions"], list, "BidsDataset summary hed_schema_versions is a list")
        self.assertTrue("dataset" in summary1)
        self.assertEqual(
            len(summary1["hed_schema_versions"]), 1, "BidsDataset summary hed_schema_versions entry has one schema"
        )
        bids2 = BidsDataset(self.library_path)
        summary2 = bids2.get_summary()
        self.assertIsInstance(summary2, dict, "BidsDataset with libraries has a summary that is a dictionary")
        self.assertTrue(
            "hed_schema_versions" in summary2, "BidsDataset with libraries has a summary with a hed_schema_versions key"
        )
        self.assertIsInstance(
            summary2["hed_schema_versions"], list, "BidsDataset with libraries hed_schema_versions in summary is a list"
        )
        self.assertEqual(
            len(summary2["hed_schema_versions"]), 2, "BidsDataset with libraries summary hed_schema_versions list has 3 schema"
        )
        self.assertTrue("dataset" in summary2)


if __name__ == "__main__":
    unittest.main()
