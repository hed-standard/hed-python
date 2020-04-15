import unittest
import os

from hedvalidation.hed_string_delimiter import HedStringDelimiter
from hedvalidation.hed_input_reader import HedInputReader
from hedvalidation.error_reporter import report_error_type
from hedvalidation.warning_reporter import report_warning_type
from hedvalidation.tag_validator import TagValidator
from hedvalidation.hed_dictionary import HedDictionary


class TestHed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml')
        cls.hed_dictionary = HedDictionary(hed_xml)
        cls.syntactic_tag_validator = TagValidator(cls.hed_dictionary, check_for_warnings=False,
                                                   run_semantic_validation=False)
        cls.syntactic_warning_tag_validator = TagValidator(cls.hed_dictionary, check_for_warnings=True,
                                                           run_semantic_validation=False)
        cls.semantic_tag_validator = TagValidator(cls.hed_dictionary, check_for_warnings=False,
                                                  run_semantic_validation=True)
        cls.semantic_warning_tag_validator = TagValidator(cls.hed_dictionary, check_for_warnings=True,
                                                          run_semantic_validation=True)
        cls.syntactic_hed_input_reader = HedInputReader("Event/Category")
        cls.syntactic_hed_input_reader._tag_validator = cls.syntactic_tag_validator
        cls.syntactic_warning_hed_input_reader = HedInputReader("Event/Category")
        cls.syntactic_warning_hed_input_reader._tag_validator = cls.syntactic_warning_tag_validator
        cls.semantic_hed_input_reader = HedInputReader("Event/Category")
        cls.semantic_hed_input_reader._tag_validator = cls.semantic_tag_validator
        cls.semantic_warning_hed_input_reader = HedInputReader("Event/Category")
        cls.semantic_warning_hed_input_reader._tag_validator = cls.semantic_warning_tag_validator

    def validator_base(self, test_strings, expected_results, expected_issues, testFunction):
        for test_key in test_strings:
            hed_string_delimiter = HedStringDelimiter(test_strings[test_key])
            test_issues = testFunction(hed_string_delimiter)
            test_result = not test_issues
            expected_issue = expected_issues[test_key]
            expected_result = expected_results[test_key]
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])


class TestHedTagGroups(TestHed):
    def validator(self, test_strings, expected_results, expected_issues):
        self.validator_base(test_strings, expected_results, expected_issues,
                            lambda hed_string_delimiter: ''.join(
                                [self.syntactic_tag_validator.run_tag_group_validators(*args) for args in
                                 zip(hed_string_delimiter.get_tag_groups(),
                                     hed_string_delimiter.get_tag_group_strings())]))

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
            'oneTildeGroup': True,
            'twoTildeGroup': True,
            'invalidTildeGroup': False
        }
        expectedIssues = {
            'noTildeGroup': '',
            'oneTildeGroup': '',
            'twoTildeGroup': '',
            'invalidTildeGroup': report_error_type('tilde',
                                                   tag='(Participant/ID 1 ~ Participant/Effect/Visual '
                                                       '~ Item/Object/Vehicle/Car,'
                                                       ' Item/ID/RedCar,'
                                                       ' Attribute/Visual/Color/Red '
                                                       '~ Attribute/Object control/Perturb)')
        }
        self.validator(testStrings, expectedResults, expectedIssues)


class FullHedString(TestHed):
    def validator(self, test_strings, expected_results, expected_issues):
        for test_key in test_strings:
            test_issues = TagValidator.run_hed_string_validators(self.semantic_warning_tag_validator,
                                                                 hed_string=test_strings[test_key])
            test_result = not test_issues
            expected_issue = expected_issues[test_key]
            expected_result = expected_results[test_key]
            self.assertEqual(test_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])

    def test_mismatched_parentheses(self):
        testStrings = {
            'extraOpening':
                '/Action/Reach/To touch,((/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px',
            'extraClosing':
                '/Action/Reach/To touch,(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px',
            'valid':
                '/Action/Reach/To touch,(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px'
        }
        expectedResults = {
            'extraOpening': False,
            'extraClosing': False,
            'valid': True
        }
        expectedIssues = {
            # I think this is right
            'extraOpening': report_error_type('bracket', tag=testStrings['extraOpening'].strip(),
                                              opening_bracket_count=2, closing_bracket_count=1),
            'extraClosing': report_error_type('bracket', tag=testStrings['extraClosing'].strip(),
                                              opening_bracket_count=1, closing_bracket_count=2),
            'valid': ''
        }

        self.validator(testStrings, expectedResults, expectedIssues)

    def test_malformed_delimiters(self):
        testStrings = {
            'missingOpeningComma':
                '/Action/Reach/To touch(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px',
            'missingClosingComma':
                '/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm)/Attribute/Spatial/Location/Screen/Top/70 px,'
                '/Attribute/Spatial/Location/Screen/Left/23 px',
            'extraOpeningComma':
                ',/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px',
            'extraClosingComma':
                '/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Spatial/Location/Screen/Top/70 px,'
                '/Attribute/Spatial/Location/Screen/Left/23 px,',
            'extraOpeningTilde':
                '~/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px',
            'extraClosingTilde':
                '/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px~',
            'multipleExtraOpeningDelimiters':
                ',~,/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Spatial/Location/Screen/Top/70 px,'
                '/Attribute/Spatial/Location/Screen/Left/23 px',
            'multipleExtraClosingDelimiters':
                '/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),'
                '/Attribute/Spatial/Location/Screen/Top/70 px,/Attribute/Spatial/Location/Screen/Left/23 px,~~,',
            'multipleExtraMiddleDelimiters':
                '/Action/Reach/To touch,'
                ',(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Spatial/Location/Screen/Top/70 px,'
                '~,/Attribute/Spatial/Location/Screen/Left/23 px',
            'valid':
                '/Action/Reach/To touch,'
                '(/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Spatial/Location/Screen/Top/70 px,'
                '/Attribute/Spatial/Location/Screen/Left/23 px',
            'validNestedParentheses':
                '/Action/Reach/To touch,'
                '((/Attribute/Spatial/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Spatial/Location/Screen/Top/70 px,'
                '/Attribute/Spatial/Location/Screen/Left/23 px),Attribute/Temporal/Duration/3 ms',
        }

        expectedResults = {
            'missingOpeningComma': False,
            'missingClosingComma': False,
            'extraOpeningComma': False,
            'extraClosingComma': False,
            'extraOpeningTilde': False,
            'extraClosingTilde': False,
            'multipleExtraOpeningDelimiters': False,
            'multipleExtraClosingDelimiters': False,
            'multipleExtraMiddleDelimiters': False,
            'valid': True,
            'validNestedParentheses': True
        }
        expectedIssues = {
            # NOT COMPLETE
            'missingOpeningComma': report_error_type('valid', tag='/Action/Reach/To touch('),
            'missingClosingComma': report_error_type('comma', tag='/Participant/Effect/Body part/Arm)/'),
            'extraOpeningComma': report_error_type('extraDelimiter', character=',', index=0,
                                                   hed_string=testStrings['extraOpeningComma']),
            'extraClosingComma': report_error_type('extraDelimiter', character=',',
                                                   index=len(testStrings['extraClosingComma']) - 1,
                                                   hed_string=testStrings['extraClosingComma']),
            'extraOpeningTilde': report_error_type('extraDelimiter', character='~', index=0,
                                                   hed_string=testStrings['extraOpeningTilde']),
            'extraClosingTilde': report_error_type('extraDelimiter', character='~',
                                                   index=len(testStrings['extraClosingTilde']) - 1,
                                                   hed_string=testStrings['extraClosingTilde']),
            'multipleExtraOpeningDelimiters': report_error_type('extraDelimiter', character=',', index=0,
                                                                hed_string=testStrings[
                                                                    'multipleExtraOpeningDelimiters'])
                                              + report_error_type('extraDelimiter', character='~', index=1,
                                                                  hed_string=testStrings[
                                                                      'multipleExtraOpeningDelimiters'])
                                              + report_error_type('extraDelimiter', character=',', index=2,
                                                                  hed_string=testStrings[
                                                                      'multipleExtraOpeningDelimiters']),
            'multipleExtraClosingDelimiters': report_error_type('extraDelimiter', character='~', index=len(
                testStrings['multipleExtraClosingDelimiters']) - 3,
                                                                hed_string=testStrings[
                                                                    'multipleExtraClosingDelimiters'])
                                              + report_error_type('extraDelimiter', character='~', index=len(
                testStrings['multipleExtraClosingDelimiters']) - 2,
                                                                  hed_string=testStrings[
                                                                      'multipleExtraClosingDelimiters'])
                                              + report_error_type('extraDelimiter', character=',', index=len(
                testStrings['multipleExtraClosingDelimiters']) - 1,
                                                                  hed_string=testStrings[
                                                                      'multipleExtraClosingDelimiters'])
                                              + report_error_type('extraDelimiter', character=',', index=len(
                testStrings['multipleExtraClosingDelimiters']) - 4,
                                                                  hed_string=testStrings[
                                                                      'multipleExtraClosingDelimiters']),
            'multipleExtraMiddleDelimiters': report_error_type('extraDelimiter', character=',', index=23,
                                                               hed_string=testStrings[
                                                                   'multipleExtraMiddleDelimiters'])
                                             + report_error_type('extraDelimiter', character='~', index=141,
                                                                 hed_string=testStrings[
                                                                     'multipleExtraMiddleDelimiters'])
                                             + report_error_type('extraDelimiter', character=',', index=142,
                                                                 hed_string=testStrings[
                                                                     'multipleExtraMiddleDelimiters']),
            'valid': '',
            'validNestedParentheses': ''
        }
        self.validator(testStrings, expectedResults, expectedIssues)

    def test_invalid_characters(self):
        testStrings = {
            'openingBrace':
                '/Attribute/Spatial/Object side/Left,/Participant/Effect{/Body part/Arm',
            'closingBrace':
                '/Attribute/Spatial/Object side/Left,/Participant/Effect}/Body part/Arm',
            'openingBracket':
                '/Attribute/Spatial/Object side/Left,/Participant/Effect[/Body part/Arm',
            'closingBracket':
                '/Attribute/Spatial/Object side/Left,/Participant/Effect]/Body part/Arm'
        }
        expectedResults = {
            'openingBrace': False,
            'closingBrace': False,
            'openingBracket': False,
            'closingBracket': False
        }
        expectedIssues = {
            # NOT COMPLETE
            'openingBrace': report_error_type('character', tag='{'),
            'closingBrace': report_error_type('character', tag='}'),
            'openingBracket': report_error_type('character', tag='['),
            'closingBracket': report_error_type('character', tag=']')
        }
        self.validator(testStrings, expectedResults, expectedIssues)


class IndividualHedTags(TestHed):
    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda hed_string_delimiter: ''.join(
                [self.syntactic_warning_tag_validator.run_individual_tag_validators(*args) for args in
                 zip(hed_string_delimiter.get_tags(),
                     hed_string_delimiter.get_formatted_tags())]))
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda hed_string_delimiter: ''.join(
                [self.syntactic_tag_validator.run_individual_tag_validators(*args) for args in
                 zip(hed_string_delimiter.get_tags(),
                     hed_string_delimiter.get_formatted_tags())]))

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter))
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter))

    def test_exist_in_schema(self):
        testString = {
            'takesValue': 'Attribute/Temporal/Duration/3 ms',
            'full': 'Attribute/Spatial/Object side/Left',
            'extensionsAllowed': 'Item/Object/Person/Driver',
            'leafExtension': 'Event/Category/Initial context/Something',
            'nonExtensionsAllowed': 'Event/Nonsense',
            'illegalComma': 'Event/Label/This is a label,This/Is/A/Tag'
        }
        expectedResults = {
            'takesValue': True,
            'full': True,
            'extensionsAllowed': True,
            'leafExtension': False,
            'nonExtensionsAllowed': False,
            'illegalComma': False
        }
        expectedIssues = {
            'takesValue': '',
            'full': '',
            'extensionsAllowed': '',
            'leafExtension': report_error_type('valid', tag=testString['leafExtension']),
            'nonExtensionsAllowed': report_error_type('valid', tag=testString['nonExtensionsAllowed']),
            'illegalComma': report_error_type('commaValid', previous_tag='Event/Label/This is a label',
                                              tag='This/Is/A/Tag')
        }
        self.validator_semantic(testString, expectedResults, expectedIssues, False)

    def test_proper_capitalization(self):
        testString = {
            'proper': 'Event/Category/Sensory presentation',
            'camelCase': 'DoubleEvent/Something',
            'takesValue': 'Attribute/Temporal rate/20 Hz',
            'numeric': 'Attribute/Repetition/20',
            'lowercase': 'Event/something'
        }
        expectedResults = {
            'proper': True,
            'camelCase': True,
            'takesValue': True,
            'numeric': True,
            'lowercase': False
        }
        expectedIssues = {
            # NOT COMPLETE
            'proper': '',
            'camelCase': '',
            'takesValue': '',
            'numeric': '',
            'lowercase': report_warning_type('cap', tag=testString['lowercase'])
        }
        self.validator_syntactic(testString, expectedResults, expectedIssues, True)

    def test_child_required(self):
        testString = {
            'hasChild': 'Event/Category/Sensory presentation',
            'missingChild': 'Event/Category'
        }
        expectedResults = {
            'hasChild': True,
            'missingChild': False
        }
        expectedIssues = {
            # NOT COMPLETE
            'hasChild': '',
            'missingChild': report_error_type('requireChild', tag=testString['missingChild'])
        }
        self.validator_semantic(testString, expectedResults, expectedIssues, True)

    def test_required_units(self):
        testString = {
            'hasRequiredUnit': 'Attribute/Temporal/Duration/3 ms',
            'missingRequiredUnit': 'Attribute/Temporal/Duration/3',
            'notRequiredNumber': 'Attribute/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Color/Red/5.2e-1',
            'timeValue': 'Item/2D shape/Clock face/8:30'
        }
        expectedResults = {
            'hasRequiredUnit': True,
            'missingRequiredUnit': False,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'timeValue': True
        }
        expectedIssues = {
            'hasRequiredUnit': "",
            'missingRequiredUnit': report_warning_type('unitClass', tag=testString['missingRequiredUnit'],
                                                       default_unit='s'),
            'notRequiredNumber': "",
            'notRequiredScientific': "",
            'timeValue': ""
        }
        self.validator_semantic(testString, expectedResults, expectedIssues, True)

    def correct_units(self):
        testString = {
            'correctUnit': 'Event/Duration/3 ms',
            'correctUnitScientific': 'Event/Duration/3.5e1 ms',
            'incorrectUnit': 'Event/Duration/3 cm',
            'notRequiredNumber': 'Attribute/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Color/Red/5e-1',
            'properTime': 'Item/2D shape/Clock face/8:30',
            'invalidTime': 'Item/2D shape/Clock face/54:54'
        }
        expectedResults = {
            'correctUnit': True,
            'correctUnitScientific': True,
            'incorrectUnit': False,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'properTime': True,
            'invalidTime': False
        }
        legalTimeUnits = [
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
        expectedIssues = {
            # NOT COMPLETE
            'correctUnit': '',
            'correctUnitScientific': '',
            'incorrectUnit': report_error_type(testString['incorrectUnit'], ",".join(list(legalTimeUnits).sort())),
            'notRequiredNumber': '',
            'notRequiredScientific': '',
            'properTime': '',
            'invalidTime': report_error_type(testString['invalidTime'], ",".join(list(legalTimeUnits).sort()))
        }
        self.validate_semantic(testString, expectedResults, expectedIssues, True)


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
                                    hed_string_delimiter: self.syntactic_hed_input_reader._validate_tag_levels_in_hed_string(
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
        testStrings = {
            'topLevelDuplicate': 'Event/Category/Sensory presentation,Event/Category/Sensory presentation',
            'groupDuplicate': 'Item/Object/Vehicle/Train,(Event/Category/Sensory presentation,'
                              'Attribute/Visual/Color/Purple,Event/Category/Sensory presentation)',
            'noDuplicate': 'Event/Category/Sensory presentation,'
                           'Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple',
            'legalDuplicate': 'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,'
                              'Event/Category/Sensory presentation)',
        }
        expectedResults = {
            'topLevelDuplicate': False,
            'groupDuplicate': False,
            'legalDuplicate': True,
            'noDuplicate': True
        }
        expectedIssues = {
            'topLevelDuplicate': report_error_type('duplicate', tag='Event/Category/Sensory presentation'),
            'groupDuplicate': report_error_type('duplicate', tag='Event/Category/Sensory presentation'),
            'legalDuplicate': '',
            'noDuplicate': ''
        }
        self.validator_syntactic(testStrings, expectedResults, expectedIssues, False)

    def test_multiple_copies_unique_tags(self):
        testStrings = {
            'legal': 'Event/Description/Rail vehicles,Item/Object/Vehicle/Train,'
                     '(Item/Object/Vehicle/Train,Event/Category/Sensory presentation)',
            'multipleDesc': 'Event/Description/Rail vehicles,'
                            'Event/Description/Locomotive-pulled or multiple units,'
                            'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Sensory presentation)'
        }
        expectedResults = {
            'legal': True,
            'multipleDesc': False
        }
        expectedIssues = {
            'legal': '',
            'multipleDesc': report_error_type('unique', tag_prefix='Event/Description')
        }
        self.validator_semantic(testStrings, expectedResults, expectedIssues, True)


class TopLevelTags(TestHed):
    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                    hed_string_delimiter: self.semantic_warning_tag_validator.run_top_level_validators(
                                    hed_string_delimiter.get_formatted_top_level_tags()))
        else:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda hed_string_delimiter: self.semantic_tag_validator.run_top_level_validators(
                                    hed_string_delimiter.get_formatted_top_level_tags()))

    def test_includes_all_required_tags(self):
        testStrings = {
            'complete': 'Event/Label/Bus,Event/Category/Sensory presentation,'
                        'Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
            'missingLabel': 'Event/Category/Sensory presentation,Event/Description/Shown a picture of a bus,'
                            'Item/Object/Vehicle/Bus',
            'missingCategory': 'Event/Label/Bus,Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
            'missingDescription': 'Event/Label/Bus,Event/Category/Sensory presentation,Item/Object/Vehicle/Bus',
            'missingAllRequired': 'Item/Object/Vehicle/Bus',
        }
        expectedResults = {
            'complete': True,
            'missingLabel': False,
            'missingCategory': False,
            'missingDescription': False,
            'missingAllRequired': False,
        }
        expectedIssues = {
            'complete': "",
            'missingLabel': report_warning_type('required', tag_prefix='Event/Label'),
            'missingCategory': report_warning_type('required', tag_prefix='Event/Category'),
            'missingDescription': report_warning_type('required', tag_prefix='Event/Description'),
            'missingAllRequired': report_warning_type('required', tag_prefix='Event/Label') + report_warning_type(
                'required', tag_prefix='Event/Category') + report_warning_type('required',
                                                                               tag_prefix='Event/Description'),
        }
        self.validator_semantic(testStrings, expectedResults, expectedIssues, True)
