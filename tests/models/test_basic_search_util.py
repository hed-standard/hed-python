import unittest
from hed import load_schema_version
from hed.models.basic_search_util import convert_query


class TestConvertQueryToForm(unittest.TestCase):
    schema = load_schema_version("8.3.0")

    def test_basic_convert(self):
        input = "@Event, Head-part*, Time-interval/1"
        expected_output = "@Event, Item/Biological-item/Anatomical-item/Body-part/Head-part*, Property/Data-property/Data-value/Spatiotemporal-value/Temporal-value/Time-interval/1"

        actual_output = convert_query(input, self.schema)
        self.assertEqual(expected_output, actual_output)

        input = "@Head-part*, Event, Time-interval/1"
        expected_output = "@Item/Biological-item/Anatomical-item/Body-part/Head-part*, Event, Property/Data-property/Data-value/Spatiotemporal-value/Temporal-value/Time-interval/1"

        actual_output = convert_query(input, self.schema)
        self.assertEqual(expected_output, actual_output)