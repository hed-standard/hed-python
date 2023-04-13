import unittest

from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString
from hed.schema.hed_schema_io import load_schema_version


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.def1 = HedString('(Condition-variable/Blech, Red, Blue, Description/This is a description)')
        hed_schema = load_schema_version('8.1.0')
        cls.def2 = HedString('(Condition-variable/Blech, Red, Blue, Description/This is a description)',
                             hed_schema=hed_schema)
        cls.def3 = HedString('(Condition-variable/Blech, Red, Label/#, Blue, Description/This is a description)')
        cls.def4 = HedString('(Condition-variable/Blech, Red, Label/#, Blue, Description/This is a description)',
                             hed_schema=hed_schema)
        cls.hed_schema = hed_schema

    # def test_constructor(self):
    #     def_entry1 = DefinitionEntry('Def1', self.def1, False, None)
    #     self.assertIsInstance(def_entry1, DefinitionEntry)
    #     self.assertIn('Condition-variable/Blech', def_entry1.tag_dict)
    #     def_entry2 = DefinitionEntry('Def2', self.def2, False, None)
    #     self.assertIsInstance(def_entry2, DefinitionEntry)
    #     self.assertNotIn('Condition-variable/Blech', def_entry2.tag_dict)
    #     def_entry3 = DefinitionEntry('Def3', self.def3, False, None)
    #     self.assertIsInstance(def_entry3, DefinitionEntry)
    #     self.assertIn('Condition-variable/Blech', def_entry3.tag_dict)
    #     def_entry4 = DefinitionEntry('Def4', self.def4, False, None)
    #     self.assertIsInstance(def_entry4, DefinitionEntry)
    #     self.assertNotIn('Condition-variable/Blech', def_entry4.tag_dict)
    #     def_entry3a = DefinitionEntry('Def3a', self.def3, True, None)
    #     self.assertIsInstance(def_entry3a, DefinitionEntry)
    #     self.assertIn('Condition-variable/Blech', def_entry3a.tag_dict)
    #     def_entry4a = DefinitionEntry('Def4a', self.def4, True, None)
    #     self.assertIsInstance(def_entry4a, DefinitionEntry)
    #     self.assertNotIn('Condition-variable/Blech', def_entry4a.tag_dict)

    def test_get_definition(self):
        def_entry1 = DefinitionEntry('Def1', self.def1, False, None)
        str1 = HedString("Green, Def/Def1, Blue")
        ret1, ret1 = def_entry1.get_definition(str1)
        def_entry1a = DefinitionEntry('Def1', self.def3, False, None)
        str1a = HedString("Green, Def/Def1, Blue", hed_schema=self.hed_schema)
        ret3, ret3 = def_entry1a.get_definition(str1a)
        def_entry1b = DefinitionEntry('Def1', self.def4, True, None)
        str2b = HedString("Green, Def/Def1, Blue", hed_schema=self.hed_schema)
        # self.assertIn('Condition-variable/Blech', def_entry1.tag_dict)
        # def_entry2 = DefinitionEntry('Def2', self.def2, False, None)
        # self.assertIsInstance(def_entry2, DefinitionEntry)
        # self.assertNotIn('Condition-variable/Blech', def_entry2.tag_dict)
        # def_entry3 = DefinitionEntry('Def3', self.def3, False, None)
        # self.assertIsInstance(def_entry3, DefinitionEntry)
        # self.assertIn('Condition-variable/Blech', def_entry3.tag_dict)
        # def_entry4 = DefinitionEntry('Def4', self.def4, False, None)
        # self.assertIsInstance(def_entry4, DefinitionEntry)
        # self.assertNotIn('Condition-variable/Blech', def_entry4.tag_dict)
        # def_entry3a = DefinitionEntry('Def3a', self.def3, True, None)
        # self.assertIsInstance(def_entry3a, DefinitionEntry)
        # self.assertIn('Condition-variable/Blech', def_entry3a.tag_dict)
        # def_entry4a = DefinitionEntry('Def4a', self.def4, True, None)
        # self.assertIsInstance(def_entry4a, DefinitionEntry)
        # self.assertNotIn('Condition-variable/Blech', def_entry4a.tag_dict)

    # def test_check_for_definitions_placeholder(self):
    #     def_dict = DefinitionDict()
    #     original_def_count = len(def_dict.defs)
    #     hed_string_obj = HedString(self.placeholder_def_string)
    #     hed_string_obj.validate(def_dict)
    #     new_def_count = len(def_dict.defs)
    #     self.assertGreater(new_def_count, original_def_count)
    #
    # placeholder_invalid_def_contents = "(Age/#,Item/TestDef2/#)"
    # placeholder_invalid_def_string = f"(Definition/TestDefPlaceholder/#,{placeholder_invalid_def_contents})"
    #
    # def test_definitions(self):
    #     test_strings = {
    #         'noGroupTag': "(Definition/ValidDef1)",
    #         'placeholderNoGroupTag': "(Definition/InvalidDef1/#)",
    #         'placeholderWrongSpot': "(Definition/InvalidDef1#)",
    #         'twoDefTags': f"(Definition/ValidDef1,Definition/InvalidDef2,{self.def_contents_string})",
    #         'twoGroupTags': f"(Definition/InvalidDef1,{self.def_contents_string},{self.def_contents_string2})",
    #         'extraOtherTags': "(Definition/InvalidDef1, InvalidContents)",
    #         'duplicateDef': f"(Definition/Def1), (Definition/Def1, {self.def_contents_string})",
    #         'duplicateDef2': f"(Definition/Def1), (Definition/Def1/#, {self.placeholder_def_contents})",
    #         'defAlreadyTagInSchema': "(Definition/Item)",
    #         'defTooManyPlaceholders': self.placeholder_invalid_def_string,
    #         'invalidPlaceholder': "(Definition/InvalidDef1/InvalidPlaceholder)",
    #         'invalidPlaceholderExtension': "(Definition/InvalidDef1/this-part-is-not-allowed/#)",
    #         'defInGroup': "(Definition/ValidDefName, (Def/ImproperlyPlacedDef))",
    #         'defExpandInGroup': "(Definition/ValidDefName, (Def-expand/ImproperlyPlacedDef, (ImproperContents)))"
    #     }
    #     expected_results = {
    #         'noGroupTag': [],
    #         'placeholderNoGroupTag': ErrorHandler.format_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
    #                                                            "InvalidDef1", expected_count=1, tag_list=[]),
    #         'placeholderWrongSpot': ErrorHandler.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
    #                                                           "InvalidDef1#"),
    #         'twoDefTags': ErrorHandler.format_error(DefinitionErrors.WRONG_NUMBER_GROUPS,
    #                                                 "ValidDef1", ["Definition/InvalidDef2"]),
    #         'twoGroupTags': ErrorHandler.format_error(DefinitionErrors.WRONG_NUMBER_GROUPS,
    #                                                   "InvalidDef1",
    #                                                   [self.def_contents_string, self.def_contents_string2]),
    #         'extraOtherTags': ErrorHandler.format_error(DefinitionErrors.WRONG_NUMBER_GROUPS, "InvalidDef1",
    #                                                     ['InvalidContents']),
    #         'duplicateDef': ErrorHandler.format_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
    #         'duplicateDef2': ErrorHandler.format_error(DefinitionErrors.DUPLICATE_DEFINITION, "Def1"),
    #         # This is not an error since re-used terms are checked elsewhere.
    #         'defAlreadyTagInSchema': [],
    #         'defTooManyPlaceholders': ErrorHandler.format_error(DefinitionErrors.WRONG_NUMBER_PLACEHOLDER_TAGS,
    #                                                             "TestDefPlaceholder", expected_count=1,
    #                                                             tag_list=["Age/#", "Item/TestDef2/#"]),
    #         'invalidPlaceholderExtension': ErrorHandler.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
    #                                                                  "InvalidDef1/this-part-is-not-allowed"),
    #         'invalidPlaceholder': ErrorHandler.format_error(DefinitionErrors.INVALID_DEFINITION_EXTENSION,
    #                                                         "InvalidDef1/InvalidPlaceholder"),
    #         'defInGroup': ErrorHandler.format_error(DefinitionErrors.DEF_TAG_IN_DEFINITION,
    #                                                 tag=HedTag("Def/ImproperlyPlacedDef"), def_name="ValidDefName"),
    #         'defExpandInGroup': ErrorHandler.format_error(DefinitionErrors.DEF_TAG_IN_DEFINITION,
    #                                                       tag=HedTag("Def-expand/ImproperlyPlacedDef"),
    #                                                       def_name="ValidDefName")
    #     }
    #
    #     self.check_def_base(test_strings, expected_results)


if __name__ == '__main__':
    unittest.main()
