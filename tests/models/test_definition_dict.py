import unittest
from hed.models.definition_dict import DefinitionDict
from hed.errors import ErrorHandler, DefinitionErrors
from hed.models.hed_string import HedString
from hed import HedTag
from hed import load_schema_version
from tests.validator.test_tag_validator_base import TestHedBase


class TestDefBase(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version("8.0.0")

    def check_def_base(self, test_strings, expected_issues):
        for test_key in test_strings:
            def_dict = DefinitionDict()
            hed_string_obj = HedString(test_strings[test_key], self.hed_schema)
            test_issues = def_dict.check_for_definitions(hed_string_obj)
            expected_params = expected_issues[test_key]
            expected_issue = self.format_errors_fully(ErrorHandler(), hed_string=hed_string_obj,
                                                      params=expected_params)
            # print(test_key)
            # print(test_issues)
            # print(expected_issue)
            self.assertCountEqual(test_issues, expected_issue, HedString(test_strings[test_key]))


class TestDefinitionDict(TestDefBase):
    def_contents_string = "(Item/TestDef1,Item/TestDef2)"
    def_contents_string2 = "(Item/TestDef3,Item/TestDef4)"
    basic_definition_string = f"(Definition/TestDef,{def_contents_string})"
    label_def_string = "def/TestDef"
    expanded_def_string = f"(Def-expand/TestDef,{def_contents_string})"
    basic_hed_string = "Item/BasicTestTag1,Item/BasicTestTag2"
    basic_hed_string_with_def = f"Item/BasicTestTag1,Item/BasicTestTag2,{label_def_string}"

    placeholder_def_contents = "(Age/#,Event)"
    placeholder_def_string = f"(Definition/TestDefPlaceholder/#,{placeholder_def_contents})"

    def test_check_for_definitions(self):
        def_dict = DefinitionDict()
        original_def_count = len(def_dict.defs)
        hed_string_obj = HedString(self.placeholder_def_string, hed_schema=self.hed_schema)
        def_dict.check_for_definitions(hed_string_obj)
        new_def_count = len(def_dict.defs)
        self.assertGreater(new_def_count, original_def_count)

    def test_check_for_definitions_placeholder(self):
        def_dict = DefinitionDict()
        original_def_count = len(def_dict.defs)
        hed_string_obj = HedString(self.placeholder_def_string, hed_schema=self.hed_schema)
        def_dict.check_for_definitions(hed_string_obj)
        new_def_count = len(def_dict.defs)
        self.assertGreater(new_def_count, original_def_count)

    placeholder_invalid_def_contents = "(Age/#,Item/TestDef2/#)"
    placeholder_invalid_def_string = f"(Definition/TestDefPlaceholder/#,{placeholder_invalid_def_contents})"

    def test_definitions(self):
        test_strings = {
            'noGroupTag': "(Definition/InvalidDef0)",
            'placeholderNoGroupTag': "(Definition/InvalidDef1/#)",
            'placeholderWrongSpot': "(Definition/InvalidDef1#)",
            'twoDefTags': f"(Definition/ValidDef1,Definition/InvalidDef2,{self.def_contents_string})",
            'twoGroupTags': f"(Definition/InvalidDef1,{self.def_contents_string},{self.def_contents_string2})",
            'extraOtherTags': "(Definition/InvalidDef1, InvalidContents)",
            'duplicateDef': f"(Definition/Def1, {self.def_contents_string}), (Definition/Def1, {self.def_contents_string})",
            'duplicateDef2': f"(Definition/Def1, {self.def_contents_string}), (Definition/Def1/#, {self.placeholder_def_contents})",
            'defTooManyPlaceholders': self.placeholder_invalid_def_string,
            'invalidPlaceholder': f"(Definition/InvalidDef1/InvalidPlaceholder, {self.def_contents_string})",
            'invalidPlaceholderExtension': f"(Definition/InvalidDef1/this-part-is-not-allowed/#, {self.def_contents_string})",
            'defInGroup': "(Definition/ValidDefName, (Def/ImproperlyPlacedDef))",
            'defExpandInGroup': "(Definition/ValidDefName, (Def-expand/ImproperlyPlacedDef, (ImproperContents)))",
            'doublePoundSignPlaceholder': f"(Definition/InvalidDef/##, {self.placeholder_def_contents})",
            'doublePoundSignDiffPlaceholder': f"(Definition/InvalidDef/#, (Age/##,Item/TestDef2))",
            'placeholdersWrongSpot': f"(Definition/InvalidDef/#, (Age/#,Item/TestDef2))",
        }
        expected_results = {
            'noGroupTag': self.format_error(DefinitionErrors.NO_DEFINITION_CONTENTS,
                                                               "InvalidDef0"),
            'placeholderNoGroupTag': self.format_error(DefinitionErrors.NO_DEFINITION_CONTENTS,"InvalidDef1/#"),
            'placeholderWrongSpot': self.format_error(DefinitionErrors.NO_DEFINITION_CONTENTS,"InvalidDef1#") + self.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                              tag=0, def_name="InvalidDef1#"),
            'twoDefTags': self.format_error(DefinitionErrors.WRONG_NUMBER_TAGS,
                                                    "ValidDef1", ["Definition/InvalidDef2"]),
            'twoGroupTags': self.format_error(DefinitionErrors.WRONG_NUMBER_GROUPS,
                                                      "InvalidDef1",
                                                      [self.def_contents_string, self.def_contents_string2]),
            'extraOtherTags': self.format_error(DefinitionErrors.NO_DEFINITION_CONTENTS, "InvalidDef1")
                              + self.format_error(DefinitionErrors.WRONG_NUMBER_TAGS, "InvalidDef1", ['InvalidContents']),
            'duplicateDef': self.format_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
            'duplicateDef2': self.format_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),

            'defTooManyPlaceholders': self.format_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                "TestDefPlaceholder", expected_count=1,
                                                                tag_list=["Age/#", "Item/TestDef2/#"]),
            'invalidPlaceholderExtension': self.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                     tag=0, def_name="InvalidDef1/this-part-is-not-allowed"),
            'invalidPlaceholder': self.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                            tag=0, def_name="InvalidDef1/InvalidPlaceholder"),
            'defInGroup': self.format_error(DefinitionErrors.DEF_TAG_IN_DEFINITION,
                                                    tag=HedTag("Def/ImproperlyPlacedDef"), def_name="ValidDefName"),
            'defExpandInGroup': self.format_error(DefinitionErrors.DEF_TAG_IN_DEFINITION,
                                                          tag=HedTag("Def-expand/ImproperlyPlacedDef"),
                                                          def_name="ValidDefName"),
            'doublePoundSignPlaceholder': self.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
                                                                     tag=0, def_name="InvalidDef/##"),
            'doublePoundSignDiffPlaceholder': self.format_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                                                                "InvalidDef", expected_count=1, tag_list=['Age/##']),
            'placeholdersWrongSpot': []
        }

        self.check_def_base(test_strings, expected_results)

    def test_expand_defs(self):
        test_strings = {
            1: "Def/TestDefPlaceholder/2471,Event",
            2: "Event,(Def/TestDefPlaceholder/2471,Event)",
            3: "Def-expand/TestDefPlaceholder/2471,(Age/2471,Item/TestDef2),Event",
        }

        expected_results = {
            1: "(Def-expand/TestDefPlaceholder/2471,(Age/2471,Item/TestDef2)),Event",
            2: "Event,((Def-expand/TestDefPlaceholder/2471,(Age/2471,Item/TestDef2)),Event)",
            # this one shouldn't change as it doesn't have a parent
            3: "Def-expand/TestDefPlaceholder/2471,(Age/2471,Item/TestDef2),Event",
        }
        def_dict = DefinitionDict()
        definition_string = "(Definition/TestDefPlaceholder/#,(Age/#,Item/TestDef2))"
        def_dict.check_for_definitions(HedString(definition_string, hed_schema=self.hed_schema))
        for key, test_string in test_strings.items():
            hed_string = HedString(test_string, hed_schema=self.hed_schema, def_dict=def_dict)
            hed_string.expand_defs()
            self.assertEqual(str(hed_string), expected_results[key])

if __name__ == '__main__':
    unittest.main()
