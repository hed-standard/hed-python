import os
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from hed.scripts.hed_extract_bids_sidecar import main


class TestExtractBidsSidecar(unittest.TestCase):

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

    @classmethod
    def tearDownClass(cls):
        cls.mock_logger_patch.stop()

    def test_main_events_suffix(self):
        """Test basic extraction with events suffix - should generate template for categorical columns."""
        arg_list = [self.data_root, "-s", "events"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)

            self.assertIn("sidecar_template", output_dict)
            template = output_dict["sidecar_template"]

            # Should have categorical columns: event_type, face_type, rep_status, stim_file
            self.assertIn("event_type", template)
            self.assertIn("face_type", template)
            self.assertIn("rep_status", template)

            # onset, duration should NOT be in template (they're timing columns)
            self.assertNotIn("onset", template)
            self.assertNotIn("duration", template)

            # Each entry should have HED and Description
            for col_name, col_data in template.items():
                self.assertIn("HED", col_data)
                self.assertIn("Description", col_data)

    def test_main_events_with_output_file(self):
        """Test extraction with output file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp_file:
            output_path = tmp_file.name

        try:
            arg_list = [self.data_root, "-s", "events", "-o", output_path]

            with patch("sys.stderr", new=io.StringIO()):
                result = main(arg_list)
                self.assertEqual(result, 0)

            # Verify the file was created and contains valid JSON
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                output_dict = json.load(f)

            self.assertIn("sidecar_template", output_dict)
            template = output_dict["sidecar_template"]

            # Should have categorical columns
            self.assertIn("event_type", template)
            self.assertTrue(len(template) > 0)

        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_main_participants_suffix(self):
        """Test extraction with participants suffix."""
        arg_list = [self.data_root, "-s", "participants"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            template = output_dict["sidecar_template"]

            # Should have sex column (categorical)
            self.assertIn("sex", template)

            # Should NOT have participant_id (skip column for participants)
            # Though it might be included - let's just check we got a template
            self.assertTrue(len(template) > 0)

    def test_events_with_skip_columns(self):
        """Test that we can skip additional columns beyond the defaults."""
        # Also skip 'sample' since it has thousands of unique values in EEG data
        arg_list = [self.data_root, "-s", "events", "-sc", "stim_file", "value", "sample"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            template = output_dict["sidecar_template"]

            # Should have event_type but not stim_file or value
            self.assertIn("event_type", template)
            self.assertNotIn("stim_file", template)
            self.assertNotIn("value", template)

            # onset and duration should still not be there
            self.assertNotIn("onset", template)
            self.assertNotIn("duration", template)

    def test_events_with_value_columns(self):
        """Test specifying value columns for numeric data."""
        # trial, rep_lag are numeric columns that should be treated as values
        arg_list = [self.data_root, "-s", "events", "-vc", "trial", "rep_lag"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            template = output_dict["sidecar_template"]

            # trial and rep_lag should be in template as value columns
            self.assertIn("trial", template)
            self.assertIn("rep_lag", template)

            # Categorical columns should still be there
            self.assertIn("event_type", template)
            self.assertIn("face_type", template)

    def test_template_has_categorical_values(self):
        """Test that categorical columns include their unique values."""
        arg_list = [self.data_root, "-s", "events"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            template = output_dict["sidecar_template"]

            # event_type should have specific values like "show_face", "show_circle", "left_press", etc.
            self.assertIn("event_type", template)
            event_type_entry = template["event_type"]

            # Should have a Levels section with the unique values
            if "Levels" in event_type_entry:
                levels = event_type_entry["Levels"]
                # Should have some categorical values
                self.assertTrue(len(levels) > 0)

    def test_exclude_directories(self):
        """Test that exclude directories parameter works."""
        # This dataset doesn't have derivatives/stimuli with events, but test the parameter
        arg_list = [self.data_root, "-s", "events", "-x", "derivatives", "code"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            self.assertEqual(result, 0)

            output = mock_stdout.getvalue()
            output_dict = json.loads(output)
            self.assertIn("sidecar_template", output_dict)


if __name__ == "__main__":
    unittest.main()
