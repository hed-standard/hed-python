import unittest
import os

from hed import schema
from hed.models import DefinitionDict, HedString
from hed.validator import DefValidator
from hed.errors import ErrorHandler, ErrorContext


class Test(unittest.TestCase):
    basic_hed_string_with_def_first_paren = None

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.realpath(os.path.join(cls.base_data_dir, "schema_tests/HED8.0.0t.xml"))
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.def_contents_string = "(Item/TestDef1,Item/TestDef2)"
        cls.basic_definition_string = f"(Definition/TestDef,{cls.def_contents_string})"
        cls.basic_definition_string_no_paren = f"Definition/TestDef,{cls.def_contents_string}"

        cls.placeholder_definition_contents = "(Acceleration/#,Item/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents})"
        cls.placeholder_definition_string_no_paren = \
            f"Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents}"



        cls.label_def_string = "Def/TestDef"
        cls.expanded_def_string = f"(Def-expand/TestDef,{cls.def_contents_string})"
        cls.basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
        cls.basic_hed_string_with_def = f"{cls.basic_hed_string},{cls.label_def_string}"
        cls.basic_hed_string_with_def_first = f"{cls.label_def_string},{cls.basic_hed_string}"
        cls.basic_hed_string_with_def_first_paren = f"({cls.label_def_string},{cls.basic_hed_string})"
        cls.placeholder_label_def_string = "Def/TestDefPlaceholder/2471"

        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Acceleration/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"


    def test_expand_def_tags_placeholder_invalid(self):
        def_validator = DefValidator()
        def_string = HedString(self.placeholder_definition_string, self.hed_schema)
        def_validator.check_for_definitions(def_string)

        placeholder_label_def_string_no_placeholder = "Def/TestDefPlaceholder"

        test_string = HedString(placeholder_label_def_string_no_placeholder, self.hed_schema)
        def_issues = def_validator.validate_def_tags(test_string)
        def_issues += def_validator.expand_def_tags(test_string)
        self.assertEqual(str(test_string), placeholder_label_def_string_no_placeholder)
        self.assertTrue(def_issues)

        def_validator = DefValidator()
        def_string = HedString(self.basic_definition_string, self.hed_schema)
        def_validator.check_for_definitions(def_string)

        label_def_string_has_invalid_placeholder = "Def/TestDef/54687"

        def_validator = DefValidator()
        def_string = HedString(self.basic_definition_string, self.hed_schema)
        def_validator.check_for_definitions(def_string)

        test_string = HedString(label_def_string_has_invalid_placeholder, self.hed_schema)
        def_issues = def_validator.validate_def_tags(test_string)
        def_issues += def_validator.expand_def_tags(test_string)
        self.assertEqual(str(test_string), label_def_string_has_invalid_placeholder)
        self.assertTrue(def_issues)


    def test_bad_def_expand(self):
        def_validator = DefValidator()
        def_string = HedString(self.placeholder_definition_string, self.hed_schema)
        def_validator.check_for_definitions(def_string)

        valid_placeholder = HedString(self.placeholder_expanded_def_string, self.hed_schema)
        def_issues = def_validator.validate_def_tags(valid_placeholder)
        self.assertFalse(def_issues)

        invalid_placeholder = HedString("(Def-expand/TestDefPlaceholder/2471,(Acceleration/21,Item/TestDef2))", self.hed_schema)
        def_issues = def_validator.validate_def_tags(invalid_placeholder)
        self.assertTrue(bool(def_issues))


    def test_duplicate_def(self):
        def_dict = DefinitionDict()
        def_string = HedString(self.placeholder_definition_string, self.hed_schema)
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.ROW, 5)
        def_dict.check_for_definitions(def_string, error_handler=error_handler)
        self.assertEqual(len(def_dict.issues), 0)

        def_validator = DefValidator([def_dict, def_dict])
        self.assertEqual(len(def_validator.issues), 1)
        self.assertTrue('ec_row' in def_validator.issues[0])

        def_dict = DefinitionDict([def_dict, def_dict, def_dict])
        self.assertEqual(len(def_dict.issues), 2)
        self.assertTrue('ec_row' in def_dict.issues[0])



class TestDefErrors(unittest.TestCase):
    basic_hed_string_with_def_first_paren = None

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.realpath(os.path.join(cls.base_data_dir, "schema_tests/HED8.0.0t.xml"))
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
        cls.placeholder_definition_contents = "(Acceleration/#,Item/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents})"
        cls.placeholder_definition_string_no_paren = \
            f"Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents}"
        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Acceleration/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"

    def base_def_validator(self, test_strings, result_strings, expand_defs, shrink_defs,
                           remove_definitions, extra_ops=None,
                           basic_definition_string=None):
        if not basic_definition_string:
            basic_definition_string = self.basic_definition_string
        def_dict = DefValidator(basic_definition_string, hed_schema=self.hed_schema)


        for key in test_strings:
            string, expected_result = test_strings[key], result_strings[key]
            test_string = HedString(string, self.hed_schema, def_dict)
            def_issues = def_dict.validate_def_tags(test_string)
            if remove_definitions:
                test_string.remove_definitions()
            if expand_defs:
                test_string.expand_defs()
            if shrink_defs:
                test_string.shrink_defs()
            self.assertEqual(False, bool(def_issues))
            self.assertEqual(test_string.get_as_short(), expected_result)

    def test_expand_def_tags(self):
        basic_def_strings = {
            'str_no_defs': self.basic_definition_string,
            'str2': self.basic_definition_string_no_paren,
            'str3': self.basic_hed_string + "," + self.basic_definition_string,
            'str4': self.basic_definition_string + "," + self.basic_hed_string,
            'str5': self.basic_hed_string_with_def,
            'str6': self.basic_hed_string_with_def_first,
            'str7': self.basic_hed_string_with_def_first_paren,
            'str8': "("  + self.basic_hed_string_with_def_first_paren + ")",
        }
        expanded_def_strings = {
            'str_no_defs': "",
            'str2': self.basic_definition_string_no_paren,
            'str3': self.basic_hed_string,
            'str4': self.basic_hed_string,
            'str5': self.basic_hed_string + "," + self.expanded_def_string,
            'str6': self.expanded_def_string + "," + self.basic_hed_string,
            'str7': "(" + self.expanded_def_string + "," + self.basic_hed_string + ")",
            'str8': "((" + self.expanded_def_string + "," + self.basic_hed_string + "))",
        }
        expanded_def_strings_with_definition = {
            'str_no_defs': self.basic_definition_string,
            'str2': self.basic_definition_string_no_paren,
            'str3': self.basic_hed_string + "," + self.basic_definition_string,
            'str4': self.basic_definition_string + "," + self.basic_hed_string,
            'str5': self.basic_hed_string + "," + self.expanded_def_string,
            'str6': self.expanded_def_string + "," + self.basic_hed_string,
            'str7': "(" + self.expanded_def_string + "," + self.basic_hed_string + ")",
            'str8': "((" + self.expanded_def_string + "," + self.basic_hed_string + "))",
        }

        self.base_def_validator(basic_def_strings, expanded_def_strings_with_definition,
                                expand_defs=True,
                                shrink_defs=False, remove_definitions=False)
        self.base_def_validator(basic_def_strings, basic_def_strings, 
                                expand_defs=False, shrink_defs=False, remove_definitions=False)
        self.base_def_validator(basic_def_strings, basic_def_strings, 
                                expand_defs=False, shrink_defs=True, remove_definitions=False)
        self.base_def_validator(expanded_def_strings_with_definition, basic_def_strings,
                                expand_defs=False, shrink_defs=True,
                                remove_definitions=False)
        self.base_def_validator(expanded_def_strings_with_definition, expanded_def_strings_with_definition,
                                expand_defs=True, shrink_defs=False,
                                remove_definitions=False)
        self.base_def_validator(basic_def_strings, expanded_def_strings, 
                                expand_defs=True, shrink_defs=False, remove_definitions=True)

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

        self.base_def_validator(basic_def_strings, expanded_def_strings_with_definition, 
                                expand_defs=True, shrink_defs=False,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(basic_def_strings, basic_def_strings, 
                                expand_defs=False, shrink_defs=False,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(basic_def_strings, basic_def_strings, 
                                expand_defs=False, shrink_defs=True,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(expanded_def_strings_with_definition, basic_def_strings, 
                                expand_defs=False, shrink_defs=True,
                                remove_definitions=False, basic_definition_string=self.placeholder_definition_string)

        self.base_def_validator(basic_def_strings, expanded_def_strings, 
                                expand_defs=True, shrink_defs=False,
                                remove_definitions=True, basic_definition_string=self.placeholder_definition_string)


    # todo: finish updating these
    # # special case test
    # def test_changing_tag_then_def_mapping(self):
    #     def_dict = DefinitionDict()
    #     def_string = HedString(self.basic_definition_string)
    #     def_string.convert_to_canonical_forms(None)
    #     def_dict.check_for_definitions(def_string)
    #     def_mapper = DefMapper(def_dict)
    #     validator = HedValidator(self.hed_schema)
    #     hed_ops = [validator, def_mapper]
    #
    #     test_string = HedString(self.label_def_string)
    #     tag = test_string.children[0]
    #     tag.tag = "Organizational-property/" + str(tag)
    #     def_issues = test_string.validate(hed_ops, expand_defs=True)
    #     self.assertFalse(def_issues)
    #     self.assertEqual(test_string.get_as_short(), f"{self.expanded_def_string}")
    #
    #     test_string = HedString(self.label_def_string)
    #     tag = test_string.children[0]
    #     tag.tag = "Organizational-property22/" + str(tag)
    #     def_issues = test_string.validate(hed_ops, expand_defs=True)
    #     self.assertTrue(def_issues)



if __name__ == '__main__':
    unittest.main()
