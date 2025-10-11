import unittest
import os

from hed.models import HedString
from hed.schema import load_schema
from hed.errors import ErrorHandler


class TestBaseTagBase(unittest.TestCase):
    schema_file = "../data/schema_tests/HED8.0.0t.xml"

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.schema_file)
        cls.hed_schema = load_schema(hed_xml)
        cls.error_handler = ErrorHandler()

    def tag_form_base(self, test_strings, expected_results, expected_errors):
        for test_key in test_strings:
            test_string_obj = HedString(test_strings[test_key], self.hed_schema)
            test_errors = test_string_obj._calculate_to_canonical_forms(hed_schema=self.hed_schema)
            expected_error = expected_errors[test_key]
            expected_result = expected_results[test_key]
            for tag in test_string_obj.tags():
                self.assertEqual(tag.base_tag, expected_result, test_strings[test_key])
                self.assertCountEqual(test_errors, expected_error, test_strings[test_key])

    def tag_form_org_base(self, test_strings, expected_results, expected_errors):
        for test_key in test_strings:
            test_string_obj = HedString(test_strings[test_key], self.hed_schema)
            test_errors = test_string_obj._calculate_to_canonical_forms(hed_schema=self.hed_schema)
            expected_error = expected_errors[test_key]
            expected_result = expected_results[test_key]
            for tag in test_string_obj.tags():
                self.assertEqual(tag.org_base_tag, expected_result, test_strings[test_key])
                self.assertCountEqual(test_errors, expected_error, test_strings[test_key])


class TestOrgBaseTag(TestBaseTagBase):
    def test_tag(self):
        test_strings = {
            "singleLevel": "Event",
            "twoLevel": "Sensory-event",
            "alreadyLong": "Item/Object/Geometric-object",
            "partialLong": "Object/Geometric-object",
            "fullShort": "Geometric-object",
        }
        expected_results = {
            "singleLevel": "Event",
            "twoLevel": "Sensory-event",
            "alreadyLong": "Item/Object/Geometric-object",
            "partialLong": "Object/Geometric-object",
            "fullShort": "Geometric-object",
        }
        expected_errors = {
            "singleLevel": [],
            "twoLevel": [],
            "alreadyLong": [],
            "partialLong": [],
            "fullShort": [],
        }
        self.tag_form_org_base(test_strings, expected_results, expected_errors)

    def test_tag_takes_value(self):
        test_strings = {
            "uniqueValue": "Label/Unique Value",
            "multiLevel": "Label/Long Unique Value With/Slash Marks",
            "partialPath": "Informational-property/Label/Unique Value",
        }
        expected_results = {
            "uniqueValue": "Label",
            "multiLevel": "Label",
            "partialPath": "Informational-property/Label",
        }
        expected_errors = {
            "uniqueValue": [],
            "multiLevel": [],
            "partialPath": [],
        }
        self.tag_form_org_base(test_strings, expected_results, expected_errors)

    def test_tag_extension_allowed(self):
        test_strings = {
            "singleLevel": "Experiment-control/extended lvl1",
            "multiLevel": "Experiment-control/extended lvl1/Extension2",
            "partialPath": "Vehicle/Boat/Yacht",
        }
        expected_results = {
            "singleLevel": "Experiment-control",
            "multiLevel": "Experiment-control",
            "partialPath": "Vehicle/Boat",
        }
        expected_errors = {
            "singleLevel": [],
            "multiLevel": [],
            "partialPath": [],
        }
        self.tag_form_org_base(test_strings, expected_results, expected_errors)


class TestBaseTag(TestBaseTagBase):
    def test_tag(self):
        test_strings = {
            "singleLevel": "Event",
            "twoLevel": "Sensory-event",
            "alreadyLong": "Item/Object/Geometric-object",
            "partialLong": "Object/Geometric-object",
            "fullShort": "Geometric-object",
        }
        expected_results = {
            "singleLevel": "Event",
            "twoLevel": "Event/Sensory-event",
            "alreadyLong": "Item/Object/Geometric-object",
            "partialLong": "Item/Object/Geometric-object",
            "fullShort": "Item/Object/Geometric-object",
        }
        expected_errors = {
            "singleLevel": [],
            "twoLevel": [],
            "alreadyLong": [],
            "partialLong": [],
            "fullShort": [],
        }
        self.tag_form_base(test_strings, expected_results, expected_errors)

    def test_tag_takes_value(self):
        test_strings = {
            "uniqueValue": "Label/Unique Value",
            "multiLevel": "Label/Long Unique Value With/Slash Marks",
            "partialPath": "Informational-property/Label/Unique Value",
        }
        expected_results = {
            "uniqueValue": "Property/Informational-property/Label",
            "multiLevel": "Property/Informational-property/Label",
            "partialPath": "Property/Informational-property/Label",
        }
        expected_errors = {
            "uniqueValue": [],
            "multiLevel": [],
            "partialPath": [],
        }
        self.tag_form_base(test_strings, expected_results, expected_errors)

    def test_tag_extension_allowed(self):
        test_strings = {
            "singleLevel": "Experiment-control/extended lvl1",
            "multiLevel": "Experiment-control/extended lvl1/Extension2",
            "partialPath": "Vehicle/Boat/Yacht",
        }
        expected_results = {
            "singleLevel": "Event/Experiment-control",
            "multiLevel": "Event/Experiment-control",
            "partialPath": "Item/Object/Man-made-object/Vehicle/Boat",
        }
        expected_errors = {
            "singleLevel": [],
            "multiLevel": [],
            "partialPath": [],
        }
        self.tag_form_base(test_strings, expected_results, expected_errors)


if __name__ == "__main__":
    unittest.main()
