"""Whole-value rules of the value classes, as the character table defines them.

The dateTimeClass rule is the BIDS Datetime format (RFC 3339 with an optional offset), shared with
hed-specification's character_sets.json; the numericClass rule uses ASCII digits only.
"""

import unittest

from hed.validator.util.char_util import CharRexValidator


class TestValueClassWholeValueRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = CharRexValidator(modern_allowed_char_rules=True)

    def test_date_times_in_the_bids_format_are_valid(self):
        for value in [
            "2026-09-30T09:55:00",
            "2026-09-30T09:55:00.5",
            "2026-09-30T09:55:00.123456",
            "2026-09-30T09:55:00Z",
            "2026-09-30T09:55:00+02:00",
            "2026-09-30T09:55:00-05:30",
            "2026-09-30T23:59:60",
            "2000-01-01T00:00:00",
        ]:
            with self.subTest(value=value):
                self.assertTrue(self.validator.is_valid_value(value, "dateTimeClass"), value)

    def test_date_times_outside_the_bids_format_are_invalid(self):
        for value in [
            "2026-09-30",
            "2026-09-30 09:55:00",
            "2026-09-30t09:55:00z",
            "2026-09-30T09:55",
            "2026-09-30T09:55:00+0200",
            "2026-09-30T09:55:00+02",
            "2026-09-30T24:00:00",
            "2026-09-30T09:55:00.1234567",
            "2026-13-01T09:55:00",
            "2026-09-32T09:55:00",
            "2026-09-30T09:60:00",
            "2026-09-30T09:55:00+99:99",
            "20260930T095500",
            "2026-W40-3T09:55:00",
            "8/8/2019",
            "not a time",
        ]:
            with self.subTest(value=value):
                self.assertFalse(self.validator.is_valid_value(value, "dateTimeClass"), value)

    def test_numeric_values_use_ascii_digits(self):
        for value in ["3", "-3.5", ".5", "3.", "1e10", "-2.5E-3", "+7"]:
            with self.subTest(value=value):
                self.assertTrue(self.validator.is_valid_value(value, "numericClass"), value)
        for value in ["", "3 mA", "1e", "abc", "3^2", "+", "\u0663", "1\u0663"]:
            with self.subTest(value=value):
                self.assertFalse(self.validator.is_valid_value(value, "numericClass"), value)


if __name__ == "__main__":
    unittest.main()
