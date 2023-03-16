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

        cls.placeholder_definition_contents = "(Item/TestDef1/#,Item/TestDef2)"
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

        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

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

        invalid_placeholder = HedString("(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/21,Item/TestDef2))", self.hed_schema)
        def_issues = def_validator.validate_def_tags(invalid_placeholder)
        self.assertTrue(bool(def_issues))


    def test_def_no_content(self):

        def_validator = DefValidator()
        def_string = HedString("(Definition/EmptyDef)", self.hed_schema)
        def_validator.check_for_definitions(def_string)

        valid_empty = HedString("Def/EmptyDef", self.hed_schema)
        def_issues = def_validator.validate_def_tags(valid_empty)
        def_issues += def_validator.expand_def_tags(valid_empty)
        self.assertEqual(str(valid_empty), "(Def-expand/EmptyDef)")
        self.assertFalse(def_issues)

        valid_empty = HedString("Def/EmptyDef", self.hed_schema)
        def_issues = def_validator.validate_def_tags(valid_empty)
        self.assertFalse(def_issues)

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

