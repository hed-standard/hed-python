"""ELEMENT_DEPRECATED for a deprecated unit or unit modifier (specification Appendix B ELEMENT_DEPRECATED b, #1506).

testaux 1.1.0 from hed-tests deprecates the unit bigauxunit and the unit modifier auxMod; auxunit and the SI unit
auxsiunit are not deprecated.
"""

import io
import json
import unittest

from hed.models import DefinitionDict, HedString, Sidecar, TabularInput
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

    def table_warnings(self, template, cells, definitions=None):
        """Count ELEMENT_DEPRECATED for a value column with this template and these cells."""
        sidecar = Sidecar(io.StringIO(json.dumps({"val": {"HED": template}})))
        lines = ["onset\tduration\tval"] + [f"{row}\t0\t{cell}" for row, cell in enumerate(cells, 1)]
        table = TabularInput(io.StringIO("\n".join(lines) + "\n"), sidecar=sidecar)
        issues = table.validate(self.schema, extra_def_dicts=definitions)
        return sum(issue["code"] == "ELEMENT_DEPRECATED" for issue in issues)

    def test_a_value_column_reports_a_template_unit_once(self):
        # Written in the template: reported with the template, not for each value.
        self.assertEqual(self.table_warnings("Aux-measure/# bigauxunit", ["3", "4", "5"]), 1)

    def test_a_value_column_does_not_report_a_definition_unit(self):
        big = DefinitionDict("(Definition/Big/#, (Aux-measure/# bigauxunit))", self.schema)
        self.assertEqual(self.table_warnings("Def/Big/#", ["3", "4", "5"], definitions=big), 0)

    def test_a_value_column_reports_each_distinct_value_with_a_deprecated_unit(self):
        cells = ["3 bigauxunit", "4 bigauxunit", "5 auxModauxsiunit", "6 auxunit"]
        self.assertEqual(self.table_warnings("Aux-measure/#", cells), 3)


if __name__ == "__main__":
    unittest.main()
