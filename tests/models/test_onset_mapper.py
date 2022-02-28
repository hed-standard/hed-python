import unittest
import os

from hed.errors import ErrorHandler, OnsetErrors, ErrorContext, ValidationErrors
from hed.models import DefinitionMapper, HedString, OnsetMapper, DefDict
from hed import schema
from hed.validator import HedValidator

from tests.validator.test_tag_validator_base import TestHedBase


# Todo: Add test case for Onset/Value and Offset/Value.  Make sure they bomb.
class Test(TestHedBase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "hed_pairs/HED8.0.0.mediawiki")
        cls.hed_schema = schema.load_schema(hed_xml_file)
        cls.placeholder_label_def_string = "def/TestDefPlaceholder/2471"
        cls.placeholder_def_contents = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_definition_string = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents})"
        cls.placeholder_expanded_def_string = "(Def-expand/TestDefPlaceholder/2471,(Item/TestDef1/2471,Item/TestDef2))"

        cls.label_def_string = "def/TestDefNormal"
        cls.def_contents = "(Item/TestDef1,Item/TestDef2)"
        cls.definition_string = f"(Definition/TestDefNormal,{cls.def_contents})"
        cls.expanded_def_string = "(Def-expand/TestDefNormal,(Item/TestDef1/2471,Item/TestDef2))"

        cls.placeholder_label_def_string2 = "def/TestDefPlaceholder/123"
        cls.placeholder_def_contents2 = "(Item/TestDef1/#,Item/TestDef2)"
        cls.placeholder_definition_string2 = f"(Definition/TestDefPlaceholder/#,{cls.placeholder_def_contents2})"
        cls.placeholder_expanded_def_string2 = "(Def-expand/TestDefPlaceholder/123,(Item/TestDef1/123,Item/TestDef2))"

    def _test_issues_base(self, test_strings, test_issues, test_context, hed_ops, expand_defs=True):
        for string, expected_params, context in zip(test_strings, test_issues, test_context):
            test_string = HedString(string)
            error_handler = ErrorHandler()
            error_handler.push_error_context(ErrorContext.HED_STRING, test_string, increment_depth_after=False)
            onset_issues = test_string.validate(hed_ops, expand_defs=expand_defs)
            issues = self.format_errors_fully(error_handler, hed_string=test_string, params=expected_params)
            # print(str(onset_issues))
            # print(str(issues))
            error_handler.pop_error_context()
            self.assertEqual(len(hed_ops[-1]._onsets), context)
            self.assertCountEqual(onset_issues, issues)

    def _test_issues_no_context(self, test_strings, test_issues, hed_ops):
        for string, expected_params in zip(test_strings, test_issues):
            test_string = HedString(string)
            error_handler = ErrorHandler()
            error_handler.push_error_context(ErrorContext.HED_STRING, test_string, increment_depth_after=False)
            onset_issues = test_string.validate(hed_ops, expand_defs=True)
            issues = self.format_errors_fully(error_handler, hed_string=test_string, params=expected_params)
            # print(str(onset_issues))
            # print(str(issues))
            error_handler.pop_error_context()
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
            "(def/TestDefInvalid, Onset)",
            "(def/TestDefPlaceholder, Onset)",
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
                              tag_list=['def/TestDefPlaceholder/2471', 'Onset', '(Event)', '(Event)']),
            [],
            self.format_error(OnsetErrors.ONSET_NO_DEF_TAG_FOUND, tag=0),
            self.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0, tag_list=['def/InvalidDef']),
            self.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=[self.placeholder_label_def_string, 'Offset', '(Event)']),
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, [onset_mapper])

    def test_basic_onset_errors_with_def_mapper(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)
        hed_ops = [def_mapper, onset_mapper]

        test_strings = [
            f"({self.placeholder_label_def_string},Onset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string},Offset)",
            f"({self.placeholder_label_def_string}, Onset, (Event), (Event))",
            f"({self.placeholder_label_def_string}, Onset, (Event))",
            "(Onset)",
            f"({self.placeholder_label_def_string}, def/TestDefPlaceholder/2, Onset, (Event))",
            "(def/TestDefInvalid, Onset)",
            "(def/TestDefPlaceholder, Onset)",
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
                              tag_list=['def/TestDefPlaceholder/2']),
            self.format_error(ValidationErrors.HED_DEF_UNMATCHED, tag=0),
            self.format_error(ValidationErrors.HED_DEF_VALUE_MISSING, tag=0),
            self.format_error(OnsetErrors.ONSET_WRONG_NUMBER_GROUPS, tag=0,
                              tag_list=[self.placeholder_label_def_string, 'Offset', '(Event)']),
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, hed_ops, expand_defs=False)

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
            "(def/TestDefInvalid, Onset)",
            "(def/TestDefPlaceholder, Onset)",
            "(def/TestDefNormal/InvalidPlaceholder, Onset)"
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
            self.format_error(OnsetErrors.ONSET_TOO_MANY_DEFS, tag=0, tag_list=['def/InvalidDef']),
            self.format_error(OnsetErrors.ONSET_DEF_UNMATCHED, tag=0),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=True),
            self.format_error(OnsetErrors.ONSET_PLACEHOLDER_WRONG, tag=0, has_placeholder=False)
        ]

        self._test_issues_base(test_strings, test_issues, expected_context, [onset_mapper])

    def test_test_interleaving_onset_offset(self):
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

        self._test_issues_base(test_strings, test_issues, expected_context, [onset_mapper])

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

        self._test_issues_base(test_strings, test_issues, expected_context, [onset_mapper])

    def test_onset_multiple_or_misplaced_errors(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_string = HedString(self.definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)
        hed_validator = HedValidator(hed_schema=self.hed_schema)
        hed_ops = [hed_validator, def_mapper, onset_mapper]

        test_strings = [
            f"{self.placeholder_label_def_string},Onset",
            f"({self.placeholder_label_def_string},Onset, Onset)",
            f"({self.placeholder_label_def_string},Onset, Offset)",
        ]
        # count of issues the line generates
        onset_list = ['Property/Data-property/Data-marker/Temporal-marker/Onset']
        offset_list = ['Property/Data-property/Data-marker/Temporal-marker/Offset']
        test_issues = [
            self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG, tag=1),
            self.format_error(ValidationErrors.HED_TAG_REPEATED, tag=2)
            + self.format_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS, tag=1,
                                multiple_tags=onset_list),
            self.format_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS, tag=1,
                              multiple_tags=offset_list),
        ]

        self._test_issues_no_context(test_strings, test_issues, hed_ops)

        test_issues = [
            self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG, tag=1),
            self.format_error(ValidationErrors.HED_TAG_REPEATED, tag=2)
            + self.format_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS, tag=1,
                                multiple_tags=onset_list),
            self.format_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS, tag=1,
                              multiple_tags=offset_list),
        ]

        # Repeat with just hed validator
        self._test_issues_no_context(test_strings, test_issues, hed_validator)

    def test_onset_multiple_or_misplaced_errors_no_validator(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_string = HedString(self.definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)
        hed_ops = [def_mapper, onset_mapper]

        test_strings = [
            f"{self.placeholder_label_def_string},Onset",
            f"({self.placeholder_label_def_string},Onset, Onset)",
            f"({self.placeholder_label_def_string},Onset, Offset)",
            f"({self.placeholder_label_def_string},Onset, Event)",
        ]
        # count of issues the line generates
        test_issues = [
            [],
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=4,
                              def_tag="Def-expand/TestDefPlaceholder/2471"),
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=4,
                              def_tag="Def-expand/TestDefPlaceholder/2471"),
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=4,
                              def_tag="Def-expand/TestDefPlaceholder/2471"),
        ]

        self._test_issues_no_context(test_strings, test_issues, hed_ops)

        # Verify it also works without def mapping
        test_issues = [
            [],
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=2,
                              def_tag=self.placeholder_label_def_string),
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=2,
                              def_tag=self.placeholder_label_def_string),
            self.format_error(OnsetErrors.ONSET_TAG_OUTSIDE_OF_GROUP, tag=2,
                              def_tag=self.placeholder_label_def_string),
        ]

        self._test_issues_no_context(test_strings, test_issues, [hed_ops[1]])

    def test_onset_two_in_one_line(self):
        def_dict = DefDict()
        def_string = HedString(self.placeholder_definition_string)
        def_string.validate(def_dict)
        def_string = HedString(self.definition_string)
        def_string.validate(def_dict)
        def_mapper = DefinitionMapper(def_dict)
        onset_mapper = OnsetMapper(def_mapper)

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

        self._test_issues_base(test_strings, test_issues, expected_context, [onset_mapper])


if __name__ == '__main__':
    unittest.main()
