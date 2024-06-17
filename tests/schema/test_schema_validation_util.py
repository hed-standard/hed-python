import os
import unittest
import hed.schema.schema_validation_util as util
from hed.errors import ErrorHandler, SchemaWarnings
from hed import load_schema_version, load_schema, HedSchemaGroup
from hed.schema.hed_schema_entry import HedSchemaEntry, HedTagEntry


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version("8.1.0")

    def validate_term_base(self, input_text, expected_issues):
        for text, issues in zip(input_text, expected_issues):
            entry = HedTagEntry(name=text, section=None)
            entry.short_tag_name = text
            test_issues = util.validate_schema_tag_new(entry)
            self.assertCountEqual(issues, test_issues)

    def validate_desc_base(self, input_descriptions, expected_issues):
        for description, issues in zip(input_descriptions, expected_issues):
            entry = HedSchemaEntry(name="dummy", section=None)
            entry.description = description
            test_issues = util.validate_schema_description_new(entry)
            self.assertCountEqual(issues, test_issues)

    def test_validate_schema_term(self):
        test_terms = [
            "invalidcaps",
            "Validcaps",
            "3numberisvalid",
            "Invalidchar#",
            "@invalidcharatstart",
        ]
        expected_issues = [
            ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION, test_terms[0], char_index=0,
                                      problem_char="i"),
            [],
            [],
            ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_TAG, test_terms[3], char_index=11,
                                      problem_char="#"),
            ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CAPITALIZATION, test_terms[4], char_index=0,
                                      problem_char="@")
            + ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_TAG, test_terms[4], char_index=0,
                                        problem_char="@"),
        ]
        self.validate_term_base(test_terms, expected_issues)

    def test_validate_schema_description(self):
        test_descs = [
            "This is a tag description with no invalid characters.",
            "This is (also) a tag description with no invalid characters.  -_:;./()+ ^",
            "This description has no invalid characters, as commas are allowed",
            "This description has multiple invalid characters at the end {}[]"
        ]
        expected_issues = [
            [],
            [],
            [],
            ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                      char_index=60, problem_char="{")
            + ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                        char_index=61, problem_char="}")
            + ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                        char_index=62, problem_char="[")
            + ErrorHandler.format_error(SchemaWarnings.SCHEMA_INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                        char_index=63, problem_char="]")

        ]
        self.validate_desc_base(test_descs, expected_issues)

    def test_schema_version_for_library(self):
        schema1 = load_schema_version("8.0.0")
        self.assertEqual(util.schema_version_for_library(schema1, ""), "8.0.0")
        self.assertEqual(util.schema_version_for_library(schema1, None), "8.0.0")

        schema2 = load_schema_version("8.3.0")
        self.assertEqual(util.schema_version_for_library(schema2, ""), "8.3.0")
        self.assertEqual(util.schema_version_for_library(schema2, None), "8.3.0")

        schema3 = load_schema_version(["testlib_2.0.0", "score_1.1.0"])
        self.assertEqual(util.schema_version_for_library(schema3, ""), "8.2.0")
        self.assertEqual(util.schema_version_for_library(schema3, None), "8.2.0")
        self.assertEqual(util.schema_version_for_library(schema3, "score"), "1.1.0")
        self.assertEqual(util.schema_version_for_library(schema3, "testlib"), "2.0.0")

        self.assertEqual(util.schema_version_for_library(schema3, "badlib"), None)
