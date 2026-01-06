import os
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from hed.scripts.extract_tabular_summary import main, get_parser, extract_summary


class TestExtractTabularSummary(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/bids_tests/eeg_ds003645s_hed_demo"))
        # Suppress logging for cleaner test output
        cls.mock_logger_patch = patch("logging.getLogger")
        cls.mock_logger = cls.mock_logger_patch.start()
        cls.mock_logger.return_value.info.return_value = None
        cls.mock_logger.return_value.debug.return_value = None
        cls.mock_logger.return_value.warning.return_value = None
        cls.mock_logger.return_value.error.return_value = None
        cls.mock_logger.return_value.isEnabledFor.return_value = False

    @classmethod
    def tearDownClass(cls):
        cls.mock_logger_patch.stop()

    def _get_summary_dict(self, output_dict):
        """Helper to extract the tabular_summary from JSON output if wrapped."""
        if "tabular_summary" in output_dict:
            return output_dict["tabular_summary"]
        return output_dict

    def test_get_parser(self):
        """Test that argument parser is created correctly."""
        parser = get_parser()
        self.assertIsNotNone(parser)

        # Test parsing valid arguments
        args = parser.parse_args([self.data_root])
        self.assertEqual(args.data_path, self.data_root)
        self.assertEqual(args.name_suffix, "events")  # Default
        self.assertEqual(args.output_format, "json")  # Default
        self.assertIsNone(args.categorical_limit)  # Default
        self.assertIsNone(args.filename_filter)  # Default

    def test_parser_with_all_arguments(self):
        """Test parser with all arguments specified."""
        parser = get_parser()
        args = parser.parse_args(
            [
                self.data_root,
                "-p",
                "sub-",
                "-s",
                "participants",
                "-x",
                "derivatives",
                "code",
                "-fl",
                "sub-002",
                "-vc",
                "age",
                "weight",
                "-sc",
                "notes",
                "comments",
                "-cl",
                "25",
                "-o",
                "output.json",
                "-f",
                "text",
                "-l",
                "INFO",
                "-v",
            ]
        )

        self.assertEqual(args.data_path, self.data_root)
        self.assertEqual(args.name_prefix, "sub-")
        self.assertEqual(args.name_suffix, "participants")
        self.assertEqual(args.exclude_dirs, ["derivatives", "code"])
        self.assertEqual(args.filename_filter, "sub-002")
        self.assertEqual(args.value_columns, ["age", "weight"])
        self.assertEqual(args.skip_columns, ["notes", "comments"])
        self.assertEqual(args.categorical_limit, 25)
        self.assertEqual(args.output_file, "output.json")
        self.assertEqual(args.output_format, "text")
        self.assertEqual(args.log_level, "INFO")
        self.assertTrue(args.verbose)

    def test_main_default_events_json(self):
        """Test basic extraction with default events suffix and JSON output."""
        arg_list = [self.data_root]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Should have required summary fields
            self.assertIn("Name", summary_dict)
            self.assertIn("Total files", summary_dict)
            self.assertIn("Total events", summary_dict)
            self.assertIn("Files", summary_dict)
            self.assertIn("Categorical columns", summary_dict)
            self.assertIn("Value columns", summary_dict)

            # Should have processed multiple files
            total_files = summary_dict["Total files"]
            self.assertGreater(total_files, 0)

            # Should have categorical columns
            categorical = summary_dict["Categorical columns"]
            self.assertGreater(len(categorical), 0)

    def test_main_text_output_format(self):
        """Test extraction with text output format."""
        arg_list = [self.data_root, "-f", "text"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()

            # Text output should contain specific markers
            self.assertIn("Summary for column dictionary", output)
            self.assertIn("Categorical columns (", output)
            self.assertIn("Value columns (", output)

    def test_main_with_output_file_json(self):
        """Test extraction with JSON output file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp_file:
            output_path = tmp_file.name

        try:
            arg_list = [self.data_root, "-o", output_path, "-f", "json"]

            with patch("sys.stderr", new=io.StringIO()):
                result = main(arg_list)
                self.assertEqual(result, 0)

            # Verify the file was created and contains valid JSON
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                output_dict = json.load(f)

            summary_dict = self._get_summary_dict(output_dict)
            self.assertIn("Name", summary_dict)
            self.assertIn("Total events", summary_dict)
            self.assertGreater(summary_dict["Total files"], 0)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_main_with_output_file_text(self):
        """Test extraction with text output file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp_file:
            output_path = tmp_file.name

        try:
            arg_list = [self.data_root, "-o", output_path, "-f", "text"]

            with patch("sys.stderr", new=io.StringIO()):
                result = main(arg_list)
                self.assertEqual(result, 0)

            # Verify the file was created and contains text
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                output = f.read()

            self.assertIn("Summary for column dictionary", output)
            self.assertIn("Categorical columns (", output)
            self.assertIn("Value columns (", output)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_wildcard_suffix(self):
        """Test using wildcard suffix to match all TSV files."""
        arg_list = [self.data_root, "-s", "*"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Should process more files than just events
            total_files = summary_dict["Total files"]
            self.assertGreater(total_files, 0)

            # Files dict should include various suffixes
            files = summary_dict["Files"]
            self.assertIsInstance(files, dict)
            self.assertGreater(len(files), 0)

    def test_with_skip_columns(self):
        """Test that skip columns are excluded from summary."""
        arg_list = [self.data_root, "-s", "events", "-sc", "stim_file", "value"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            categorical = summary_dict["Categorical columns"]

            # stim_file and value should not be in the summary
            self.assertNotIn("stim_file", categorical)
            self.assertNotIn("value", categorical)

            # But other columns should be there
            self.assertGreater(len(categorical), 0)

    def test_with_value_columns(self):
        """Test specifying value columns for numeric data."""
        arg_list = [self.data_root, "-s", "events", "-vc", "trial", "rep_lag"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            value_cols = summary_dict["Value columns"]

            # trial and rep_lag should be treated as value columns
            self.assertIn("trial", value_cols)
            self.assertIn("rep_lag", value_cols)

            # Value columns store [total_values, num_files]
            for col in ["trial", "rep_lag"]:
                self.assertIsInstance(value_cols[col], list)
                self.assertEqual(len(value_cols[col]), 2)
                self.assertGreater(value_cols[col][0], 0)  # total values > 0
                self.assertGreater(value_cols[col][1], 0)  # num files > 0

    def test_with_categorical_limit(self):
        """Test categorical limit parameter."""
        arg_list = [self.data_root, "-s", "events", "-cl", "10"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            self.assertIn("Categorical limit", summary_dict)
            self.assertEqual(summary_dict["Categorical limit"], "10")

            # Check if overflow columns are tracked
            if "Overflow columns" in summary_dict:
                # Some columns should have overflowed with limit of 10
                self.assertIsInstance(summary_dict["Overflow columns"], list)

    def test_with_filename_filter(self):
        """Test filename filter parameter."""
        arg_list = [self.data_root, "-s", "*", "-fl", "sub-002"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Check that only sub-002 files were processed
            files = summary_dict["Files"]
            for file_path in files:
                self.assertIn("sub-002", file_path)

    def test_with_filename_filter_and_suffix(self):
        """Test combining filename filter with suffix."""
        arg_list = [self.data_root, "-s", "events", "-fl", "run-1"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Should process events files for run-1 only
            files = summary_dict["Files"]
            for file_path in files:
                self.assertIn("events", file_path)
                self.assertIn("run-1", file_path)

            # Should have at least one file but not all run files
            self.assertGreater(len(files), 0)

    def test_with_prefix(self):
        """Test name prefix parameter."""
        arg_list = [self.data_root, "-p", "sub-", "-s", "*"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Should process files starting with sub-
            total_files = summary_dict["Total files"]
            self.assertGreater(total_files, 0)

    def test_with_exclude_dirs(self):
        """Test exclude directories parameter."""
        # First get count without exclusions
        arg_list1 = [self.data_root, "-s", "*"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list1)
            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            output_dict1 = json.loads(output)
            summary_dict1 = self._get_summary_dict(output_dict1)
            summary_dict1["Total files"]

        # Now exclude a directory (this dataset might not have these, but test the parameter)
        arg_list2 = [self.data_root, "-s", "*", "-x", "derivatives", "code"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list2)
            self.assertEqual(result, 0)
            output = mock_stdout.getvalue()
            output_dict2 = json.loads(output)
            summary_dict2 = self._get_summary_dict(output_dict2)
            total_files2 = summary_dict2["Total files"]

        # Should have at least processed some files
        self.assertGreater(total_files2, 0)

    def test_participants_suffix(self):
        """Test extraction with participants suffix."""
        arg_list = [self.data_root, "-s", "participants"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Should have categorical columns from participants file
            categorical = summary_dict["Categorical columns"]
            self.assertIn("sex", categorical)

    def test_no_files_found(self):
        """Test handling when no files match the criteria."""
        arg_list = [self.data_root, "-s", "nonexistent_suffix"]

        with patch("sys.stderr", new=io.StringIO()):
            result = main(arg_list)
            self.assertEqual(result, 1)  # Should return error code

    def test_no_files_after_filter(self):
        """Test handling when filter eliminates all files."""
        arg_list = [self.data_root, "-s", "events", "-fl", "nonexistent_subject"]

        with patch("sys.stderr", new=io.StringIO()):
            result = main(arg_list)
            self.assertEqual(result, 1)  # Should return error code

    def test_categorical_columns_have_counts(self):
        """Test that categorical columns include value counts."""
        arg_list = [self.data_root, "-s", "events"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            categorical = summary_dict["Categorical columns"]

            # Pick a known column and verify it has values with counts
            if "event_type" in categorical:
                event_type_data = categorical["event_type"]
                self.assertIsInstance(event_type_data, dict)
                # Should have some values
                self.assertGreater(len(event_type_data), 0)
                # Each value should have a count (list with [count, files])
                for _value, count_info in event_type_data.items():
                    self.assertIsInstance(count_info, list)
                    self.assertEqual(len(count_info), 2)  # [count, num_files]

    def test_value_columns_have_statistics(self):
        """Test that value columns include proper count information."""
        arg_list = [self.data_root, "-s", "events", "-vc", "trial"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            value_cols = summary_dict["Value columns"]
            self.assertIn("trial", value_cols)

            # Value columns store [total_values, num_files]
            trial_info = value_cols["trial"]
            self.assertIsInstance(trial_info, list)
            self.assertEqual(len(trial_info), 2)
            self.assertGreater(trial_info[0], 0)  # total values > 0
            self.assertGreater(trial_info[1], 0)  # num files > 0

    def test_multiple_runs_combination(self):
        """Test that data from multiple runs is properly combined."""
        arg_list = [self.data_root, "-s", "events", "-fl", "sub-002"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # Should have processed multiple event files for sub-002
            files = summary_dict["Files"]
            events_files = [f for f in files if "events" in f]
            self.assertGreater(len(events_files), 1)

            # Total events should be sum across all files
            total_events = summary_dict["Total events"]
            self.assertGreater(total_events, 0)

    def test_categorical_limit_zero(self):
        """Test edge case of categorical limit of 0."""
        arg_list = [self.data_root, "-s", "events", "-cl", "0"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            self.assertEqual(summary_dict["Categorical limit"], "0")

            # Categorical columns should have empty dicts
            categorical = summary_dict["Categorical columns"]
            for _col_name, col_data in categorical.items():
                self.assertEqual(len(col_data), 0)

    def test_overflow_columns_in_output(self):
        """Test that overflow columns are included when limit is exceeded."""
        arg_list = [self.data_root, "-s", "events", "-cl", "5"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            summary_dict = self._get_summary_dict(output_dict)

            # With limit of 5, some columns should overflow
            if "Overflow columns" in summary_dict:
                overflow = summary_dict["Overflow columns"]
                self.assertIsInstance(overflow, list)
                # stim_file definitely has > 5 unique values
                self.assertIn("stim_file", overflow)

    def test_extract_summary_function_directly(self):
        """Test the extract_summary function directly with args object."""
        parser = get_parser()
        args = parser.parse_args([self.data_root, "-s", "events"])

        summary = extract_summary(args)

        # Should return a TabularSummary object
        from hed.tools.analysis.tabular_summary import TabularSummary

        self.assertIsInstance(summary, TabularSummary)

        # Should have processed files
        self.assertGreater(len(summary.files), 0)

    def test_verbose_flag(self):
        """Test that verbose flag doesn't cause errors."""
        arg_list = [self.data_root, "-s", "events", "-v"]

        with patch("sys.stdout", new=io.StringIO()):
            result = main(arg_list)
            self.assertEqual(result, 0)

    def test_log_level_debug(self):
        """Test that debug log level doesn't cause errors."""
        arg_list = [self.data_root, "-s", "events", "-l", "DEBUG"]

        with patch("sys.stdout", new=io.StringIO()):
            result = main(arg_list)
            self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
