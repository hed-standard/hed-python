"""Tests for validate_hed_string script."""

import os
import io
import unittest
from unittest.mock import patch
from hed.scripts.validate_hed_string import main


class TestValidateHedString(unittest.TestCase):
    """Test validate_hed_string script functionality."""

    def test_valid_string(self):
        """Test validation of a valid HED string."""
        arg_list = ["Event, (Action, Move)", "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 0, "Valid string should return 0")
        self.assertIn("valid", output.lower())

    def test_invalid_string(self):
        """Test validation of an invalid HED string."""
        arg_list = ["InvalidTag", "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1, "Invalid string should return 1")
        self.assertIn("error", output.lower())

    def test_with_definitions(self):
        """Test validation with definitions."""
        arg_list = ["Event, Def/MyDef", "-sv", "8.3.0", "-d", "(Definition/MyDef, (Action, Move))", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 0, "Valid string with definitions should return 0")
        self.assertIn("valid", output.lower())

    def test_invalid_definitions(self):
        """Test that invalid definitions are caught before HED string validation."""
        arg_list = ["Event, Def/MyDef", "-sv", "8.3.0", "-d", "(Definition/MyDef, InvalidTag)", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1, "Invalid definitions should return 1")
        self.assertIn("error", output.lower())

    def test_json_output(self):
        """Test JSON output format."""
        arg_list = ["InvalidTag", "-sv", "8.3.0", "-f", "json", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 1)
        # Should be valid JSON
        import json

        try:
            json.loads(output)
        except json.JSONDecodeError:
            self.fail("Output should be valid JSON")

    def test_output_file(self):
        """Test writing output to a file."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            output_file = f.name

        try:
            arg_list = ["Event", "-sv", "8.3.0", "-o", output_file, "--no-log"]
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
        arg_list = ["Event", "-sv", "8.3.0", "-w", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()):
            result = main(arg_list)

        # Should still validate successfully
        self.assertEqual(result, 0)

    def test_verbose_output(self):
        """Test verbose logging output."""
        arg_list = ["Event", "-sv", "8.3.0", "-v"]

        with patch("sys.stdout", new=io.StringIO()), patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            result = main(arg_list)
            stderr_output = mock_stderr.getvalue()

        self.assertEqual(result, 0)
        # Verbose mode should produce INFO level messages
        self.assertIn("INFO", stderr_output)

    def test_no_log_option(self):
        """Test --no-log option suppresses all logging."""
        arg_list = ["Event", "-sv", "8.3.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()), patch("sys.stderr", new=io.StringIO()) as mock_stderr:
            result = main(arg_list)
            stderr_output = mock_stderr.getvalue()

        self.assertEqual(result, 0)
        # No log option should suppress all logging to stderr
        self.assertEqual(stderr_output, "", "stderr should be empty with --no-log")

    def test_multiple_schemas(self):
        """Test validation with multiple schema versions."""
        # Test with base + library schema
        arg_list = ["Event, Action", "-sv", "8.3.0", "-sv", "score_1.1.0", "--no-log"]

        with patch("sys.stdout", new=io.StringIO()) as mock_stdout:
            result = main(arg_list)
            output = mock_stdout.getvalue()

        self.assertEqual(result, 0, "Valid string with multiple schemas should return 0")
        self.assertIn("valid", output.lower())


if __name__ == "__main__":
    unittest.main()
