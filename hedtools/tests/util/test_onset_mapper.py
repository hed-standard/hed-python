import unittest
import os

from hed.models.def_mapper import DefinitionMapper
from hed.models.onset_mapper import OnsetMapper
from hed import schema
from hed.models.def_dict import DefDict
from hed.models.hed_string import HedString
from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import OnsetErrors, ErrorContext
from tests.validator.test_tag_validator_base import TestHedBase


class Test(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "legacy_xml/HED8.0.0-alpha.2.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.placeholder_label_def_string = f"def/TestDefPlaceholder/2471"
        cls.placeholder_def_contents = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents})"
        cls.placeholder_expanded_def_string = f"(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

        cls.label_def_string = f"def/TestDefNormal"
        cls.def_contents = "(Item/TestDef1,Item/TestDef2)"
        cls.definition_string = f"(Definition/TestDefNormal,{cls.def_contents})"
        cls.expanded_def_string = f"(Def-expand/TestDefNormal,(Item/TestDef1/2471,Item/TestDef2))"

        cls.placeholder_label_def_string2 = f"def/TestDefPlaceholder/123"
        cls.placeholder_def_contents2 = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_definition_string2 = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents2})"
        cls.placeholder_expanded_def_string2 = f"(Def-expand/TestDefPlaceholder/123,(Item/TestDef1/123,Item/TestDef2))"

    def _test_issues_base(self, test_strings, test_issues, test_context, onset_mapper):
        for string, expected_params, context in zip(test_strings, test_issues, test_context):
            test_string = HedString(string)
            error_handler = ErrorHandler()
            error_handler.push_error_context(ErrorContext.HED_STRING, test_string, increment_depth_after=False)
            onset_issues = test_string.validate(onset_mapper, expand_defs=True)
            # print(str(onset_issues))
            issues = self.really_format_errors(error_handler, hed_string=test_string, params=expected_params)
            error_handler.pop_error_context()
            self.assertEqual(len(onset_mapper._onsets), context)
            self.assertCountEqual(onset_issues, issues)

    def test_basic_onset_errors(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)

        test_strings = [
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string}, Onset, (Event), (Event))",
            f"({self.placeholder_label_def_string}, Onset, (Event))",
            "(Onset)",
            f"({self.placeholder_label_def_string}, def/InvalidDef, Onset, (Event))",
            f"(def/TestDefNormal, Onset)",
            f"(def/TestDefPlaceholder, Onset)"
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
            1
        ]
        # count of issues the line generates
        test_issues = [
            [],
            [],
            self.format_error_but_not_really(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            self.format_error_but_not_really(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0, tag_list=['def/TestDefPlaceholder/2471', 'Onset', '(Event)', '(Event)']),
            [],
            self.format_error_but_not_really(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, tag=0),
            self.format_error_but_not_really(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0, tag_list= ['def/InvalidDef']),
            self.format_error_but_not_really(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error_but_not_really(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True)
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, onset_mapper)

    def test_basic_onset_errors_expanded(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_string = HedString(self.definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)

        test_strings = [
            f"({self.placeholder_expanded_def_string},Onset)",
            f"({self.placeholder_expanded_def_string},Offset)",
            f"({self.placeholder_expanded_def_string},Offset)",
            f"({self.placeholder_expanded_def_string}, Onset, (Event), (Event))",
            f"({self.placeholder_expanded_def_string}, Onset, (Event))",
            "(Onset)",
            f"({self.placeholder_expanded_def_string}, def/InvalidDef, Onset, (Event))",
            f"(def/TestDefInvalid, Onset)",
            f"(def/TestDefPlaceholder, Onset)",
            f"(def/TestDefNormal/InvalidPlaceholder, Onset)"
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
            self.format_error_but_not_really(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            self.format_error_but_not_really(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0, tag_list=[self.placeholder_expanded_def_string, 'Onset', '(Event)', '(Event)']),
            [],
            self.format_error_but_not_really(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, tag=0),
            self.format_error_but_not_really(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0, tag_list= ['def/InvalidDef']),
            self.format_error_but_not_really(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error_but_not_really(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True)
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, onset_mapper)

    def test_test_interleving_onset_offset(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_string = HedString(self.definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)

        test_strings = [
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string2},Onset)",
            f"Event",
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
            self.format_error_but_not_really(OnsetErrors.OFFSET_BEFORE_ONSET, tag=0),
            [],
            [],
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, onset_mapper)

    def test_onset_with_defs_in_them(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)

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

        self._test_issues_base(test_strings, test_issues, expected_context, onset_mapper)

if __name__ == '__main__':
    unittest.main()





