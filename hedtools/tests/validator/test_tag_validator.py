import unittest
import os

from hed.models.hed_string import HedString
from hed.validator.event_validator import EventValidator
from hed.errors import error_reporter
from hed import schema
from hed.errors.error_types import ValidationErrors, ValidationWarnings, ErrorContext


class TestHedBase(unittest.TestCase):
    schema_file = None

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(hed_xml)
        cls.error_handler = error_reporter.ErrorHandler()

    def format_error_but_not_really(self, error_type, *args, **kwargs):
        """
            The parameters vary based on what type of error this is.

            Note: If you want to pass a tag as a number to this function, you will need to pass tag as a keyword.

        Parameters
        ----------
        error_type : str
            The type of error for this.  Registered with @hed_error or @hed_tag_error.
        args: args
            The rest of the unnamed args
        kwargs :
            The other parameters to pass down to the error handling func.
        Returns
        -------
        error: [{}]
            A single error
        """
        _ = self.error_handler.format_error(error_type, *args, **kwargs)
        # Save off params
        params = [error_type, args, kwargs]
        # return params
        return [params]

    def really_format_errors(self, error_handler, hed_string, params):
        formatted_errors = []
        for code, args, kwargs in params:
            if 'tag' in kwargs and isinstance(kwargs['tag'], int):
                kwargs['tag'] = hed_string.get_all_tags()[kwargs['tag']]
            formatted_errors += error_handler.format_error(code, *args, **kwargs)

        return formatted_errors


class TestValidatorBase(TestHedBase):
    compute_forms = True
    hed_schema = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.error_handler = error_reporter.ErrorHandler()
        cls.syntactic_hed_input_reader = EventValidator(hed_schema=cls.hed_schema,
                                                        run_semantic_validation=False, check_for_warnings=False)
        cls.syntactic_tag_validator = cls.syntactic_hed_input_reader._tag_validator
        cls.syntactic_warning_hed_input_reader = EventValidator(hed_schema=cls.hed_schema,
                                                                run_semantic_validation=False, check_for_warnings=True)
        cls.syntactic_warning_tag_validator = cls.syntactic_warning_hed_input_reader._tag_validator
        cls.semantic_hed_input_reader = EventValidator(hed_schema=cls.hed_schema,
                                                       run_semantic_validation=True, check_for_warnings=False)
        cls.semantic_tag_validator = cls.semantic_hed_input_reader._tag_validator
        cls.semantic_warning_hed_input_reader = EventValidator(hed_schema=cls.hed_schema,
                                                               run_semantic_validation=True, check_for_warnings=True)
        cls.semantic_warning_tag_validator = cls.semantic_warning_hed_input_reader._tag_validator

    def validator_base(self, test_strings, expected_results, expected_issues, test_function, error_handler):
        for test_key in test_strings:
            hed_string_obj = HedString(test_strings[test_key])
            error_handler.reset_error_context()
            error_handler.push_error_context(ErrorContext.HED_STRING, hed_string_obj, increment_depth_after=False)
            test_issues = []
            if self.compute_forms:
                test_issues += hed_string_obj.convert_to_canonical_forms(self.hed_schema, error_handler)
            if not test_issues:
                test_issues += test_function(hed_string_obj)
            test_result = not test_issues
            expected_params = expected_issues[test_key]
            expected_result = expected_results[test_key]

            expected_issue = self.really_format_errors(error_handler, hed_string=hed_string_obj,
                                                       params=expected_params)
            error_handler.pop_error_context()
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])

    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        validator = self.syntactic_hed_input_reader
        if check_for_warnings is True:
            validator = self.syntactic_warning_hed_input_reader
        self.validator_base(test_strings, expected_results, expected_issues,
                            self.string_obj_func(validator), validator._error_handler)

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        validator = self.semantic_hed_input_reader
        if check_for_warnings is True:
            validator = self.semantic_warning_hed_input_reader
        self.validator_base(test_strings, expected_results, expected_issues,
                            self.string_obj_func(validator), validator._error_handler)


class TestHed3(TestValidatorBase):
    schema_file = "../data/HED8.0.0-alpha.3.xml"


class IndividualHedTagsShort(TestHed3):
    @staticmethod
    def string_obj_func(validator):
        return validator._validate_individual_tags_in_hed_string

    def test_exist_in_schema(self):
        test_strings = {
            'takesValue': 'Duration/3 ms',
            'full': 'Animal-agent',
            'extensionsAllowed': 'Item/Beaver',
            'leafExtension': 'Experiment-procedure/Something',
            'nonExtensionsAllowed': 'Event/Nonsense',
            'invalidExtension': 'Attribute/Red',
            'invalidExtension2': 'Attribute/Red/Extension2',
            'usedToBeIllegalComma': 'Attribute/Informational/Label/This is a label,This/Is/A/Tag',
        }
        expected_results = {
            'takesValue': True,
            'full': True,
            'extensionsAllowed': True,
            'leafExtension': False,
            'nonExtensionsAllowed': False,
            'invalidExtension': False,
            'invalidExtension2': False,
            'usedToBeIllegalComma': False
        }
        expected_issues = {
            'takesValue': [],
            'full': [],
            'extensionsAllowed': [],
            'leafExtension': self.format_error_but_not_really(ValidationErrors.INVALID_EXTENSION, tag=0),
            'nonExtensionsAllowed': self.format_error_but_not_really(ValidationErrors.INVALID_EXTENSION, tag=0),
            'invalidExtension': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0, index_in_tag=10,
                                                                 index_in_tag_end=13,
                                                                 expected_parent_tag="Attribute/Sensory/Visual/Color/CSS-color/Red-color/Red"),
            'invalidExtension2': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0, index_in_tag=10,
                                                                  index_in_tag_end=13,
                                                                  expected_parent_tag="Attribute/Sensory/Visual/Color/CSS-color/Red-color/Red"),
            'usedToBeIllegalComma': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND, tag=1,
                                                                     index_in_tag=0, index_in_tag_end=4),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_proper_capitalization(self):
        test_strings = {
            'proper': 'Event/Sensory-event',
            'camelCase': 'EvEnt/Something',
            'takesValue': 'Attribute/Temporal rate/20 Hz',
            'numeric': 'Repetition/20',
            'lowercase': 'Event/something'
        }
        expected_results = {
            'proper': True,
            'camelCase': True,
            'takesValue': True,
            'numeric': True,
            'lowercase': False
        }
        expected_issues = {
            'proper': [],
            'camelCase': [],
            'takesValue': [],
            'numeric': [],
            'lowercase': self.format_error_but_not_really(ValidationWarnings.CAPITALIZATION, tag=0)
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, True)

    def test_child_required(self):
        test_strings = {
            'hasChild': 'Experimental-stimulus',
            'missingChild': 'Label'
        }
        expected_results = {
            'hasChild': True,
            'missingChild': False
        }
        expected_issues = {
            'hasChild': [],
            'missingChild': self.format_error_but_not_really(ValidationErrors.REQUIRE_CHILD, tag=0)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_required_units(self):
        test_strings = {
            'hasRequiredUnit': 'Duration/3 ms',
            'missingRequiredUnit': 'Duration/3',
            'notRequiredNoNumber': 'Color/Red',
            'notRequiredNumber': 'Color/Red/0.5',
            'notRequiredScientific': 'Color/Red/5.2e-1',
            'timeValue': 'Item/2D shape/Clock face/08:30',
            # Update test - This one is currently marked as valid because clock face isn't in hed3
            'invalidTimeValue': 'Item/2D shape/Clock face/8:30',
        }
        expected_results = {
            'hasRequiredUnit': True,
            'missingRequiredUnit': False,
            'notRequiredNoNumber': True,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'timeValue': True,
            'invalidTimeValue': True,
        }
        legal_clock_time_units = ['hour:min', 'hour:min:sec']
        expected_issues = {
            'hasRequiredUnit': [],
            'missingRequiredUnit': self.format_error_but_not_really(ValidationWarnings.UNIT_CLASS_DEFAULT_USED, tag=0,
                                                                    default_unit='s'),
            'notRequiredNoNumber': [],
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'timeValue': [],
            'invalidTimeValue': [],
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_correct_units(self):
        test_strings = {
            'correctUnit': 'Duration/3 ms',
            'correctUnitScientific': 'Duration/3.5e1 ms',
            'correctPluralUnit': 'Duration/3 milliseconds',
            'correctNoPluralUnit': 'Frequency/3 hertz',
            'correctNonSymbolCapitalizedUnit': 'Duration/3 MilliSeconds',
            'correctSymbolCapitalizedUnit': 'Frequency/3 kHz',
            'incorrectUnit': 'Duration/3 cm',
            'incorrectPluralUnit': 'Frequency/3 hertzs',
            'incorrectSymbolCapitalizedUnit': 'Frequency/3 hz',
            'incorrectSymbolCapitalizedUnitModifier': 'Frequency/3 KHz',
            'notRequiredNumber': 'Color/Red/0.5',
            'notRequiredScientific': 'Color/Red/5e-1',
            # Update tests - 8.0 currently has no clockTime nodes.
            # 'properTime': 'Item/2D shape/Clock face/08:30',
            # 'invalidTime': 'Item/2D shape/Clock face/54:54'
        }
        expected_results = {
            'correctUnit': True,
            'correctUnitScientific': True,
            'correctPluralUnit': True,
            'correctNoPluralUnit': True,
            'correctNonSymbolCapitalizedUnit': True,
            'correctSymbolCapitalizedUnit': True,
            'incorrectUnit': False,
            'incorrectPluralUnit': False,
            'incorrectSymbolCapitalizedUnit': False,
            'incorrectSymbolCapitalizedUnitModifier': False,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            # 'properTime': True,
            # 'invalidTime': True
        }
        legal_time_units = ['s', 'second', 'day', 'minute', 'hour']
        legal_clock_time_units = ['hour:min', 'hour:min:sec']
        legal_freq_units = ['Hz', 'hertz']

        expected_issues = {
            'correctUnit': [],
            'correctUnitScientific': [],
            'correctPluralUnit': [],
            'correctNoPluralUnit': [],
            'correctNonSymbolCapitalizedUnit': [],
            'correctSymbolCapitalizedUnit': [],
            'incorrectUnit': self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                              tag=0, unit_class_units=legal_time_units),
            'incorrectPluralUnit': self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                    tag=0, unit_class_units=legal_freq_units),
            'incorrectSymbolCapitalizedUnit': self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                               tag=0,
                                                                               unit_class_units=legal_freq_units),
            'incorrectSymbolCapitalizedUnitModifier': self.format_error_but_not_really(
                ValidationErrors.UNIT_CLASS_INVALID_UNIT, tag=0, unit_class_units=legal_freq_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            # 'properTime': [],
            # 'invalidTime': self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,  tag=0,
            #                                 unit_class_units=legal_clock_time_units)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_extensions(self):
        test_strings = {
            'invalidExtension': 'Experiment-control/Animal-agent',
        }
        expected_results = {
            'invalidExtension': False,
        }
        expected_issues = {
            'invalidExtension': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                                 index_in_tag=19, index_in_tag_end=31,
                                                                 expected_parent_tag="Agent/Animal-agent"),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_invalid_placeholder_in_normal_string(self):
        test_strings = {
            'invalidPlaceholder': 'Duration/# ms',
        }
        expected_results = {
            'invalidPlaceholder': False,
        }
        expected_issues = {
            'invalidPlaceholder': self.format_error_but_not_really(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                   tag=0,
                                                                   index_in_tag=9, index_in_tag_end=10),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_span_reporting(self):
        test_strings = {
            'orgTagDifferent': 'Duration/23 hz',
            'orgTagDifferent2': 'Duration/23 hz, Duration/23 hz',
        }
        expected_results = {
            'orgTagDifferent': False,
            'orgTagDifferent2': False,
        }
        tag_unit_class_units = ['day', 'hour', 'minute', 's', 'second']
        expected_issues = {
            'orgTagDifferent': self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                tag=0,
                                                                unit_class_units=tag_unit_class_units),
            'orgTagDifferent2': self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                 tag=0,
                                                                 unit_class_units=tag_unit_class_units)
                                + self.format_error_but_not_really(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                   tag=1,
                                                                   unit_class_units=tag_unit_class_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class TestTagLevels3(TestHed3):
    @staticmethod
    def string_obj_func(validator):
        return validator._validate_groups_in_hed_string

    def test_no_duplicates(self):
        test_strings = {
            'topLevelDuplicate': 'Event/Sensory-event,Event/Sensory-event',
            'groupDuplicate': 'Item/Object/Man-made-object/VehicleTrain,(Event/Sensory-event,'
                              'Attribute/Sensory/Visual/Color/CSS-color/Purple-color/Purple,Event/Sensory-event)',
            'noDuplicate': 'Event/Sensory-event,'
                           'Item/Object/Man-made-object/VehicleTrain,'
                           'Attribute/Sensory/Visual/Color/CSS-color/Purple-color/Purple',
            'legalDuplicate': 'Item/Object/Man-made-object/VehicleTrain,(Item/Object/Man-made-object/VehicleTrain,'
                              'Event/Sensory-event)',
        }
        expected_results = {
            'topLevelDuplicate': False,
            'groupDuplicate': False,
            'legalDuplicate': True,
            'noDuplicate': True
        }
        expected_issues = {
            'topLevelDuplicate': self.format_error_but_not_really(ValidationErrors.DUPLICATE,
                                                                  tag=1),
            'groupDuplicate': self.format_error_but_not_really(ValidationErrors.DUPLICATE,
                                                               tag=3),
            'legalDuplicate': [],
            'noDuplicate': []
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)

    def test_no_duplicates_semantic(self):
        test_strings = {
            'mixedLevelDuplicates': 'Man-made-object/Vehicle/Boat, Vehicle/Boat',
            'mixedLevelDuplicates2': 'Man-made-object/Vehicle/Boat, Boat'
        }
        expected_results = {
            'mixedLevelDuplicates': False,
            'mixedLevelDuplicates2': False,
        }
        expected_issues = {
            'mixedLevelDuplicates': self.format_error_but_not_really(ValidationErrors.DUPLICATE,
                                                                     tag=1),
            'mixedLevelDuplicates2': self.format_error_but_not_really(ValidationErrors.DUPLICATE,
                                                                      tag=1),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_topLevelTagGroup_validation(self):
        test_strings = {
            'invalid1': 'Definition/InvalidDef',
            'valid1': '(Definition/ValidDef)',
            'valid2': '(Definition/ValidDef), (Definition/ValidDef2)',
            'invalid2': '(Event, (Definition/InvalidDef2))',
            'invalidTwoInOne': '(Definition/InvalidDef2, Definition/InvalidDef3)',
            'invalid2TwoInOne': '(Definition/InvalidDef2, Onset)',
        }
        expected_results = {
            'invalid1': False,
            'valid1': True,
            'valid2': True,
            'invalid2': False,
            'invalidTwoInOne': False,
            'invalid2TwoInOne': False,
        }
        expected_issues = {
            'invalid1': self.format_error_but_not_really(ValidationErrors.HED_TOP_LEVEL_TAG,
                                                         tag=0),
            'valid1': [],
            'valid2': [],
            'invalid2': self.format_error_but_not_really(ValidationErrors.HED_TOP_LEVEL_TAG,
                                                         tag=1),
            'invalidTwoInOne': self.format_error_but_not_really(ValidationErrors.HED_MULTIPLE_TOP_TAGS,
                                                                tag=0,
                                                                multiple_tags="Attribute/Informational/Definition/InvalidDef3".split(", ")),
            'invalid2TwoInOne': self.format_error_but_not_really(ValidationErrors.HED_MULTIPLE_TOP_TAGS,
                                                                 tag=0,
                                                                 multiple_tags="Data-property/Spatiotemporal-property/Temporal-property/Onset".split(", ")),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_taggroup_validation(self):
        test_strings = {
            'invalid1': 'Def-Expand/InvalidDef',
            'invalid2': 'Def-Expand/InvalidDef, Event, (Event)',
            'invalid3': 'Event, (Event), Def-Expand/InvalidDef',
            'valid1': '(Def-Expand/ValidDef)',
            'valid2': '(Def-Expand/ValidDef), (Def-Expand/ValidDef2)',
            'valid3': '(Event, (Def-Expand/InvalidDef2))',
            # This case should possibly be flagged as invalid
            'semivalid1': '(Def-Expand/InvalidDef2, Def-Expand/InvalidDef3)',
            'semivalid2': '(Def-Expand/InvalidDef2, Onset)',
        }
        expected_results = {
            'invalid1': False,
            'invalid2': False,
            'invalid3': False,
            'valid1': True,
            'valid2': True,
            'valid3': True,
            'semivalid1': True,
            'semivalid2': True,
        }
        expected_issues = {
            'invalid1': self.format_error_but_not_really(ValidationErrors.HED_TAG_GROUP_TAG,
                                                         tag=0),
            'invalid2': self.format_error_but_not_really(ValidationErrors.HED_TAG_GROUP_TAG,
                                                         tag=0),
            'invalid3': self.format_error_but_not_really(ValidationErrors.HED_TAG_GROUP_TAG,
                                                         tag=2),
            'valid1': [],
            'valid2': [],
            'valid3': [],
            'semivalid1': [],
            'semivalid2': []
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


if __name__ == '__main__':
    unittest.main()
