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


# Run the tests
if __name__ == "__main__":
    unittest.main(argv=[""], exit=False)
