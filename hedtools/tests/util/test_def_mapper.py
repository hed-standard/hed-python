import unittest
import os

from hed.util.def_mapper import DefinitionMapper
from hed import schema
from hed.util.def_dict import DefDict
from hed.util.hed_string import HedString
from hed.util import error_reporter


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "legacy_xml/HED8.0.0-alpha.2.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.base_dict = DefDict()
        cls.def_contents_string = "(Item/TestDef1,Item/TestDef2)"
        cls.basic_def_string = f"(Definition/TestDef,{cls.def_contents_string})"
        cls.basic_def_string_no_paren = f"Definition/TestDef,{cls.def_contents_string}"
        cls.label_def_string = f"Def/TestDef"
        cls.expanded_def_string = f"(Def-expand/TestDef,{cls.def_contents_string})"
        cls.basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
        cls.basic_hed_string_with_def = f"{cls.basic_hed_string},{cls.label_def_string}"
        cls.basic_hed_string_with_def_first = f"{cls.label_def_string},{cls.basic_hed_string}"
        cls.basic_hed_string_with_def_first_paren = f"({cls.label_def_string},{cls.basic_hed_string})"

        cls.placeholder_label_def_string = f"def/TestDefPlaceholder/2471"
        cls.placeholder_def_contents = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_def_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents})"
        cls.placeholder_expanded_def_string = f"(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"

    def test_replace_and_remove_tags(self):
        def_dict = DefDict()
        def_dict.check_for_definitions(HedString(self.basic_def_string))
        def_mapper = DefinitionMapper(def_dict)

        test_string = HedString(self.basic_def_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_def_string_no_paren)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_hed_string + "," + self.basic_def_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_def_string + "," + self.basic_hed_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.basic_hed_string + "," + self.expanded_def_string)

        test_string = HedString(self.basic_hed_string_with_def_first)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.expanded_def_string + "," + self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def_first_paren)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), "(" + self.expanded_def_string + "," + self.basic_hed_string + ")")


    def test_replace_and_remove_tags_no_expand(self):
        def_dict = DefDict()
        def_dict.check_for_definitions(HedString(self.basic_def_string))
        def_mapper = DefinitionMapper(def_dict)

        test_string = HedString(self.basic_def_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_def_string_no_paren)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_hed_string + "," + self.basic_def_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_def_string + "," + self.basic_hed_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), self.basic_hed_string + "," + self.label_def_string)

        test_string = HedString(self.basic_hed_string_with_def_first)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), self.label_def_string + "," + self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def_first_paren)
        def_issues = def_mapper.replace_and_remove_tags(test_string, do_not_expand_labels=True)
        self.assertEqual(str(test_string), "(" + self.label_def_string + "," + self.basic_hed_string + ")")


    def test_replace_and_remove_tags_placeholder(self):
        def_dict = DefDict()
        def_dict.check_for_definitions(HedString(self.placeholder_def_string))
        def_mapper = DefinitionMapper(def_dict)

        test_string = HedString(self.placeholder_def_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), "")

        # result_string = def_mapper.replace_and_remove_tags(HedString(self.basic_def_string_no_paren)
        # self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_hed_string + "," + self.placeholder_def_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.placeholder_def_string + "," + self.basic_hed_string)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.placeholder_hed_string_with_def)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.basic_hed_string + "," + self.placeholder_expanded_def_string)

        test_string = HedString(self.placeholder_hed_string_with_def_first)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), self.placeholder_expanded_def_string + "," + self.basic_hed_string)

        test_string = HedString(self.placeholder_hed_string_with_def_first_paren)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")")

    def test_replace_and_remove_tags_placeholder_invalid(self):
        def_dict = DefDict()
        def_dict.check_for_definitions(HedString(self.placeholder_def_string))
        def_mapper = DefinitionMapper(def_dict)

        placeholder_label_def_string_no_placeholder = f"def/TestDefPlaceholder"

        test_string = HedString(placeholder_label_def_string_no_placeholder)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), placeholder_label_def_string_no_placeholder)
        self.assertTrue(def_issues)
        actual_issues = []
        for issue in def_issues:
            actual_issues += error_reporter.ErrorHandler().format_error(**issue)

        def_dict = DefDict()
        def_dict.check_for_definitions(HedString(self.basic_def_string))
        def_mapper = DefinitionMapper(def_dict)

        label_def_string_has_inavlid_placeholder = f"def/TestDef/54687"

        test_string = HedString(label_def_string_has_inavlid_placeholder)
        def_issues = def_mapper.replace_and_remove_tags(test_string)
        self.assertEqual(str(test_string), label_def_string_has_inavlid_placeholder)
        self.assertTrue(def_issues)
        actual_issues = []
        for issue in def_issues:
            actual_issues += error_reporter.ErrorHandler().format_error(**issue)


    def test__check_tag_starts_with(self):
        target_tag_name = "definition/"

        test_tags = ["Definition/TempTestDef", "Informational/Definition/TempTestDef",
                     "Attribute/Informational/Definition/TempTestDef"]

        for tag in test_tags:
            result = DefinitionMapper._check_tag_starts_with(tag, target_tag_name)
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()





