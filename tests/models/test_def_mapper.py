import unittest
import os

from hed import schema
from hed.models import DefDict, DefinitionMapper, HedString
from hed.validator import HedValidator


class Test(unittest.TestCase):
    basic_hed_string_with_def_first_paren = None

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "hed_pairs/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.def_contents_string = "(Item/TestDef1,Item/TestDef2)"
        cls.basic_definition_string = f"(Definition/TestDef,{cls.def_contents_string})"
        cls.basic_definition_string_no_paren = f"Definition/TestDef,{cls.def_contents_string}"
        cls.label_def_string = "Def/TestDef"
        cls.expanded_def_string = f"(Def-expand/TestDef,{cls.def_contents_string})"
        cls.basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
        cls.basic_hed_string_with_def = f"{cls.basic_hed_string},{cls.label_def_string}"
        cls.basic_hed_string_with_def_first = f"{cls.label_def_string},{cls.basic_hed_string}"
        cls.basic_hed_string_with_def_first_paren = f"({cls.label_def_string},{cls.basic_hed_string})"
        cls.placeholder_label_def_string = "Def/TestDefPlaceholder/2471"
        cls.placeholder_definition_contents = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents})"
        cls.placeholder_definition_string_no_paren = f"Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents}"
        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"

        cls.valid_definition_strings = {
            'str_no_defs': False,
            'str2': True,
            'str3': False,
            'str4': False,
            'str5': False,
            'str6': False,
            'str7': False,
        }
        cls.mark_all_as_valid_strings = {
            'str_no_defs': False,
            'str2': False,
            'str3': False,
            'str4': False,
            'str5': False,
            'str6': False,
            'str7': False,
        }

    def base_def_validator(self, test_strings, result_strings, valid_strings, expand_defs, shrink_defs, remove_definitions, extra_ops=None,
                           basic_definition_string=None):
        if not basic_definition_string:
            basic_definition_string = self.basic_definition_string
        def_dict = DefDict()
        def_string = HedString(basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)

        def_mapper = DefinitionMapper(def_dict)
        hed_ops = []
        if extra_ops:
            hed_ops += extra_ops
        hed_ops.append(def_mapper)

        for key in test_strings:
            string, result, invalid = test_strings[key], result_strings[key], valid_strings[key]
            test_string = HedString(string)
            def_issues = test_string.validate(hed_ops, expand_defs=expand_defs, shrink_defs=shrink_defs, remove_definitions=remove_definitions)
            self.assertEqual(invalid, bool(def_issues))
            self.assertEqual(test_string.get_as_short(), result)

    def test_expand_def_tags(self):
        basic_def_strings = {
            'str_no_defs': self.basic_definition_string,
            'str2': self.basic_definition_string_no_paren,
            'str3': self.basic_hed_string + "," + self.basic_definition_string,
            'str4': self.basic_definition_string + "," + self.basic_hed_string,
            'str5': self.basic_hed_string_with_def,
            'str6': self.basic_hed_string_with_def_first,
            'str7': self.basic_hed_string_with_def_first_paren,
        }
        expanded_def_strings = {
            'str_no_defs': "",
            'str2': self.basic_definition_string_no_paren,
            'str3': self.basic_hed_string,
            'str4': self.basic_hed_string,
            'str5': self.basic_hed_string + "," + self.expanded_def_string,
            'str6': self.expanded_def_string + "," + self.basic_hed_string,
            'str7': "(" + self.expanded_def_string + "," + self.basic_hed_string + ")"
        }
        expanded_def_strings_with_definition = {
            'str_no_defs': self.basic_definition_string,
            'str2': self.basic_definition_string_no_paren,
            'str3': self.basic_hed_string + "," + self.basic_definition_string,
            'str4': self.basic_definition_string + "," + self.basic_hed_string,
            'str5': self.basic_hed_string + "," + self.expanded_def_string,
            'str6': self.expanded_def_string + "," + self.basic_hed_string,
            'str7': "(" + self.expanded_def_string + "," + self.basic_hed_string + ")"
        }

        self.base_def_validator(basic_def_strings, expanded_def_strings_with_definition, self.mark_all_as_valid_strings, expand_defs=True, shrink_defs=False, remove_definitions=False)
        self.base_def_validator(basic_def_strings, basic_def_strings, self.mark_all_as_valid_strings, expand_defs=False, shrink_defs=False, remove_definitions=False)
        self.base_def_validator(basic_def_strings, basic_def_strings, self.mark_all_as_valid_strings, expand_defs=False, shrink_defs=True, remove_definitions=False)
        self.base_def_validator(expanded_def_strings_with_definition, basic_def_strings, self.mark_all_as_valid_strings, expand_defs=False, shrink_defs=True, remove_definitions=False)
        self.base_def_validator(expanded_def_strings_with_definition, expanded_def_strings_with_definition, self.mark_all_as_valid_strings, expand_defs=True, shrink_defs=False, remove_definitions=False)
        self.base_def_validator(basic_def_strings, expanded_def_strings, self.mark_all_as_valid_strings, expand_defs=True, shrink_defs=False, remove_definitions=True)

        validator = HedValidator(self.hed_schema)
        extra_ops = [validator]

        self.base_def_validator(basic_def_strings, expanded_def_strings_with_definition, self.valid_definition_strings, expand_defs=True, shrink_defs=False,
                                extra_ops=extra_ops, remove_definitions=False)

    # special case test
    def test_changing_tag_then_def_mapping(self):
        def_dict = DefDict()
        def_string = HedString(self.basic_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)
        validator = HedValidator(self.hed_schema)
        hed_ops = [validator, def_mapper]

        test_string = HedString(self.label_def_string)
        tag = test_string.get_direct_children()[0]
        tag.tag = "Organizational-property/" + str(tag)
        def_issues = test_string.validate(hed_ops, expand_defs=True)
        self.assertFalse(def_issues)
        self.assertEqual(test_string.get_as_short(), f"{self.expanded_def_string}")

        test_string = HedString(self.label_def_string)
        tag = test_string.get_direct_children()[0]
        tag.tag = "Organizational-property22/" + str(tag)
        def_issues = test_string.validate(hed_ops, expand_defs=True)
        self.assertTrue(def_issues)

    def test_expand_def_tags_placeholder(self):
        basic_def_strings = {
            'str_no_defs': self.placeholder_definition_string,
            'str2': self.placeholder_definition_string_no_paren,
            'str3': self.basic_hed_string + "," + self.placeholder_definition_string,
            'str4': self.placeholder_definition_string + "," + self.basic_hed_string,
            'str5': self.placeholder_hed_string_with_def,
            'str6': self.placeholder_hed_string_with_def_first,
            'str7': self.placeholder_hed_string_with_def_first_paren,
        }
        expanded_def_strings = {
            'str_no_defs': "",
            'str2': self.placeholder_definition_string_no_paren,
            'str3': self.basic_hed_string,
            'str4': self.basic_hed_string,
            'str5': self.basic_hed_string + "," + self.placeholder_expanded_def_string,
            'str6': self.placeholder_expanded_def_string + "," + self.basic_hed_string,
            'str7': "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")",
        }
        expanded_def_strings_with_definition = {
            'str_no_defs': self.placeholder_definition_string,
            'str2': self.placeholder_definition_string_no_paren,
            'str3': self.basic_hed_string + "," + self.placeholder_definition_string,
            'str4': self.placeholder_definition_string + "," + self.basic_hed_string,
            'str5': self.basic_hed_string + "," + self.placeholder_expanded_def_string,
            'str6': self.placeholder_expanded_def_string + "," + self.basic_hed_string,
            'str7': "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")",
        }

        self.base_def_validator(basic_def_strings, expanded_def_strings_with_definition, self.mark_all_as_valid_strings,
                                expand_defs=True, shrink_defs=False,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(basic_def_strings, basic_def_strings, self.mark_all_as_valid_strings,
                                expand_defs=False, shrink_defs=False,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(basic_def_strings, basic_def_strings, self.mark_all_as_valid_strings,
                                expand_defs=False, shrink_defs=True,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(expanded_def_strings_with_definition, basic_def_strings, self.mark_all_as_valid_strings,
                                expand_defs=False, shrink_defs=True,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(basic_def_strings, expanded_def_strings, self.mark_all_as_valid_strings,
                                expand_defs=True, shrink_defs=False,
                                remove_definitions=True, basic_definition_string=self.placeholder_definition_string)

        validator = HedValidator(self.hed_schema)
        extra_ops = [validator]
        self.base_def_validator(basic_def_strings, expanded_def_strings_with_definition, self.valid_definition_strings,
                                expand_defs=True, shrink_defs=False,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string,
                                extra_ops=extra_ops)

    def test_expand_def_tags_placeholder_invalid(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
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

        label_def_string_has_invalid_placeholder = "def/TestDef/54687"

        test_string = HedString(label_def_string_has_invalid_placeholder)
        test_string.convert_to_canonical_forms(None)
        def_issues = def_mapper.expand_def_tags(test_string)
        self.assertEqual(str(test_string), label_def_string_has_invalid_placeholder)
        self.assertTrue(def_issues)

    def test_bad_def_expand(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.convert_to_canonical_forms(None)
        def_dict.check_for_definitions(def_string)
        def_mapper = DefinitionMapper(def_dict)

        valid_placeholder = HedString(self.placeholder_expanded_def_string)
        def_issues = valid_placeholder.validate(def_mapper)
        self.assertFalse(def_issues)

        invalid_placeholder = HedString("(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/21,Item/TestDef2))")
        def_issues = invalid_placeholder.validate(def_mapper)
        self.assertTrue(bool(def_issues))



if __name__ == '__main__':
    unittest.main()
