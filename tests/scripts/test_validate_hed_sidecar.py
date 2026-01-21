"""Tests for validate_hed_sidecar script."""

import os
import io
import json
import unittest
import tempfile
from unittest.mock import patch
from hed.scripts.validate_hed_sidecar import main


class TestValidateHedSidecar(unittest.TestCase):
    """Test validate_hed_sidecar script functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary valid sidecar file
        self.valid_sidecar_content = {
            "event_type": {
                "HED": {
                    "show_face": "Sensory-event, Visual-presentation, Face",
                    "press_button": "Agent-action, Participant-response, Press",
                }
            }
        }
        self.valid_sidecar_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        json.dump(self.valid_sidecar_content, self.valid_sidecar_file)
        self.valid_sidecar_file.close()

        # Create a temporary invalid sidecar file
        self.invalid_sidecar_content = {"event_type": {"HED": {"show_face": "InvalidTag"}}}
        self.invalid_sidecar_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        json.dump(self.invalid_sidecar_content, self.invalid_sidecar_file)
        self.invalid_sidecar_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.valid_sidecar_file.name):
            os.remove(self.valid_sidecar_file.name)
        if os.path.exists(self.invalid_sidecar_file.name):
            os.remove(self.invalid_sidecar_file.name)

    def test_valid_sidecar(self):
        """Test validation of a valid HED sidecar."""
        arg_list = [self.valid_sidecar_file.name, "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 0, "Valid sidecar should return 0")
        self.assertIn("valid", output.lower())

    def test_invalid_sidecar(self):
        """Test validation of an invalid HED sidecar."""
        arg_list = [self.invalid_sidecar_file.name, "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1, "Invalid sidecar should return 1")
        self.assertIn("error", output.lower())

    def test_json_output(self):
        """Test JSON output format."""
        arg_list = [self.invalid_sidecar_file.name, "-sv", "8.3.0", "-f", "json", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1)
        # Should be valid JSON
        try:
            json.loads(output)
        except json.JSONDecodeError:
            self.fail("Output should be valid JSON")

    def test_output_file(self):
        """Test writing output to a file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            arg_list = [self.valid_sidecar_file.name, "-sv", "8.3.0", "-o", output_file, "--no-log"]
            result = main(arg_list)

            self.assertEqual(result, 0)
            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r") as f:
                content = f.read()
                self.assertIn("valid", content.lower())
        finally:
            if os.path.exists(output_file):
                os.remove(output_file)

    def test_check_for_warnings(self):
        """Test --check-for-warnings flag."""
        arg_list = [self.valid_sidecar_file.name, "-sv", "8.3.0", "-w", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()):
            result = main(arg_list)
            # Just checking that it runs without crashing, as the valid sidecar might not have warnings
            self.assertEqual(result, 0)

    def test_missing_file(self):
        """Test handling of missing file."""
        arg_list = ["non_existent_file.json", "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()):
            # The script catches exceptions and logs error, returns 1
            result = main(arg_list)

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
