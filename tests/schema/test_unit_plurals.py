"""Unit plurals come from the specification's unit_plurals.json (specification 3.1.4.4 and A.8, issue #1517)."""

import unittest

from hed import HedString
from hed.schema import load_schema_version
from hed.schema.unit_plurals import load_unit_plurals, unit_name_forms


def codes(hed_string, schema):
    """Return the issue codes of validating hed_string against schema."""
    return [issue["code"] for issue in HedString(hed_string, schema).validate()]


class TestUnitPluralsFile(unittest.TestCase):
    def test_the_packaged_file_has_the_properties_of_a8_1(self):
        plurals = load_unit_plurals()
        self.assertEqual(list(plurals), sorted(plurals))
        self.assertEqual(len(set(plurals.values())), len(plurals))
        for key, value in plurals.items():
            with self.subTest(key=key):
                for text in (key, value):
                    self.assertTrue(text.isascii())
                    self.assertNotIn(" ", text)
                self.assertTrue(value == key or value not in plurals)

    def test_unit_name_forms(self):
        self.assertEqual(unit_name_forms("second"), {"second", "seconds"})
        self.assertEqual(unit_name_forms("hertz"), {"hertz"})
        self.assertEqual(unit_name_forms("degree-Celsius"), {"degree-Celsius", "degrees-Celsius"})
        # Not a key: no plural, and nothing is derived by a rule.
        self.assertEqual(unit_name_forms("degree Celsius"), {"degree Celsius"})
        self.assertEqual(unit_name_forms("uV"), {"uV"})
        # Keys are case-sensitive.
        self.assertEqual(unit_name_forms("Volt"), {"Volt", "Volts"})
        self.assertEqual(unit_name_forms("volt"), {"volt", "volts"})


class TestUnitPluralsInValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_850 = load_schema_version("8.5.0")
        cls.schema_820 = load_schema_version("8.2.0")
        cls.score_200 = load_schema_version("score_2.0.0")

    def test_the_rows_of_issue_1517(self):
        self.assertEqual(codes("Quantity/3 degrees-Celsius", self.schema_850), [])
        self.assertEqual(codes("Quantity/3 degree-Celsiuses", self.schema_850), ["UNITS_INVALID"])
        self.assertEqual(codes("Quantity/3 degrees Celsius", self.schema_850), ["UNITS_INVALID"])
        self.assertEqual(codes("RPP-absolute-amplitude/3 uVs", self.score_200), ["UNITS_INVALID"])
        self.assertEqual(codes("RPP-absolute-amplitude/3 uV", self.score_200), [])

    def test_a_name_that_is_its_own_plural(self):
        self.assertEqual(codes("Frequency/3 hertz", self.schema_850), [])
        self.assertEqual(codes("Frequency/3 kilohertz", self.schema_850), [])

    def test_a_modifier_goes_before_the_listed_plural(self):
        self.assertEqual(codes("Time-value/3 milliseconds", self.schema_850), [])
        self.assertEqual(codes("Quantity/3 millidegrees-Celsius", self.schema_850), [])

    def test_an_entry_applies_only_to_a_unit_name_of_the_schema_in_use(self):
        # 8.2.0 lists Volt, 8.5.0 lists volt; no tag of 8.2.0 takes electricPotentialUnits, so compare the forms.
        forms_820 = set()
        for unit in self.schema_820.unit_classes["electricPotentialUnits"].units.values():
            forms_820.update(unit.derivative_units)
        forms_850 = set()
        for unit in self.schema_850.unit_classes["electricPotentialUnits"].units.values():
            forms_850.update(unit.derivative_units)
        self.assertIn("Volts", forms_820)
        self.assertNotIn("volts", forms_820)
        self.assertIn("volts", forms_850)
        self.assertNotIn("Volts", forms_850)
        self.assertEqual(codes("Quantity/3 volts", self.schema_850), [])
        self.assertEqual(codes("Quantity/3 Volts", self.schema_850), ["UNITS_INVALID"])

    def test_a_unit_symbol_takes_no_plural(self):
        # second is a key of the file; its symbol s is not and takes no plural.
        self.assertEqual(codes("Time-value/3 ms", self.schema_850), [])
        self.assertEqual(codes("Time-value/3 mss", self.schema_850), ["UNITS_INVALID"])


if __name__ == "__main__":
    unittest.main()
