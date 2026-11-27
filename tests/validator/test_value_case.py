"""Tag expressions compare values with case (specification 3.2.3, #1507) and identical definitions (#1520).

Node names, a tag extension and a definition name compare without regard to case; the value that replaces ``#``
compares exactly as written. Identical definitions of one name are one definition; definitions that differ in the
case of a value are different (specification 3.2.8.1, DEFINITION_INVALID i).
"""

import io
import json
import unittest

from hed import DefinitionDict, HedString, Sidecar, load_schema_version
from hed.validator import HedValidator


class TestRepeatedValueCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.4.0")
        cls.definitions = DefinitionDict("(Definition/MyDef/#, (Label/#))", cls.schema)

    def codes(self, text):
        issues = HedValidator(self.schema, def_dicts=self.definitions).validate(HedString(text, self.schema), False)
        return [issue["code"] for issue in issues if issue["code"] == "TAG_EXPRESSION_REPEATED"]

    def test_values_that_differ_in_case_are_not_repeated(self):
        for text in (
            "Label/abc, Label/ABC",
            "ID/a1, ID/A1",
            "(Label/abc, Red), (Label/Abc, Red)",
            "Def/MyDef/abc, Def/MyDef/ABC",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.codes(text), [])

    def test_names_and_extensions_that_differ_in_case_are_repeated(self):
        for text in ("Label/abc, label/abc", "Red/Blech, Red/blech", "Def/MyDef/abc, Def/mydef/abc"):
            with self.subTest(text=text):
                self.assertEqual(self.codes(text), ["TAG_EXPRESSION_REPEATED"])


class TestIdenticalDefinitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_schema_version("8.4.0")

    def sidecar_codes(self, entries):
        sidecar = Sidecar(io.StringIO(json.dumps({"defs": {"HED": entries}})))
        return [issue["code"] for issue in sidecar.validate(self.schema)]

    def test_identical_definitions_in_one_string_are_one_definition(self):
        for text in (
            "(Definition/X, (Red)), (Definition/X, (Red))",
            "(Definition/Z), (Definition/Z)",
            "(Definition/X, (Red, Blue)), (Definition/x, (blue, red))",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.sidecar_codes({"a": text}), [])

    def test_definitions_of_one_name_that_differ_in_one_string_are_invalid(self):
        self.assertEqual(
            self.sidecar_codes({"a": "(Definition/X, (Red)), (Definition/X, (Blue))"}), ["DEFINITION_INVALID"]
        )

    def test_definitions_that_differ_in_the_case_of_a_value_are_different(self):
        entries = {"a": "(Definition/X, (Label/abc))", "b": "(Definition/X, (Label/ABC))"}
        self.assertEqual(self.sidecar_codes(entries), ["DEFINITION_INVALID"])
        definitions = DefinitionDict("(Definition/X, (Label/abc))", self.schema)
        definitions.add_definitions("(Definition/X, (Label/ABC))", self.schema)
        self.assertEqual([issue["code"] for issue in definitions.issues], ["DEFINITION_INVALID"])

    def test_contents_in_another_order_are_identical(self):
        entries = {"a": "(Definition/X, (Red, (Blue, Label/abc)))", "b": "(Definition/X, ((Label/abc, Blue), Red))"}
        self.assertEqual(self.sidecar_codes(entries), [])

    def test_repeated_def_tags_are_still_repeated(self):
        definitions = DefinitionDict("(Definition/X, (Red))", self.schema)
        issues = HedValidator(self.schema, def_dicts=definitions).validate(
            HedString("Def/X, Def/X", self.schema), False
        )
        self.assertEqual([issue["code"] for issue in issues], ["TAG_EXPRESSION_REPEATED"])


if __name__ == "__main__":
    unittest.main()
