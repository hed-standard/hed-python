"""Value characters follow the schema and the specification's character_sets.json.

The value-text set (from HED 8.5.0 a textClass value may not contain (, ), # or ~), the declaration-wins gate
(decisions D2 and D5, 2026-09-30), the value-text rule for a placeholder without a value class (D3), the
double-quote rule, and the messages that name the character, its code point, its index and the set.
"""

import os
import unittest

from hed import HedString, HedTag, load_schema, load_schema_version
from hed.errors.error_types import SchemaWarnings, ValidationErrors
from hed.schema.hed_schema_constants import character_types
from hed.validator import HedValidator

VALUE_TEXT_ALLOWS = "value-text (text excluding left and right parentheses, number sign, and tilde)"
NAME_SETS = "letters, digits, hyphen, underscore, nonascii"


class TestValueText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = os.path.join(os.path.dirname(__file__), "../data/schema_tests/value_text_8.5.0.mediawiki")
        cls.schema_850 = load_schema(os.path.realpath(fixture))
        cls.schema_840 = load_schema_version("8.4.0")
        cls.schema_820 = load_schema_version("8.2.0")

    def value_issues(self, schema, tag_text):
        return HedValidator(schema).validate_units(HedTag(tag_text, schema), allow_placeholders=False)

    def string_issues(self, schema, text):
        return HedValidator(schema).validate(HedString(text, schema), allow_placeholders=False)

    def test_value_text_is_text_without_the_structural_characters(self):
        text, value_text = character_types["text"], character_types["value-text"]
        self.assertEqual(text - value_text, set("()#~"))
        for char in ["'", '"', ";", "%", " ", "/", "nonascii"]:
            self.assertIn(char, value_text)
        for char in ",[]{}":
            self.assertNotIn(char, value_text)

    def test_structural_characters_are_rejected_by_the_value_class(self):
        """The rejection comes from the value-class character check, not from parsing the string."""
        for value in ["a)", "(a)", "trial #3", "a~b"]:
            with self.subTest(value=value):
                issues = self.value_issues(self.schema_850, f"Note/{value}")
                self.assertTrue(issues)
                self.assertEqual({issue["code"] for issue in issues}, {ValidationErrors.CHARACTER_INVALID})
                self.assertEqual({issue["char_set"] for issue in issues}, {"value-text"})
        for value in ["It's 50% done; ok?", "Un café", "A plain note."]:
            with self.subTest(value=value):
                self.assertEqual(self.value_issues(self.schema_850, f"Note/{value}"), [])

    def test_earlier_schemas_still_allow_them_in_the_value_class(self):
        """8.4.0 keeps textClass on text: the value-class check passes, and only the string parse objects."""
        for value in ["a)", "(a)", "trial #3", "a~b"]:
            with self.subTest(value=value):
                self.assertEqual(self.value_issues(self.schema_840, f"Description/{value}"), [])

    def test_the_message_names_the_character_code_point_index_and_set(self):
        issues = self.value_issues(self.schema_850, "Note/a)")
        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0]["message"],
            f'Invalid character ")" (U+0029) at index 6 of "Note/a)": textClass allows {VALUE_TEXT_ALLOWS}',
        )
        self.assertEqual(issues[0]["char_set"], "value-text")
        self.assertEqual(issues[0]["code_point"], "U+0029")

        issues = self.value_issues(self.schema_840, "Label/reaching?")
        self.assertEqual(
            issues[0]["message"],
            f'Invalid character "?" (U+003F) at index 14 of "Label/reaching?": nameClass allows {NAME_SETS}',
        )
        self.assertEqual(issues[0]["char_set"], NAME_SETS)

    def test_value_invalid_names_the_whole_value_rule(self):
        issues = self.value_issues(self.schema_840, "Duration/abc s")
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.VALUE_INVALID])
        self.assertEqual(
            issues[0]["message"],
            "'Duration/abc s' has an invalid value portion for value class 'numericClass': numericClass requires "
            "an optionally signed decimal number, with optional scientific-notation exponent",
        )

    def test_the_schema_row_is_compliant(self):
        codes = {issue["code"] for issue in self.schema_850.check_compliance()}
        self.assertEqual(codes - {SchemaWarnings.SCHEMA_PRERELEASE_VERSION_USED}, set())


class TestDeclarationWinsGate(unittest.TestCase):
    """D2 and D5: from 8.5.0 the schema's allowedCharacter declaration defines the class; before, the defaults."""

    @classmethod
    def setUpClass(cls):
        fixture = os.path.join(os.path.dirname(__file__), "../data/schema_tests/value_text_8.5.0.mediawiki")
        cls.schema_850 = load_schema(os.path.realpath(fixture))
        cls.schema_840 = load_schema_version("8.4.0")
        cls.schema_820 = load_schema_version("8.2.0")

    def value_issues(self, schema, tag_text):
        return HedValidator(schema).validate_units(HedTag(tag_text, schema), allow_placeholders=False)

    def test_released_schemas_keep_accepting_non_ascii_names(self):
        """8.3.0 and 8.4.0 declare nameClass without nonascii; the specification's defaults win there."""
        self.assertEqual(self.value_issues(self.schema_840, "Label/café"), [])
        self.assertEqual(self.value_issues(self.schema_840, "Creation-date/2026-09-30T09:55:00.5Z"), [])

    def test_the_declaration_wins_on_8_5_0(self):
        """The fixture's dateTimeClass row lacks period, so a fractional second fails on this 8.5.0 schema."""
        issues = self.value_issues(self.schema_850, "Time-stamp/2026-09-30T09:55:00.5")
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.CHARACTER_INVALID])
        self.assertEqual(issues[0]["char_set"], "digits, T, hyphen, colon")
        self.assertEqual(issues[0]["code_point"], "U+002E")
        self.assertTrue(issues[0]["message"].endswith(": dateTimeClass allows digits, T, hyphen, colon"))
        self.assertEqual(self.value_issues(self.schema_850, "Time-stamp/2026-09-30T09:55:00"), [])
        # The row of the 8.5.0 prerelease carries nonascii, so names keep their accents.
        self.assertEqual(self.value_issues(self.schema_850, "Tag-name/café"), [])

    def test_a_class_the_schema_defines_follows_its_declaration_on_every_version(self):
        self.assertEqual(self.value_issues(self.schema_850, "Tag-id/a.1"), [])
        issues = self.value_issues(self.schema_850, "Tag-id/a-1")
        self.assertEqual(issues[0]["char_set"], "letters, digits, period")
        self.assertTrue(issues[0]["message"].endswith(": idClass allows letters, digits, period"))

    def test_pre_8_3_0_text_values_keep_the_text_set(self):
        """8.0.0 to 8.2.0 enumerate the textClass characters without underscore or apostrophe; hedtools has
        always applied the 8.3.0 text set there and still does (char_util.LEGACY_TEXT_DEFAULTS), so
        ID/left_hand.png in an 8.2.0 dataset keeps its verdict."""
        for value in ["left_hand.png", "Don't", "a=b <c> & d!"]:
            with self.subTest(value=value):
                self.assertEqual(self.value_issues(self.schema_820, f"Description/{value}"), [])
        issues = self.value_issues(self.schema_820, "Description/a[b")
        self.assertEqual(issues[0]["char_set"], "text")


class TestValueWithoutValueClass(unittest.TestCase):
    """D3: a placeholder that declares no valueClass takes value-text."""

    @classmethod
    def setUpClass(cls):
        cls.schema_840 = load_schema_version("8.4.0")

    def value_issues(self, tag_text):
        return HedValidator(self.schema_840).validate_units(HedTag(tag_text, self.schema_840), allow_placeholders=False)

    def test_identifier_characters_are_accepted(self):
        for tag_text in [
            "DOI/10.1000/abc?x=1",
            "UUID/123e4567-e89b",
            "Keyboard-key/a=b",
            "URL/x.org/a;b",
            "Pathname/data/sub-01",
        ]:
            with self.subTest(tag=tag_text):
                self.assertEqual(self.value_issues(tag_text), [])

    def test_structural_characters_are_rejected(self):
        issues = self.value_issues("DOI/10.1000/(abc)")
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.CHARACTER_INVALID] * 2)
        self.assertEqual([issue["code_point"] for issue in issues], ["U+0028", "U+0029"])
        self.assertEqual({issue["char_set"] for issue in issues}, {"value-text"})
        self.assertEqual(
            issues[0]["message"],
            'Invalid character "(" (U+0028) at index 12 of "DOI/10.1000/(abc)": a value with no value class allows '
            + VALUE_TEXT_ALLOWS,
        )
        for tag_text in ["UUID/a#b", "UUID/a~b", "Keyboard-key/a,b"]:
            with self.subTest(tag=tag_text):
                codes = {issue["code"] for issue in self.value_issues(tag_text)}
                self.assertEqual(codes, {ValidationErrors.CHARACTER_INVALID})

    def test_a_full_validation_agrees(self):
        validator = HedValidator(self.schema_840)
        self.assertEqual(validator.validate(HedString("Keyboard-key/a=b, Red", self.schema_840), False), [])
        issues = validator.validate(HedString("UUID/a#b", self.schema_840), allow_placeholders=False)
        self.assertIn(ValidationErrors.CHARACTER_INVALID, {issue["code"] for issue in issues})


class TestDoubleQuote(unittest.TestCase):
    """Appendix B CHARACTER_INVALID a: a double quote is invalid anywhere in a HED string."""

    def test_double_quote_in_a_text_value(self):
        schema = load_schema_version("8.4.0")
        issues = HedValidator(schema).validate(HedString('Description/He said "hi"', schema), allow_placeholders=False)
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.CHARACTER_INVALID] * 2)
        self.assertEqual([issue["code_point"] for issue in issues], ["U+0022", "U+0022"])
        self.assertEqual({issue["char_set"] for issue in issues}, {"forbidden"})


if __name__ == "__main__":
    unittest.main()
