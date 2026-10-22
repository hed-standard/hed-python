import os
import unittest

from hed import schema
from hed.errors import ErrorContext, ErrorHandler
from hed.models import DefinitionDict, HedString
from hed.validator import DefValidator, HedValidator


class Test(unittest.TestCase):
    basic_hed_string_with_def_first_paren = None

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
        cls.hed_schema = schema.load_schema_version("8.0.0")
        cls.def_contents_string = "(Item/TestDef1,Item/TestDef2)"
        cls.basic_definition_string = f"(Definition/TestDef,{cls.def_contents_string})"
        cls.basic_definition_string_no_paren = f"Definition/TestDef,{cls.def_contents_string}"

        cls.placeholder_definition_contents = "(Acceleration/#,Item/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents})"
        cls.placeholder_definition_string_no_paren = (
            f"Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents}"
        )
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
        test_string.expand_defs()
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
        test_string.expand_defs()
        self.assertEqual(str(test_string), label_def_string_has_invalid_placeholder)
        self.assertTrue(def_issues)

    def test_bad_def_expand(self):
        def_validator = DefValidator()
        def_string = HedString(self.placeholder_definition_string, self.hed_schema)
        def_validator.check_for_definitions(def_string)

        valid_placeholder = HedString(self.placeholder_expanded_def_string, self.hed_schema)
        def_issues = def_validator.validate_def_tags(valid_placeholder)
        self.assertFalse(def_issues)

        invalid_placeholder = HedString(
            "(Def-expand/TestDefPlaceholder/2471,(Acceleration/21,Item/TestDef2))", self.hed_schema
        )
        def_issues = def_validator.validate_def_tags(invalid_placeholder)
        self.assertTrue(bool(def_issues))

    def test_def_expand_contents_in_any_order(self):
        """The tags of a Def-expand group may be in a different order from the definition (issue #1455)."""
        def_validator = DefValidator()
        def_validator.check_for_definitions(HedString(self.basic_definition_string, self.hed_schema))
        def_validator.check_for_definitions(HedString(self.placeholder_definition_string, self.hed_schema))
        def_validator.check_for_definitions(
            HedString("(Definition/TestNested,(Item/TestDef1,(Item/TestDef2,Item/TestDef3)))", self.hed_schema)
        )
        def_validator.check_for_definitions(
            HedString(
                "(Definition/TestSiblings/#,((Item/TestDef1,Acceleration/#),(Item/TestDef2,Item/TestDef3)))",
                self.hed_schema,
            )
        )

        reordered = [
            "(Def-expand/TestDef,(Item/TestDef2,Item/TestDef1))",
            "(Def-expand/TestDef,(item/testdef2,Item/TestDef1))",
            "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef2,Acceleration/2471))",
            "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef2,Acceleration/2471)),Item/BasicTestTag1",
            "(Def-expand/TestNested,((Item/TestDef3,Item/TestDef2),Item/TestDef1))",
            "(Def-expand/TestSiblings/2471,((Item/TestDef3,Item/TestDef2),(Acceleration/2471,Item/TestDef1)))",
        ]
        for hed_string in reordered:
            def_issues = def_validator.validate_def_tags(HedString(hed_string, self.hed_schema))
            self.assertEqual(def_issues, [], hed_string)

        still_invalid = [
            "(Def-expand/TestDef,(Item/TestDef2,Item/TestDef3))",
            "(Def-expand/TestDef,(Item/TestDef2,Item/TestDef1,Item/TestDef1))",
            "(Def-expand/TestDef,(Item/TestDef2,(Item/TestDef1)))",
            "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef2,Acceleration/21))",
            "(Def-expand/TestNested,((Item/TestDef3,Item/TestDef1),Item/TestDef2))",
            "(Def-expand/TestSiblings/2471,((Item/TestDef3,Item/TestDef1),(Acceleration/2471,Item/TestDef2)))",
        ]
        for hed_string in still_invalid:
            def_issues = def_validator.validate_def_tags(HedString(hed_string, self.hed_schema))
            self.assertTrue(def_issues, hed_string)
            self.assertEqual(def_issues[0]["code"], "DEF_EXPAND_INVALID", hed_string)

    def test_def_expand_order_with_released_schema(self):
        """The reproduction from issue #1455 validates in both orders with HED 8.4.0."""
        hed_schema = schema.load_schema_version("8.4.0")
        def_dict = DefinitionDict(
            [
                "(Definition/SlowPresentation/#, (Condition-variable/Presentation, "
                "Visual-presentation, Computer-screen, Temporal-rate/#))"
            ],
            hed_schema,
        )
        for hed_string in [
            "Sensory-event, ((Def-expand/SlowPresentation/1 Hz, (Computer-screen, "
            "Condition-variable/Presentation, Temporal-rate/1 Hz, Visual-presentation)), Onset)",
            "Sensory-event, ((Def-expand/SlowPresentation/1 Hz, (Condition-variable/Presentation, "
            "Visual-presentation, Computer-screen, Temporal-rate/1 Hz)), Onset)",
        ]:
            issues = HedString(hed_string, hed_schema, def_dict=def_dict).validate(allow_placeholders=False)
            self.assertEqual(issues, [], hed_string)

    def test_duplicate_def(self):
        def_dict = DefinitionDict()
        def_string = HedString(self.placeholder_definition_string, self.hed_schema)
        error_handler = ErrorHandler()
        error_handler.push_error_context(ErrorContext.ROW, 5)
        def_dict.check_for_definitions(def_string, error_handler=error_handler)
        self.assertEqual(len(def_dict.issues), 0)
        def_dict2 = DefinitionDict()
        def_dict2.add_definitions("(Definition/testdefplaceholder/#,(Acceleration/#,Item, Red))", self.hed_schema)
        self.assertEqual(len(def_dict2.issues), 0)
        def_dict3 = DefinitionDict([def_dict, def_dict2])
        self.assertEqual(len(def_dict3.issues), 1)

        #
        # def_validator = DefValidator([def_dict, def_dict2])
        # self.assertEqual(len(def_validator.issues), 1)


class TestDefErrors(unittest.TestCase):
    basic_hed_string_with_def_first_paren = None

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
        cls.hed_schema = schema.load_schema_version("8.0.0")
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
        cls.placeholder_definition_string_no_paren = (
            f"Definition/TestDefPlaceholder/#,{cls.placeholder_definition_contents}"
        )
        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Acceleration/2471,Item/TestDef2))"

        cls.placeholder_hed_string_with_def = f"{cls.basic_hed_string},{cls.placeholder_label_def_string}"
        cls.placeholder_hed_string_with_def_first = f"{cls.placeholder_label_def_string},{cls.basic_hed_string}"
        cls.placeholder_hed_string_with_def_first_paren = f"({cls.placeholder_label_def_string},{cls.basic_hed_string})"

    def base_def_validator(
        self,
        test_strings,
        result_strings,
        expand_defs,
        shrink_defs,
        remove_definitions,
        extra_ops=None,
        basic_definition_string=None,
    ):
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
            "str_no_defs": self.basic_definition_string,
            "str2": self.basic_definition_string_no_paren,
            "str3": self.basic_hed_string + "," + self.basic_definition_string,
            "str4": self.basic_definition_string + "," + self.basic_hed_string,
            "str5": self.basic_hed_string_with_def,
            "str6": self.basic_hed_string_with_def_first,
            "str7": self.basic_hed_string_with_def_first_paren,
            "str8": "(" + self.basic_hed_string_with_def_first_paren + ")",
        }
        expanded_def_strings = {
            "str_no_defs": "",
            "str2": self.basic_definition_string_no_paren,
            "str3": self.basic_hed_string,
            "str4": self.basic_hed_string,
            "str5": self.basic_hed_string + "," + self.expanded_def_string,
            "str6": self.expanded_def_string + "," + self.basic_hed_string,
            "str7": "(" + self.expanded_def_string + "," + self.basic_hed_string + ")",
            "str8": "((" + self.expanded_def_string + "," + self.basic_hed_string + "))",
        }
        expanded_def_strings_with_definition = {
            "str_no_defs": self.basic_definition_string,
            "str2": self.basic_definition_string_no_paren,
            "str3": self.basic_hed_string + "," + self.basic_definition_string,
            "str4": self.basic_definition_string + "," + self.basic_hed_string,
            "str5": self.basic_hed_string + "," + self.expanded_def_string,
            "str6": self.expanded_def_string + "," + self.basic_hed_string,
            "str7": "(" + self.expanded_def_string + "," + self.basic_hed_string + ")",
            "str8": "((" + self.expanded_def_string + "," + self.basic_hed_string + "))",
        }

        self.base_def_validator(
            basic_def_strings,
            expanded_def_strings_with_definition,
            expand_defs=True,
            shrink_defs=False,
            remove_definitions=False,
        )
        self.base_def_validator(
            basic_def_strings, basic_def_strings, expand_defs=False, shrink_defs=False, remove_definitions=False
        )
        self.base_def_validator(
            basic_def_strings, basic_def_strings, expand_defs=False, shrink_defs=True, remove_definitions=False
        )
        self.base_def_validator(
            expanded_def_strings_with_definition,
            basic_def_strings,
            expand_defs=False,
            shrink_defs=True,
            remove_definitions=False,
        )
        self.base_def_validator(
            expanded_def_strings_with_definition,
            expanded_def_strings_with_definition,
            expand_defs=True,
            shrink_defs=False,
            remove_definitions=False,
        )
        self.base_def_validator(
            basic_def_strings, expanded_def_strings, expand_defs=True, shrink_defs=False, remove_definitions=True
        )

    def test_expand_def_tags_placeholder(self):
        basic_def_strings = {
            "str_no_defs": self.placeholder_definition_string,
            "str2": self.placeholder_definition_string_no_paren,
            "str3": self.basic_hed_string + "," + self.placeholder_definition_string,
            "str4": self.placeholder_definition_string + "," + self.basic_hed_string,
            "str5": self.placeholder_hed_string_with_def,
            "str6": self.placeholder_hed_string_with_def_first,
            "str7": self.placeholder_hed_string_with_def_first_paren,
        }
        expanded_def_strings = {
            "str_no_defs": "",
            "str2": self.placeholder_definition_string_no_paren,
            "str3": self.basic_hed_string,
            "str4": self.basic_hed_string,
            "str5": self.basic_hed_string + "," + self.placeholder_expanded_def_string,
            "str6": self.placeholder_expanded_def_string + "," + self.basic_hed_string,
            "str7": "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")",
        }
        expanded_def_strings_with_definition = {
            "str_no_defs": self.placeholder_definition_string,
            "str2": self.placeholder_definition_string_no_paren,
            "str3": self.basic_hed_string + "," + self.placeholder_definition_string,
            "str4": self.placeholder_definition_string + "," + self.basic_hed_string,
            "str5": self.basic_hed_string + "," + self.placeholder_expanded_def_string,
            "str6": self.placeholder_expanded_def_string + "," + self.basic_hed_string,
            "str7": "(" + self.placeholder_expanded_def_string + "," + self.basic_hed_string + ")",
        }

        self.base_def_validator(
            basic_def_strings,
            expanded_def_strings_with_definition,
            expand_defs=True,
            shrink_defs=False,
            remove_definitions=False,
            basic_definition_string=self.placeholder_definition_string,
        )

        self.base_def_validator(
            basic_def_strings,
            basic_def_strings,
            expand_defs=False,
            shrink_defs=False,
            remove_definitions=False,
            basic_definition_string=self.placeholder_definition_string,
        )

        self.base_def_validator(
            basic_def_strings,
            basic_def_strings,
            expand_defs=False,
            shrink_defs=True,
            remove_definitions=False,
            basic_definition_string=self.placeholder_definition_string,
        )

        self.base_def_validator(
            expanded_def_strings_with_definition,
            basic_def_strings,
            expand_defs=False,
            shrink_defs=True,
            remove_definitions=False,
            basic_definition_string=self.placeholder_definition_string,
        )

        self.base_def_validator(
            basic_def_strings,
            expanded_def_strings,
            expand_defs=True,
            shrink_defs=False,
            remove_definitions=True,
            basic_definition_string=self.placeholder_definition_string,
        )


class TestDefValueCharacterIndex(unittest.TestCase):
    """A character error in a Def or Def-expand placeholder value is indexed within the displayed tag.

    The validated tag is the definition's placeholder tag with the value substituted (``Label/a?``), so without
    the offset the index pointed into that hidden tag (PR #1442, Copilot round 2).
    """

    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.4.0")
        cls.defs = DefinitionDict("(Definition/Test/#, (Label/#))", cls.hed_schema)
        cls.assertEqual(cls(), cls.defs.issues, [])

    def issues(self, text):
        hed_string = HedString(text, self.hed_schema, def_dict=self.defs)
        validator = HedValidator(self.hed_schema, def_dicts=self.defs)
        return validator.validate(hed_string, allow_placeholders=False)

    def test_def_value_index_is_within_the_def_tag(self):
        issues = self.issues("Def/Test/a?")
        self.assertEqual(len(issues), 1)
        self.assertIn('"?" (U+003F) at index 10 of "Def/Test/a?"', issues[0]["message"])

    def test_def_expand_value_index_is_within_the_def_expand_tag(self):
        issues = self.issues("(Def-expand/Test/a?, (Label/a?))")
        messages = [issue["message"] for issue in issues]
        self.assertEqual(len(messages), 2)
        self.assertTrue(any('at index 17 of "Def-expand/Test/a?"' in message for message in messages), messages)
        self.assertTrue(any('at index 7 of "Label/a?"' in message for message in messages), messages)

    def test_a_plain_tag_is_unchanged(self):
        issues = self.issues("Label/a?")
        self.assertEqual(len(issues), 1)
        self.assertIn('at index 7 of "Label/a?"', issues[0]["message"])


if __name__ == "__main__":
    unittest.main()
