import unittest
import os

from hed.util.hed_string import HedString
from hed.validator.hed_validator import HedValidator
from hed.util import error_reporter
from hed.util.error_types import ValidationErrors, ValidationWarnings
from hed.validator.tag_validator import TagValidator
from hed import schema


class TestHed(unittest.TestCase):
    schema_file = '../data/legacy_xml/HED7.1.1.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(hed_xml)
        cls.error_handler = error_reporter.ErrorHandler()
        cls.syntactic_tag_validator = TagValidator(check_for_warnings=False,
                                                   run_semantic_validation=False)
        cls.syntactic_warning_tag_validator = TagValidator(check_for_warnings=True,
                                                           run_semantic_validation=False)
        cls.semantic_tag_validator = TagValidator(cls.hed_schema, check_for_warnings=False,
                                                  run_semantic_validation=True)
        cls.semantic_warning_tag_validator = TagValidator(cls.hed_schema, check_for_warnings=True,
                                                          run_semantic_validation=True)
        cls.syntactic_hed_input_reader = HedValidator()
        cls.syntactic_hed_input_reader._tag_validator = cls.syntactic_tag_validator
        cls.syntactic_warning_hed_input_reader = HedValidator()
        cls.syntactic_warning_hed_input_reader._tag_validator = cls.syntactic_warning_tag_validator
        cls.semantic_hed_input_reader = HedValidator(hed_schema=cls.hed_schema)
        cls.semantic_hed_input_reader._tag_validator = cls.semantic_tag_validator
        cls.semantic_warning_hed_input_reader = HedValidator(hed_schema=cls.hed_schema)
        cls.semantic_warning_hed_input_reader._tag_validator = cls.semantic_warning_tag_validator

    def validator_base(self, test_strings, expected_results, expected_issues, test_function, convert_tags=False):
        for test_key in test_strings:
            hed_string_delimiter = HedString(test_strings[test_key])
            test_issues = []
            if convert_tags:
                test_issues += hed_string_delimiter.calculate_canonical_forms(self.hed_schema)
            if not test_issues:
                test_issues += test_function(hed_string_delimiter)
            test_result = not test_issues
            expected_issue = expected_issues[test_key]
            expected_result = expected_results[test_key]
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])

    # Likely temp during restructure.  Same as above but function takes a string.
    def validator_base_string(self, test_strings, expected_results, expected_issues, test_function):
        for test_key in test_strings:
            test_issues = test_function(test_strings[test_key])
            test_result = not test_issues
            expected_issue = expected_issues[test_key]
            expected_result = expected_results[test_key]
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])
            self.assertEqual(test_result, expected_result, test_strings[test_key])


class FullHedString(TestHed):
    def validator(self, test_strings, expected_results, expected_issues):
        for test_key in test_strings:
            test_issues = self.semantic_warning_tag_validator.run_hed_string_validators(hed_string=test_strings[test_key])
            test_result = not test_issues
            expected_issue = expected_issues[test_key]
            expected_result = expected_results[test_key]
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])

    def test_mismatched_parentheses(self):
        test_strings = {
            'extraOpening':
                '/Action/Reach/To touch,((/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            'extraClosing':
                '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),),'
                '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            'valid':
                '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px'
        }
        expected_results = {
            'extraOpening': False,
            'extraClosing': False,
            'valid': True
        }
        expected_issues = {
            'extraOpening': self.error_handler.format_error(ValidationErrors.PARENTHESES, opening_parentheses_count=2,
                                                                     closing_parentheses_count=1),
                                                                     #hed_string=test_strings['extraOpening']
                                                                     # ),
            'extraClosing': self.error_handler.format_error(ValidationErrors.PARENTHESES, opening_parentheses_count=1,
                                                                     closing_parentheses_count=2),
                                                                     #hed_string=test_strings['extraClosing']),
            'valid': []
        }

        self.validator(test_strings, expected_results, expected_issues)

    def test_malformed_delimiters(self):
        test_strings = {
            'missingOpeningComma':
                '/Action/Reach/To touch(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            'missingClosingComma':
                '/Action/Reach/To touch,'
                '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)/Attribute/Location/Screen/Top/70 px,'
                '/Attribute/Location/Screen/Left/23 px',
            'extraOpeningComma':
                ',/Action/Reach/To touch,'
                '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            'extraClosingComma':
                '/Action/Reach/To touch,'
                '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,'
                '/Attribute/Location/Screen/Left/23 px,',
            # 'extraOpeningParen':
            #     '(/Action/Reach/To touch,'
            #     '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
            #     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            # 'extraClosingParen':
            #     '/Action/Reach/To touch,'
            #     '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
            #     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px)',
            'multipleExtraOpeningDelimiters':
                ',,,/Action/Reach/To touch,'
                '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,'
                '/Attribute/Location/Screen/Left/23 px',
            'multipleExtraClosingDelimiters':
                '/Action/Reach/To touch,'
                '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px,,,,',
            'multipleExtraMiddleDelimiters':
                '/Action/Reach/To touch,'
                ',(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,'
                ',,/Attribute/Location/Screen/Left/23 px',
            'valid':
                '/Action/Reach/To touch,'
                '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,'
                '/Attribute/Location/Screen/Left/23 px',
            'validNestedParentheses':
                '/Action/Reach/To touch,'
                '((/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,'
                '/Attribute/Location/Screen/Left/23 px),Event/Duration/3 ms',
            'validNestedParentheses2':
                '/Action/Reach/To touch,'
                '(((/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,'
                '/Attribute/Location/Screen/Left/23 px)),Event/Duration/3 ms',
            'validNestedParentheses3':
                'Thing, (Thing, (Thing))',
            'validNestedParentheses4': 'Thing, ((Thing, (Thing)), Thing)',
            'invalidNestedParentheses': 'Thing, ((Thing, (Thing)) Thing)',
            #'emptyGroup': 'Thing, ()'
        }

        expected_results = {
            'missingOpeningComma': False,
            'missingClosingComma': False,
            'extraOpeningComma': False,
            'extraClosingComma': False,
            'extraOpeningParen': False,
            'extraClosingParen': False,
            'multipleExtraOpeningDelimiters': False,
            'multipleExtraClosingDelimiters': False,
            'multipleExtraMiddleDelimiters': False,
            'valid': True,
            'validNestedParentheses': True,
            'validNestedParentheses2': True,
            'validNestedParentheses3': True,
            'validNestedParentheses4': True,
            'invalidNestedParentheses': False,
            # 'emptyGroup': False
        }
        expected_issues = {
            'missingOpeningComma': self.error_handler.format_error(ValidationErrors.COMMA_MISSING, 
                                                                       tag='/Action/Reach/To touch('),
            'missingClosingComma': self.error_handler.format_error(ValidationErrors.COMMA_MISSING, 
                                                                       tag='/Participant/Effect/Body part/Arm)'),
            'extraOpeningComma': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',', char_index=0,
                                                                          hed_string=test_strings['extraOpeningComma']),
            'extraClosingComma': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                          char_index=len(
                                                                              test_strings['extraClosingComma']) - 1,
                                                                          hed_string=test_strings['extraClosingComma']),
            # 'extraOpeningParen': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character='(', index=0,
            #                                       hed_string=test_strings['extraOpeningParen']),
            # 'extraClosingParen': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=')',
            #                                       index=len(test_strings['extraClosingParen']) - 1,
            #                                       hed_string=test_strings['extraClosingParen']),
            'extraOpeningParen': self.error_handler.format_error(ValidationErrors.PARENTHESES, opening_parentheses_count=2,
                                                                          closing_parentheses_count=1),
            'extraClosingParen': self.error_handler.format_error(ValidationErrors.PARENTHESES, opening_parentheses_count=1,
                                                                          closing_parentheses_count=2),
            'multipleExtraOpeningDelimiters': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                       char_index=0,
                                                                                       hed_string=test_strings[
                                                                                           'multipleExtraOpeningDelimiters'])
                                              + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                         char_index=1,
                                                                                         hed_string=test_strings[
                                                                                             'multipleExtraOpeningDelimiters'])
                                              + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                         char_index=2,
                                                                                         hed_string=test_strings[
                                                                                             'multipleExtraOpeningDelimiters']),
            'multipleExtraClosingDelimiters': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                       char_index=len(test_strings[
                                                                                                          'multipleExtraClosingDelimiters']) - 1,
                                                                                       hed_string=test_strings[
                                                                                           'multipleExtraClosingDelimiters'])
                                              + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                         char_index=len(test_strings[
                                                                                                            'multipleExtraClosingDelimiters']) - 2,
                                                                                         hed_string=test_strings[
                                                                                             'multipleExtraClosingDelimiters'])
                                              + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                         char_index=len(test_strings[
                                                                                                            'multipleExtraClosingDelimiters']) - 3,
                                                                                         hed_string=test_strings[
                                                                                             'multipleExtraClosingDelimiters'])
                                              + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',',
                                                                                         char_index=len(test_strings[
                                                                                                            'multipleExtraClosingDelimiters']) - 4,
                                                                                         hed_string=test_strings[
                                                                                             'multipleExtraClosingDelimiters']),
            'multipleExtraMiddleDelimiters': self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',', char_index=23,
                                                                                      hed_string=test_strings[
                                                                                          'multipleExtraMiddleDelimiters'])
                                             + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',', char_index=125,
                                                                                        hed_string=test_strings[
                                                                                            'multipleExtraMiddleDelimiters'])
                                             + self.error_handler.format_error(ValidationErrors.EMPTY_TAG, character=',', char_index=126,
                                                                                        hed_string=test_strings[
                                                                                            'multipleExtraMiddleDelimiters']),
            'valid': [],
            'validNestedParentheses': [],
            'validNestedParentheses2': [],
            'validNestedParentheses3': [],
            'validNestedParentheses4': [],
            'invalidNestedParentheses': self.error_handler.format_error(ValidationErrors.COMMA_MISSING, 
                                                                            tag="Thing)) "),
            # 'emptyGroup': []
        }
        self.validator(test_strings, expected_results, expected_issues)

    def test_invalid_characters(self):
        test_strings = {
            'openingBrace':
                '/Attribute/Object side/Left,/Participant/Effect{/Body part/Arm',
            'closingBrace':
                '/Attribute/Object side/Left,/Participant/Effect}/Body part/Arm',
            'openingBracket':
                '/Attribute/Object side/Left,/Participant/Effect[/Body part/Arm',
            'closingBracket':
                '/Attribute/Object side/Left,/Participant/Effect]/Body part/Arm'
        }
        expected_results = {
            'openingBrace': False,
            'closingBrace': False,
            'openingBracket': False,
            'closingBracket': False
        }
        expected_issues = {
            'openingBrace': self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, character='{', char_index=47,
                                                                hed_string=test_strings['openingBrace']),
            'closingBrace': self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, character='}', char_index=47,
                                                                hed_string=test_strings['closingBrace']),
            'openingBracket': self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, character='[', char_index=47,
                                                                  hed_string=test_strings['openingBracket']),
            'closingBracket': self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, character=']', char_index=47,
                                                                  hed_string=test_strings['closingBracket'])
        }
        self.validator(test_strings, expected_results, expected_issues)


class IndividualHedTags(TestHed):
    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.syntactic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter))
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.syntactic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter))

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings, convert_tags=False):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), convert_tags=convert_tags)
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), convert_tags=convert_tags)

    def test_exist_in_schema(self):
        test_strings = {
            'takesValue': 'Event/Duration/3 ms',
            'full': 'Attribute/Object side/Left',
            'extensionsAllowed': 'Item/Object/Person/Driver',
            'leafExtension': 'Event/Category/Initial context/Something',
            'nonExtensionsAllowed': 'Event/Nonsense',
            'usedToBeIllegalComma': 'Event/Label/This is a label,This/Is/A/Tag',
            'testExtensionExists': 'Item/Object/Person/Event',
            'testExtensionExists2': "Category/Initial Context/Category",
            'testInvalidShortForm': "Category/Initial Context",
        }
        expected_results = {
            'takesValue': True,
            'full': True,
            'extensionsAllowed': True,
            'leafExtension': False,
            'nonExtensionsAllowed': False,
            'usedToBeIllegalComma': False,
            'testExtensionExists': False,
            'testExtensionExists2': False,
            'testInvalidShortForm': False,
        }
        expected_issues = {
            'takesValue': [],
            'full': [],
            'extensionsAllowed': [],
            'leafExtension': self.error_handler.format_error(ValidationErrors.INVALID_EXTENSION, tag=test_strings['leafExtension']),
            'nonExtensionsAllowed': self.error_handler.format_error(ValidationErrors.INVALID_EXTENSION, 
                                                                        tag=test_strings['nonExtensionsAllowed']),
            'usedToBeIllegalComma': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                                        tag="This/Is/A/Tag",
                                                                        index=0, index_end=4,
                                                                        hed_string=test_strings['usedToBeIllegalComma']),
            'testExtensionExists': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, tag="Item/Object/Person/Event",
                                                                           index=19, index_end=24,
                                                                           expected_parent_tag="Event"),
            'testExtensionExists2': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                                        tag="Category/Initial Context/Category",
                                                                        index=0, index_end=8,
                                                                        hed_string=test_strings['testExtensionExists2']),
            'testInvalidShortForm': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                                        index=0, index_end=8,
                                                                        tag="Category/Initial Context"),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False, convert_tags=True)

    def test_proper_capitalization(self):
        test_strings = {
            'proper': 'Event/Category/Sensory presentation',
            'camelCase': 'DoubleEvent/Something',
            'takesValue': 'Attribute/Temporal rate/20 Hz',
            'numeric': 'Attribute/Repetition/20',
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
            'lowercase': self.error_handler.format_error(ValidationWarnings.CAPITALIZATION, tag=test_strings['lowercase'])
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, True)

    def test_child_required(self):
        test_strings = {
            'hasChild': 'Event/Category/Experimental stimulus',
            'missingChild': 'Event/Category'
        }
        expected_results = {
            'hasChild': True,
            'missingChild': False
        }
        expected_issues = {
            'hasChild': [],
            'missingChild': self.error_handler.format_error(ValidationErrors.REQUIRE_CHILD, tag=test_strings['missingChild'])
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_required_units(self):
        test_strings = {
            'hasRequiredUnit': 'Event/Duration/3 ms',
            'missingRequiredUnit': 'Event/Duration/3',
            'notRequiredNoNumber': 'Attribute/Color/Red',
            'notRequiredNumber': 'Attribute/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Color/Red/5.2e-1',
            'timeValue': 'Item/2D shape/Clock face/08:30',
            'invalidTimeValue': 'Item/2D shape/Clock face/8:30'
        }
        expected_results = {
            'hasRequiredUnit': True,
            'missingRequiredUnit': False,
            'notRequiredNoNumber': True,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'timeValue': True,
            'invalidTimeValue': False
        }
        legal_clock_time_units = ['hour:min', 'hour:min:sec']
        expected_issues = {
            'hasRequiredUnit': [],
            'missingRequiredUnit': self.error_handler.format_error(ValidationWarnings.UNIT_CLASS_DEFAULT_USED, tag=test_strings['missingRequiredUnit'],
                                                                         default_unit='s'),
            'notRequiredNoNumber': [],
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'timeValue': [],
            'invalidTimeValue': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                    tag=test_strings['invalidTimeValue'],
                                                                    unit_class_units=legal_clock_time_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_correct_units(self):
        test_strings = {
            'correctUnit': 'Event/Duration/3 ms',
            'correctUnitScientific': 'Event/Duration/3.5e1 ms',
            'correctPluralUnit': 'Event/Duration/3 milliseconds',
            'correctNoPluralUnit': 'Attribute/Temporal rate/3 hertz',
            'correctNonSymbolCapitalizedUnit': 'Event/Duration/3 MilliSeconds',
            'correctSymbolCapitalizedUnit': 'Attribute/Temporal rate/3 kHz',
            'incorrectUnit': 'Event/Duration/3 cm',
            'incorrectPluralUnit': 'Attribute/Temporal rate/3 hertzs',
            'incorrectSymbolCapitalizedUnit': 'Attribute/Temporal rate/3 hz',
            'incorrectSymbolCapitalizedUnitModifier': 'Attribute/Temporal rate/3 KHz',
            'notRequiredNumber': 'Attribute/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Color/Red/5e-1',
            'properTime': 'Item/2D shape/Clock face/08:30',
            'invalidTime': 'Item/2D shape/Clock face/54:54',
            # Theses should both fail, as this tag validator isn't set to accept placeholders
            'placeholderNoUnit': 'Event/Duration/#',
            'placeholderUnit': 'Event/Duration/# ms',
            'placeholderWrongUnit': 'Event/Duration/# hz'
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
            'properTime': True,
            'invalidTime': False,
            'placeholderNoUnit': False,
            'placeholderUnit': False,
            'placeholderWrongUnit': False
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
            'incorrectUnit': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                 tag=test_strings['incorrectUnit'],
                                                                 unit_class_units=legal_time_units),
            'incorrectPluralUnit': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                       tag=test_strings['incorrectPluralUnit'],
                                                                       unit_class_units=legal_freq_units),
            'incorrectSymbolCapitalizedUnit': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                                  tag=test_strings[
                                                                                      'incorrectSymbolCapitalizedUnit'],
                                                                                  unit_class_units=legal_freq_units),
            'incorrectSymbolCapitalizedUnitModifier': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                                          tag=test_strings[
                                                                                              'incorrectSymbolCapitalizedUnitModifier'],
                                                                                          unit_class_units=legal_freq_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'properTime': [],
            'invalidTime': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT,  tag=test_strings['invalidTime'],
                                                               unit_class_units=legal_clock_time_units),

            'placeholderNoUnit': self.error_handler.format_error(ValidationWarnings.UNIT_CLASS_DEFAULT_USED,
                                                                      tag=test_strings['placeholderNoUnit'],
                                                                      default_unit="s")
                                + self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, char_index=15, character="#",
                                                                  hed_string=test_strings["placeholderNoUnit"]),
            'placeholderUnit': self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, char_index=15, character="#",
                                                                  hed_string=test_strings["placeholderUnit"]),
            'placeholderWrongUnit': self.error_handler.format_error(ValidationErrors.INVALID_CHARACTER, char_index=15, character="#",
                                                                  hed_string=test_strings["placeholderWrongUnit"])
                                    + self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                 tag=test_strings['placeholderWrongUnit'],
                                                                 unit_class_units=legal_time_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


class HedTagLevels(TestHed):
    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                    hed_string_delimiter: self.syntactic_warning_hed_input_reader._validate_tag_levels_in_hed_string(
                                    hed_string_delimiter))
        else:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                    hed_string_delimiter:
                                self.syntactic_hed_input_reader._validate_tag_levels_in_hed_string(
                                    hed_string_delimiter))

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                    hed_string_delimiter: self.semantic_warning_hed_input_reader._validate_tag_levels_in_hed_string(
                                    hed_string_delimiter))
        else:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                    hed_string_delimiter: self.semantic_hed_input_reader._validate_tag_levels_in_hed_string(
                                    hed_string_delimiter))

    def test_no_duplicates(self):
        test_strings = {
            'topLevelDuplicate': 'Event/Category/Sensory presentation,Event/Category/Sensory presentation',
            'groupDuplicate': 'Item/Object/Vehicle/Train,(Event/Category/Sensory presentation,'
                              'Attribute/Visual/Color/Purple,Event/Category/Sensory presentation)',
            'noDuplicate': 'Event/Category/Sensory presentation,'
                           'Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple',
            'legalDuplicate': 'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,'
                              'Event/Category/Sensory presentation)',
        }
        expected_results = {
            'topLevelDuplicate': False,
            'groupDuplicate': False,
            'legalDuplicate': True,
            'noDuplicate': True
        }
        expected_issues = {
            'topLevelDuplicate': self.error_handler.format_error(ValidationErrors.DUPLICATE, 
                                                                     tag='Event/Category/Sensory presentation',
                                                                     hed_string=test_strings["topLevelDuplicate"]),
            'groupDuplicate': self.error_handler.format_error(ValidationErrors.DUPLICATE, 
                                                                  tag='Event/Category/Sensory presentation',
                                                                  hed_string=test_strings["groupDuplicate"]),
            'legalDuplicate': [],
            'noDuplicate': []
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)

    def test_multiple_copies_unique_tags(self):
        test_strings = {
            'legal': 'Event/Description/Rail vehicles,Item/Object/Vehicle/Train,'
                     '(Item/Object/Vehicle/Train,Event/Category/Sensory presentation)',
            'multipleDesc': 'Event/Description/Rail vehicles,'
                            'Event/Description/Locomotive-pulled or multiple units,'
                            'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Sensory presentation)',
            # This is legal as this is a hed2 schema, thus doesn't have a short form Description/
            'multipleDescIncShort': 'Event/Description/Rail vehicles,'
                            'Description/Locomotive-pulled or multiple units,'
                            'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Sensory presentation)'
        }
        expected_results = {
            'legal': True,
            'multipleDesc': False,
            'multipleDescIncShort': True
        }
        expected_issues = {
            'legal': [],
            'multipleDesc': self.error_handler.format_error(ValidationErrors.MULTIPLE_UNIQUE, tag_prefix='Event/Description'),
            'multipleDescIncShort': []
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


class RequiredTags(TestHed):
    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                    hed_string_delimiter: self.semantic_warning_tag_validator._run_tag_validators(
                                    hed_string_delimiter.get_all_tags()))
        else:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda hed_string_delimiter: self.semantic_tag_validator._run_tag_validators(
                                    hed_string_delimiter.get_all_tags()))

    def test_includes_all_required_tags(self):
        test_strings = {
            'complete': 'Event/Label/Bus,Event/Category/Sensory presentation,'
                        'Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
            'missingLabel': 'Event/Category/Sensory presentation,Event/Description/Shown a picture of a bus,'
                            'Item/Object/Vehicle/Bus',
            'missingCategory': 'Event/Label/Bus,Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
            'missingDescription': 'Event/Label/Bus,Event/Category/Sensory presentation,Item/Object/Vehicle/Bus',
            'missingAllRequired': 'Item/Object/Vehicle/Bus',
        }
        expected_results = {
            'complete': True,
            'missingLabel': False,
            'missingCategory': False,
            'missingDescription': False,
            'missingAllRequired': False,
        }
        expected_issues = {
            'complete': [],
            'missingLabel': self.error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,  tag_prefix='Event/Label'),
            'missingCategory': self.error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,
                                                                     tag_prefix='Event/Category'),
            'missingDescription': self.error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,
                                                                        tag_prefix='Event/Description'),
            'missingAllRequired': self.error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,
                                                                        tag_prefix='Event/Label')
                                  + self.error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,
                                                                    tag_prefix='Event/Category')
                                  + self.error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,
                                                                    tag_prefix='Event/Description'),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


class TestHedInvalidChars(TestHed):
    def validator(self, test_strings, expected_results, expected_issues):
        self.validator_base_string(test_strings, expected_results, expected_issues,
                                   lambda
                                       string:
                                   self.syntactic_hed_input_reader._tag_validator.run_hed_string_validators(
                                       string))

    def test_no_more_than_two_tildes(self):
        testStrings = {
            'noTildeGroup': 'Event/Category/Sensory presentation,'
                            '(Item/Object/Vehicle/Train,Event/Category/Sensory presentation)',
            'oneTildeGroup': 'Event/Category/Sensory presentation,'
                             '(Item/Object/Vehicle/Car ~ Attribute/Object control/Perturb)',
            'twoTildeGroup': 'Event/Category/Sensory presentation,'
                             '(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar,'
                             ' Attribute/Visual/Color/Red)',
            'invalidTildeGroup': 'Event/Category/Sensory presentation,'
                                 '(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car,'
                                 ' Item/ID/RedCar, Attribute/Visual/Color/Red ~ Attribute/Object control/Perturb)',
        }
        expectedResults = {
            'noTildeGroup': True,
            'oneTildeGroup': False,
            'twoTildeGroup': False,
            'invalidTildeGroup': False
        }
        expectedIssues = {
            'noTildeGroup': [],
            'oneTildeGroup': self.error_handler.format_error(ValidationErrors.TILDES_NOT_SUPPORTED, 
                                                                 hed_string=testStrings['oneTildeGroup'],
                                                                 character="~", char_index=61),
            'twoTildeGroup': self.error_handler.format_error(ValidationErrors.TILDES_NOT_SUPPORTED, 
                                                                 hed_string=testStrings['twoTildeGroup'],
                                                                 character="~", char_index=54)
                             + self.error_handler.format_error(ValidationErrors.TILDES_NOT_SUPPORTED, 
                                                                   hed_string=testStrings['twoTildeGroup'],
                                                                   character="~", char_index=82),
            'invalidTildeGroup': self.error_handler.format_error(ValidationErrors.TILDES_NOT_SUPPORTED, 
                                                                     hed_string=testStrings['invalidTildeGroup'],
                                                                     character="~", char_index=54)
                                 + self.error_handler.format_error(ValidationErrors.TILDES_NOT_SUPPORTED, 
                                                                       hed_string=testStrings['invalidTildeGroup'],
                                                                       character="~", char_index=82)
                                 + self.error_handler.format_error(ValidationErrors.TILDES_NOT_SUPPORTED, 
                                                                       hed_string=testStrings['invalidTildeGroup'],
                                                                       character="~", char_index=152)
        }
        self.validator(testStrings, expectedResults, expectedIssues)


class TestHedTags(TestHed):
    def test_valid_comma_separated_paths(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = True
        issues = self.semantic_tag_validator.run_hed_string_validators(hed_string)
        self.assertEqual(result, True)
        self.assertCountEqual(issues, [])



class TestOldHed(TestHed):
    schema_file = '../data/legacy_xml/HED7.0.4.xml'


class OldIndividualHedTags(TestOldHed):
    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter))
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter))

    def test_required_units(self):
        test_strings = {
            'hasRequiredUnit': 'Event/Duration/3 ms',
            'missingRequiredUnit': 'Event/Duration/3',
            'notRequiredNumber': 'Attribute/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Color/Red/5.2e-1',
            'timeValue': 'Item/2D shape/Clock face/08:30'
        }
        expected_results = {
            'hasRequiredUnit': True,
            'missingRequiredUnit': False,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'timeValue': True
        }
        expected_issues = {
            'hasRequiredUnit': "",
            'missingRequiredUnit': self.error_handler.format_error(ValidationWarnings.UNIT_CLASS_DEFAULT_USED, tag=test_strings['missingRequiredUnit'],
                                                                         default_unit='s'),
            'notRequiredNumber': "",
            'notRequiredScientific': "",
            'timeValue': ""
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_correct_units(self):
        test_strings = {
            'correctUnit': 'Event/Duration/3 ms',
            'correctUnitWord': 'Event/Duration/3 milliseconds',
            'correctUnitScientific': 'Event/Duration/3.5e1 ms',
            'incorrectUnit': 'Event/Duration/3 cm',
            'incorrectUnitWord': 'Event/Duration/3 nanoseconds',
            'incorrectPrefix': 'Event/Duration/3 ns',
            'notRequiredNumber': 'Attribute/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Color/Red/5e-1',
            'properTime': 'Item/2D shape/Clock face/08:30',
            'invalidTime': 'Item/2D shape/Clock face/54:54'
        }
        expected_results = {
            'correctUnit': True,
            'correctUnitWord': True,
            'correctUnitScientific': True,
            'incorrectUnit': False,
            'incorrectUnitWord': False,
            'incorrectPrefix': False,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'properTime': True,
            'invalidTime': False
        }
        legal_time_units = [
            's',
            'second',
            'seconds',
            'centiseconds',
            'centisecond',
            'cs',
            'hour:min',
            'day',
            'days',
            'ms',
            'milliseconds',
            'millisecond',
            'minute',
            'minutes',
            'hour',
            'hours',
        ]
        expected_issues = {
            'correctUnit': [],
            'correctUnitWord': [],
            'correctUnitScientific': [],
            'incorrectUnit': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                 tag=test_strings['incorrectUnit'],
                                                                 unit_class_units=legal_time_units),
            'incorrectUnitWord': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                     tag=test_strings['incorrectUnitWord'],
                                                                     unit_class_units=legal_time_units),
            'incorrectPrefix': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT, 
                                                                   tag=test_strings['incorrectPrefix'],
                                                                   unit_class_units=legal_time_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'properTime': [],
            'invalidTime': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT,  tag=test_strings['invalidTime'],
                                                               unit_class_units=legal_time_units)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


if __name__ == '__main__':
    unittest.main()
