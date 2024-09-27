import unittest
import os

from hed import load_schema
from hed.errors import HedFileError, HedExceptions


class TestHedSchema(unittest.TestCase):
    base_schema_dir = '../data/schema_tests/wiki_tests/'

    @classmethod
    def setUpClass(cls):
        cls.full_base_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.base_schema_dir)
        cls.files_and_errors = {
            "HED_schema_no_start.mediawiki": HedExceptions.SCHEMA_SECTION_MISSING,
            "HED_schema_no_end.mediawiki": HedExceptions.SCHEMA_SECTION_MISSING,
            "HED_hed_no_end.mediawiki": HedExceptions.SCHEMA_SECTION_MISSING,
            "HED_separator_invalid.mediawiki": HedExceptions.WIKI_SEPARATOR_INVALID,
            "HED_header_missing.mediawiki": HedExceptions.SCHEMA_HEADER_MISSING,
            "HED_header_invalid.mediawiki": HedExceptions.SCHEMA_HEADER_INVALID,
            "empty_file.mediawiki": HedExceptions.SCHEMA_HEADER_INVALID,
            "HED_header_invalid_version.mediawiki": HedExceptions.SCHEMA_VERSION_INVALID,
            "HED_header_missing_version.mediawiki": HedExceptions.SCHEMA_VERSION_INVALID,
            "HED_header_unknown_attribute.mediawiki": HedExceptions.SCHEMA_UNKNOWN_HEADER_ATTRIBUTE,
            "HED_header_bad_library.mediawiki": HedExceptions.BAD_HED_LIBRARY_NAME,
            "HED_schema_out_of_order.mediawiki": HedExceptions.SCHEMA_SECTION_MISSING,
            "empty_node.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line2.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line3.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line4.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line5.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line6.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "malformed_line7.mediawiki": HedExceptions.WIKI_DELIMITERS_INVALID,
            "empty_node.xml": HedExceptions.HED_SCHEMA_NODE_NAME_INVALID
        }

        cls.expected_count = {
            "empty_node.mediawiki": 1,
            "malformed_line.mediawiki": 1,
            "malformed_line2.mediawiki": 2,
            "malformed_line3.mediawiki": 2,
            "malformed_line4.mediawiki": 1,
            "malformed_line5.mediawiki": 1,
            "malformed_line6.mediawiki": 2,
            "malformed_line7.mediawiki": 2,
            'HED_schema_no_start.mediawiki': 1
        }
        cls.expected_line_numbers = {
            "empty_node.mediawiki": [9],
            "malformed_line.mediawiki": [9],
            "malformed_line2.mediawiki": [9, 9],
            "malformed_line3.mediawiki": [9, 9],
            "malformed_line4.mediawiki": [9],
            "malformed_line5.mediawiki": [9],
            "malformed_line6.mediawiki": [9, 10],
            "malformed_line7.mediawiki": [9, 10],
        }

    def test_invalid_schema(self):
        for filename, error in self.files_and_errors.items():
            full_filename = self.full_base_folder + filename
            with self.assertRaises(HedFileError) as context:
                load_schema(full_filename)
                # all of these should produce exceptions.
            from hed.errors import ErrorContext, get_printable_issue_string

            # Verify basic properties of exception
            expected_line_numbers = self.expected_line_numbers.get(filename, [])
            if expected_line_numbers:
                for issue, expected in zip(context.exception.issues, expected_line_numbers):
                    self.assertEqual(issue[ErrorContext.ROW], expected)
            issues = context.exception.issues

            self.assertIsInstance(get_printable_issue_string(issues), str)

            self.assertTrue(context.exception.args[0] == error)
            self.assertTrue(context.exception.filename == full_filename)

    def test_merging_errors_schema(self):
        for filename, error in self.files_and_errors.items():
            full_filename = self.full_base_folder + filename
            with self.assertRaises(HedFileError) as context:
                load_schema(full_filename)
                # all of these should produce exceptions.
            from hed.errors import ErrorHandler, ErrorContext, get_printable_issue_string
            from hed.errors.error_types import SchemaAttributeErrors
            # Verify basic properties of exception
            expected_line_numbers = self.expected_line_numbers.get(filename, [])
            if expected_line_numbers:
                for issue, expected in zip(context.exception.issues, expected_line_numbers):
                    self.assertEqual(issue[ErrorContext.ROW], expected)

            error_handler = ErrorHandler()

            error_handler.push_error_context(ErrorContext.ROW, 1)
            error_handler.push_error_context(ErrorContext.COLUMN, 2)

            issues = error_handler.format_error_with_context(SchemaAttributeErrors.SCHEMA_ATTRIBUTE_INVALID,
                                                             "error_attribute", source_tag="error_tag")
            error_handler.pop_error_context()
            error_handler.pop_error_context()

            issues += context.exception.issues
            self.assertIsInstance(get_printable_issue_string(issues), str)

            self.assertTrue(context.exception.args[0] == error)
            self.assertTrue(context.exception.filename == full_filename)

    def test_attribute_invalid(self):
        path = os.path.join(self.full_base_folder, "attribute_unknown1.mediawiki")
        schema = load_schema(path)
        issues = schema.check_compliance()
        self.assertEqual(len(issues), 7)
