import random;
import unittest;
import os;

from hedvalidation.hed_string_delimiter import HedStringDelimiter;
from hedvalidation.hed_input_reader import HedInputReader;
from hedvalidation.error_reporter import report_error_type;
from hedvalidation.warning_reporter import report_warning_type;
from hedvalidation.tag_validator import TagValidator;
from hedvalidation.hed_dictionary import HedDictionary;


class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.generic_hed_input_reader = HedInputReader('Event/Category/')
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/HED.xml');
        self.hed_dictionary = HedDictionary(hed_xml);
        self.tagValidator = TagValidator(self.hed_dictionary)

    def validate(self, test_strings, expected_results, expected_issues):
        for test in test_strings:
            expected_issue = expected_issues[test]

            validation_issues = self.generic_hed_input_reader._validate_hed_string(test_strings[test])

            self.assertEqual(validation_issues, expected_issue, test_strings[test])
            self.assertCountEqual(validation_issues, expected_issue, test_strings[test])

    def validate_semantic_base(self, test_strings, expected_issues, expected_results, testFunction):
        for test_key in test_strings:
            hed_string_delimiter = HedStringDelimiter(test_strings[test_key])
            test_result = testFunction(hed_string_delimiter)
            expected_issue = expected_issues[test_key]
            expected_result = expected_results[test_key]
            has_no_issues = (test_result == "")

            if has_no_issues is True and expected_result is True:
                self.assertTrue(has_no_issues, test_strings[test_key])
            else:
                self.assertEqual(test_result, expected_issue, test_strings[test_key])
                self.assertCountEqual(test_result, expected_issue, test_strings[test_key])

    def validate_syntactic_base(self, test_strings, expected_issues, expected_results, testFunction):
        for test_key in test_strings:
            hed_string_delimiter = HedStringDelimiter(test_strings[test_key])
            testResult = testFunction(str(hed_string_delimiter), str(test_strings[test_key]))
            expectedIssue = expected_issues[test_key]
            expectedResult = expected_results[test_key]
            has_no_issues = (testResult == "")
            if has_no_issues is True and expectedResult is True:
                self.assertTrue(has_no_issues, test_strings[test_key])
            else:
                self.assertEqual(testResult, expectedIssue, test_strings[test_key])
                self.assertCountEqual(testResult, expectedIssue, test_strings[test_key])

    def test_mismatched_parentheses(self):
        testStrings = {
            'extraOpening': \
                '/Action/Reach/To touch,((/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            'extraClosing': \
                '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            'valid': \
                '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px'
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

        self.validate(testStrings, expectedResults, expectedIssues)

    ##########################################################################################################################################
    # Validator does not properly report errors with commas and does not report any error for extra tildes. (issue 3)
    ###########################################################################################################################################
    # def test_malformed_delimiters(self):
    #     testStrings = {
    #         'missingOpeningComma' : \
    #             '/Action/Reach/To touch(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
    #         'missingCLosingComma' : \
    #             '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
    #         'extraOpeningComma' : \
    #             ',/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
    #         'extraClosingComma' : \
    #             '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px,',
    #         'extraOpeningTilde' : \
    #             '~/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
    #         'extraClosingTilde' : \
    #             '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px~',
    #         'multipleExtraOpeningDelimiters' : \
    #             ',~,/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
    #         'multipleExtraClosingDelimiters' : \
    #             '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px,~~,',
    #         'multipleExtraMiddleDelimiters' : \
    #             '/Action/Reach/To touch,,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,~,/Attribute/Location/Screen/Left/23 px',
    #         'valid' : \
    #             '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
    #         'validNestedParentheses' : \
    #             '/Action/Reach/To touch,((/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px),Event/Duration/3 ms',
    #     }
    #
    #     expectedResults = {
    #         'missingOpeningComma' : False,
    #         'missingClosingComma' : False,
    #         'extraOpeningComma' : False,
    #         'extraClosingComma' : False,
    #         'extraOpeningTilde' : False,
    #         'extraClosingTilde' : False,
    #         'multipleExtraOpeningDelimiters' : False,
    #         'multipleExtraClosingDelimiters' : False,
    #         'multipleExtraMiddleDelimiters' : False,
    #         'valid' : True,
    #         'validNestedParentheses' : True
    #     }
    #     expectedIssues = {
    #         #NOT COMPLETE
    #         'missingOpeningComma' : report_error_type('comma'),
    #         'missingClosingComma': report_error_type('comma'),
    #         'extraOpeningComma': report_error_type('comma'),
    #         'extraClosingComma': report_error_type('comma'),
    #         'extraOpeningTilde': report_error_type('tilde'),
    #         'extraClosingTilde': report_error_type('tilde'),
    #         'multipleExtraOpeningDelimiters': report_error_type('comma'),
    #         'multipleExtraClosingDelimiters': report_error_type('comma'),
    #         'multipleExtraMiddleDelimiters': report_error_type('comma'),
    #         'valid': '',
    #         'validNestedParentheses': ''
    #     }
    #
    #     self.validate(testStrings, expectedResults, expectedIssues)

    def test_invalid_characters(self):
        testStrings = {
            'openingBrace': \
                '/Attribute/Object side/Left,/Participant/Effect{/Body part/Arm',
            'closingBrace': \
                '/Attribute/Object side/Left,/Participant/Effect}/Body part/Arm',
            'openingBracket': \
                '/Attribute/Object side/Left,/Participant/Effect[/Body part/Arm',
            'closingBracket': \
                '/Attribute/Object side/Left,/Participant/Effect]/Body part/Arm'
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
        self.validate(testStrings, expectedResults, expectedIssues)

    def validate_semantic(self, test_strings, expected_issues, expected_results, check_for_warnings):
        self.semanticHedInputReader = HedInputReader('Event/Category/', check_for_warnings=check_for_warnings)
        self.validate_semantic_base(test_strings, expected_issues, expected_results, \
                                    lambda hed_input: self.semanticHedInputReader. \
                                    _validate_individual_tags_in_hed_string(hed_input))

    # COME BACK TO THIS
    def test_exist_in_schema(self):
        testString = {
            'takesValue': 'Attribute/Duration/3 ms',
            'full': 'Attribute/Object side/Left',
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
        self.validate_semantic(testString, expectedIssues, expectedResults, False)

    def validate_syntactic(self, test_strings, expected_issues, expected_results, check_for_warnings=False):
        self.syntacticTagValidator = TagValidator(self.hed_dictionary, check_for_warnings, False)
        self.validate_syntactic_base(test_strings, expected_results, expected_issues,
                                     lambda parsed_string, original_tag:
                                     self.syntacticTagValidator.check_capitalization(formatted_tag=parsed_string,
                                                                                     original_tag=original_tag))

    def test_proper_capitalization(self):
        # errors with camelCase test string not being a valid test string
        testString = {
            'proper': 'Event/Category/Experimental stimulus',
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
        self.validate_syntactic(testString, expectedIssues, expectedIssues)

    #######################################################################################################
    # # need to address issue 3 before this test will preform properly
    #######################################################################################################
    # def test_no_more_than_two_tildes(self):
    #     testStrings = {
    #         'noTildeGroup': 'Event/Category/Experimental stimulus,(Item/Object/Vehicle/Train,Event/Category/Experimental stimulus)',
    #         'oneTildeGroup': 'Event/Category/Experimental stimulus,(Item/Object/Vehicle/Car ~ Attribute/Object control/Perturb)',
    #         'twoTildeGroup': 'Event/Category/Experimental stimulus,(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar, Attribute/Visual/Color/Red)',
    #         'invalidTildeGroup': 'Event/Category/Experimental stimulus,(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar, Attribute/Visual/Color/Red ~ Attribute/Object control/Perturb)',
    #     }
    #     expectedResults = {
    #         'noTildeGroup': True,
    #         'oneTildeGroup': True,
    #         'twoTildeGroup': True,
    #         'invalidTildeGroup': False
    #     }
    #     expectedIssues = {
    #         'noTildeGroup': '',
    #         'oneTildeGroup': '',
    #         'twoTildeGroup': '',
    #         'invalidTildeGroup': report_error_type('tilde', tag='Event/Category/Experimental stimulus,(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar, Attribute/Visual/Color/Red ~ Attribute/Object control/Perturb)')
    #     }
    #     # uses seemantic validaiton
    #     self.validate(testStrings, expectedResults, expectedIssues)

    ########################################################################
    # validator is not reporting an error with these tags
    # inside of the error reporter there is nothing to deal with required prefix missing
    ########################################################################
    # def validate_syntactic_1(self,testStrings, expectedResults, expectedIssues):
    #     self.validate_syntactic_base(testStrings, expectedResults, expectedIssues, lambda parsedString, originalTag:
    #    self.tagValidator.run_top_level_validators(formatted_top_level_tags=parsedString))
    #
    # def test_includes_all_required_tags(self):
    #     testStrings = {
    #         'complete': 'Event/Label/Bus,Event/Category/Experimental stimulus,Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
    #         'missingLabel': 'Event/Category/Experimental stimulus,Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
    #         'missingCategory': 'Event/Label/Bus,Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
    #         'missingDescription': 'Event/Label/Bus,Event/Category/Experimental stimulus,Item/Object/Vehicle/Bus',
    #         'missingAllRequired': 'Item/Object/Vehicle/Bus',
    #     }
    #     expectedResults = {
    #         'complete': True,
    #         'missingLabel': False,
    #         'missingCategory': False,
    #         'missingDescription': False,
    #         'missingAllRequired': False,
    #     }
    #     expectedIssues = {
    #         'complete': "",
    #         'missingLabel': report_error_type('valid', tag=testStrings['missingLabel']),
    #         'missingCategory': report_error_type('valid', tag=testStrings['missingCategory']),
    #         'missingDescription': report_error_type('valid', tag=testStrings['missingDescription']),
    #         'missingAllRequired': report_error_type('valid', tag=testStrings['missingAllRequired']),
    #     }
    #     self.validate_syntactic_1(testStrings, expectedIssues, expectedResults)

    ####################################################################################
    # Alexander has specific error messages being reported for missing children
    ####################################################################################

    def test_child_required(self):
        testString = {
            'hasChild': 'Event/Category/Experimental stimulus',
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
        self.validate_semantic(testString, expectedIssues, expectedResults, True)

    def test_required_units(self):
        testString = {
            'hasRequiredUnit': 'Attribute/Duration/3 ms',
            'missingRequiredUnit': 'Attribute/Duration/3',
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
            'missingRequiredUnit': report_warning_type('unitClass', testString['missingRequiredUnit'], 's'),
            'notRequiredNumber': "",
            'notRequiredScientific': "",
            'timeValue': ""
        }
        self.validate_semantic(testString, expectedIssues, expectedResults, True)

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
        self.validate_semantic(testString, expectedResults, expectedIssues)

    def validate_syntactic_duplicates(self, test_strings, expected_issues, expected_results, check_for_warnings):
        self.syntacticTagValidator = TagValidator(self.hed_dictionary, check_for_warnings, False)
        for test_key in test_strings:
            hed_string_delimiter = HedStringDelimiter(test_strings[test_key])
            testResult = self.generic_hed_input_reader._validate_tag_levels_in_hed_string(hed_string_delimiter)
            expectedIssue = expected_issues[test_key]
            expectedResult = expected_results[test_key]
            has_no_issues = (testResult == "")
            if has_no_issues is True and expectedResult is True:
                self.assertTrue(has_no_issues, test_strings[test_key])
            else:
                self.assertEqual(testResult, expectedIssue, test_strings[test_key])
                self.assertCountEqual(testResult, expectedIssue, test_strings[test_key])

    def test_no_duplicates(self):
        testStrings = {
            'topLevelDuplicate': 'Event/Category/Experimental stimulus,Event/Category/Experimental stimulus',
            'groupDuplicate': 'Item/Object/Vehicle/Train,(Event/Category/Experimental stimulus,Attribute/Visual/Color/Purple,Event/Category/Experimental stimulus)',
            'noDuplicate': 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple',
            'legalDuplicate': 'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Experimental stimulus)',
        }
        expectedResults = {
            'topLevelDuplicate': False,
            'groupDuplicate': False,
            'legalDuplicate': True,
            'noDuplicate': True
        }
        expectedIssues = {
            'topLevelDuplicate': report_error_type('duplicate', tag='Event/Category/Experimental stimulus'),
            'groupDuplicate': report_error_type('duplicate', tag='Event/Category/Experimental stimulus'),
            'legalDuplicate': '',
            'noDuplicate': ''
        }
        self.validate_syntactic_duplicates(testStrings, expectedIssues, expectedResults, True)

    def multiple_copies_unique_tags(self):
        testStrings = {
            'legal': 'Event/Description/Rail vehicles,Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Experimental stimulus)',
            'multipleDesc': 'Event/Description/Rail vehicles,Event/Description/Locomotive-pulled or multiple units,Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Experimental stimulus)'
        }
        expectedResults = {
            'legal': True,
            'multipleDesc': False
        }
        expectedIssues = {
            'legal': '',
            'multipleDesc': report_error_type()
        }
        self.validate(testStrings, expectedResults, expectedIssues)
