import unittest
import json

from hed.schema import HedKey, HedSectionKey
from hed.schema.schema_compare import compare_schemas, find_matching_tags, \
    _pretty_print_diff_all, _pretty_print_missing_all, compare_differences
from hed import load_schema_version

from . import util_create_schemas


class TestSchemaComparison(unittest.TestCase):
    def test_find_matching_tags(self):
        # create entries for schema1
        schema1 = util_create_schemas.load_schema1()
        schema2 = util_create_schemas.load_schema2()

        result = find_matching_tags(schema1, schema2)
        # Check if the result is correct
        self.assertEqual(len(result[HedSectionKey.Tags]), 3)
        self.assertIn("TestNode", result[HedSectionKey.Tags])
        self.assertIn("TestNode2", result[HedSectionKey.Tags])
        self.assertIn("TestNode3", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode4", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode5", result[HedSectionKey.Tags])

        # Test with include_summary=True
        match_string = find_matching_tags(schema1, schema2, output='string', include_summary=True)
        self.assertIsInstance(match_string, str)
        self.assertIn("Tags:", match_string)
        # print(match_string)

        json_style_dict = find_matching_tags(schema1, schema2, output='dict', include_summary=True)
        self.assertIsInstance(json_style_dict, dict)
        self.assertIn("summary", json_style_dict)

        result_string = json.dumps(json_style_dict, indent=4)
        self.assertIsInstance(result_string, str)

        # Optionally, you can also test the case without include_summary
        match_string_no_summary = find_matching_tags(schema1, schema2, output='string', include_summary=False)
        self.assertIsInstance(match_string_no_summary, str)
        self.assertNotIn("Tags:", match_string_no_summary)

        json_style_dict_no_summary = find_matching_tags(schema1, schema2, output='dict', include_summary=False)
        self.assertIsInstance(json_style_dict_no_summary, dict)
        self.assertNotIn("summary", json_style_dict_no_summary)

    def test_compare_schemas(self):
        schema1 = util_create_schemas.load_schema1()
        schema2 = util_create_schemas.load_schema2()

        matches, not_in_schema1, not_in_schema2, unequal_entries = compare_schemas(schema1, schema2)

        # Check if the result is correct
        self.assertEqual(len(matches[HedSectionKey.Tags]), 2)  # Three matches should be found
        self.assertIn("TestNode", matches[HedSectionKey.Tags])
        self.assertIn("TestNode2", matches[HedSectionKey.Tags])
        self.assertNotIn("TestNode3", matches[HedSectionKey.Tags])

        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 1)  # One tag not in schema2
        self.assertIn("TestNode4", not_in_schema2[HedSectionKey.Tags])  # "TestNode4" is not in schema2

        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 1)  # One tag not in schema1
        self.assertIn("TestNode5", not_in_schema1[HedSectionKey.Tags])  # "TestNode5" is not in schema1

        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 1)  # No unequal entries should be found
        self.assertIn("TestNode3", unequal_entries[HedSectionKey.Tags])

    def test_compare_differences(self):
        schema1 = util_create_schemas.load_schema1()
        schema2 = util_create_schemas.load_schema2()

        not_in_schema1, not_in_schema2, unequal_entries = compare_differences(schema1, schema2)

        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 1)  # One tag not in schema2
        self.assertIn("TestNode4", not_in_schema2[HedSectionKey.Tags])  # "TestNode4" is not in schema2

        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 1)  # One tag not in schema1
        self.assertIn("TestNode5", not_in_schema1[HedSectionKey.Tags])  # "TestNode5" is not in schema1

        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 1)  # No unequal entries should be found
        self.assertIn("TestNode3", unequal_entries[HedSectionKey.Tags])

        # Test with include_summary=True, string output
        diff_string_with_summary = compare_differences(schema1, schema2, output='string', include_summary=True)
        self.assertIsInstance(diff_string_with_summary, str)
        self.assertIn("Tags:", diff_string_with_summary)
        # print(diff_string_with_summary)

        # Test with include_summary=True, dict output
        diff_dict_with_summary = compare_differences(schema1, schema2, output='dict', include_summary=True)
        self.assertIsInstance(diff_dict_with_summary, dict)
        self.assertIn("summary", diff_dict_with_summary)

        # Optionally, test without include_summary, string output
        diff_string_no_summary = compare_differences(schema1, schema2, output='string', include_summary=False)
        self.assertIsInstance(diff_string_no_summary, str)
        self.assertNotIn("Tags:", diff_string_no_summary)

        # Optionally, test without include_summary, dict output
        diff_dict_no_summary = compare_differences(schema1, schema2, output='dict', include_summary=False)
        self.assertIsInstance(diff_dict_no_summary, dict)
        self.assertNotIn("summary", diff_dict_no_summary)

    def test_compare_score_lib_versions(self):
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        not_in_schema1, not_in_schema2, unequal_entries = compare_differences(schema1, schema2,
                                                                              attribute_filter=HedKey.InLibrary)
 
        
        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 21)
        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 10)
        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 61)

        diff_string = compare_differences(schema1, schema1, attribute_filter=HedKey.InLibrary, output='string',
                                          sections=None)
        self.assertFalse(diff_string)
        diff_string = compare_differences(schema1, schema2, attribute_filter=HedKey.InLibrary, output='string',
                                          sections=None)

        self.assertIsInstance(diff_string, str)

        json_style_dict = compare_differences(schema1, schema2, attribute_filter=HedKey.InLibrary, output='dict',
                                              sections=None)
        self.assertIsInstance(json_style_dict, dict)

        result_string = json.dumps(json_style_dict, indent=4)
        self.assertIsInstance(result_string, str)
