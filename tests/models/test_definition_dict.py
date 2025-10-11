import unittest
from hed.models.definition_dict import DefinitionDict
from hed.errors import ErrorHandler, DefinitionErrors, ValidationErrors, ErrorSeverity
from hed.models.hed_string import HedString
from hed import HedTag
from hed import load_schema_version
from tests.validator.test_tag_validator_base import TestHedBase


class TestDefBase(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version("8.4.0")

    def check_def_base(self, test_strings, expected_issues):
        for test_key in test_strings:
            def_dict = DefinitionDict()
            def_dict.add_definitions("(Definition/OkayDef, (White))", self.hed_schema)
            hed_string_obj = HedString(test_strings[test_key], self.hed_schema)
            test_issues = def_dict.check_for_definitions(hed_string_obj)
            issues = [issue for issue in test_issues if issue["severity"] < ErrorSeverity.WARNING]
            expected_params = expected_issues[test_key]
            expected_issue = self.format_errors_fully(ErrorHandler(), hed_string=hed_string_obj, params=expected_params)
            self.assertCountEqual(issues, expected_issue, HedString(test_strings[test_key], self.hed_schema))


class TestDefinitionDict(TestDefBase):
    def_contents_string = "(Item,Red)"
    def_contents_string2 = "(Property, Blue)"
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

    placeholder_invalid_def_contents = "(Age/#,Item-count/#)"
    placeholder_invalid_def_string = f"(Definition/TestDefPlaceholder/#,{placeholder_invalid_def_contents})"

    def test_definitions(self):
        test_strings = {
            "noGroupTag": "(Definition/InvalidDef0)",
            "placeholderNoGroupTag": "(Definition/InvalidDef1/#)",
            "placeholderWrongSpot": "(Definition/InvalidDef1#)",
            "twoDefTags": f"(Definition/InvalidDef1,Definition/InvalidDef2,{self.def_contents_string})",
            "twoGroupTags": f"(Definition/InvalidDef1,{self.def_contents_string},{self.def_contents_string2})",
            "extraValidTags": "(Definition/InvalidDefA, Red, Blue)",
            "extraOtherTags": "(Definition/InvalidDef1, Black)",
            "duplicateDef": (f"(Definition/Def1, {self.def_contents_string}), " f"(Definition/Def1, (Green))"),
            "duplicateDef2": (
                f"(Definition/Def1, {self.def_contents_string}), " f"(Definition/Def1/#, {self.placeholder_def_contents})"
            ),
            "defTooManyPlaceholders": self.placeholder_invalid_def_string,
            "invalidPlaceholder": f"(Definition/InvalidDef1/InvalidPlaceholder, {self.def_contents_string})",
            "invalidPlaceholderExtension": f"(Definition/InvalidDef1/this-part-is-not-allowed/#, {self.def_contents_string})",
            "defInGroup": "(Definition/ValidDefName, (Def/OkayDef))",
            "defExpandInGroup": "(Definition/ValidDefName, (Def-expand/OkayDef, (White)))",
            "doublePoundSignPlaceholder": f"(Definition/InvalidDef/##, {self.placeholder_def_contents})",
            "doublePoundSignDiffPlaceholder": "(Definition/InvalidDef/#, (Age/##,Item/TestDef2))",
            "placeholdersWrongSpot": "(Definition/InvalidDef/#, (Age/#,Item/TestDef2))",
        }
        expected_results = {
            "noGroupTag": [],
            "placeholderNoGroupTag": self.format_error(DefinitionErrors.NO_DEFINITION_CONTENTS, "InvalidDef1/#"),
            "placeholderWrongSpot": self.format_error(DefinitionErrors.NO_DEFINITION_CONTENTS, "InvalidDef1#")
            + self.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION, tag=0, def_name="InvalidDef1#"),
            "twoDefTags": self.format_error(
                ValidationErrors.HED_RESERVED_TAG_REPEATED,
                "Definition/InvalidDef2",
                "(Definition/InvalidDef1,Definition/InvalidDef2,(Item,Red))",
            ),
            "twoGroupTags": self.format_error(
                ValidationErrors.HED_RESERVED_TAG_GROUP_ERROR,
                "(Definition/InvalidDef1,(Item,Red),(Property,Blue))",
                2,
                ["Definition/InvalidDef1"],
            ),
            "extraValidTags": self.format_error(
                ValidationErrors.HED_TAGS_NOT_ALLOWED, "Red", "(Definition/InvalidDefA,Red,Blue)"
            ),
            "extraOtherTags": self.format_error(
                ValidationErrors.HED_TAGS_NOT_ALLOWED, "Black", "(Definition/InvalidDef1,Black)"
            ),
            "duplicateDef": self.format_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
            "duplicateDef2": self.format_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
            "defTooManyPlaceholders": self.format_error(
                DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
                "TestDefPlaceholder",
                expected_count=1,
                tag_list=["Age/#", "Item-count/#"],
            ),
            "invalidPlaceholderExtension": self.format_error(
                ValidationErrors.INVALID_VALUE_CLASS_CHARACTER,
                "Definition/InvalidDef1/this-part-is-not-allowed/#",
                "/",
                value_class="nameClass",
            ),
            "invalidPlaceholder": self.format_error(
                ValidationErrors.INVALID_VALUE_CLASS_CHARACTER,
                "Definition/InvalidDef1/InvalidPlaceholder",
                "/",
                value_class="nameClass",
            ),
            "defInGroup": self.format_error(
                DefinitionErrors.DEF_TAG_IN_DEFINITION, tag=HedTag("Def/OkayDef", self.hed_schema), def_name="ValidDefName"
            ),
            "defExpandInGroup": self.format_error(
                ValidationErrors.HED_TAGS_NOT_ALLOWED,
                tag=HedTag("Definition/ValidDefName", self.hed_schema),
                group="(Definition/ValidDefName,(Def-expand/OkayDef,(White)))",
            ),
            "doublePoundSignPlaceholder": self.format_error(
                DefinitionErrors.INVALID_DEFINITION_EXTENSION, tag=0, def_name="InvalidDef/##"
            ),
            "doublePoundSignDiffPlaceholder": self.format_error(
                DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS, "InvalidDef", expected_count=1, tag_list=["Age/##"]
            ),
            "placeholdersWrongSpot": [],
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

    def test_altering_definition_contents(self):
        def_dict = DefinitionDict("(Definition/DefName, (Event, Action))", self.hed_schema)
        hed_string1 = HedString("Def/DefName", self.hed_schema, def_dict)
        hed_string2 = HedString("Def/DefName", self.hed_schema, def_dict)
        hed_string1.expand_defs()
        hed_string2.expand_defs()
        hed_string1.remove([hed_string1.get_all_tags()[2]])

        self.assertNotEqual(hed_string1, hed_string2)

    def test_add_definition(self):
        # Bad input string
        def_dict = DefinitionDict()
        def_dict.add_definitions("(Definition/testdefplaceholder,(Acceleration/#,Item/TestDef2,Red))", self.hed_schema)
        self.assertEqual(len(def_dict.issues), 2)
        errors = [issue for issue in def_dict.issues if issue["severity"] < ErrorSeverity.WARNING]
        self.assertEqual(len(errors), 1)
        self.assertEqual(len(def_dict.defs), 0)

        # Good input string
        def_dict2 = DefinitionDict()
        def_dict2.add_definitions("(Definition/testdefplaceholder/#,(Acceleration/#,Item/TestDef2, Red))", self.hed_schema)
        self.assertEqual(len(def_dict2.issues), 1)
        self.assertEqual(len(def_dict2.defs), 1)


if __name__ == "__main__":
    unittest.main()
