import unittest
import os

from hed.util.def_mapper import DefinitionMapper
from hed.util.hed_schema import HedSchema

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "HED8.0.0-alpha.1.xml")
        cls.hed_schema = HedSchema(hed_xml_file)
        cls.base_def_mapper = DefinitionMapper(hed_schema=cls.hed_schema)
        cls.basic_def_string = "(Definition/TestDef, Organizational/TestOrg, (Item/TestDef1, Item/TestDef2))"
        cls.basic_hed_string = "Item/BasicTestTag1, Item/BasicTestTag2"

    def test_add_definitions(self):
        def_mapper = DefinitionMapper(hed_schema=self.hed_schema)
        original_def_count = len(def_mapper._defs)
        def_mapper.add_definitions(self.basic_def_string)
        new_def_count = len(def_mapper._defs)
        self.assertGreater(new_def_count, original_def_count)

    def test_replace_and_remove_tags(self):
        def_mapper = DefinitionMapper(hed_schema=self.hed_schema)
        def_mapper.add_definitions(self.basic_def_string)

        result_string = def_mapper.replace_and_remove_tags(self.basic_def_string)
        self.assertEqual(result_string, "")

        result_string = def_mapper.replace_and_remove_tags(self.basic_hed_string + ", " + self.basic_def_string)
        self.assertEqual(result_string, self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(self.basic_def_string + ", " + self.basic_hed_string)
        self.assertEqual(result_string, self.basic_hed_string)

    def test__check_tag_starts_with(self):
        possible_tag_list = ["definition", "informational/definition", "attribute/informational/definition"]

        test_tags = ["Definition/TempTestDef", "Informational/Definition/TempTestDef",
                     "Attribute/Informational/Definition/TempTestDef"]

        for tag in test_tags:
            result = DefinitionMapper._check_tag_starts_with(tag, possible_tag_list)
            self.assertTrue(result)

    def test__check_for_definitions(self):
        def_mapper = DefinitionMapper(hed_schema=self.hed_schema)
        original_def_count = len(def_mapper._defs)
        def_mapper._check_for_definitions(self.basic_def_string)
        new_def_count = len(def_mapper._defs)
        self.assertGreater(new_def_count, original_def_count)

    def test__find_tag_group_extent(self):
        input_strings = [
            (1, self.basic_def_string),
            (1, self.basic_def_string + ", " + self.basic_hed_string),
            (1, self.basic_hed_string + ", " + self.basic_def_string),
            (len(self.basic_hed_string) + 4, self.basic_hed_string + ", " + self.basic_def_string)
        ]
        expected_strings = [
            self.basic_def_string,
            self.basic_def_string + ", ",
            self.basic_hed_string + ", " + self.basic_def_string,
            ", " + self.basic_def_string
        ]
        expected_strings_no_comma = [
            self.basic_def_string,
            self.basic_def_string,
            self.basic_hed_string + ", " + self.basic_def_string,
            self.basic_def_string
        ]

        for (input_index, input_string), expected_string, expected_string_no_comma \
                in zip(input_strings, expected_strings, expected_strings_no_comma):
            min_i, max_i = DefinitionMapper._find_tag_group_extent(input_string, input_index, True)
            result_string = input_string[min_i:max_i]
            self.assertEqual(result_string, expected_string)

            min_i, max_i = DefinitionMapper._find_tag_group_extent(input_string, input_index, False)
            result_string = input_string[min_i:max_i]
            self.assertEqual(result_string, expected_string_no_comma)


if __name__ == '__main__':
    unittest.main()





