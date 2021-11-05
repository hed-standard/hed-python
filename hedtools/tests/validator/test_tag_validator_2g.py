import unittest

from hed.models.hed_string import HedString
from hed.errors.error_types import ValidationErrors
from tests.validator.test_tag_validator_base import TestValidatorBase
from functools import partial


class TestHed(TestValidatorBase):
    schema_file = '../data/legacy_xml/HED7.1.1.xml'


class FullHedString(TestHed):
    compute_forms = False

    @staticmethod
    def string_obj_func(validator, check_for_warnings):
        return validator._tag_validator.run_hed_string_validators

    def test_mismatched_parentheses(self):
        test_strings = {
            'extraOpening':
                'Action/Reach/To touch,((Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
                'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px',
            'extraClosing':
                'Action/Reach/To touch,(Attribute/Object side/Left,Participant/Effect/Body part/Arm),),'
                'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px',
            'valid':
                'Action/Reach/To touch,(Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
                'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px'
        }
        expected_results = {
            'extraOpening': False,
            'extraClosing': False,
            'valid': True
        }
        expected_issues = {
            'extraOpening': self.format_error_but_not_really(ValidationErrors.HED_PARENTHESES_MISMATCH,
                                                             opening_parentheses_count=2,
                                                             closing_parentheses_count=1),
            'extraClosing': self.format_error_but_not_really(ValidationErrors.HED_PARENTHESES_MISMATCH,
                                                             opening_parentheses_count=1,
                                                             closing_parentheses_count=2),
            'valid': []
        }

        self.validator_syntactic(test_strings, expected_results, expected_issues, False)

    def test_malformed_delimiters(self):
        test_strings = {
            'missingOpeningComma':
                'Action/Reach/To touch(Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
                'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px',
            'missingClosingComma':
                'Action/Reach/To touch,'
                '(Attribute/Object side/Left,Participant/Effect/Body part/Arm)Attribute/Location/Screen/Top/70 px,'
                'Attribute/Location/Screen/Left/23 px',
            'extraOpeningComma':
                ',Action/Reach/To touch,'
                '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
                'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px',
            'extraClosingComma':
                'Action/Reach/To touch,'
                '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,'
                'Attribute/Location/Screen/Left/23 px,',
            # 'extraOpeningParen':
            #     '(Action/Reach/To touch,'
            #     '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
            #     'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px',
            # 'extraClosingParen':
            #     'Action/Reach/To touch,'
            #     '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
            #     'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px)',
            'multipleExtraOpeningDelimiters':
                ',,,Action/Reach/To touch,'
                '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,'
                'Attribute/Location/Screen/Left/23 px',
            'multipleExtraClosingDelimiters':
                'Action/Reach/To touch,'
                '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),'
                'Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px,,,,',
            'multipleExtraMiddleDelimiters':
                'Action/Reach/To touch,'
                ',(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,'
                ',,Attribute/Location/Screen/Left/23 px',
            'valid':
                'Action/Reach/To touch,'
                '(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,'
                'Attribute/Location/Screen/Left/23 px',
            'validNestedParentheses':
                'Action/Reach/To touch,'
                '((Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,'
                'Attribute/Location/Screen/Left/23 px),Event/Duration/3 ms',
            'validNestedParentheses2':
                'Action/Reach/To touch,'
                '(((Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,'
                'Attribute/Location/Screen/Left/23 px)),Event/Duration/3 ms',
            'validNestedParentheses3':
                'Thing, (Thing, (Thing))',
            'validNestedParentheses4': 'Thing, ((Thing, (Thing)), Thing)',
            'invalidNestedParentheses': 'Thing, ((Thing, (Thing)) Thing)',
            # 'emptyGroup': 'Thing, ()'
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
            'missingOpeningComma': self.format_error_but_not_really(ValidationErrors.HED_COMMA_MISSING,
                                                                    tag="Action/Reach/To touch("),
            'missingClosingComma': self.format_error_but_not_really(ValidationErrors.HED_COMMA_MISSING,
                                                                    tag="Participant/Effect/Body part/Arm)"),
            'extraOpeningComma': self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                                                  source_string=test_strings['extraOpeningComma'],
                                                                  char_index=0),
            'extraClosingComma': self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                                                  source_string=test_strings['extraClosingComma'],
                                                                  char_index=len(
                                                                      test_strings['extraClosingComma']) - 1),
            # 'extraOpeningParen': self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
            #                                                       character='(', index_in_tag=0),
            # 'extraClosingParen': self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY, character=')',
            #                                       index_in_tag=len(test_strings['extraClosingParen']) - 1),
            'extraOpeningParen': self.format_error_but_not_really(ValidationErrors.HED_PARENTHESES_MISMATCH,
                                                                  opening_parentheses_count=2,
                                                                  closing_parentheses_count=1),
            'extraClosingParen': self.format_error_but_not_really(ValidationErrors.HED_PARENTHESES_MISMATCH,
                                                                  opening_parentheses_count=1,
                                                                  closing_parentheses_count=2),
            'multipleExtraOpeningDelimiters': self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                                                               source_string=test_strings[
                                                                                   'multipleExtraOpeningDelimiters'],
                                                                               char_index=0)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraOpeningDelimiters'],
                                               char_index=1)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraOpeningDelimiters'],
                                               char_index=2),
            'multipleExtraClosingDelimiters': self.format_error_but_not_really(
                ValidationErrors.HED_TAG_EMPTY,
                source_string=test_strings['multipleExtraClosingDelimiters'],
                char_index=len(test_strings['multipleExtraClosingDelimiters']) - 1)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraClosingDelimiters'],
                                               char_index=len(test_strings['multipleExtraClosingDelimiters']) - 2)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraClosingDelimiters'],
                                               char_index=len(test_strings['multipleExtraClosingDelimiters']) - 3)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraClosingDelimiters'],
                                               char_index=len(test_strings['multipleExtraClosingDelimiters']) - 4),
            'multipleExtraMiddleDelimiters': self.format_error_but_not_really(
                ValidationErrors.HED_TAG_EMPTY,
                source_string=test_strings['multipleExtraMiddleDelimiters'], char_index=22)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraMiddleDelimiters'],
                                               char_index=121)
            + self.format_error_but_not_really(ValidationErrors.HED_TAG_EMPTY,
                                               source_string=test_strings['multipleExtraMiddleDelimiters'],
                                               char_index=122),
            'valid': [],
            'validNestedParentheses': [],
            'validNestedParentheses2': [],
            'validNestedParentheses3': [],
            'validNestedParentheses4': [],
            'invalidNestedParentheses': self.format_error_but_not_really(ValidationErrors.HED_COMMA_MISSING,
                                                                         tag="Thing)) "),
            # 'emptyGroup': []
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)

    def test_invalid_characters(self):
        test_strings = {
            'openingBrace':
                'Attribute/Object side/Left,Participant/Effect{/Body part/Arm',
            'closingBrace':
                'Attribute/Object side/Left,Participant/Effect}/Body part/Arm',
            'openingBracket':
                'Attribute/Object side/Left,Participant/Effect[/Body part/Arm',
            'closingBracket':
                'Attribute/Object side/Left,Participant/Effect]/Body part/Arm'
        }
        expected_results = {
            'openingBrace': False,
            'closingBrace': False,
            'openingBracket': False,
            'closingBracket': False
        }
        expected_issues = {
            'openingBrace': self.format_error_but_not_really(ValidationErrors.HED_CHARACTER_INVALID, char_index=45,
                                                             source_string=test_strings['openingBrace']),
            'closingBrace': self.format_error_but_not_really(ValidationErrors.HED_CHARACTER_INVALID, char_index=45,
                                                             source_string=test_strings['closingBrace']),
            'openingBracket': self.format_error_but_not_really(ValidationErrors.HED_CHARACTER_INVALID, char_index=45,
                                                               source_string=test_strings['openingBracket']),
            'closingBracket': self.format_error_but_not_really(ValidationErrors.HED_CHARACTER_INVALID, char_index=45,
                                                               source_string=test_strings['closingBracket'])
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)

    def test_string_extra_slash_space(self):
        test_strings = {
            'twoLevelDoubleSlash': 'Event//Extension',
            'threeLevelDoubleSlash': 'Vehicle//Boat//Tanker',
            'tripleSlashes': 'Vehicle///Boat///Tanker',
            'mixedSingleAndDoubleSlashes': 'Vehicle//Boat/Tanker',
            'singleSlashWithSpace': 'Event/ Extension',
            'doubleSlashSurroundingSpace': 'Event/ /Extension',
            'doubleSlashThenSpace': 'Event// Extension',
            'sosPattern': 'Event///   ///Extension',
            'alternatingSlashSpace': 'Vehicle/ / Boat/ / Tanker',
            'leadingDoubleSlash': '//Event/Extension',
            'trailingDoubleSlash': 'Event/Extension//',
            'leadingDoubleSlashWithSpace': '/ /Event/Extension',
            'trailingDoubleSlashWithSpace': 'Event/Extension/ /',
        }
        # expected_event_extension = 'Event/Extension'
        # expected_tanker = 'Item/Object/Man-made/Vehicle/Boat/Tanker'
        expected_results = {
            'twoLevelDoubleSlash': False,
            'threeLevelDoubleSlash': False,
            'tripleSlashes': False,
            'mixedSingleAndDoubleSlashes': False,
            'singleSlashWithSpace': False,
            'doubleSlashSurroundingSpace': False,
            'doubleSlashThenSpace': False,
            'sosPattern': False,
            'alternatingSlashSpace': False,
            'leadingDoubleSlash': False,
            'trailingDoubleSlash': False,
            'leadingDoubleSlashWithSpace': False,
            'trailingDoubleSlashWithSpace': False,
        }
        expected_errors = {
            'twoLevelDoubleSlash': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                    index_in_tag=5,
                                                                    index_in_tag_end=7, tag=0),
            'threeLevelDoubleSlash': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                      index_in_tag=7,
                                                                      index_in_tag_end=9, tag=0)
            + self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                               index_in_tag=13, index_in_tag_end=15, tag=0),
            'tripleSlashes': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY, index_in_tag=7,
                                                              index_in_tag_end=10, tag=0)
            + self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                               index_in_tag=14, index_in_tag_end=17, tag=0),
            'mixedSingleAndDoubleSlashes': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                            index_in_tag=7, index_in_tag_end=9, tag=0),
            'singleSlashWithSpace': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                     index_in_tag=5, index_in_tag_end=7, tag=0),
            'doubleSlashSurroundingSpace': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                            index_in_tag=5, index_in_tag_end=8, tag=0),
            'doubleSlashThenSpace': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                     index_in_tag=5, index_in_tag_end=8, tag=0),
            'sosPattern': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY, index_in_tag=5,
                                                           index_in_tag_end=14, tag=0),
            'alternatingSlashSpace': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                      index_in_tag=7,
                                                                      index_in_tag_end=11, tag=0)
            + self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                               index_in_tag=15, index_in_tag_end=19, tag=0),
            'leadingDoubleSlash': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                   index_in_tag=0,
                                                                   index_in_tag_end=2, tag=0),
            'trailingDoubleSlash': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                    index_in_tag=15,
                                                                    index_in_tag_end=17, tag=0),
            'leadingDoubleSlashWithSpace': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                            index_in_tag=0, index_in_tag_end=3, tag=0),
            'trailingDoubleSlashWithSpace': self.format_error_but_not_really(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                                             index_in_tag=15, index_in_tag_end=18,
                                                                             tag=0),
        }
        self.validator_syntactic(test_strings, expected_results, expected_errors, False)

    def test_no_more_than_two_tildes(self):
        test_strings = {
            'noTildeGroup': 'Event/Category/Initial context,'
                            '(Item/Object/Vehicle/Train,Event/Category/Initial context)',
            'oneTildeGroup': 'Event/Category/Initial context,'
                             '(Item/Object/Vehicle/Car ~ Attribute/Object control/Perturb)',
            'twoTildeGroup': 'Event/Category/Initial context,'
                             '(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar,'
                             ' Attribute/Visual/Color/Red)',
            'invalidTildeGroup': 'Event/Category/Initial context,'
                                 '(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car,'
                                 ' Item/ID/RedCar, Attribute/Visual/Color/Red ~ Attribute/Object control/Perturb)',
        }
        expected_results = {
            'noTildeGroup': True,
            'oneTildeGroup': False,
            'twoTildeGroup': False,
            'invalidTildeGroup': False
        }
        expected_issues = {
            'noTildeGroup': [],
            'oneTildeGroup': self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                                              source_string=test_strings['oneTildeGroup'],
                                                              char_index=56),
            'twoTildeGroup': self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                                              source_string=test_strings['twoTildeGroup'],
                                                              char_index=49)
            + self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                               source_string=test_strings['twoTildeGroup'], char_index=77),
            'invalidTildeGroup': self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                                                  source_string=test_strings['invalidTildeGroup'],
                                                                  char_index=49)
            + self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                               source_string=test_strings['invalidTildeGroup'], char_index=77)
            + self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                               source_string=test_strings['invalidTildeGroup'], char_index=147)
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)


class IndividualHedTags(TestHed):
    @staticmethod
    def string_obj_func(validator, check_for_warnings):
        return partial(validator._validate_individual_tags_in_hed_string, check_for_warnings=check_for_warnings)

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
            'leafExtension': self.format_error_but_not_really(ValidationErrors.INVALID_EXTENSION, tag=0),
            'nonExtensionsAllowed': self.format_error_but_not_really(ValidationErrors.INVALID_EXTENSION,
                                                                     tag=0),
            'usedToBeIllegalComma': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                     tag=1,
                                                                     index_in_tag=0, index_in_tag_end=4),
            'testExtensionExists': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                                    index_in_tag=19, index_in_tag_end=24,
                                                                    expected_parent_tag="Event"),
            'testExtensionExists2': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                     tag=0,
                                                                     index_in_tag=0, index_in_tag_end=8),
            'testInvalidShortForm': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                     index_in_tag=0, index_in_tag_end=8,
                                                                     tag=0),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_proper_capitalization(self):
        test_strings = {
            'proper': 'Event/Category/Initial context',
            'camelCase': 'EvEnt/Something',
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
            'lowercase': self.format_error_but_not_really(ValidationErrors.HED_STYLE_WARNING, tag=0)
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
            'missingChild': self.format_error_but_not_really(ValidationErrors.HED_TAG_REQUIRES_CHILD, tag=0)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_required_units(self):
        test_strings = {
            'hasRequiredUnit': 'Event/Duration/3 ms',
            'missingRequiredUnit': 'Event/Duration/3',
            'notRequiredNoNumber': 'Attribute/Visual/Color/Red',
            'notRequiredNumber': 'Attribute/Visual/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Visual/Color/Red/5.2e-1',
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
            'missingRequiredUnit': self.format_error_but_not_really(ValidationErrors.HED_UNITS_DEFAULT_USED, tag=0,
                                                                    default_unit='s'),
            'notRequiredNoNumber': [],
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'timeValue': [],
            'invalidTimeValue': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID,
                                                                 tag=0,
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
            'notRequiredNumber': 'Attribute/Visual/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Visual/Color/Red/5e-1',
            'properTime': 'Item/2D shape/Clock face/08:30',
            'invalidTime': 'Item/2D shape/Clock face/54:54',
            # Theses should both fail, as this tag validator isn't set to accept placeholders
            'placeholderNoUnit': 'Event/Duration/#',
            'placeholderUnit': 'Event/Duration/# ms',
            'placeholderWrongUnit': 'Event/Duration/# hz',
            'placeholderWrongUnitSecondTag': 'Event, Event/Duration/# hz',
            'noExtensionRequireChild': 'Event/Duration',
            'noExtension': 'Attribute/Temporal rate'
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
            'placeholderWrongUnit': False,
            'placeholderWrongUnitSecondTag': False,
            'noExtensionRequireChild': False,
            'noExtension': True
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
            'incorrectUnit': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID,
                                                              tag=0,
                                                              unit_class_units=legal_time_units),
            'incorrectPluralUnit': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID,
                                                                    tag=0,
                                                                    unit_class_units=legal_freq_units),
            'incorrectSymbolCapitalizedUnit': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID,
                                                                               tag=0,
                                                                               unit_class_units=legal_freq_units),
            'incorrectSymbolCapitalizedUnitModifier': self.format_error_but_not_really(
                ValidationErrors.HED_UNITS_INVALID,
                tag=0,
                unit_class_units=legal_freq_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'properTime': [],
            'invalidTime': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                                            unit_class_units=legal_clock_time_units),

            'placeholderNoUnit': self.format_error_but_not_really(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                  tag=0, index_in_tag=15, index_in_tag_end=16,
                                                                  actual_error=ValidationErrors.HED_VALUE_INVALID)
            + self.format_error_but_not_really(ValidationErrors.HED_UNITS_DEFAULT_USED, tag=0, default_unit="s"),
            'placeholderUnit': self.format_error_but_not_really(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                tag=0, index_in_tag=15, index_in_tag_end=16,
                                                                actual_error=ValidationErrors.HED_VALUE_INVALID),
            'placeholderWrongUnit': self.format_error_but_not_really(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                     tag=0, index_in_tag=15, index_in_tag_end=16,
                                                                     actual_error=ValidationErrors.HED_VALUE_INVALID)
            + self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                               unit_class_units=legal_time_units),
            'placeholderWrongUnitSecondTag': self.format_error_but_not_really(
                ValidationErrors.INVALID_TAG_CHARACTER, tag=1, index_in_tag=15, index_in_tag_end=16,
                actual_error=ValidationErrors.HED_VALUE_INVALID)
            + self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=1,
                                               unit_class_units=legal_time_units),
            'noExtensionRequireChild': self.format_error_but_not_really(ValidationErrors.HED_TAG_REQUIRES_CHILD, tag=0),
            'noExtension': []
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


class HedTagLevels(TestHed):
    @staticmethod
    def string_obj_func(validator, check_for_warnings):
        return validator._validate_groups_in_hed_string

    def test_no_duplicates(self):
        test_strings = {
            'topLevelDuplicate': 'Event/Category/Initial context,Event/Category/Initial context',
            'groupDuplicate': 'Item/Object/Vehicle/Train,(Event/Category/Initial context,'
                              'Attribute/Visual/Color/Purple,Event/Category/Initial context)',
            'noDuplicate': 'Event/Category/Initial context,'
                           'Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple',
            'legalDuplicate': 'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,'
                              'Event/Category/Initial context)',
        }
        expected_results = {
            'topLevelDuplicate': False,
            'groupDuplicate': False,
            'legalDuplicate': True,
            'noDuplicate': True
        }
        expected_issues = {
            'topLevelDuplicate': self.format_error_but_not_really(ValidationErrors.HED_TAG_REPEATED,
                                                                  tag=1),
            'groupDuplicate': self.format_error_but_not_really(ValidationErrors.HED_TAG_REPEATED,
                                                               tag=3),
            'legalDuplicate': [],
            'noDuplicate': []
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)

    def test_empty_groups(self):
        test_strings = {
            'emptyGroup': 'Event, ()'
        }
        expected_results = {
            'emptyGroup': False
        }
        expected_issues = {
            'emptyGroup': self.format_error_but_not_really(ValidationErrors.HED_GROUP_EMPTY, tag=1000 + 1)
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)


class RequiredTags(TestHed):
    @staticmethod
    def string_obj_func(validator, check_for_warnings):
        return partial(validator._validate_tags_in_hed_string, check_for_warnings=check_for_warnings)

    def test_includes_all_required_tags(self):
        test_strings = {
            'complete': 'Event/Label/Bus,Event/Category/Initial context,'
                        'Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus,'
                        'Event/Category/NotMissing',
            'missingLabel': 'Event/Category/Initial context,Event/Description/Shown a picture of a bus,'
                            'Item/Object/Vehicle/Bus',
            'missingCategory': 'Event/Label/Bus,Event/Description/Shown a picture of a bus,Item/Object/Vehicle/Bus',
            'missingDescription': 'Event/Label/Bus,Event/Category/Initial context,Item/Object/Vehicle/Bus',
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
            'missingLabel': self.format_error_but_not_really(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                                             tag_prefix='Event/Label'),
            'missingCategory': self.format_error_but_not_really(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                                                tag_prefix='Event/Category'),
            'missingDescription': self.format_error_but_not_really(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                                                   tag_prefix='Event/Description'),
            'missingAllRequired': self.format_error_but_not_really(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                                                   tag_prefix='Event/Label')
            + self.format_error_but_not_really(ValidationErrors.HED_REQUIRED_TAG_MISSING, tag_prefix='Event/Category')
            + self.format_error_but_not_really(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                               tag_prefix='Event/Description'),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_multiple_copies_unique_tags(self):
        test_strings = {
            'legal': 'Event/Description/Rail vehicles,Item/Object/Vehicle/Train,'
                     '(Item/Object/Vehicle/Train,Event/Category/Initial context)',
            'multipleDesc': 'Event/Description/Rail vehicles,'
                            'Event/Description/Locomotive-pulled or multiple units,'
                            'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,Event/Category/Initial context)',
            # I think this is illegal in hed2 style schema now.
            'multipleDescIncShort': 'Event/Description/Rail vehicles,'
                                    'Description/Locomotive-pulled or multiple units,'
                                    'Item/Object/Vehicle/Train,(Item/Object/Vehicle/Train,\
                                    Event/Category/Initial context)'
        }
        expected_results = {
            'legal': True,
            'multipleDesc': False,
            'multipleDescIncShort': False
        }
        expected_issues = {
            'legal': [],
            'multipleDesc': self.format_error_but_not_really(ValidationErrors.HED_TAG_NOT_UNIQUE,
                                                             tag_prefix='Event/Description'),
            'multipleDescIncShort': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                     tag=1, index_in_tag=0, index_in_tag_end=11)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class TestHedInvalidChars(TestHed):
    compute_forms = False

    @staticmethod
    def string_obj_func(validator, check_for_warnings):
        return validator._tag_validator.run_hed_string_validators

    def test_no_more_than_two_tildes(self):
        test_strings = {
            'noTildeGroup': 'Event/Category/Initial context,'
                            '(Item/Object/Vehicle/Train,Event/Category/Initial context)',
            'oneTildeGroup': 'Event/Category/Initial context,'
                             '(Item/Object/Vehicle/Car ~ Attribute/Object control/Perturb)',
            'twoTildeGroup': 'Event/Category/Initial context,'
                             '(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar,'
                             ' Attribute/Visual/Color/Red)',
            'invalidTildeGroup': 'Event/Category/Initial context,'
                                 '(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car,'
                                 ' Item/ID/RedCar, Attribute/Visual/Color/Red ~ Attribute/Object control/Perturb)',
        }
        expected_results = {
            'noTildeGroup': True,
            'oneTildeGroup': False,
            'twoTildeGroup': False,
            'invalidTildeGroup': False
        }
        expected_issues = {
            'noTildeGroup': [],
            'oneTildeGroup': self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                                              source_string=test_strings['oneTildeGroup'],
                                                              char_index=56),
            'twoTildeGroup': self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                                              source_string=test_strings['twoTildeGroup'],
                                                              char_index=49)
            + self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                               source_string=test_strings['twoTildeGroup'], char_index=77),
            'invalidTildeGroup': self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                                                  source_string=test_strings['invalidTildeGroup'],
                                                                  char_index=49)
            + self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                               source_string=test_strings['invalidTildeGroup'], char_index=77)
            + self.format_error_but_not_really(ValidationErrors.HED_TILDES_UNSUPPORTED,
                                               source_string=test_strings['invalidTildeGroup'], char_index=147)
        }
        self.validator_syntactic(test_strings, expected_results, expected_issues, False)


class TestHedTags(TestHed):
    def test_valid_comma_separated_paths(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = True
        issues = self.semantic_tag_validator.run_hed_string_validators(HedString(hed_string))
        self.assertEqual(result, True)
        self.assertCountEqual(issues, [])


class TestOldHed(TestHed):
    schema_file = '../data/legacy_xml/HED7.0.4.xml'


class OldIndividualHedTags(TestOldHed):
    @staticmethod
    def string_obj_func(validator, check_for_warnings):
        return partial(validator._validate_individual_tags_in_hed_string, check_for_warnings=check_for_warnings)

    def test_required_units(self):
        test_strings = {
            'hasRequiredUnit': 'Event/Duration/3 ms',
            'missingRequiredUnit': 'Event/Duration/3',
            'notRequiredNumber': 'Attribute/Visual/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Visual/Color/Red/5.2e-1',
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
            'missingRequiredUnit': self.format_error_but_not_really(ValidationErrors.HED_UNITS_DEFAULT_USED, tag=0,
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
            'notRequiredNumber': 'Attribute/Visual/Color/Red/0.5',
            'notRequiredScientific': 'Attribute/Visual/Color/Red/5e-1',
            'properTime': 'Item/2D shape/Clock face/08:30',
            'invalidTime': 'Item/2D shape/Clock face/54:54',
            'multiUnitClass': 'Attribute/Direction/Top/32 degrees',
            'multiUnitClassBad': 'Attribute/Direction/Top/32 notdegrees'
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
            'invalidTime': False,
            'multiUnitClass': True,
            'multiUnitClassBad': False
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
        legal_multi_unit = \
            "cm,degree,degrees,feet,foot,km,m,meter,meters,mile,miles,mm,pixel,pixels,px,radian,radians".split(",")
        expected_issues = {
            'correctUnit': [],
            'correctUnitWord': [],
            'correctUnitScientific': [],
            'incorrectUnit': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                                              unit_class_units=legal_time_units),
            'incorrectUnitWord': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                                                  unit_class_units=legal_time_units),
            'incorrectPrefix': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                                                unit_class_units=legal_time_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'properTime': [],
            'invalidTime': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                                            unit_class_units=legal_time_units),
            'multiUnitClass': [],
            'multiUnitClassBad': self.format_error_but_not_really(ValidationErrors.HED_UNITS_INVALID, tag=0,
                                                                  unit_class_units=legal_multi_unit),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


if __name__ == '__main__':
    unittest.main()
