import unittest
import copy


from hed.schema import HedKey, HedSectionKey
from hed.schema.schema_compare import compare_schemas
from hed.schema.schema_compare import (gather_schema_changes, find_matching_tags, pretty_print_change_dict,
                                       compare_differences)
from hed import load_schema_version, load_schema

from tests.schema import util_create_schemas
import os


class TestSchemaComparison(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/schema_tests/')

    def test_find_matching_tags(self):
        # create entries for schema1
        schema1 = util_create_schemas.load_schema1()
        schema2 = util_create_schemas.load_schema2()

        result = find_matching_tags(schema1, schema2, return_string=False)
        # Check if the result is correct
        self.assertEqual(len(result[HedSectionKey.Tags]), 3)
        self.assertIn("TestNode", result[HedSectionKey.Tags])
        self.assertIn("TestNode2", result[HedSectionKey.Tags])
        self.assertIn("TestNode3", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode4", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode5", result[HedSectionKey.Tags])

        match_string = find_matching_tags(schema1, schema2)
        self.assertIsInstance(match_string, str)
        self.assertIn("Tags:", match_string)

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

    def test_compare_and_summarize_schemas_test(self):
        schema1 = load_schema(os.path.join(self.base_data, "schema_compare.mediawiki"), name="Schema1")
        self.assertEqual(schema1.source_format, ".mediawiki")
        schema2 = load_schema(os.path.join(self.base_data, "schema_compare2.mediawiki"), name="Schema2")
        self.assertEqual(schema2.source_format, ".mediawiki")

        result = gather_schema_changes(schema1, schema2)
        self.assertEqual(sum(len(x) for x in result.values()), 30)
        schema_string = pretty_print_change_dict(result, title=f"Differences between {schema1.name} and {schema2.name}")
        # this test may need updating if the text format changes
        found_issues = schema_string.count("):")
        self.assertEqual(found_issues, 30)

    def test_compare_differences(self):
        schema1 = util_create_schemas.load_schema1()
        schema2 = util_create_schemas.load_schema2()

        _, not_in_schema1, not_in_schema2, unequal_entries = compare_schemas(schema1, schema2)

        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 1)  # One tag not in schema2
        self.assertIn("TestNode4", not_in_schema2[HedSectionKey.Tags])  # "TestNode4" is not in schema2

        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 1)  # One tag not in schema1
        self.assertIn("TestNode5", not_in_schema1[HedSectionKey.Tags])  # "TestNode5" is not in schema1

        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 1)  # No unequal entries should be found
        self.assertIn("TestNode3", unequal_entries[HedSectionKey.Tags])

        diff_string_with_summary = compare_differences(schema1, schema2)
        self.assertIsInstance(diff_string_with_summary, str)
        self.assertIn("Tags:", diff_string_with_summary)

    def test_compare_score_lib_versions(self):
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        _, not_in_schema1, not_in_schema2, unequal_entries = compare_schemas(schema1, schema2,
                                                                             attribute_filter=HedKey.InLibrary)

        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 21)
        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 10)
        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 80)

        diff_string = compare_differences(schema1, schema2, attribute_filter=HedKey.InLibrary)
        # Do a half-hearted check that all the above showed up in the output
        self.assertTrue(diff_string)
        for item in not_in_schema1[HedSectionKey.Tags].keys():
            self.assertIn(item, diff_string)
        for item in not_in_schema2[HedSectionKey.Tags].keys():
            self.assertIn(item, diff_string)
        for item in unequal_entries[HedSectionKey.Tags].keys():
            self.assertIn(item, diff_string)

    def test_compare_identical_schemas(self):
        schema1 = load_schema_version("score_1.0.0")
        schema2 = copy.deepcopy(schema1)
        diff_string = compare_differences(schema1, schema2, attribute_filter=HedKey.InLibrary)
        self.assertFalse(diff_string)
