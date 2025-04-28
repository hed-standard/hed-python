import os
import unittest
import json
from unittest.mock import patch, mock_open
from hed.tools.bids.bids_util import (parse_bids_filename, group_by_suffix, get_schema_from_description)


class TestGetSchemaFromDescription(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data='{"HEDVersion": "8.0.0"}')
    @patch("hed.schema.hed_schema_io.load_schema_version")
    def test_valid_description(self, mock_load_schema_version, mock_file):
        """Test that a valid dataset_description.json correctly calls load_schema_version"""
        mock_load_schema_version.return_value = "Mocked Schema"
        root_path = "mock/path"
        result = get_schema_from_description(root_path)

        mock_file.assert_called_once_with(
            os.path.join(os.path.abspath(root_path), "dataset_description.json"), "r"
        )
        mock_load_schema_version.assert_called_once_with("8.0.0")
        self.assertEqual(result, "Mocked Schema")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_missing_file(self, mock_file):
        """Test that a missing dataset_description.json returns None"""
        root_path = "mock/path"
        result = get_schema_from_description(root_path)
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data='invalid json')
    def test_invalid_json(self, mock_file):
        """Test that an invalid JSON file returns None"""
        root_path = "mock/path"
        result = get_schema_from_description(root_path)
        self.assertIsNone(result)

    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    @patch("hed.schema.hed_schema_io.load_schema_version", return_value="Mocked Schema")
    def test_missing_hed_version(self, mock_load_schema_version, mock_file):
        """Test that a missing HEDVersion key calls load_schema_version with None"""
        root_path = "mock/path"
        result = get_schema_from_description(root_path) # Debugging
        mock_load_schema_version.assert_called_once_with(None)
        self.assertEqual(result, "Mocked Schema")


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

    @patch("hed.tools.bids.bids_util.walk_back")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_merged_sidecar_no_overlap(self, mock_open_func, mock_walk_back):
        from hed.tools.bids.bids_util import get_merged_sidecar
        mock_sidecar1_content = json.dumps({"key1": "value1"})
        mock_sidecar2_content = json.dumps({"key2": "value2"})

        # Mock walk_back to return full file paths
        mock_walk_back.return_value = ["/root/sidecar1.json", "/root/sidecar2.json"]

        # Mock open() to return the correct file contents
        mock_open_func.side_effect = [
            mock_open(read_data=mock_sidecar2_content).return_value,  # sidecar2 is processed first (LIFO)
            mock_open(read_data=mock_sidecar1_content).return_value   # sidecar1 is processed last
        ]

        # Run the function
        merged = get_merged_sidecar("/root", "file.tsv")

        # Expected result (sidecar2 processed first, then sidecar1 updates it)
        expected = {"key1": "value1", "key2": "value2"}
        self.assertEqual(merged, expected)

    @patch("hed.tools.bids.bids_util.walk_back")
    @patch("builtins.open", new_callable=mock_open)
    def test_get_merged_sidecar_overlap(self, mock_open_func, mock_walk_back):
        from hed.tools.bids.bids_util import get_merged_sidecar
        mock_sidecar1_content = json.dumps({"key1": "value1", "key2": "value2"})
        mock_sidecar2_content = json.dumps({"key2": "value3", "key4": "value4"})

        # Mock walk_back to return full file paths
        mock_walk_back.return_value = ["/root/sidecar1.json", "/root/sidecar2.json"]

        # Mock open() to return the correct file contents
        mock_open_func.side_effect = [
            mock_open(read_data=mock_sidecar2_content).return_value,  # sidecar2 is processed first (LIFO)
            mock_open(read_data=mock_sidecar1_content).return_value   # sidecar1 is processed last
        ]

        # Run the function
        merged = get_merged_sidecar("/root", "file.tsv")

        # Expected result (sidecar2 processed first, then sidecar1 updates it)
        expected = {"key1": "value1", "key2": "value2", "key4": "value4"}
        self.assertEqual(merged, expected)


class TestGetCandidates(unittest.TestCase):

    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("hed.tools.bids.bids_util.parse_bids_filename")
    @patch("hed.tools.bids.bids_util.matches_criteria")
    def test_get_candidates_valid_files(self, mock_matches_criteria, mock_parse_bids_filename, mock_isfile,
                                        mock_listdir):
        from hed.tools.bids.bids_util import get_candidates

        mock_listdir.return_value = ["file1.json", "file2.json", "file3.txt"]
        mock_isfile.side_effect = lambda path: path.endswith(".json")

        mock_parse_bids_filename.side_effect = lambda path: {"ext": ".json", "suffix": "events",
                                                             "entities": {"subject": "01"},
                                                             "bad": []} if path.endswith(".json") else None
        mock_matches_criteria.side_effect = lambda json_dict, tsv_dict: json_dict["suffix"] == tsv_dict["suffix"]

        source_dir = os.path.abspath("/test")
        candidates = get_candidates(source_dir, {"suffix": "events", "entities": {"subject": "01"}, "bad": []})
        expected_candidates =  [os.path.abspath(os.path.join(source_dir, "file1.json")),
                                os.path.abspath(os.path.join(source_dir, "file2.json"))]
        self.assertEqual(candidates, expected_candidates)


    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("hed.tools.bids.bids_util.parse_bids_filename")
    @patch("hed.tools.bids.bids_util.matches_criteria")
    def test_get_candidates_no_valid_files(self, mock_matches_criteria, mock_parse_bids_filename, mock_isfile,
                                           mock_listdir):
        from hed.tools.bids.bids_util import get_candidates

        mock_listdir.return_value = ["file1.json", "file2.json"]
        mock_isfile.return_value = True

        mock_parse_bids_filename.side_effect = lambda path: {"ext": ".json", "suffix": "events",
                                                             "entities": {"subject": "01"}, "bad": True}
        mock_matches_criteria.return_value = False

        source_dir = os.path.abspath("/test")
        candidates = get_candidates(source_dir, {"suffix": "events", "entities": {"subject": "01"}})

        self.assertEqual(candidates, [])

    @patch("os.listdir")
    @patch("os.path.isfile")
    @patch("hed.tools.bids.bids_util.parse_bids_filename")
    @patch("hed.tools.bids.bids_util.matches_criteria")
    def test_get_candidates_mixed_files(self, mock_matches_criteria, mock_parse_bids_filename, mock_isfile,
                                        mock_listdir):
        from hed.tools.bids.bids_util import get_candidates

        mock_listdir.return_value = ["file1.json", "file2.json", "file3.json"]
        mock_isfile.return_value = True

        def mock_parse(path):
            if "file3.json" in path:
                return {"ext": ".json", "suffix": "events", "entities": {"subject": "01"}, "bad": True}  # Invalid
            return {"ext": ".json", "suffix": "events", "entities": {"subject": "01"}, "bad": False}  # Valid

        mock_parse_bids_filename.side_effect = mock_parse
        mock_matches_criteria.side_effect = lambda json_dict, tsv_dict: not json_dict.get("bad")

        source_dir = os.path.abspath("/test")
        candidates = get_candidates(source_dir, {"suffix": "events", "entities": {"subject": "01"}})

        expected_candidates = [
            os.path.abspath(os.path.join(source_dir, "file1.json")),
            os.path.abspath(os.path.join(source_dir, "file2.json"))
        ]
        self.assertEqual(candidates, expected_candidates)


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

    @patch("hed.tools.bids.bids_util.get_candidates")
    def test_walk_back_candidate_in_root(self, mock_get_candidates):
        from hed.tools.bids.bids_util import walk_back
        # System root directory ("/" on Unix, "C:\" or equivalent on Windows)
        dataset_root = os.path.abspath(os.sep)
        file_path = os.path.join(dataset_root, "level1", "file.tsv")  # File in the dataset

        # Define the side effect for get_candidates
        def side_effect(directory, file_path):
            if directory == os.path.join(dataset_root, "level1"):
                return [os.path.join(directory, "file1.json")]
            return []  # No other matches

        mock_get_candidates.side_effect = side_effect
        result = list(walk_back(dataset_root, file_path))
        expected_result = [os.path.join(dataset_root, "level1", "file1.json")]
        self.assertEqual(result, expected_result)

    @patch("hed.tools.bids.bids_util.get_candidates")
    def test_walk_back_single_match(self, mock_get_candidates):
        from hed.tools.bids.bids_util import walk_back

        dataset_root = os.path.abspath(os.path.join(os.sep, "dataset"))
        file_path = os.path.join(dataset_root, "subdir", "file.tsv")  # File inside dataset

        # Mock candidates only at the expected level
        def mock_candidates(directory, file_path):
            if directory == os.path.abspath(os.path.join(dataset_root, "subdir")):
                return [os.path.join(dataset_root, "subdir","file1.json")]
            return []

        mock_get_candidates.side_effect = mock_candidates

        result = list(walk_back(dataset_root, file_path))
        expected_result= [os.path.join(dataset_root, "subdir", "file1.json")]
        self.assertEqual(result, expected_result)

    @patch("hed.tools.bids.bids_util.get_candidates")
    def test_walk_back_no_match(self, mock_get_candidates):
        from hed.tools.bids.bids_util import walk_back

        dataset_root = os.path.abspath("/root")  # Ensure cross-platform compatibility
        file_path = os.path.join(dataset_root, "subdir", "file.tsv")  # Place file inside root

        # Always return an empty list (no candidates found at any directory level)
        mock_get_candidates.side_effect = lambda directory, filename: []
        result = list(walk_back(dataset_root, file_path))
        self.assertEqual(result, [])  # Expecting an empty list since no matches are found

    @patch("hed.tools.bids.bids_util.get_candidates")
    def test_walk_back_multiple_candidates(self, mock_get_candidates):
        from hed.tools.bids.bids_util import walk_back

        dataset_root = os.path.abspath("/root")  # Normalize root path
        file_path = os.path.join(dataset_root, "level1", "file.tsv")  # File inside level1

        # Define the side effect for get_candidates
        def side_effect(directory, file_path):
            if directory == os.path.join(dataset_root, "level1"):  # First level with multiple candidates
                return [os.path.join(directory, "file1.json"), os.path.join(directory, "file2.json")]
            return []  # No other matches in the hierarchy

        mock_get_candidates.side_effect = side_effect

        # Expecting an exception due to multiple candidates
        with self.assertRaises(Exception) as context:
            list(walk_back(dataset_root, file_path))
        # Check that the error message contains the expected code
        self.assertIn("MULTIPLE_INHERITABLE_FILES", str(context.exception))


if __name__ == "__main__":
    unittest.main()
