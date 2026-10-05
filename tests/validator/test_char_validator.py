"""CharValidator and CharRexValidator: the string, tag and value-class character checks."""

import os
import unittest

from hed import load_schema, load_schema_version
from hed.errors.error_types import ValidationErrors
from hed.validator.util.char_util import CharRexValidator, CharValidator


class TestGetProblemChars(unittest.TestCase):
    """Without a schema the validator trusts the declaration it is given and uses the newest defaults."""

    @classmethod
    def setUpClass(cls):
        cls.char_rex_val = CharRexValidator()

    def test_nameClass_valid_string(self):
        self.assertEqual(self.char_rex_val.get_problem_chars("HelloWorld", "nameClass"), [])

    def test_nameClass_with_invalid_characters(self):
        self.assertEqual(self.char_rex_val.get_problem_chars("Hello World123#", "nameClass"), [(5, " "), (14, "#")])

    def test_nameClass_with_special_characters(self):
        self.assertEqual(self.char_rex_val.get_problem_chars("Invalid@String!", "nameClass"), [(7, "@"), (14, "!")])

    def test_nameClass_nonascii_characters(self):
        # The newest nameClass defaults include nonascii; $ and ! are still out.
        self.assertEqual(self.char_rex_val.get_problem_chars("Hello$你好!", "nameClass"), [(5, "$"), (8, "!")])

    def test_empty_string(self):
        self.assertEqual(self.char_rex_val.get_problem_chars("", "nameClass"), [])

    def test_a_declared_class_the_file_has_no_defaults_for(self):
        """A value class of the schema's own follows its declaration, here newline, tab and nonascii only."""
        declared = ["newline", "tab", "nonascii"]
        self.assertEqual(
            self.char_rex_val.get_problem_chars("Hello\nWor\t你好", "testClass", declared_names=declared),
            [(0, "H"), (1, "e"), (2, "l"), (3, "l"), (4, "o"), (6, "W"), (7, "o"), (8, "r")],
        )
        self.assertEqual(
            self.char_rex_val.get_problem_chars("Hello123", "testClass", declared_names=declared),
            [(0, "H"), (1, "e"), (2, "l"), (3, "l"), (4, "o"), (5, "1"), (6, "2"), (7, "3")],
        )

    def test_declaration_is_used_when_no_schema_fixes_the_version(self):
        self.assertEqual(self.char_rex_val.get_problem_chars("a)#~", "textClass", declared_names=["text"]), [])
        self.assertEqual(
            self.char_rex_val.get_problem_chars("a)#~", "textClass", declared_names=["value-text"]),
            [(1, ")"), (2, "#"), (3, "~")],
        )

    def test_literal_and_alias_names_in_a_declaration(self):
        declared = ["digits", "T", "slash"]
        self.assertEqual(
            self.char_rex_val.get_problem_chars("12T/3t", "posixPath", declared_names=declared), [(5, "t")]
        )

    def test_unknown_declared_name_falls_back_to_the_defaults(self):
        """An unknown name is a schema compliance error; validation uses the file's defaults for the class."""
        self.assertEqual(
            self.char_rex_val.get_problem_chars("a)#~", "textClass", declared_names=["bogus-set"]),
            [(1, ")"), (2, "#"), (3, "~")],
        )
        # A class with neither usable declaration nor defaults constrains nothing.
        self.assertEqual(self.char_rex_val.get_problem_chars("a)#~", "ownClass", declared_names=["bogus-set"]), [])

    def test_is_valid_value(self):
        self.assertTrue(self.char_rex_val.is_valid_value("1e10", "numericClass"))
        self.assertFalse(self.char_rex_val.is_valid_value("abc", "numericClass"))
        self.assertTrue(self.char_rex_val.is_valid_value("2026-09-30T09:55:00.5Z", "dateTimeClass"))
        self.assertFalse(self.char_rex_val.is_valid_value("2026-09-30", "dateTimeClass"))
        self.assertIs(self.char_rex_val.is_valid_value("anything", "nameClass"), True)


class TestAllowedNamesGate(unittest.TestCase):
    """Decisions D2 and D5 (2026-09-30): the declaration wins from standard schema 8.5.0, the defaults before."""

    @classmethod
    def setUpClass(cls):
        fixture = os.path.join(os.path.dirname(__file__), "../data/schema_tests/value_text_8.5.0.mediawiki")
        cls.schema_850 = load_schema(os.path.realpath(fixture))
        cls.schema_840 = load_schema_version("8.4.0")
        cls.schema_820 = load_schema_version("8.2.0")

    def test_defaults_win_before_8_5_0(self):
        validator = CharRexValidator(hed_schema=self.schema_840)
        declared = ["letters", "digits", "underscore", "hyphen"]  # what 8.3.0 and 8.4.0 say, without nonascii
        self.assertEqual(
            validator.allowed_names("nameClass", declared), ["letters", "digits", "hyphen", "underscore", "nonascii"]
        )
        self.assertEqual(
            validator.allowed_names("dateTimeClass", ["digits", "T", "hyphen", "colon"]),
            ["digits", "T", "hyphen", "colon", "period", "plus", "Z"],
        )
        self.assertEqual(validator.allowed_names("textClass", ["text"]), ["text"])

    def test_defaults_follow_the_standard_version(self):
        validator = CharRexValidator(hed_schema=self.schema_820)
        self.assertEqual(
            validator.allowed_names("nameClass", ["letters", "digits", "_", "-"]),
            ["letters", "digits", "hyphen", "underscore"],
        )
        # textClass before 8.3.0 keeps the text set, not the enumeration the file records (LEGACY_TEXT_DEFAULTS).
        self.assertEqual(validator.allowed_names("textClass", ["letters", "digits", "blank", "+"]), ["text"])

    def test_declaration_wins_from_8_5_0(self):
        validator = CharRexValidator(hed_schema=self.schema_850)
        declared = ["digits", "T", "hyphen", "colon"]
        self.assertEqual(validator.allowed_names("dateTimeClass", declared), declared)
        self.assertEqual(validator.allowed_names("textClass", ["value-text"]), ["value-text"])

    def test_a_schema_defined_class_always_follows_its_declaration(self):
        for schema in (self.schema_820, self.schema_840, self.schema_850):
            validator = CharRexValidator(hed_schema=schema)
            self.assertEqual(
                validator.allowed_names("idClass", ["letters", "digits", "period"]), ["letters", "digits", "period"]
            )

    def test_no_declaration_means_the_defaults(self):
        validator = CharRexValidator(hed_schema=self.schema_850)
        self.assertEqual(validator.allowed_names("textClass", None), ["value-text"])
        self.assertEqual(validator.allowed_names("idClass", None), [])


class TestStringLevelCharacters(unittest.TestCase):
    """check_invalid_character_issues: Appendix B CHARACTER_INVALID a and b."""

    def issues(self, text, allow_placeholders=False, modern=True):
        return CharValidator(modern_allowed_char_rules=modern).check_invalid_character_issues(text, allow_placeholders)

    def test_double_quote_and_brackets_are_forbidden(self):
        issues = self.issues('Label/a"b, Item/[c]')
        self.assertEqual([issue["code"] for issue in issues], [ValidationErrors.CHARACTER_INVALID] * 3)
        self.assertEqual([issue["code_point"] for issue in issues], ["U+0022", "U+005B", "U+005D"])
        self.assertEqual({issue["char_set"] for issue in issues}, {"forbidden"})
        self.assertIn('Invalid character """ (U+0022) at index 7 of', issues[0]["message"])
        self.assertIn('no HED string may contain [ ] ~ " or a control character', issues[0]["message"])

    def test_a_tilde_keeps_its_advice_and_gains_the_keys(self):
        issues = self.issues("a ~ b")
        self.assertEqual(issues[0]["code"], ValidationErrors.CHARACTER_INVALID)
        self.assertIn("Tildes not supported", issues[0]["message"])
        self.assertEqual((issues[0]["char_set"], issues[0]["code_point"]), ("forbidden", "U+007E"))

    def test_control_characters_are_forbidden(self):
        issues = self.issues("Item/Bl\x08, Item/a\x85")
        self.assertEqual([issue["code_point"] for issue in issues], ["U+0008", "U+0085"])
        self.assertEqual({issue["char_set"] for issue in issues}, {"forbidden"})

    def test_control_characters_are_forbidden_before_8_3_0_too(self):
        # CHARACTER_INVALID a applies to every HED string; before 8.3.0 the C1 range is also non-ASCII, but
        # the forbidden verdict comes first.
        issues = self.issues("Item/Bl\x08, Item/a\x85", modern=False)
        self.assertEqual([issue["code_point"] for issue in issues], ["U+0008", "U+0085"])
        self.assertEqual({issue["char_set"] for issue in issues}, {"forbidden"})

    def test_non_printable_characters_outside_the_control_ranges_are_allowed(self):
        # The file's nonascii set accepts U+00A0 (no-break space), which str.isprintable() rejects; the
        # string-level check follows the file's code ranges, not isprintable().
        self.assertEqual(self.issues("Label/a\xa0b, Label/c\u200bd"), [])

    def test_curly_braces_only_where_placeholders_are_allowed(self):
        self.assertEqual(self.issues("{col}, Red", allow_placeholders=True), [])
        issues = self.issues("{col}, Red", allow_placeholders=False)
        self.assertEqual([issue["code_point"] for issue in issues], ["U+007B", "U+007D"])
        self.assertEqual({issue["char_set"] for issue in issues}, {"structural"})
        self.assertIn("curly braces may appear only in a sidecar column reference", issues[0]["message"])

    def test_schemas_before_8_3_0_allow_only_ascii(self):
        self.assertEqual(self.issues("Label/café", modern=True), [])
        issues = self.issues("Label/café", modern=False)
        self.assertEqual((issues[0]["char_set"], issues[0]["code_point"]), ("ascii", "U+00E9"))
        self.assertIn("schemas before 8.3.0 allow only ASCII characters", issues[0]["message"])


if __name__ == "__main__":
    unittest.main()
