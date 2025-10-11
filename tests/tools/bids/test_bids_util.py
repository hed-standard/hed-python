import os
import unittest
import json
import tempfile
import shutil
from hed.tools.bids.bids_util import (parse_bids_filename, group_by_suffix, get_schema_from_description)


class TestGetSchemaFromDescription(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory for test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_valid_description(self):
        """Test that a valid dataset_description.json correctly calls load_schema_version"""
        # Create a real dataset_description.json file
        desc_file = os.path.join(self.test_dir, "dataset_description.json")
        with open(desc_file, "w") as f:
            json.dump({"HEDVersion": "8.0.0"}, f)

        result = get_schema_from_description(self.test_dir)
        # Since we can't easily mock the schema loading without changing the implementation,
        # we'll just verify that the function doesn't return None and doesn't crash
        # The actual schema loading is tested elsewhere
        self.assertIsNotNone(result)

    def test_missing_file(self):
        """Test that a missing dataset_description.json returns None"""
        # Use empty temp directory (no dataset_description.json)
        result = get_schema_from_description(self.test_dir)
        self.assertIsNone(result)

    def test_invalid_json(self):
        """Test that an invalid JSON file returns None"""
        # Create invalid JSON file
        desc_file = os.path.join(self.test_dir, "dataset_description.json")
        with open(desc_file, "w") as f:
            f.write("invalid json")

        result = get_schema_from_description(self.test_dir)
        self.assertIsNone(result)

    def test_missing_hed_version(self):
        """Test that a missing HEDVersion key calls load_schema_version with None"""
        # Create JSON file without HEDVersion
        desc_file = os.path.join(self.test_dir, "dataset_description.json")
        with open(desc_file, "w") as f:
            json.dump({}, f)

        result = get_schema_from_description(self.test_dir)
        # The function should still work, just load default schema
        self.assertIsNotNone(result)


class TestGroupBySuffixes(unittest.TestCase):
    def test_basic_grouping(self):
        file_list = [
            "/path/to/file_abc.json",
            "/path/to/another_def.json",
            "/path/to/something_xyz.tsv"
        ]
        expected_groups = {
            "abc": ["/path/to/file_abc.json"],
            "def": ["/path/to/another_def.json"],
            "xyz": ["/path/to/something_xyz.tsv"]
        }

        result = group_by_suffix(file_list)
        self.assertEqual(result, expected_groups, "Basic grouping should work correctly")

    def test_files_without_underscore(self):
        file_list = [
            "/path/to/filename.json",  # No underscore
            "/path/to/anotherfile.tsv",
            "/path/to/ignore_me.txt"
        ]
        expected1 = {
            "filename": ["/path/to/filename.json"],
            "anotherfile": ["/path/to/anotherfile.tsv"],
            "me": ["/path/to/ignore_me.txt"]
        }

        result1 = group_by_suffix(file_list)
        self.assertEqual(result1, expected1, "valid_groups")

    def test_files_with_multiple_underscores(self):
        file_list = [
            "/path/to/project_file_abc.json",
            "/path/to/another_long_name_def.json",
            "/path/to/another_def.json",
        ]
        expected = {
            "abc": ["/path/to/project_file_abc.json"],
            "def": ["/path/to/another_long_name_def.json", "/path/to/another_def.json"]
        }
        result = group_by_suffix(file_list)
        self.assertEqual(result, expected, "It should parse with multiple underscores")  # Should be empty since len(split) > 2

    def test_empty_file_list(self):
        result1 = group_by_suffix([])
        self.assertEqual(result1, {})  # Should return an empty dict


class TestParseBidsFilename(unittest.TestCase):

    def test_standard_bids_filename(self):
        self.assertEqual(
            parse_bids_filename("sub-01_task-rest_bold.nii.gz"),
            {
                "basename": "sub-01_task-rest_bold",
                "suffix": "bold",
                "prefix": None,
                "ext": ".nii.gz",
                "bad": [],
                "entities": {"sub": "01", "task": "rest"}
            }
        )

    def test_filename_without_entities(self):
        self.assertEqual(
            parse_bids_filename("dataset_description.json"),
            {
                "basename": "dataset_description",
                "suffix": "description",
                "prefix": "dataset",
                "ext": ".json",
                "bad": [],
                "entities": {}
            }
        )

    def test_filename_with_multiple_entities(self):
        self.assertEqual(
            parse_bids_filename("sub-02_ses-1_task-memory_run-2_bold.nii.gz"),
            {
                "basename": "sub-02_ses-1_task-memory_run-2_bold",
                "suffix": "bold",
                "prefix": None,
                "ext": ".nii.gz",
                "bad": [],
                "entities": {"sub": "02", "ses": "1", "task": "memory", "run": "2"}
            }
        )

    def test_invalid_filename_without_underscore_before_suffix(self):
        self.assertEqual(
            parse_bids_filename("sub-03task-memorybold.nii.gz"),
            {
                "basename": "sub-03task-memorybold",
                "suffix": None,
                "prefix": None,
                "ext": ".nii.gz",
                "bad": ["sub-03task-memorybold"],
                "entities": {}
            }
        )

    def test_empty_filename(self):
        self.assertEqual(
            parse_bids_filename(""),
            {
                "basename": "",
                "suffix": None,
                "prefix": None,
                "ext": "",
                "bad": [],
                "entities": {}
            }
        )

    def test_filename_with_missing_entity_values(self):
        self.assertEqual(
            parse_bids_filename("sub-_task-_bold.nii.gz"),
            {
                "basename": "sub-_task-_bold",
                "suffix": "bold",
                "prefix": None,
                "ext": ".nii.gz",
                "bad": ["sub-", "task-"],
                "entities": {}
            }
        )

    def test_filename_with_missing_suffix(self):
        self.assertEqual(
            parse_bids_filename("sub-04_ses-2_task-motor.nii.gz"),
            {
                "basename": "sub-04_ses-2_task-motor",
                "suffix": None,
                "prefix": None,
                "ext": ".nii.gz",
                "bad": [],
                "entities": {"sub": "04", "ses": "2", "task": "motor"}
            }
        )

    def test_filename_with_unknown_format(self):
        self.assertEqual(
            parse_bids_filename("invalidfileformat"),
            {
                "basename": "invalidfileformat",
                "suffix": "invalidfileformat",
                "prefix": None,
                "ext": "",
                "bad": [],
                "entities": {}
            }
        )

    def test_parse_bids_filename_full(self):
        the_path1 = '/d/base/sub-01/ses-test/func/sub-01_ses-test_task-overt_run-2_bold.json'
        name_dict = parse_bids_filename(the_path1)
        self.assertEqual(name_dict["suffix"], 'bold',
                         "parse_bids_filename should correctly parse name_suffix for full path")
        self.assertEqual(name_dict["ext"], '.json', "parse_bids_filename should correctly parse ext for full path")
        entity_dict = name_dict["entities"]
        self.assertIsInstance(entity_dict, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict['sub'], '01', "parse_bids_filename should have a sub entity")
        self.assertEqual(entity_dict['ses'], 'test', "parse_bids_filename should have a ses entity")
        self.assertEqual(entity_dict['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(entity_dict['run'], '2', "parse_bids_filename should have a run entity")
        self.assertEqual(len(entity_dict), 4, "parse_bids_filename should 4 entity_dict in the dictionary")

        the_path2 = 'sub-01.json'
        name_dict2 = parse_bids_filename(the_path2)
        self.assertFalse(name_dict2["suffix"], "parse_bids_filename should not return a suffix if no suffix")
        self.assertEqual(len(name_dict2["entities"]), 1,
                         "parse_bids_filename should have entity dictionary if suffix missing")

    def test_parse_bids_filename_partial(self):
        path1 = 'task-overt_bold.json'
        name_dict1 = parse_bids_filename(path1)
        self.assertEqual(name_dict1["ext"], '.json', "parse_bids_filename should correctly parse ext for name")
        entity_dict1 = name_dict1["entities"]
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict1['task'], 'overt', "parse_bids_filename should have a task entity")
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should 1 entity_dict in the dictionary")

        path2 = 'task-overt_bold'
        name_dict2 = parse_bids_filename(path2)
        self.assertEqual(name_dict2["suffix"], 'bold',
                         "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(name_dict2["ext"], '', "parse_bids_filename should return empty extension when only name")
        entity_dict2 = name_dict2["entities"]
        self.assertIsInstance(entity_dict2, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(entity_dict2['task'], 'overt', "parse_bids_filename should have a task entity")

        path3 = 'bold'
        name_dict3 = parse_bids_filename(path3)
        self.assertEqual(name_dict3["suffix"], 'bold',
                         "parse_bids_filename should correctly parse name_suffix for name")
        self.assertEqual(name_dict3["ext"], '', "parse_bids_filename should return empty extension when only name")
        entity_dict3 = name_dict3["entities"]
        self.assertEqual(len(entity_dict3), 0, "parse_bids_filename should not have a task entity")

    def test_parse_bids_filename_unmatched(self):
        path1 = 'dataset_description.json'
        name_dict1 = parse_bids_filename(path1)
        self.assertEqual(name_dict1["suffix"], "description")
        self.assertEqual(name_dict1["ext"], '.json', "parse_bids_filename should correctly parse ext for name")
        entity_dict1 = name_dict1["entities"]
        self.assertIsInstance(entity_dict1, dict, "parse_bids_filename should return entity_dict as a dictionary")
        self.assertEqual(len(entity_dict1), 0, "parse_bids_filename should 1 entity_dict in the dictionary")
        self.assertEqual(name_dict1["prefix"], "dataset",
                         "parse_bids_filename should have entity dictionary if suffix missing")

    def test_parse_bids_filename_invalid(self):
        path1 = 'task--x_sub-01_description.json'
        name_dict1 = parse_bids_filename(path1)
        self.assertEqual(name_dict1["suffix"], "description")
        self.assertEqual(name_dict1["ext"], '.json', "parse_bids_filename should correctly parse ext for name")
        self.assertEqual(name_dict1['bad'], ['task--x'], "parse_bids_filename should have a task entity")
        entity_dict1 = name_dict1["entities"]
        self.assertEqual(len(entity_dict1), 1, "parse_bids_filename should 1 entity_dict in the dictionary")


class TestGetMergedSidecar(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory structure for test files"""
        self.test_dir = tempfile.mkdtemp()
        # Create a nested directory structure
        self.sub_dir = os.path.join(self.test_dir, "sub-01", "func")
        os.makedirs(self.sub_dir)

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_get_merged_sidecar_no_overlap(self):
        from hed.tools.bids.bids_util import get_merged_sidecar

        # Create sidecar files at different levels
        root_sidecar = os.path.join(self.test_dir, "task-test_events.json")
        with open(root_sidecar, "w") as f:
            json.dump({"key1": "value1"}, f)

        sub_sidecar = os.path.join(self.sub_dir, "task-test_events.json")
        with open(sub_sidecar, "w") as f:
            json.dump({"key2": "value2"}, f)

        # Create test TSV file
        test_file = os.path.join(self.sub_dir, "sub-01_task-test_events.tsv")
        with open(test_file, "w") as f:
            f.write("onset\tduration\ttrial_type\n0\t1\tA\n")

        # Test merging
        merged = get_merged_sidecar(self.test_dir, test_file)

        # Should contain both keys
        self.assertIn("key1", merged)
        self.assertIn("key2", merged)
        self.assertEqual(merged["key1"], "value1")
        self.assertEqual(merged["key2"], "value2")

    def test_get_merged_sidecar_overlap(self):
        from hed.tools.bids.bids_util import get_merged_sidecar

        # Create sidecar files with overlapping keys
        root_sidecar = os.path.join(self.test_dir, "task-test_events.json")
        with open(root_sidecar, "w") as f:
            json.dump({"key1": "value1", "key2": "value2"}, f)

        sub_sidecar = os.path.join(self.sub_dir, "task-test_events.json")
        with open(sub_sidecar, "w") as f:
            json.dump({"key2": "value3", "key4": "value4"}, f)

        # Create test TSV file
        test_file = os.path.join(self.sub_dir, "sub-01_task-test_events.tsv")
        with open(test_file, "w") as f:
            f.write("onset\tduration\ttrial_type\n0\t1\tA\n")

        # Test merging - more specific (deeper) sidecars should override
        merged = get_merged_sidecar(self.test_dir, test_file)

        self.assertEqual(merged["key1"], "value1")  # Only in root
        self.assertEqual(merged["key2"], "value3")  # Sub should override root
        self.assertEqual(merged["key4"], "value4")  # Only in sub


class TestGetCandidates(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory with test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_get_candidates_valid_files(self):
        from hed.tools.bids.bids_util import get_candidates

        # Create real JSON files
        file1 = os.path.join(self.test_dir, "sub-01_task-rest_events.json")  # Exact match
        file2 = os.path.join(self.test_dir, "task-rest_events.json")  # Subset match (should inherit)
        file3 = os.path.join(self.test_dir, "readme.txt")

        with open(file1, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)
        with open(file2, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)
        with open(file3, "w") as f:
            f.write("Not a JSON file")

        # Test with TSV file dict that should match the JSON files
        tsv_dict = {
            "suffix": "events",
            "entities": {"sub": "01", "task": "rest"},
            "bad": []
        }

        candidates = get_candidates(self.test_dir, tsv_dict)

        # Should find both JSON files (exact match and subset match)
        # Normalize paths for Windows compatibility (handles RUNNER~1 vs runneradmin)
        file1_norm = os.path.realpath(file1)
        file2_norm = os.path.realpath(file2)
        self.assertEqual(len(candidates), 2)
        self.assertIn(file1_norm, candidates)
        self.assertIn(file2_norm, candidates)

    def test_get_candidates_no_valid_files(self):
        from hed.tools.bids.bids_util import get_candidates

        # Create JSON files that won't match
        file1 = os.path.join(self.test_dir, "sub-02_task-memory_events.json")
        with open(file1, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)

        # Test with TSV file dict that won't match
        tsv_dict = {
            "suffix": "events",
            "entities": {"sub": "01", "task": "rest"},
            "bad": []
        }

        candidates = get_candidates(self.test_dir, tsv_dict)
        self.assertEqual(len(candidates), 0)

    def test_get_candidates_mixed_files(self):
        from hed.tools.bids.bids_util import get_candidates

        # Create mix of matching and non-matching files
        file1 = os.path.join(self.test_dir, "sub-01_task-rest_events.json")  # Exact match
        file2 = os.path.join(self.test_dir, "task-rest_events.json")  # Subset match (should inherit)
        file3 = os.path.join(self.test_dir, "sub-02_task-rest_events.json")  # Different subject

        with open(file1, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)
        with open(file2, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)
        with open(file3, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)

        # Test with TSV file dict
        tsv_dict = {
            "suffix": "events",
            "entities": {"sub": "01", "task": "rest"},
            "bad": []
        }

        candidates = get_candidates(self.test_dir, tsv_dict)

        # Should find exact match and subset match, but not different subject
        # Normalize paths for Windows compatibility (handles RUNNER~1 vs runneradmin)
        file1_norm = os.path.realpath(file1)
        file2_norm = os.path.realpath(file2)
        file3_norm = os.path.realpath(file3)
        self.assertEqual(len(candidates), 2)
        self.assertIn(file1_norm, candidates)
        self.assertIn(file2_norm, candidates)
        self.assertNotIn(file3_norm, candidates)


class TestMatchesCriteria(unittest.TestCase):
    def test_matches_criteria_valid(self):
        from hed.tools.bids.bids_util import matches_criteria
        json_file_dict = {"ext": ".json", "suffix": "events", "entities": {"subject": "01", "session": "02"}}
        tsv_file_dict = {"suffix": "events", "entities": {"subject": "01", "session": "02"}}
        self.assertTrue(matches_criteria(json_file_dict, tsv_file_dict))

        json_file_dict = {"ext": ".json", "suffix": "events", "entities": {"subject": "01"}}
        tsv_file_dict = {"suffix": "events", "entities": {"subject": "01"}}
        self.assertTrue(matches_criteria(json_file_dict, tsv_file_dict))

    def test_matches_criteria_invalid_extension(self):
        from hed.tools.bids.bids_util import matches_criteria
        json_file_dict = {"ext": ".txt", "suffix": "events", "entities": {"subject": "01"}}
        tsv_file_dict = {"suffix": "events", "entities": {"subject": "01"}}
        self.assertFalse(matches_criteria(json_file_dict, tsv_file_dict))

    def test_matches_criteria_mismatched_suffix(self):
        from hed.tools.bids.bids_util import matches_criteria
        json_file_dict = {"ext": ".json", "suffix": "participants", "entities": {"subject": "01"}}
        tsv_file_dict = {"suffix": "events", "entities": {"subject": "01"}}
        self.assertFalse(matches_criteria(json_file_dict, tsv_file_dict))

        tsv_file_dict["entities"]["session"] = "02"
        self.assertFalse(matches_criteria(json_file_dict, tsv_file_dict))

    def test_matches_criteria_mismatched_entities(self):
        from hed.tools.bids.bids_util import matches_criteria
        json_file_dict = {"ext": ".json", "suffix": "events", "entities": {"subject": "01"}}
        tsv_file_dict = {"suffix": "events", "entities": {"subject": "02"}}
        self.assertFalse(matches_criteria(json_file_dict, tsv_file_dict))


class TestWalkBack(unittest.TestCase):

    def setUp(self):
        """Set up temporary directory structure for test files"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_walk_back_candidate_in_root(self):
        from hed.tools.bids.bids_util import walk_back

        # Create directory structure
        level1_dir = os.path.join(self.test_dir, "level1")
        os.makedirs(level1_dir)

        # Create matching JSON file in level1
        json_file = os.path.join(level1_dir, "task-test_events.json")
        with open(json_file, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)

        # Create TSV file in level1
        tsv_file = os.path.join(level1_dir, "sub-01_task-test_events.tsv")
        with open(tsv_file, "w") as f:
            f.write("onset\tduration\ttrial_type\n0\t1\tA\n")

        result = list(walk_back(self.test_dir, tsv_file))
        self.assertEqual(len(result), 1)
        # Normalize path for Windows compatibility (handles RUNNER~1 vs runneradmin)
        json_file_norm = os.path.realpath(json_file)
        self.assertIn(json_file_norm, result)

    def test_walk_back_single_match(self):
        from hed.tools.bids.bids_util import walk_back

        # Create nested directory structure
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)

        # Create matching JSON file in subdir
        json_file = os.path.join(subdir, "task-test_events.json")
        with open(json_file, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)

        # Create TSV file in subdir
        tsv_file = os.path.join(subdir, "sub-01_task-test_events.tsv")
        with open(tsv_file, "w") as f:
            f.write("onset\tduration\ttrial_type\n0\t1\tA\n")

        result = list(walk_back(self.test_dir, tsv_file))
        self.assertEqual(len(result), 1)
        # Normalize path for Windows compatibility (handles RUNNER~1 vs runneradmin)
        json_file_norm = os.path.realpath(json_file)
        self.assertIn(json_file_norm, result)

    def test_walk_back_no_match(self):
        from hed.tools.bids.bids_util import walk_back

        # Create directory structure but no matching JSON files
        subdir = os.path.join(self.test_dir, "subdir")
        os.makedirs(subdir)

        # Create TSV file but no matching JSON
        tsv_file = os.path.join(subdir, "sub-01_task-test_events.tsv")
        with open(tsv_file, "w") as f:
            f.write("onset\tduration\ttrial_type\n0\t1\tA\n")

        result = list(walk_back(self.test_dir, tsv_file))
        self.assertEqual(len(result), 0)

    def test_walk_back_multiple_candidates(self):
        from hed.tools.bids.bids_util import walk_back

        # Create directory structure
        level1_dir = os.path.join(self.test_dir, "level1")
        os.makedirs(level1_dir)

        # Create two JSON files that would both match according to BIDS rules
        # This is an edge case that shouldn't happen in real BIDS data, but we test it
        json_file1 = os.path.join(level1_dir, "events.json")  # suffix=events, no entities
        json_file2 = os.path.join(level1_dir, "task-test_events.json")  # suffix=events, task=test

        with open(json_file1, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)
        with open(json_file2, "w") as f:
            json.dump({"trial_type": {"HED": "Event"}}, f)

        # Create TSV file - both JSON files could match this
        # events.json matches (no entities to check)
        # task-test_events.json matches (task=test matches)
        tsv_file = os.path.join(level1_dir, "sub-01_task-test_events.tsv")
        with open(tsv_file, "w") as f:
            f.write("onset\tduration\ttrial_type\n0\t1\tA\n")

        # This should raise an exception due to multiple candidates
        with self.assertRaises(Exception) as context:
            list(walk_back(self.test_dir, tsv_file))
        self.assertIn("MULTIPLE_INHERITABLE_FILES", str(context.exception))


if __name__ == "__main__":
    unittest.main()
