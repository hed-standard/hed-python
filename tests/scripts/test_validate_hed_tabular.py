"""Tests for validate_hed_tabular script."""

import os
import io
import json
import unittest
import tempfile
import pandas as pd
from unittest.mock import patch
from hed.scripts.validate_hed_tabular import main


class TestValidateHedTabular(unittest.TestCase):
    """Test validate_hed_tabular script functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary valid tabular file
        self.valid_data = {
            "onset": [1.0, 2.0],
            "duration": [0.5, 0.5],
            "trial_type": ["show_face", "press_button"],
            "HED": ["Sensory-event", "Agent-action"],
        }
        self.valid_df = pd.DataFrame(self.valid_data)
        self.valid_tabular_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tsv")
        self.valid_df.to_csv(self.valid_tabular_file.name, sep="\t", index=False)
        self.valid_tabular_file.close()

        # Create a temporary invalid tabular file
        self.invalid_data = {"onset": [1.0], "duration": [0.5], "HED": ["InvalidTag"]}
        self.invalid_df = pd.DataFrame(self.invalid_data)
        self.invalid_tabular_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tsv")
        self.invalid_df.to_csv(self.invalid_tabular_file.name, sep="\t", index=False)
        self.invalid_tabular_file.close()

        # Sidecar setup
        self.valid_sidecar_content = {"trial_type": {"HED": {"show_face": "Sensory-event", "press_button": "Agent-action"}}}
        self.valid_sidecar_file = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
        json.dump(self.valid_sidecar_content, self.valid_sidecar_file)
        self.valid_sidecar_file.close()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.valid_tabular_file.name):
            os.remove(self.valid_tabular_file.name)
        if os.path.exists(self.invalid_tabular_file.name):
            os.remove(self.invalid_tabular_file.name)
        if os.path.exists(self.valid_sidecar_file.name):
            os.remove(self.valid_sidecar_file.name)

    def test_valid_tabular(self):
        """Test validation of a tabular file with valid HED."""
        arg_list = [self.valid_tabular_file.name, "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 0, "Valid tabular should return 0")
        self.assertIn("valid", output.lower())

    def test_invalid_tabular(self):
        """Test validation of a tabular file with invalid HED."""
        arg_list = [self.invalid_tabular_file.name, "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1, "Invalid tabular should return 1")
        self.assertIn("error", output.lower())

    def test_validation_with_sidecar(self):
        """Test validation with a sidecar."""
        # Create data that needs sidecar to be valid (empty HED column but valid trial_type)
        data = {"onset": [1.0], "duration": [0.5], "trial_type": ["show_face"], "HED": [""]}
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tsv") as f:
            df.to_csv(f.name, sep="\t", index=False)
            tabular_filename = f.name

        try:
            arg_list = [tabular_filename, "-s", self.valid_sidecar_file.name, "-sv", "8.3.0", "--no-log"]

            with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
                result = main(arg_list)
                output = mock_stdout.getvalue()

            self.assertEqual(result, 0)
            self.assertIn("valid", output.lower())
        finally:
            if os.path.exists(tabular_filename):
                os.remove(tabular_filename)

    def test_error_limiting(self):
        """Test error limiting options."""
        # Create data with repeated errors
        data = {"HED": ["InvalidTag"] * 5}
        df = pd.DataFrame(data)
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".tsv") as f:
            df.to_csv(f.name, sep="\t", index=False)
            tabular_filename = f.name

        try:
            # Test with limit
            arg_list = [tabular_filename, "-sv", "8.3.0", "-el", "2", "--no-log"]
            with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
                result = main(arg_list)
                output = mock_stdout.getvalue()

            self.assertEqual(result, 1)
            # Should mention filtering
            self.assertIn("after filtering", output)

        finally:
            if os.path.exists(tabular_filename):
                os.remove(tabular_filename)

    def test_json_output(self):
        """Test JSON output format."""
        arg_list = [self.invalid_tabular_file.name, "-sv", "8.3.0", "-f", "json", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1)
        # Should be valid JSON
        try:
            json.loads(output)
        except json.JSONDecodeError:
            self.fail("Output should be valid JSON")

    def test_missing_file(self):
        """Test handling of missing file."""
        arg_list = ["non_existent_file.tsv", "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()):
            # The script catches exceptions and logs error, returns 1
            result = main(arg_list)

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
