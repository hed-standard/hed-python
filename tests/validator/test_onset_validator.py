import copy
import unittest
import os

from hed.errors import ErrorHandler, OnsetErrors, ErrorContext, ValidationErrors
from hed.models import HedString, DefinitionDict
from hed import schema
from hed.validator import HedValidator, OnsetValidator

from tests.validator.test_tag_validator_base import TestHedBase


# Todo: Add test case for Onset/Value and Offset/Value.  Make sure they bomb.
class Test(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "schema_tests/HED8.0.0.mediawiki")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.placeholder_label_def_string = "Def/TestDefPlaceholder/2471"
        cls.placeholder_def_contents = "(Action/TestDef1/#,Action/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents})"
        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Action/TestDef1/2471,Action/TestDef2))"

        cls.label_def_string = "Def/TestDefNormal"
        cls.def_contents = "(Action/TestDef1,Action/TestDef2)"
        cls.definition_string = f"(Definition/TestDefNormal,{cls.def_contents})"
        cls.expanded_def_string = "(Def-expand/TestDefNormal,(Action/TestDef1/2471,Action/TestDef2))"

        cls.placeholder_label_def_string2 = "Def/TestDefPlaceholder/123"
        cls.placeholder_def_contents2 = "(Action/TestDef1/#,Action/TestDef2)"
        cls.placeholder_definition_string2 = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents2})"
        cls.placeholder_expanded_def_string2 = "(Def-expand/TestDefPlaceholder/123,(Action/TestDef1/123,Action/TestDef2))"

        cls.def_dict_placeholder = DefinitionDict()
        def_string = HedString(cls.placeholder_definition_string, hed_schema=cls.hed_schema)
        cls.def_dict_placeholder.check_for_definitions(def_string)
        cls.def_dict_both = copy.deepcopy(cls.def_dict_placeholder)
        def_string = HedString(cls.definition_string, hed_schema=cls.hed_schema)
        cls.def_dict_both.check_for_definitions(def_string)


    def _test_issues_base(self, test_strings, test_issues, test_context, placeholder_def_only):
        if placeholder_def_only:
            validator = OnsetValidator(self.def_dict_placeholder)
        else:
            validator = OnsetValidator(self.def_dict_both)
        for string, expected_params, context in zip(test_strings, test_issues, test_context):
            test_string = HedString(string, self.hed_schema)
            error_handler = ErrorHandler()
            error_handler.push_error_context(ErrorContext.HED_STRING, test_string)

            onset_issues = []
            onset_issues += validator.validate_onset_offset(test_string)

            error_handler.add_context_and_filter(onset_issues)
            test_string.shrink_defs()
            issues = self.format_errors_fully(error_handler, hed_string=test_string, params=expected_params)
            # print(str(onset_issues))
            # print(str(issues))
            error_handler.pop_error_context()
            self.assertEqual(len(validator._onsets), context)
            self.assertCountEqual(onset_issues, issues)

    def _test_issues_no_context(self, test_strings, test_issues):
        hed_validator = HedValidator(self.hed_schema, self.def_dict_both)
        for string, expected_params in zip(test_strings, test_issues):
            test_string = HedString(string)
            error_handler = ErrorHandler(check_for_warnings=False)
            error_handler.push_error_context(ErrorContext.HED_STRING, test_string)
            onset_issues = hed_validator.validate(test_string, False)
            error_handler.add_context_and_filter(onset_issues)
            issues = self.format_errors_fully(error_handler, hed_string=test_string, params=expected_params)
            # print(str(onset_issues))
            # print(str(issues))
            error_handler.pop_error_context()
            self.assertCountEqual(onset_issues, issues)

    def test_basic_onset_errors(self):
        test_strings = [
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string}, Onset, (Event), (Event))",
            f"({self.placeholder_label_def_string}, Onset, (Event))",
            "(Onset)",
            f"({self.placeholder_label_def_string}, Def/InvalidDef, Onset, (Event))",
            "(Def/TestDefInvalid, Onset)",
            "(Def/TestDefPlaceholder, Onset)",
            f"({self.placeholder_label_def_string}, Offset, (Event))"
        ]
        # count of how many onset names are in the mapper after the line is run
        expected_context = [
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            1
        ]
        # count of issues the line generates
        test_issues = [
            [],
            [],
            self.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=['Def/TestDefPlaceholder/2471', 'Onset', '(Event)', '(Event)']),
            [],
            self.format_error(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, tag=0),
            self.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0, tag_list=['Def/InvalidDef']),
            self.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=[self.placeholder_label_def_string, 'Offset', '(Event)']),
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, placeholder_def_only=True)

    def test_basic_onset_errors_with_def_mapper(self):
        test_strings = [
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string}, Onset, (Event), (Event))",
            f"({self.placeholder_label_def_string}, Onset, (Event))",
            "(Onset)",
            f"({self.placeholder_label_def_string}, Def/TestDefPlaceholder/2, Onset, (Event))",
            "(Def/TestDefInvalid, Onset)",
            "(Def/TestDefPlaceholder, Onset)",
            f"({self.placeholder_label_def_string}, Offset, (Event))"
        ]
        # count of how many onset names are in the mapper after the line is run
        expected_context = [
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            1
        ]
        # count of issues the line generates
        test_issues = [
            [],
            [],
            self.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=[self.placeholder_label_def_string, 'Onset', '(Event)', '(Event)']),
            [],
            self.format_error(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, tag=0),
            self.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0,
                              tag_list=['Def/TestDefPlaceholder/2']),
            self.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=[self.placeholder_label_def_string, 'Offset', '(Event)']),
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, placeholder_def_only=True)

    def test_basic_onset_errors_expanded(self):
        test_strings = [
            f"({self.placeholder_expanded_def_string},Onset)",
            f"({self.placeholder_expanded_def_string},Offset)",
            f"({self.placeholder_expanded_def_string},Offset)",
            f"({self.placeholder_expanded_def_string}, Onset, (Event), (Event))",
            f"({self.placeholder_expanded_def_string}, Onset, (Event))",
            "(Onset)",
            f"({self.placeholder_expanded_def_string}, Def/InvalidDef, Onset, (Event))",
            "(Def/TestDefInvalid, Onset)",
            "(Def/TestDefPlaceholder, Onset)",
            "(Def/TestDefNormal/InvalidPlaceholder, Onset)"
        ]
        # count of how many onset names are in the mapper after the line is run
        expected_context = [
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
            1,
            1
        ]
        # count of issues the line generates
        test_issues = [
            [],
            [],
            self.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=[self.placeholder_expanded_def_string, 'Onset', '(Event)', '(Event)']),
            [],
            self.format_error(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, tag=0),
            self.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0, tag_list=['Def/InvalidDef']),
            self.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=False)
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, placeholder_def_only=False)

    def test_test_interleaving_onset_offset(self):
        test_strings = [
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string2},Onset)",
            "Event",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.label_def_string}, Onset)",
            f"({self.placeholder_label_def_string2},Offset)",
        ]
        # count of how many onset names are in the mapper after the line is run
        expected_context = [
            1,
            2,
            2,
            1,
            1,
            2,
            1,
        ]
        # count of issues the line generates
        test_issues = [
            [],
            [],
            [],
            [],
            self.format_error(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            [],
            [],
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, placeholder_def_only=False)

    def test_onset_with_defs_in_them(self):
        test_strings = [
            f"({self.placeholder_label_def_string},Onset, ({self.label_def_string}))",
        ]
        # count of how many onset names are in the mapper after the line is run
        expected_context = [
            1,
        ]
        # count of issues the line generates
        test_issues = [
            []
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, placeholder_def_only=True)

    def test_onset_multiple_or_misplaced_errors(self):
        test_strings = [
            f"{self.placeholder_label_def_string},Onset",
            f"({self.placeholder_label_def_string},Onset, Onset)",
            f"({self.placeholder_label_def_string},Onset, Offset)",
        ]
        test_issues = [
            self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG, tag=1),
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=2, def_tag="Def/TestDefPlaceholder/2471"),
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=2, def_tag="Def/TestDefPlaceholder/2471"),
        ]

        self._test_issues_no_context(test_strings, test_issues)

    def test_onset_two_in_one_line(self):
        test_strings = [
            f"({self.placeholder_label_def_string},Onset), ({self.placeholder_label_def_string2},Onset)",
            f"({self.placeholder_label_def_string2},Offset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string},Offset), ({self.placeholder_label_def_string2},Onset)",
            f"({self.placeholder_label_def_string},Onset), ({self.placeholder_label_def_string},Onset)",
        ]
        # count of how many onset names are in the mapper after the line is run
        expected_context = [
            2,
            1,
            0,
            1,
            1,
            2
        ]
        # count of issues the line generates
        test_issues = [
            [],
            [],
            [],
            [],
            [],
            []
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, placeholder_def_only=False)


if __name__ == '__main__':
    unittest.main()
