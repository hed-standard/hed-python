"""The packaged copy of the specification's character_sets.json and the CharacterSets view of it."""

import json
import os
import re
import unittest

from hed.validator.util.character_sets import CHARACTER_SETS_FILENAME, CharacterSets, code_point


class TestCharacterSetsFile(unittest.TestCase):
    """The file is loaded unchanged, every regex compiles, and the file's own examples hold in Python."""

    @classmethod
    def setUpClass(cls):
        cls.sets = CharacterSets.load()
        path = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "../../hed/validator/util", CHARACTER_SETS_FILENAME)
        )
        with open(path, encoding="utf-8") as f:
            cls.raw = json.load(f)

    def test_the_file_has_every_section_the_validators_read(self):
        for key in (
            "sets",
            "aliases",
            "literal_names",
            "declaration_wins_from",
            "value_class_defaults",
            "value_class_words",
            "hed_string",
        ):
            self.assertIn(key, self.raw)
        self.assertEqual(self.raw["declaration_wins_from"]["standard_version"], "8.5.0")
        self.assertEqual(self.sets.declaration_wins_from, "8.5.0")

    def test_every_set_regex_compiles_and_single_character_sets_match_their_code(self):
        for name, entry in self.sets.sets.items():
            with self.subTest(name=name):
                regex = re.compile(entry["regex"])
                match = re.fullmatch(r"ASCII code (\d+).*", entry["description"])
                if match:
                    char = chr(int(match.group(1)))
                    self.assertTrue(regex.fullmatch(char), f"{name} should match {char!r}")
                    self.assertFalse(regex.fullmatch("a") and char != "a", f"{name} should match only {char!r}")

    def test_the_examples_recorded_in_the_file_hold(self):
        for name, entry in self.sets.sets.items():
            for char in entry.get("tests", {}).get("valid", []):
                with self.subTest(name=name, valid=char):
                    self.assertEqual(self.sets.problem_characters(char, [name]), [])
            for char in entry.get("tests", {}).get("invalid", []):
                with self.subTest(name=name, invalid=char):
                    self.assertEqual(self.sets.problem_characters(char, [name]), [(0, char)])
        for class_name, entry in self.sets.value_class_words.items():
            rule = self.sets.word_rule(class_name)
            for value in entry["tests"]["valid"]:
                with self.subTest(class_name=class_name, valid=value):
                    self.assertTrue(rule.match(value))
            for value in entry["tests"]["invalid"]:
                with self.subTest(class_name=class_name, invalid=value):
                    self.assertFalse(rule.match(value))

    def test_aliases_and_literal_names(self):
        self.assertEqual(self.sets.canonical_name("slash"), "forward-slash")
        for name in ("slash", "forward-slash", "T", "+", "value-text"):
            self.assertTrue(self.sets.is_known_name(name), name)
        for name in ("bogus", "", "Tt"):
            self.assertFalse(self.sets.is_known_name(name), name)
        self.assertIn("slash", self.sets.known_names())
        self.assertEqual(self.sets.problem_characters("/T+.", ["slash", "T", "+"]), [(3, ".")])
        self.assertEqual(self.sets.problem_characters("t", ["T"]), [(0, "t")])
        with self.assertRaises(KeyError):
            self.sets.regex_for(["bogus"])

    def test_defaults_follow_the_from_version(self):
        self.assertEqual(self.sets.defaults_for("nameClass", "8.2.0"), ["letters", "digits", "hyphen", "underscore"])
        self.assertEqual(
            self.sets.defaults_for("nameClass", "8.3.0"), ["letters", "digits", "hyphen", "underscore", "nonascii"]
        )
        self.assertEqual(self.sets.defaults_for("textClass", "8.4.0"), ["text"])
        self.assertEqual(self.sets.defaults_for("textClass", "8.5.0"), ["value-text"])
        self.assertEqual(self.sets.defaults_for("textClass", None), ["value-text"])
        self.assertEqual(self.sets.defaults_for("textClass", "8.0.0")[:3], ["letters", "digits", "blank"])
        self.assertEqual(self.sets.defaults_for("idClass", "8.5.0"), [])

    def test_describe(self):
        self.assertEqual(
            self.sets.describe(["value-text"]),
            "value-text (text excluding left and right parentheses, number sign, and tilde)",
        )
        self.assertEqual(self.sets.describe(["letters", "digits", "T"]), "letters, digits, T")
        self.assertEqual(self.sets.describe(["T"]), "T")
        self.assertEqual(self.sets.describe(["+"]), '"+"')
        self.assertEqual(self.sets.describe(["letters", "+"]), 'letters, "+"')
        self.assertEqual(self.sets.word_rule_description("nameClass"), "")
        self.assertTrue(self.sets.word_rule_description("numericClass").startswith("an optionally signed decimal"))

    def test_hed_string_rules(self):
        self.assertEqual(self.sets.forbidden_characters, set('[]~"'))
        self.assertEqual(self.sets.forbidden_code_ranges, [(0, 31), (127, 159)])
        for character in '[]~"\x00\x1f\x7f\x85\x9f':
            self.assertTrue(self.sets.is_forbidden(character), code_point(character))
        # The ranges, not str.isprintable(), decide: U+00A0 and U+200B are not printable but are allowed.
        for character in " a\xa0\u200b\ufeff\u4f60":
            self.assertFalse(self.sets.is_forbidden(character), code_point(character))
        self.assertEqual(self.sets.column_braces, {"{", "}"})
        self.assertEqual(
            self.sets.describe_forbidden(),
            'no HED string may contain [ ] ~ " or a control character (codes 0-31, 127-159)',
        )
        self.assertEqual(self.sets.tag_chars, ["name"])

    def test_code_point(self):
        self.assertEqual(code_point("?"), "U+003F")
        self.assertEqual(code_point("\x85"), "U+0085")
        self.assertEqual(code_point("\U0001f600"), "U+1F600")


if __name__ == "__main__":
    unittest.main()
