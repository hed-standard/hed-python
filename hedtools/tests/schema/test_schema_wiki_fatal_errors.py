import unittest
import os

from hed import schema
from hed import HedFileError, HedExceptions


class TestHedSchema(unittest.TestCase):
    base_schema_dir = '../data/invalid_wiki_schemas/'

    @classmethod
    def setUpClass(cls):
        cls.full_base_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.base_schema_dir)
        cls.files_and_errors = {
            "HED_schema_no_start.mediawiki": HedExceptions.SCHEMA_START_MISSING,
            "HED_schema_no_end.mediawiki": HedExceptions.SCHEMA_END_INVALID,
            "HED_hed_no_end.mediawiki": HedExceptions.HED_END_INVALID,
            "HED_separator_invalid.mediawiki": HedExceptions.INVALID_SECTION_SEPARATOR,
            "HED_header_missing.mediawiki": HedExceptions.SCHEMA_HEADER_MISSING,
            "HED_header_invalid.mediawiki": HedExceptions.SCHEMA_HEADER_INVALID,
            "HED_header_invalid_version.mediawiki": HedExceptions.BAD_HED_SEMANTIC_VERSION,
            "HED_header_missing_version.mediawiki": HedExceptions.BAD_HED_SEMANTIC_VERSION,
            "HED_header_bad_library.mediawiki": HedExceptions.BAD_HED_LIBRARY_NAME,
            "HED_schema_out_of_order.mediawiki": HedExceptions.SCHEMA_START_MISSING,
            "empty_node.mediawiki": HedExceptions.HED_SCHEMA_WIKI_WARNINGS,
            "malformed_line.mediawiki": HedExceptions.HED_SCHEMA_WIKI_WARNINGS,
            "malformed_line2.mediawiki": HedExceptions.HED_SCHEMA_WIKI_WARNINGS,
            "malformed_line3.mediawiki": HedExceptions.HED_SCHEMA_WIKI_WARNINGS,
            "malformed_line4.mediawiki": HedExceptions.HED_SCHEMA_WIKI_WARNINGS,
            "malformed_line5.mediawiki": HedExceptions.HED_SCHEMA_WIKI_WARNINGS,
            "empty_node.xml": HedExceptions.HED_SCHEMA_NODE_NAME_INVALID
        }

        cls.expected_count = {
            "empty_node.mediawiki": 1,
            "malformed_line.mediawiki": 1,
            "malformed_line2.mediawiki": 1,
            "malformed_line3.mediawiki": 1,
            "malformed_line4.mediawiki": 1,
            "malformed_line5.mediawiki": 1,
        }
    def test_invalid_schema(self):
        for filename, error in self.files_and_errors.items():
            full_filename = self.full_base_folder + filename

            try:
                loaded_schema = schema.load_schema(full_filename)
                # all of these should produce exceptions.
                self.assertFalse(True)
            except HedFileError as e:
                self.assertEqual(e.error_type, error)
                if filename in self.expected_count:
                    self.assertEqual(len(e.issues), self.expected_count[filename])
                pass
