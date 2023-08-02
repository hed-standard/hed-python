import unittest
import os
import io
import json


from hed.schema import HedKey, HedSectionKey, from_string
from hed.schema.schema_compare import compare_schemas, find_matching_tags, \
    _pretty_print_diff_all, _pretty_print_missing_all, compare_differences
from hed import load_schema_version


class TestSchemaComparison(unittest.TestCase):

    library_schema_start = """HED library="testcomparison" version="1.1.0" withStandard="8.2.0" unmerged="true"

'''Prologue'''

!# start schema

"""

    library_schema_end = """
!# end schema

!# end hed
    """

    def _get_test_schema(self, node_lines):
        library_schema_string = self.library_schema_start + "\n".join(node_lines) + self.library_schema_end
        test_schema = from_string(library_schema_string, ".mediawiki")

        return test_schema

    def load_schema1(self):
        test_nodes = ["'''TestNode''' <nowiki> [This is a simple test node]</nowiki>\n",
                      " *TestNode2",
                      " *TestNode3",
                      " *TestNode4"
                     ]
        return self._get_test_schema(test_nodes)

    def load_schema2(self):
        test_nodes = ["'''TestNode''' <nowiki> [This is a simple test node]</nowiki>\n",
                      " *TestNode2",
                      " **TestNode3",
                      " *TestNode5"
                     ]

        return self._get_test_schema(test_nodes)

    def test_find_matching_tags(self):
        # create entries for schema1
        schema1 = self.load_schema1()
        schema2 = self.load_schema2()

        result = find_matching_tags(schema1, schema2)
        # Check if the result is correct
        self.assertEqual(len(result[HedSectionKey.Tags]), 3)
        self.assertIn("TestNode", result[HedSectionKey.Tags])
        self.assertIn("TestNode2", result[HedSectionKey.Tags])
        self.assertIn("TestNode3", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode4", result[HedSectionKey.Tags])
        self.assertNotIn("TestNode5", result[HedSectionKey.Tags])

        match_string = find_matching_tags(schema1, schema2, output='string')
        self.assertIsInstance(match_string, str)
        # print(match_string)

        json_style_dict = find_matching_tags(schema1, schema2, output='dict')
        self.assertIsInstance(json_style_dict, dict)

        result_string = json.dumps(json_style_dict, indent=4)
        self.assertIsInstance(result_string, str)

    def test_compare_schemas(self):
        schema1 = self.load_schema1()
        schema2 = self.load_schema2()

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
        schema1 = self.load_schema1()
        schema2 = self.load_schema2()

        not_in_schema1, not_in_schema2, unequal_entries = compare_differences(schema1, schema2)

        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 1)  # One tag not in schema2
        self.assertIn("TestNode4", not_in_schema2[HedSectionKey.Tags])  # "TestNode4" is not in schema2

        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 1)  # One tag not in schema1
        self.assertIn("TestNode5", not_in_schema1[HedSectionKey.Tags])  # "TestNode5" is not in schema1

        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 1)  # No unequal entries should be found
        self.assertIn("TestNode3", unequal_entries[HedSectionKey.Tags])

        diff_string = compare_differences(schema1, schema2, output='string')
        self.assertIsInstance(diff_string, str)
        # print(diff_string)

    def test_compare_score_lib_versions(self):
        schema1 = load_schema_version("score_1.0.0")
        schema2 = load_schema_version("score_1.1.0")
        not_in_schema1, not_in_schema2, unequal_entries = compare_differences(schema1, schema2,
                                                                              attribute_filter=HedKey.InLibrary)
        self.assertEqual(len(not_in_schema1[HedSectionKey.Tags]), 21)
        self.assertEqual(len(not_in_schema2[HedSectionKey.Tags]), 10)
        self.assertEqual(len(unequal_entries[HedSectionKey.Tags]), 61)

        diff_string = compare_differences(schema1, schema2, attribute_filter=HedKey.InLibrary, output='string',
                                          sections=None)
        self.assertIsInstance(diff_string, str)
        # print(diff_string)

        json_style_dict = compare_differences(schema1, schema2, attribute_filter=HedKey.InLibrary, output='dict',
                                          sections=None)
        self.assertIsInstance(json_style_dict, dict)

        result_string = json.dumps(json_style_dict, indent=4)
        self.assertIsInstance(result_string, str)