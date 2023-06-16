import unittest
import os
import copy
from hed.schema import schema_compliance
from hed import schema
from hed.errors import ErrorHandler, SchemaWarnings


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.1.0")

    def validate_term_base(self, input_text, expected_issues):
        for text, issues in zip(input_text, expected_issues):
            test_issues = schema_compliance.validate_schema_term(text)
            self.assertCountEqual(issues, test_issues)

    def validate_desc_base(self, input_descriptions, expected_issues):
        for description, issues in zip(input_descriptions, expected_issues):
            test_issues = schema_compliance.validate_schema_description("dummy", description)
            self.assertCountEqual(issues, test_issues)

    def test_validate_schema(self):
        schema_path_with_issues = '../data/schema_tests/HED8.0.0.mediawiki'
        schema_path_with_issues = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_path_with_issues)
        hed_schema = schema.load_schema(schema_path_with_issues)
        issues = hed_schema.check_compliance()
        self.assertTrue(isinstance(issues, list))
        self.assertTrue(len(issues) > 1)

    def test_validate_schema_term(self):
        test_terms = [
            "invalidcaps",
            "Validcaps",
            "3numberisvalid",
            "Invalidchar#",
            "@invalidcharatstart",
        ]
        expected_issues = [
            ErrorHandler.format_error(SchemaWarnings.INVALID_CAPITALIZATION, test_terms[0], char_index=0,
                                      problem_char="i"),
            [],
            [],
            ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_TAG, test_terms[3], char_index=11,
                                      problem_char="#"),
            ErrorHandler.format_error(SchemaWarnings.INVALID_CAPITALIZATION, test_terms[4], char_index=0,
                                      problem_char="@"),
        ]
        self.validate_term_base(test_terms, expected_issues)

    def test_validate_schema_description(self):
        test_descs = [
            "This is a tag description with no invalid characters.",
            "This is (also) a tag description with no invalid characters.  -_:;./()+ ^",
            "This description has no invalid characters, as commas are allowed",
            "This description has multiple invalid characters at the end @$%*"
        ]
        expected_issues = [
            [],
            [],
            [],
            ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                      char_index=60, problem_char="@")
            + ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                        char_index=61, problem_char="$")
            + ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                        char_index=62, problem_char="%")
            + ErrorHandler.format_error(SchemaWarnings.INVALID_CHARACTERS_IN_DESC, test_descs[3], "dummy",
                                        char_index=63, problem_char="*")

        ]
        self.validate_desc_base(test_descs, expected_issues)

    def test_util_placeholder(self):
        tag_entry = self.hed_schema.all_tags["Event"]
        attribute_name = "unitClass"
        self.assertTrue(schema_compliance.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name))
        attribute_name = "unitClass"
        tag_entry = self.hed_schema.all_tags["Age/#"]
        self.assertFalse(schema_compliance.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name))

    def test_util_suggested(self):
        tag_entry = self.hed_schema.all_tags["Event/Sensory-event"]
        attribute_name = "suggestedTag"
        self.assertFalse(schema_compliance.tag_exists_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = self.hed_schema.all_tags["Property"]
        self.assertFalse(schema_compliance.tag_exists_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["suggestedTag"] = "InvalidSuggestedTag"
        self.assertTrue(schema_compliance.tag_exists_check(self.hed_schema, tag_entry, attribute_name))

    def test_util_rooted(self):
        tag_entry = self.hed_schema.all_tags["Event"]
        attribute_name = "rooted"
        self.assertFalse(schema_compliance.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = self.hed_schema.all_tags["Property"]
        self.assertFalse(schema_compliance.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "Event"
        self.assertFalse(schema_compliance.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "NotRealTag"
        self.assertTrue(schema_compliance.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))