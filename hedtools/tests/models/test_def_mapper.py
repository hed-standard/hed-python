import unittest
import os

from hed import schema, HedString
from hed.models import DefDict, DefinitionMapper
from hed import HedValidator


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "hed_pairs/HED8.0.0.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.base_dict = DefDict()
        cls.def_contents_string = "(Item/TestDef1,Item/TestDef2)"
        cls.basic_definition_string = f"(Definition/TestDef,{cls.def_contents_string})"
        cls.basic_definition_string_no_paren = f"Definition/TestDef,{cls.def_contents_string}"
        cls.label_def_string = "Def/TestDef"
        cls.expanded_def_string = f"(Def-expand/TestDef,{cls.def_contents_string})"
        cls.basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
        cls.basic_hed_string_with_def = f"{cls.basic_hed_string},{cls.label_def_string}"
        cls.basic_hed_string_with_def_first = f"{cls.label_def_string},{cls.basic_hed_string}"
        cls.basic_hed_string_with_def_first_paren = f"({cls.label_def_string},{cls.basic_hed_string})"
        cls.placeholder_label_def_string = "def/TestDefPlaceholder/2471"
        cls.placeholder_def_contents = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_def_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents})"
        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"

    def test_expand_def_tags(self):
        def_dict = DefDict()
        def_string = HedString(self.basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)

        test_string = HedString(self.basic_definition_string)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_definition_string_no_paren)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_definition_string_no_paren)

        test_string = HedString(self.basic_hed_string + "," + self.basic_definition_string)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_definition_string + "," + self.basic_hed_string)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string + "," + self.expanded_def_string)

        test_string = HedString(self.basic_hed_string_with_def_first)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.expanded_def_string + "," + self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def_first_paren)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), "(" + self.expanded_def_string + "," + self.basic_hed_string + ")")

    def test_expand_def_tags_with_validator(self):
        def_dict = DefDict()
        def_string = HedString(self.basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)
        validator = HedValidator(self.hed_schema)
        validators = [validator, def_mapper]

        test_string = HedString(self.basic_definition_string)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertEqual(test_string.get_as_short(), "")

        test_string = HedString(self.basic_definition_string_no_paren)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertTrue(def_issues)
        self.assertEqual(test_string.get_as_short(), self.basic_definition_string_no_paren)

        test_string = HedString(self.basic_hed_string + "," + self.basic_definition_string)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), self.basic_hed_string)

        test_string = HedString(self.basic_definition_string + "," + self.basic_hed_string)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), self.basic_hed_string + "," + self.expanded_def_string)

        test_string = HedString(self.basic_hed_string_with_def_first)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), self.expanded_def_string + "," + self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def_first_paren)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), "(" + self.expanded_def_string + "," + self.basic_hed_string + ")")

    def test_changing_tag_then_def_mapping(self):
        def_dict = DefDict()
        def_string = HedString(self.basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)
        validator = HedValidator(self.hed_schema)
        validators = [validator, def_mapper]

        test_string = HedString(self.label_def_string)
        tag = test_string.get_direct_children()[0]
        tag.tag = "Organizational-property/" + str(tag)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), f"{self.expanded_def_string}")

        test_string = HedString(self.label_def_string)
        tag = test_string.get_direct_children()[0]
        tag.tag = "Organizational-property22/" + str(tag)
        def_issues = test_string.validate(validators, expand_defs=True)
        self.assertTrue(def_issues)

    def test_expand_def_tags_no_expand(self):
        def_dict = DefDict()
        def_string = HedString(self.basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)

        test_string = HedString(self.basic_definition_string)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_definition_string_no_paren)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_definition_string_no_paren)

        test_string = HedString(self.basic_hed_string + "," + self.basic_definition_string)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_definition_string + "," + self.basic_hed_string)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.basic_hed_string_with_def)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string_with_def)

        test_string = HedString(self.basic_hed_string_with_def_first)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string_with_def_first)

        test_string = HedString(self.basic_hed_string_with_def_first_paren)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string_with_def_first_paren)

    def test_expand_def_tags_placeholder(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_def_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)

        test_string = HedString(self.placeholder_def_string)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_hed_string + "," + self.placeholder_def_string)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.placeholder_def_string + "," + self.basic_hed_string)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.placeholder_hed_string_with_def)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string + "," + self.placeholder_expanded_def_string)

        test_string = HedString(self.placeholder_hed_string_with_def_first)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.placeholder_expanded_def_string + "," + self.basic_hed_string)

        test_string = HedString(self.placeholder_hed_string_with_def_first_paren)
        def_issues = test_string.validate(def_mapper, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string),
                         "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")")

    def test_expand_def_tags_placeholder_no_expand(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_def_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)
        test_string = HedString(self.placeholder_def_string)

        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), "")

        test_string = HedString(self.basic_hed_string + "," + self.placeholder_def_string)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.placeholder_def_string + "," + self.basic_hed_string)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.basic_hed_string)

        test_string = HedString(self.placeholder_hed_string_with_def)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.placeholder_hed_string_with_def)

        test_string = HedString(self.placeholder_hed_string_with_def_first)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.placeholder_hed_string_with_def_first)

        test_string = HedString(self.placeholder_hed_string_with_def_first_paren)
        def_issues = test_string.validate(def_mapper, expand_defs=False)
        self.assertFalse(def_issues)
        self.assertEqual(str(test_string), self.placeholder_hed_string_with_def_first_paren)

    def test_expand_def_tags_placeholder_invalid(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_def_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)

        placeholder_label_def_string_no_placeholder = "def/TestDefPlaceholder"

        test_string = HedString(placeholder_label_def_string_no_placeholder)
        test_string.convert_to_canonical_forms(None)
        def_issues = def_mapper.expand_def_tags(test_string)
        self.assertEqual(str(test_string), placeholder_label_def_string_no_placeholder)
        self.assertTrue(def_issues)

        def_dict = DefDict()
        def_string = HedString(self.basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)

        label_def_string_has_inavlid_placeholder = "def/TestDef/54687"

        test_string = HedString(label_def_string_has_inavlid_placeholder)
        test_string.convert_to_canonical_forms(None)
        def_issues = def_mapper.expand_def_tags(test_string)
        self.assertEqual(str(test_string), label_def_string_has_inavlid_placeholder)
        self.assertTrue(def_issues)

    def test__check_tag_starts_with(self):
        target_tag_name = "definition/"

        test_tags = ["Definition/TempTestDef", "Informational/Definition/TempTestDef",
                     "Attribute/Informational/Definition/TempTestDef"]

        for tag in test_tags:
            result = DefDict._check_tag_starts_with(tag, target_tag_name)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
