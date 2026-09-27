import re
import unittest

from hed.validator.util.char_util import CharRexValidator


class TestGetProblemIndices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.char_rex_val = CharRexValidator()

    def test_nameClass_valid_string(self):
        # Only uppercase and lowercase letters allowed for nameClass
        self.assertEqual(self.char_rex_val.get_problem_chars("HelloWorld", "nameClass"), [])

    def test_nameClass_with_invalid_characters(self):
        # Invalid characters in "nameClass": space
        self.assertEqual(self.char_rex_val.get_problem_chars("Hello World123#", "nameClass"), [(5, " "), (14, "#")])

    def test_nameClass_with_special_characters(self):
        # Invalid special characters in "nameClass"
        self.assertEqual(self.char_rex_val.get_problem_chars("Invalid@String!", "nameClass"), [(7, "@"), (14, "!")])

    def test_testClass_with_newline_and_tab(self):
        # "testClass" allows newline, tab, and non-ASCII characters but not ascii
        self.assertEqual(
            self.char_rex_val.get_problem_chars("Hello\nWor\t你好", "testClass"),
            [(0, "H"), (1, "e"), (2, "l"), (3, "l"), (4, "o"), (6, "W"), (7, "o"), (8, "r")],
        )

    def test_testClass_with_invalid_characters(self):
        # Invalid characters in "testClass": ASCII letters and digits not allowed
        self.assertEqual(
            self.char_rex_val.get_problem_chars("Hello123", "testClass"),
            [(0, "H"), (1, "e"), (2, "l"), (3, "l"), (4, "o"), (5, "1"), (6, "2"), (7, "3")],
        )

    def test_empty_string(self):
        # Empty string should always return an empty list
        self.assertEqual(self.char_rex_val.get_problem_chars("", "nameClass"), [])

    def test_nameClass_nonascii_characters(self):
        # Non-ASCII characters are allowed in "nameClass" but $ an ! are not
        self.assertEqual(self.char_rex_val.get_problem_chars("Hello$你好!", "nameClass"), [(5, "$"), (8, "!")])

    def test_schema_declaration_is_used_when_it_names_complete_sets(self):
        """A declaration of complete sets replaces the table; an enumerated one does not."""
        self.assertEqual(self.char_rex_val.get_problem_chars("a)#~", "textClass", declared_names=["text"]), [])
        self.assertEqual(
            self.char_rex_val.get_problem_chars("a)#~", "textClass", declared_names=["value-text"]),
            [(1, ")"), (2, "#"), (3, "~")],
        )
        # nameClass is declared without nonascii in every released schema; the table (with nonascii) still applies.
        self.assertEqual(
            self.char_rex_val.get_problem_chars(
                "a你", "nameClass", declared_names=["letters", "digits", "underscore", "hyphen"]
            ),
            [],
        )


class TestCharacterRegexTable(unittest.TestCase):
    """Every entry of class_regex.json must be a regular expression that matches its own character."""

    def test_every_entry_compiles_and_the_single_characters_match_themselves(self):
        table = CharRexValidator()._rex_dict["char_regex"]
        for name, regex in table.items():
            with self.subTest(name=name):
                re.compile(regex)
        expected = {
            "left-paren": "(",
            "right-paren": ")",
            "backslash": "\\",
            "vertical-bar": "|",
            "number-sign": "#",
            "tilde": "~",
            "asterisk": "*",
            "plus": "+",
            "period": ".",
            "question-mark": "?",
            "caret": "^",
            "dollar": "$",
        }
        for name, char in expected.items():
            with self.subTest(name=name):
                self.assertTrue(re.fullmatch(table[name], char))


# Run the tests
if __name__ == "__main__":
    unittest.main(argv=[""], exit=False)
