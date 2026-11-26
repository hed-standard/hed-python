"""ELEMENT_DEPRECATED for a deprecated unit or unit modifier (specification Appendix B ELEMENT_DEPRECATED b, #1506).

testaux 1.1.0 from hed-tests deprecates the unit bigauxunit and the unit modifier auxMod; auxunit and the SI unit
auxsiunit are not deprecated.
"""

import unittest

from hed.models import DefinitionDict, HedString
from hed.validator import HedValidator
from tests.schema.util_test_schemas import load_test_schema


class TestDeprecatedUnits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_test_schema("testaux_1.1.0")

    def codes(self, text, definitions=None, allow_placeholders=False):
        validator = HedValidator(self.schema, def_dicts=definitions, definitions_allowed=True)
        issues = validator.validate(HedString(text, self.schema), allow_placeholders=allow_placeholders)
        return [issue["code"] for issue in issues]

    def test_a_deprecated_unit_or_modifier_is_reported(self):
        for text in ("Aux-measure/3 bigauxunit", "Aux-measure/3 auxModauxsiunit"):
            with self.subTest(text=text):
                self.assertEqual(self.codes(text), ["ELEMENT_DEPRECATED"])

    def test_units_that_are_not_deprecated_pass(self):
        for text in ("Aux-measure/3 auxunit", "Aux-measure/3 auxsiunit"):
            with self.subTest(text=text):
                self.assertEqual(self.codes(text), [])

    def test_the_message_names_the_deprecated_element(self):
        issues = HedValidator(self.schema).validate(HedString("Aux-measure/3 auxModauxsiunit", self.schema), False)
        self.assertIn("'auxMod'", issues[0]["message"])

    def test_a_definition_reports_its_unit_once(self):
        for text in (
            "(Definition/Big/#, (Aux-measure/# bigauxunit))",
            "(Definition/Fixed, (Aux-measure/3 bigauxunit))",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.codes(text, allow_placeholders=True), ["ELEMENT_DEPRECATED"])
                self.assertEqual(
                    [issue["code"] for issue in DefinitionDict(text, self.schema).issues], ["ELEMENT_DEPRECATED"]
                )

    def test_a_def_reports_only_a_unit_written_in_its_value(self):
        written_in_definition = DefinitionDict("(Definition/Big/#, (Aux-measure/# bigauxunit))", self.schema)
        self.assertEqual(self.codes("Def/Big/3", written_in_definition), [])
        open_definition = DefinitionDict("(Definition/Open/#, (Aux-measure/#))", self.schema)
        self.assertEqual(self.codes("Def/Open/3 bigauxunit", open_definition), ["ELEMENT_DEPRECATED"])
        expanded = "(Def-expand/Open/3 bigauxunit, (Aux-measure/3 bigauxunit))"
        self.assertEqual(self.codes(expanded, open_definition), ["ELEMENT_DEPRECATED"])


if __name__ == "__main__":
    unittest.main()
