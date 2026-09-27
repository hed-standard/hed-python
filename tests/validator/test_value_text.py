"""The value-text character set: from HED 8.5.0 a textClass value may not contain (, ), # or ~."""

import os
import unittest

from hed import HedTag, load_schema, load_schema_version
from hed.errors.error_types import SchemaWarnings, ValidationErrors
from hed.schema.hed_schema_constants import character_types
from hed.validator import HedValidator


class TestValueText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = os.path.join(os.path.dirname(__file__), "../data/schema_tests/value_text_8.5.0.mediawiki")
        cls.schema_850 = load_schema(os.path.realpath(fixture))
        cls.schema_840 = load_schema_version("8.4.0")

    def test_value_text_is_text_without_the_structural_characters(self):
        text, value_text = character_types["text"], character_types["value-text"]
        self.assertEqual(text - value_text, set("()#~"))
        for char in ["'", '"', ";", "%", " ", "/", "nonascii"]:
            self.assertIn(char, value_text)
        for char in ",[]{}":
            self.assertNotIn(char, value_text)

    def test_structural_characters_are_rejected_by_the_value_class(self):
        """The rejection comes from the value-class character check, not from parsing the string."""
        validator = HedValidator(self.schema_850)
        for value in ["a)", "(a)", "trial #3", "a~b"]:
            with self.subTest(value=value):
                issues = validator.validate_units(HedTag(f"Note/{value}", self.schema_850), allow_placeholders=False)
                self.assertTrue(issues)
                self.assertEqual({issue["code"] for issue in issues}, {ValidationErrors.CHARACTER_INVALID})
        for value in ["It's 50% done; ok?", "Un café", "A plain note."]:
            with self.subTest(value=value):
                issues = validator.validate_units(HedTag(f"Note/{value}", self.schema_850), allow_placeholders=False)
                self.assertEqual(issues, [])

    def test_earlier_schemas_still_allow_them_in_the_value_class(self):
        """8.4.0 keeps textClass on text: the value-class check passes, and only the string parse objects."""
        validator = HedValidator(self.schema_840)
        for value in ["a)", "(a)", "trial #3", "a~b"]:
            with self.subTest(value=value):
                tag = HedTag(f"Description/{value}", self.schema_840)
                self.assertEqual(validator.validate_units(tag, allow_placeholders=False), [])

    def test_the_schema_row_is_compliant(self):
        codes = {issue["code"] for issue in self.schema_850.check_compliance()}
        self.assertEqual(codes - {SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED}, set())


if __name__ == "__main__":
    unittest.main()
