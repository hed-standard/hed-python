import unittest
import os

from hed.util.def_mapper import DefinitionMapper
from hed import schema
from hed.util.def_dict import DefDict
from hed.util import error_reporter
from hed.util.error_types import DefinitionErrors
from hed.util.hed_string import HedString

class TestDefBase(unittest.TestCase):
    schema_file = '../data/HED8.0.0-alpha.1.xml'

    @classmethod
    def setUpClass(cls):
        cls.error_handler = error_reporter.ErrorHandler()
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(hed_xml)

    def check_def_base(self, test_strings, expected_issues):
        for test_key in test_strings:
            def_dict = DefDict(self.hed_schema)
            test_issues = def_dict.check_for_definitions(HedString(test_strings[test_key]))
            expected_issue = expected_issues[test_key]
            self.assertCountEqual(test_issues, expected_issue, HedString(test_strings[test_key]))


class TestDefDict(TestDefBase):
    def_contents_string = "(Item/TestDef1,Item/TestDef2)"
    def_contents_string2 = "(Item/TestDef3,Item/TestDef4)"
    basic_def_string = f"(Definition/TestDef,{def_contents_string})"
    label_def_string = f"def/TestDef"
    expanded_def_string = f"(defexp/TestDef,{def_contents_string})"
    basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
    basic_hed_string_with_def = f"Item/BasicTestTag1,Item/BasicTestTag2,{label_def_string}"

    placeholder_def_contents = "(Item/TestDef1/#,Item/TestDef2)"
    placehodler_def_string = f"Definition/TestDefPlaceholder/#,{placeholder_def_contents}"

    def test_check_for_definitions(self):
        def_dict = DefDict(hed_schema=self.hed_schema)
        original_def_count = len(def_dict._defs)
        def_dict.check_for_definitions(HedString(self.basic_def_string))
        new_def_count = len(def_dict._defs)
        self.assertGreater(new_def_count, original_def_count)

    def test_check_for_definitions_placeholder(self):
        def_dict = DefDict(hed_schema=self.hed_schema)
        original_def_count = len(def_dict._defs)
        def_dict.check_for_definitions(HedString(self.placehodler_def_string))
        new_def_count = len(def_dict._defs)
        self.assertGreater(new_def_count, original_def_count)

    placeholder_invalid_def_contents = "(Item/TestDef1/#,Item/TestDef2/#)"
    placeholder_invalid_def_string = f"(Definition/TestDefPlaceholder/#,{placeholder_invalid_def_contents})"

    def test_definitions(self):
        test_strings = {
            'noGroupTag': "Definition/ValidDef1",
            'placeholderNoGroupTag': "Definition/InvalidDef1/#",
            'placeholderWrongSpot': "Definition/InvalidDef1#",
            'twoDefTags': f"Definition/ValidDef1,Definition/InvalidDef2,{self.def_contents_string}",
            'twoGroupTags': f"Definition/InvalidDef1,{self.def_contents_string},{self.def_contents_string2}",
            'duplicateDef': f"(Definition/Def1), (Definition/Def1, {self.def_contents_string})",
            'duplicateDef2': f"(Definition/Def1), (Definition/Def1/#, {self.placeholder_def_contents})",
            'defAlreadyTagInSchema': f"Definition/Item",
            'defTooManyPlaceholders': self.placeholder_invalid_def_string,
            'invalidPlaceholder': f"Definition/InvalidDef1/InvalidPlaceholder",
            'invalidPlaceholderExtension': f"Definition/InvalidDef1/thispartisnotallowed/#",
        }
        expected_results = {
            'noGroupTag': [],
            'placeholderNoGroupTag': self.error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS, "InvalidDef1",
                                                                                 [], expected_count=1),
            'placeholderWrongSpot': self.error_handler.format_definition_error(DefinitionErrors.INVALID_DEF_EXTENSION, "InvalidDef1#"),
            'twoDefTags': self.error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_DEF_TAGS, "ValidDef1", ["Definition/InvalidDef2"]),
            'twoGroupTags': self.error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_GROUP_TAGS, "InvalidDef1", [self.def_contents_string, self.def_contents_string2]),
            'duplicateDef': self.error_handler.format_definition_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
            'duplicateDef2': self.error_handler.format_definition_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
            'defAlreadyTagInSchema': self.error_handler.format_definition_error(DefinitionErrors.TAG_IN_SCHEMA, "Item"),
            'defTooManyPlaceholders': self.error_handler.format_definition_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS, "TestDefPlaceholder",
                                                                                 ["Item/TestDef1/#", "Item/TestDef2/#"], expected_count=1),
            'invalidPlaceholderExtension': self.error_handler.format_definition_error(DefinitionErrors.INVALID_DEF_EXTENSION, "InvalidDef1/thispartisnotallowed"),
            'invalidPlaceholder': self.error_handler.format_definition_error(DefinitionErrors.INVALID_DEF_EXTENSION, "InvalidDef1/InvalidPlaceholder"),
        }

        self.check_def_base(test_strings, expected_results)

    def test__check_tag_starts_with(self):
        possible_tag_list = ["definition", "informational/definition", "attribute/informational/definition"]

        test_tags = ["Definition/TempTestDef", "Informational/Definition/TempTestDef",
                     "Attribute/Informational/Definition/TempTestDef"]

        for tag in test_tags:
            result = DefinitionMapper._check_tag_starts_with(tag, possible_tag_list)
            self.assertTrue(result)



if __name__ == '__main__':
    unittest.main()





