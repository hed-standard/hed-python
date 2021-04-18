import unittest
import os

from hed.util.def_mapper import DefinitionMapper
from hed import schema
from hed.util.def_dict import DefDict
from hed.util.hed_string import HedString


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "HED8.0.0-alpha.1.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.base_dict = DefDict(hed_schema=cls.hed_schema)
        cls.def_contents_string = "(Item/TestDef1,Item/TestDef2)"
        cls.basic_def_string = f"(Definition/TestDef,{cls.def_contents_string})"
        cls.basic_def_string_no_paren = f"Definition/TestDef,{cls.def_contents_string}"
        cls.label_def_string = f"def/TestDef"
        cls.expanded_def_string = f"(defexp/TestDef,{cls.def_contents_string})"
        cls.basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
        cls.basic_hed_string_with_def = f"{cls.basic_hed_string},{cls.label_def_string}"
        cls.basic_hed_string_with_def_first = f"{cls.label_def_string},{cls.basic_hed_string}"
        cls.basic_hed_string_with_def_first_paren = f"({cls.label_def_string},{cls.basic_hed_string})"

        cls.placeholder_label_def_string = f"def/TestDefPlaceholder/2471"
        cls.placeholder_def_contents = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_def_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents})"
        cls.placeholder_expanded_def_string = f"(defexp/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"


    def test_replace_and_remove_tags(self):
        def_dict = DefDict(hed_schema=self.hed_schema)
        def_dict.check_for_definitions(HedString(self.basic_def_string))
        def_mapper = DefinitionMapper(def_dict, hed_schema=self.hed_schema)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_def_string))
        self.assertEqual(str(result_string), "")

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_def_string_no_paren))
        self.assertEqual(str(result_string), "")

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_hed_string + "," + self.basic_def_string))
        self.assertEqual(str(result_string), self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_def_string + "," + self.basic_hed_string))
        self.assertEqual(str(result_string), self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_hed_string_with_def))
        self.assertEqual(str(result_string), self.basic_hed_string + "," + self.expanded_def_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_hed_string_with_def_first))
        self.assertEqual(str(result_string), self.expanded_def_string + "," + self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_hed_string_with_def_first_paren))
        self.assertEqual(str(result_string), "(" + self.expanded_def_string + "," + self.basic_hed_string + ")")

    def test_replace_and_remove_tags_placeholder(self):
        def_dict = DefDict(hed_schema=self.hed_schema)
        def_dict.check_for_definitions(HedString(self.placeholder_def_string))
        def_mapper = DefinitionMapper(def_dict, hed_schema=self.hed_schema)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.placeholder_def_string))
        self.assertEqual(str(result_string), "")

        # result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_def_string_no_paren)
        # self.assertEqual(str(result_string), "")

        result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_hed_string + "," + self.placeholder_def_string))
        self.assertEqual(str(result_string), self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.placeholder_def_string + "," + self.basic_hed_string))
        self.assertEqual(str(result_string), self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.placeholder_hed_string_with_def))
        self.assertEqual(str(result_string), self.basic_hed_string + "," + self.placeholder_expanded_def_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.placeholder_hed_string_with_def_first))
        self.assertEqual(str(result_string), self.placeholder_expanded_def_string + "," + self.basic_hed_string)

        result_string = def_mapper.replace_and_remove_tags(HedString(self.placeholder_hed_string_with_def_first_paren))
        self.assertEqual(str(result_string), "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")")


    def test__check_tag_starts_with(self):
        possible_tag_list = ["definition", "informational/definition", "attribute/informational/definition"]

        test_tags = ["Definition/TempTestDef", "Informational/Definition/TempTestDef",
                     "Attribute/Informational/Definition/TempTestDef"]

        for tag in test_tags:
            result = DefinitionMapper._check_tag_starts_with(tag, possible_tag_list)
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()





