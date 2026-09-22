import math
import unittest

import pandas as pd

from hed.models import ColumnSource, ListColumnSource, TabularInput, distinct_values


class TestDistinctValues(unittest.TestCase):
    def test_maps_each_distinct_text_to_its_rows_in_first_occurrence_order(self):
        values = ["Red", "Blue", "Red", "Green", "Blue", "Red"]
        self.assertEqual(distinct_values(values), {"Red": [0, 2, 5], "Blue": [1, 4], "Green": [3]})

    def test_missing_values_are_dropped(self):
        values = [None, float("nan"), "", "n/a", "Red", math.nan, "n/a"]
        self.assertEqual(distinct_values(values), {"Red": [4]})

    def test_non_strings_become_text_and_bytes_are_decoded(self):
        values = [3, 3.5, b"Blue", 3]
        self.assertEqual(distinct_values(values), {"3": [0, 3], "3.5": [1], "Blue": [2]})

    def test_empty_column(self):
        self.assertEqual(distinct_values([]), {})


class TestListColumnSource(unittest.TestCase):
    def setUp(self):
        self.source = ListColumnSource({"onset": [1.0, 2.0], "HED": ["Red", "n/a"]})

    def test_is_a_column_source(self):
        self.assertIsInstance(self.source, ColumnSource)

    def test_column_names_in_order(self):
        self.assertEqual(self.source.column_names(), ["onset", "HED"])

    def test_distinct_values_of_a_column(self):
        self.assertEqual(self.source.distinct_values("HED"), {"Red": [0]})
        self.assertEqual(self.source.distinct_values("onset"), {"1.0": [0], "2.0": [1]})

    def test_unknown_column_is_empty(self):
        self.assertEqual(self.source.distinct_values("missing"), {})

    def test_no_mapper_and_no_base_input_by_default(self):
        self.assertIsNone(self.source.column_mapper())
        self.assertIsNone(self.source.as_base_input())


class TestBaseInputAsColumnSource(unittest.TestCase):
    def setUp(self):
        self.tabular = TabularInput(pd.DataFrame({"onset": [1.0, 2.0, 3.0], "HED": ["Red", "n/a", "Red"]}))

    def test_is_a_column_source(self):
        self.assertIsInstance(self.tabular, ColumnSource)

    def test_column_names_and_distinct_values(self):
        self.assertEqual(self.tabular.column_names(), ["onset", "HED"])
        self.assertEqual(self.tabular.distinct_values("HED"), {"Red": [0, 2]})
        self.assertEqual(self.tabular.distinct_values("missing"), {})

    def test_mapper_and_base_input_are_its_own(self):
        self.assertIs(self.tabular.column_mapper(), self.tabular._mapper)
        self.assertIs(self.tabular.as_base_input(), self.tabular)
        self.assertIsNone(self.tabular.get_sidecar())


if __name__ == "__main__":
    unittest.main()
