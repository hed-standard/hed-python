import unittest
import os

from hed.errors import error_reporter
from hed import schema
from hed.errors.error_types import ValidationErrors, DefinitionErrors
from hed.schema.hed_schema_group import HedSchemaGroup
from hed.errors.exceptions import HedFileError
from tests.validator.test_tag_validator_base import TestValidatorBase
from functools import partial


class TestHed3(TestValidatorBase):
    schema_file = None

    @classmethod
    def setUpClass(cls):
        schema_file = '../data/validator_tests/HED8.0.0_added_tests.mediawiki'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = schema.load_schema(hed_xml)
        hed_schema2 = schema.load_schema(hed_xml, schema_namespace="tl:")
        cls.hed_schema = HedSchemaGroup([hed_schema1, hed_schema2])

        cls.error_handler = error_reporter.ErrorHandler()
        super().setUpClass()

    def test_invalid_load(self):
        schema_file = '../data/schema_tests/HED8.0.0t.xml'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = schema.load_schema(hed_xml, schema_namespace="tl:")
        hed_schema2 = schema.load_schema(hed_xml, schema_namespace="tl:")

        self.assertRaises(HedFileError, HedSchemaGroup, [hed_schema1, hed_schema2])

    def test_invalid_load_prefix(self):
        schema_file = '../data/schema_tests/HED8.0.0t.xml'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = schema.load_schema(hed_xml)
        hed_schema2 = schema.load_schema(hed_xml)

        self.assertRaises(HedFileError, HedSchemaGroup, [hed_schema1, hed_schema2])


class IndividualHedTagsShort(TestHed3):
    @staticmethod
    def string_obj_func(validator):
        return partial(validator._validate_individual_tags_in_hed_string)

    def test_exist_in_schema(self):
        test_strings = {
            'takesValue': 'tl:Duration/3 ms',
            'full': 'tl:Animal-agent',
            'extensionsAllowed': 'tl:Item/Beaver',
            'leafExtension': 'tl:Experiment-procedure/Something',
            'nonExtensionsAllowed': 'tl:Event/Nonsense',
            'invalidExtension': 'tl:Agent/Red',
            'invalidExtension2': 'tl:Agent/Red/Extension2',
            'usedToBeIllegalComma': 'tl:Label/This is a label,tl:This/Is/A/Tag',
            'legalDef': 'tl:Def/Item',
            'legalDefExpand': 'tl:Def-expand/Item',
            'illegalDefinition': 'tl:Definition/Item',
            'unknownPrefix': 'ul:Definition/Item'
        }
        expected_results = {
            'takesValue': True,
            'full': True,
            'extensionsAllowed': True,
            'leafExtension': False,
            'nonExtensionsAllowed': False,
            'invalidExtension': False,
            'invalidExtension2': False,
            'usedToBeIllegalComma': False,
            'legalDef': True,
            'legalDefExpand': True,
            'illegalDefinition': False,
            'unknownPrefix': False
        }
        expected_issues = {
            'takesValue': [],
            'full': [],
            'extensionsAllowed': [],
            'leafExtension': self.format_error(ValidationErrors.TAG_EXTENSION_INVALID, tag=0),
            'nonExtensionsAllowed': self.format_error(ValidationErrors.TAG_EXTENSION_INVALID, tag=0),
            'invalidExtension': self.format_error(
                ValidationErrors.INVALID_PARENT_NODE, tag=0, index_in_tag=9, index_in_tag_end=12,
                expected_parent_tag="Property/Sensory-property/Sensory-attribute/Visual-attribute" +
                                    "/Color/CSS-color/Red-color/Red"),
            'invalidExtension2': self.format_error(
                ValidationErrors.INVALID_PARENT_NODE, tag=0, index_in_tag=9, index_in_tag_end=12,
                expected_parent_tag="Property/Sensory-property/Sensory-attribute/Visual-attribute" +
                                    "/Color/CSS-color/Red-color/Red"),
            'usedToBeIllegalComma': self.format_error(ValidationErrors.NO_VALID_TAG_FOUND, tag=1,
                                                      index_in_tag=3, index_in_tag_end=7),
            'legalDef': [],
            'legalDefExpand': [],
            'illegalDefinition': self.format_error(DefinitionErrors.BAD_DEFINITION_LOCATION, tag=0),
            'unknownPrefix': self.format_error(
                ValidationErrors.HED_LIBRARY_UNMATCHED, tag=0, unknown_prefix="ul:", known_prefixes=["", "tl:"]),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_proper_capitalization(self):
        test_strings = {
            'proper': 'tl:Event/Sensory-event',
            'camelCase': 'tl:EvEnt/Sensory-event',
            'takesValue': 'tl:Sampling-rate/20 Hz',
            'numeric': 'tl:Statistical-uncertainty/20',
            'lowercase': 'tl:Event/sensory-event'
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
            'lowercase': self.format_error(ValidationErrors.STYLE_WARNING, tag=0)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_child_required(self):
        test_strings = {
            'hasChild': 'tl:Experimental-stimulus',
            'missingChild': 'tl:Label'
        }
        expected_results = {
            'hasChild': True,
            'missingChild': False
        }
        expected_issues = {
            'hasChild': [],
            'missingChild': self.format_error(ValidationErrors.TAG_REQUIRES_CHILD, tag=0)
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_required_units(self):
        test_strings = {
            'hasRequiredUnit': 'Duration/3 ms',
            'missingRequiredUnit': 'Duration/3',
            'notRequiredNoNumber': 'Age',
            'notRequiredNumber': 'Age/0.5',
            'notRequiredScientific': 'Age/5.2e-1',
            'timeValue': 'Clock-face/08:30',
            # Update test - This one is currently marked as valid because clock face isn't in hed3
            'invalidTimeValue': 'Clock-face/8:30',
        }
        expected_results = {
            'hasRequiredUnit': True,
            'missingRequiredUnit': False,
            'notRequiredNoNumber': True,
            'notRequiredNumber': True,
            'notRequiredScientific': True,
            'timeValue': False,
            'invalidTimeValue': False,
        }
        # legal_clock_time_units = ['hour:min', 'hour:min:sec']
        expected_issues = {
            'hasRequiredUnit': [],
            'missingRequiredUnit': self.format_error(
                ValidationErrors.UNITS_MISSING, tag=0, default_unit='s'),
            'notRequiredNoNumber': [],
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'timeValue': self.format_error(
                ValidationErrors.TAG_EXTENDED, tag=0, index_in_tag=10, index_in_tag_end=None),
            'invalidTimeValue': self.format_error(
                ValidationErrors.TAG_EXTENDED, tag=0, index_in_tag=10, index_in_tag_end=None),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_correct_units(self):
        test_strings = {
            'correctUnit': 'tl:Duration/3 ms',
            'correctUnitScientific': 'tl:Duration/3.5e1 ms',
            'correctPluralUnit': 'tl:Duration/3 milliseconds',
            'correctNoPluralUnit': 'tl:Frequency/3 hertz',
            'correctNonSymbolCapitalizedUnit': 'tl:Duration/3 MilliSeconds',
            'correctSymbolCapitalizedUnit': 'tl:Frequency/3 kHz',
            'incorrectUnit': 'tl:Duration/3 cm',
            'incorrectPluralUnit': 'tl:Frequency/3 hertzs',
            'incorrectSymbolCapitalizedUnit': 'tl:Frequency/3 hz',
            'incorrectSymbolCapitalizedUnitModifier': 'tl:Frequency/3 KHz',
            'notRequiredNumber': 'tl:Statistical-accuracy/0.5',
            'notRequiredScientific': 'tl:Statistical-accuracy/5e-1',
            'specialAllowedCharBadUnit': 'tl:Creation-date/bad_date',
            'specialAllowedCharUnit': 'tl:Creation-date/1900-01-01T01:01:01',
            # todo: restore these when we have a currency node in the valid beta schema.
            # 'specialAllowedCharCurrency': 'Event/Currency-Test/$100',
            # 'specialNotAllowedCharCurrency': 'Event/Currency-Test/@100'
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
            'specialAllowedCharBadUnit': False,
            'specialAllowedCharUnit': True,
            'properTime': True,
            'invalidTime': True,
            # 'specialAllowedCharCurrency': True,
            # 'specialNotAllowedCharCurrency': False,
        }
        legal_time_units = ['s', 'second', 'day', 'minute', 'hour']
        # legal_clock_time_units = ['hour:min', 'hour:min:sec']
        # legal_datetime_units = ['YYYY-MM-DDThh:mm:ss']
        legal_freq_units = ['Hz', 'hertz']
        # legal_currency_units = ['dollar', "$", "point"]

        expected_issues = {
            'correctUnit': [],
            'correctUnitScientific': [],
            'correctPluralUnit': [],
            'correctNoPluralUnit': [],
            'correctNonSymbolCapitalizedUnit': [],
            'correctSymbolCapitalizedUnit': [],
            'incorrectUnit': self.format_error(
                ValidationErrors.UNITS_INVALID, tag=0, units=legal_time_units),
            'incorrectPluralUnit': self.format_error(
                ValidationErrors.UNITS_INVALID, tag=0, units=legal_freq_units),
            'incorrectSymbolCapitalizedUnit': self.format_error(
                ValidationErrors.UNITS_INVALID, tag=0, units=legal_freq_units),
            'incorrectSymbolCapitalizedUnitModifier': self.format_error(
                ValidationErrors.UNITS_INVALID, tag=0, units=legal_freq_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            'specialAllowedCharBadUnit':  self.format_error(ValidationErrors.VALUE_INVALID, tag=0),
            'specialAllowedCharUnit': [],
            # 'properTime': [],
            # 'invalidTime': self.format_error(ValidationErrors.UNITS_INVALID,  tag=0,
            #                                 units=legal_clock_time_units)
            # 'specialAllowedCharCurrency': [],
            # 'specialNotAllowedCharCurrency': self.format_error(ValidationErrors.UNITS_INVALID,
            #                                                                    tag=0,
            #                                                                    units=legal_currency_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_extensions(self):
        test_strings = {
            'invalidExtension': 'tl:Experiment-control/Animal-agent',
        }
        expected_results = {
            'invalidExtension': False,
        }
        expected_issues = {
            'invalidExtension': self.format_error(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                  index_in_tag=19 + 3, index_in_tag_end=31 + 3,
                                                  expected_parent_tag="Agent/Animal-agent"),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_invalid_placeholder_in_normal_string(self):
        test_strings = {
            'invalidPlaceholder': 'tl:Duration/# ms',
        }
        expected_results = {
            'invalidPlaceholder': False,
        }
        expected_issues = {
            'invalidPlaceholder': self.format_error(ValidationErrors.INVALID_TAG_CHARACTER,
                                                    tag=0, index_in_tag=12, index_in_tag_end=13,
                                                    actual_error=ValidationErrors.PLACEHOLDER_INVALID),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_span_reporting(self):
        test_strings = {
            'orgTagDifferent': 'tl:Duration/23 hz',
            'orgTagDifferent2': 'tl:Duration/23 hz, Duration/23 hz',
        }
        expected_results = {
            'orgTagDifferent': False,
            'orgTagDifferent2': False,
        }
        tag_unit_class_units = ['day', 'hour', 'minute', 's', 'second']
        expected_issues = {
            'orgTagDifferent': self.format_error(ValidationErrors.UNITS_INVALID, tag=0,
                                                 units=tag_unit_class_units),
            'orgTagDifferent2': self.format_error(ValidationErrors.UNITS_INVALID, tag=0,
                                                  units=tag_unit_class_units)
            + self.format_error(ValidationErrors.UNITS_INVALID, tag=1,
                                units=tag_unit_class_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class TestTagLevels3(TestHed3):
    @staticmethod
    def string_obj_func(validator):
        return validator._group_validator.run_tag_level_validators

    def test_no_duplicates(self):
        test_strings = {
            'topLevelDuplicate': 'tl:Event/Sensory-event,tl:Event/Sensory-event',
            'groupDuplicate': 'tl:Item/Object/Man-made-object/VehicleTrain,(tl:Event/Sensory-event,'
                              'tl:Purple-color/Purple,tl:Event/Sensory-event)',
            'noDuplicate': 'tl:Event/Sensory-event,'
                           'tl:Item/Object/Man-made-object/VehicleTrain,'
                           'tl:Purple-color/Purple',
            'legalDuplicate': 'tl:Item/Object/Man-made-object/VehicleTrain,\
            (tl:Item/Object/Man-made-object/VehicleTrain,'
                              'tl:Event/Sensory-event)',
        }
        expected_results = {
            'topLevelDuplicate': False,
            'groupDuplicate': False,
            'legalDuplicate': True,
            'noDuplicate': True
        }
        expected_issues = {
            'topLevelDuplicate': self.format_error(ValidationErrors.HED_TAG_REPEATED, tag=1),
            'groupDuplicate': self.format_error(ValidationErrors.HED_TAG_REPEATED, tag=3),
            'legalDuplicate': [],
            'noDuplicate': []
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_no_duplicates_semantic(self):
        test_strings = {
            'mixedLevelDuplicates': 'tl:Man-made-object/Vehicle/Boat, tl:Vehicle/Boat',
            'mixedLevelDuplicates2': 'tl:Man-made-object/Vehicle/Boat, tl:Boat'
        }
        expected_results = {
            'mixedLevelDuplicates': False,
            'mixedLevelDuplicates2': False,
        }
        expected_issues = {
            'mixedLevelDuplicates': self.format_error(ValidationErrors.HED_TAG_REPEATED,
                                                      tag=1),
            'mixedLevelDuplicates2': self.format_error(ValidationErrors.HED_TAG_REPEATED,
                                                       tag=1),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_topLevelTagGroup_validation(self):
        test_strings = {
            'invalid1': 'tl:Definition/InvalidDef',
            'valid1': '(tl:Definition/ValidDef)',
            'valid2': '(tl:Definition/ValidDef), (tl:Definition/ValidDef2)',
            'invalid2': '(tl:Event, (tl:Definition/InvalidDef2))',
            'invalidTwoInOne': '(tl:Definition/InvalidDef2, tl:Definition/InvalidDef3)',
            'invalid2TwoInOne': '(tl:Definition/InvalidDef2, tl:Onset)',
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
            'invalid1': self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG,
                                          tag=0, actual_error=ValidationErrors.DEFINITION_INVALID)
            + self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG, tag=0),
            'valid1': [],
            'valid2': [],
            'invalid2': self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG, tag=1, actual_error=ValidationErrors.DEFINITION_INVALID)
            + self.format_error(ValidationErrors.HED_TOP_LEVEL_TAG, tag=1),
            'invalidTwoInOne': self.format_error(
                ValidationErrors.HED_MULTIPLE_TOP_TAGS, tag=0,
                multiple_tags="tl:Definition/InvalidDef3".split(", ")),
            'invalid2TwoInOne': self.format_error(
                ValidationErrors.HED_MULTIPLE_TOP_TAGS, tag=0,
                multiple_tags="tl:Onset".split(", ")),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_taggroup_validation(self):
        test_strings = {
            'invalid1': 'tl:Def-Expand/InvalidDef',
            'invalid2': 'tl:Def-Expand/InvalidDef, tl:Event, (tl:Event)',
            'invalid3': 'tl:Event, (tl:Event), tl:Def-Expand/InvalidDef',
            'valid1': '(tl:Def-Expand/ValidDef)',
            'valid2': '(tl:Def-Expand/ValidDef), (tl:Def-Expand/ValidDef2)',
            'valid3': '(tl:Event, (tl:Def-Expand/InvalidDef2))',
            # This case should possibly be flagged as invalid
            'semivalid1': '(tl:Def-Expand/InvalidDef2, tl:Def-Expand/InvalidDef3)',
            'semivalid2': '(tl:Def-Expand/InvalidDef2, tl:Onset)',
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
            'invalid1': self.format_error(ValidationErrors.HED_TAG_GROUP_TAG, tag=0),
            'invalid2': self.format_error(ValidationErrors.HED_TAG_GROUP_TAG, tag=0),
            'invalid3': self.format_error(ValidationErrors.HED_TAG_GROUP_TAG, tag=2),
            'valid1': [],
            'valid2': [],
            'valid3': [],
            'semivalid1': [],
            'semivalid2': []
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class RequiredTags(TestHed3):
    @staticmethod
    def string_obj_func(validator):
        return partial(validator._group_validator.run_all_tags_validators)

    def test_includes_all_required_tags(self):
        test_strings = {
            'complete': 'Animal-agent, Action, tl:Animal-agent, tl:Action',
            'missingAgent': 'Action, tl:Animal-agent, tl:Action',
            'missingAction': 'Animal-agent, tl:Animal-agent, tl:Action',
            'inSubGroup': 'Animal-agent, (Action, tl:Animal-agent, tl:Action)',
            'missingAll': 'Event'
        }
        expected_results = {
            'complete': True,
            'missingAgent': False,
            'missingAction': False,
            'inSubGroup': True,
            'missingAll': False,
        }
        expected_issues = {
            'complete': [],
            'missingAgent': self.format_error(ValidationErrors.REQUIRED_TAG_MISSING,
                                              tag_namespace='Agent/Animal-agent'),
            'missingAction': self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace='Action'),
            'inSubGroup': [],
            'missingAll':
                self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace='Action')
                + self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace='Agent/Animal-agent')
                + self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace='tl:Action')
                + self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace='tl:Agent/Animal-agent'),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_multiple_copies_unique_tags(self):
        test_strings = {
            'legal': 'tl:Event-context,'
                     '(Vehicle,Event), Animal-agent, Action, tl:Animal-agent, tl:Action',
            'multipleDesc': 'tl:Event-context,'
                            'tl:Event-context,'
                            'Vehicle,(Vehicle,tl:Event-context), Animal-agent, Action, tl:Animal-agent, tl:Action',
            'multipleDescIncShort': 'tl:Event-context,'
                                    'tl:Organizational-property/Event-context,'
                                    ' Animal-agent, Action, tl:Animal-agent, tl:Action'
        }
        expected_results = {
            'legal': True,
            'multipleDesc': False,
            'multipleDescIncShort': False
        }
        expected_issues = {
            'legal': [],
            'multipleDesc': self.format_error(ValidationErrors.TAG_NOT_UNIQUE,
                                              tag_namespace='tl:Property/Organizational-property/Event-context'),
            'multipleDescIncShort': self.format_error(ValidationErrors.TAG_NOT_UNIQUE,
                                                      tag_namespace='tl:Property/Organizational-property/Event-context'),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


if __name__ == '__main__':
    unittest.main()
