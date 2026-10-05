"""The char_set and code_point keys travel from the error call onto the issue dictionary."""

import unittest

from hed.errors.error_reporter import ISSUE_DETAIL_KEYS, ErrorHandler
from hed.errors.error_types import ValidationErrors


class TestIssueDetailKeys(unittest.TestCase):
    def test_string_level_error_carries_the_keys(self):
        issue = ErrorHandler.format_error(
            ValidationErrors.CHARACTER_INVALID,
            char_index=1,
            source_string="a[b",
            char_set="forbidden",
            code_point="U+005B",
            allows="no brackets",
        )[0]
        self.assertEqual(issue["char_set"], "forbidden")
        self.assertEqual(issue["code_point"], "U+005B")
        self.assertEqual(issue["message"], 'Invalid character "[" (U+005B) at index 1 of "a[b": no brackets')
        self.assertNotIn("allows", issue)

    def test_keys_are_absent_when_not_given(self):
        issue = ErrorHandler.format_error(ValidationErrors.CHARACTER_INVALID, char_index=1, source_string="a[b")[0]
        for key in ISSUE_DETAIL_KEYS:
            self.assertNotIn(key, issue)
        self.assertEqual(issue["message"], 'Invalid character "[" (U+005B) at index 1 of "a[b"')

    def test_tag_level_errors_carry_the_keys(self):
        issue = ErrorHandler.format_error(
            ValidationErrors.INVALID_TAG_CHARACTER,
            tag="Item/a*",
            index_in_tag=6,
            index_in_tag_end=7,
            char_index=6,
            char_set="name",
            code_point="U+002A",
            allows="a tag extension allows name",
        )[0]
        self.assertEqual(issue["code"], ValidationErrors.CHARACTER_INVALID)
        self.assertEqual((issue["char_set"], issue["code_point"]), ("name", "U+002A"))
        self.assertEqual(
            issue["message"], 'Invalid character "*" (U+002A) at index 6 of "Item/a*": a tag extension allows name'
        )
        issue = ErrorHandler.format_error(
            ValidationErrors.INVALID_VALUE_CLASS_CHARACTER,
            tag="Label/a?",
            problem_tag="?",
            value_class="nameClass",
            char_index=7,
            char_set="letters, digits",
            code_point="U+003F",
            allows="nameClass allows letters, digits",
        )[0]
        self.assertEqual((issue["char_set"], issue["code_point"]), ("letters, digits", "U+003F"))
        self.assertTrue(issue["message"].endswith(": nameClass allows letters, digits"))

    def test_value_invalid_names_the_rule(self):
        issue = ErrorHandler.format_error(
            ValidationErrors.INVALID_VALUE_CLASS_VALUE,
            tag="Duration/abc s",
            index_in_tag=0,
            index_in_tag_end=14,
            value_class="numericClass",
            rule="a number",
        )[0]
        self.assertEqual(issue["code"], ValidationErrors.VALUE_INVALID)
        self.assertTrue(issue["message"].endswith(": numericClass requires a number"))


if __name__ == "__main__":
    unittest.main()
