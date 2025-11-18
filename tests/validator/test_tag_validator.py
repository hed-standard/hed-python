import unittest

from hed.errors.error_types import ValidationErrors, DefinitionErrors
from tests.validator.test_tag_validator_base import TestValidatorBase
from hed.schema.hed_schema_io import load_schema_version
from functools import partial


# todo: update these tests(TagValidator no longer exists)
class TestHed(TestValidatorBase):
    schema_file = "../data/schema_tests/HED8.2.0.mediawiki"


class IndividualHedTagsShort(TestHed):
    hed_schema = load_schema_version("score_1.1.0")

    @staticmethod
    def string_obj_func(validator):
        return partial(validator._validate_individual_tags_in_hed_string)

    def test_exist_in_schema(self):
        test_strings = {
            "takesValue": "Duration/3 ms",
            "full": "Animal-agent",
            "extensionsAllowed": "Item/Beaver",
            "leafExtension": "Experiment-procedure/Something",
            "nonExtensionsAllowed": "Event/Nonsense",
            "invalidExtension": "Agent/Red",
            "invalidExtension2": "Agent/Red/Extension2",
            "usedToBeIllegalComma": "Label/This is a label,This/Is/A/Tag",
            "legalDef": "Def/Item",
            "legalDefExpand": "Def-expand/Item",
            "illegalDefinition": "Definition/Item",
        }
        expected_results = {
            "takesValue": True,
            "full": True,
            "extensionsAllowed": True,
            "leafExtension": False,
            "nonExtensionsAllowed": False,
            "invalidExtension": False,
            "invalidExtension2": False,
            "usedToBeIllegalComma": False,
            "legalDef": True,
            "legalDefExpand": True,
            "illegalDefinition": False,
        }
        expected_issues = {
            "takesValue": [],
            "full": [],
            "extensionsAllowed": [],
            "leafExtension": self.format_error(ValidationErrors.TAG_EXTENSION_INVALID, tag=0),
            "nonExtensionsAllowed": self.format_error(ValidationErrors.TAG_EXTENSION_INVALID, tag=0),
            "invalidExtension": self.format_error(
                ValidationErrors.INVALID_PARENT_NODE,
                tag=0,
                index_in_tag=6,
                index_in_tag_end=9,
                expected_parent_tag="Property/Sensory-property/Sensory-attribute/Visual-attribute"
                + "/Color/CSS-color/Red-color/Red",
            ),
            "invalidExtension2": self.format_error(
                ValidationErrors.INVALID_PARENT_NODE,
                tag=0,
                index_in_tag=6,
                index_in_tag_end=9,
                expected_parent_tag="Property/Sensory-property/Sensory-attribute/Visual-attribute"
                + "/Color/CSS-color/Red-color/Red",
            ),
            "usedToBeIllegalComma": self.format_error(
                ValidationErrors.NO_VALID_TAG_FOUND, tag=1, index_in_tag=0, index_in_tag_end=4
            ),
            "legalDef": [],
            "legalDefExpand": [],
            "illegalDefinition": self.format_error(DefinitionErrors.BAD_DEFINITION_LOCATION, tag=0),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_proper_capitalization(self):
        test_strings = {
            "proper": "Event/Sensory-event",
            "camelCase": "EvEnt/Sensory-event",
            "takesValue": "Sampling-rate/20 Hz",
            "numeric": "Statistical-uncertainty/20",
            "lowercase": "Event/sensory-event",
        }
        expected_results = {"proper": True, "camelCase": True, "takesValue": True, "numeric": True, "lowercase": False}
        expected_issues = {
            "proper": [],
            "camelCase": [],
            "takesValue": [],
            "numeric": [],
            "lowercase": self.format_error(ValidationErrors.STYLE_WARNING, tag=0),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_child_required(self):
        test_strings = {"hasChild": "Experimental-stimulus", "missingChild": "Label"}
        expected_results = {"hasChild": True, "missingChild": False}
        expected_issues = {"hasChild": [], "missingChild": self.format_error(ValidationErrors.TAG_REQUIRES_CHILD, tag=0)}
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_required_units(self):
        test_strings = {
            "hasRequiredUnit": "Duration/3 ms",
            "missingUnit": "Duration/3",
            "notRequiredNoNumber": "Age",
            "notRequiredNumber": "Age/0.5",
            "notRequiredScientific": "Age/5.2e-1",
            "timeValue": "Clock-face/08:30",
            # Update test - This one is currently marked as valid because clock face isn't in hed3
            "invalidTimeValue": "Clock-face/8:30",
        }
        expected_results = {
            "hasRequiredUnit": True,
            "missingUnit": True,
            "notRequiredNoNumber": True,
            "notRequiredNumber": True,
            "notRequiredScientific": True,
            "timeValue": False,
            "invalidTimeValue": False,
        }
        # legal_clock_time_units = ['hour:min', 'hour:min:sec']
        expected_issues = {
            "hasRequiredUnit": [],
            "missingUnit": [],
            "notRequiredNoNumber": [],
            "notRequiredNumber": [],
            "notRequiredScientific": [],
            "timeValue": self.format_error(ValidationErrors.TAG_EXTENDED, tag=0, index_in_tag=10, index_in_tag_end=None),
            "invalidTimeValue": self.format_error(
                ValidationErrors.TAG_EXTENDED, tag=0, index_in_tag=10, index_in_tag_end=None
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_correct_units(self):
        test_strings = {
            "correctUnit": "Duration/3 s",
            "incorrectUnit": "Duration/3 cm",
            "incorrectSiUsage": "Duration/3 decaday",
            "incorrectPluralUnit": "Frequency/3 hertzs",
            "incorrectSymbolCapitalizedUnit": "Frequency/3 hz",
            "incorrectSymbolCapitalizedUnitModifier": "Frequency/3 KHz",
            "notRequiredNumber": "Statistical-accuracy/0.5",
            "notRequiredScientific": "Statistical-accuracy/5e-1",
            "specialAllowedCharBadUnit": "Creation-date/ba",
            "specialAllowedCharUnit": "Creation-date/1900-01-01T01:01:01",
            "voltsTest1": "Finding-amplitude/30 v",
            "voltsTest2": "Finding-amplitude/30 Volt",
            "voltsTest3": "Finding-amplitude/30 volts",
            "voltsTest4": "Finding-amplitude/30 VOLTS",
            "voltsTest5": "Finding-amplitude/30 kv",
            "voltsTest6": "Finding-amplitude/30 kiloVolt",
            "voltsTest7": "Finding-amplitude/30 KiloVolt",
            "volumeTest1": "Sound-volume/5 dB",
            "volumeTest2": "Sound-volume/5 kdB",  # Invalid, not SI unit
            "volumeTest3": "Sound-volume/5 candela",
            "volumeTest4": "Sound-volume/5 kilocandela",
            "volumeTest5": "Sound-volume/5 cd",
            "volumeTest6": "Sound-volume/5 kcd",
            "volumeTest7": "Sound-volume/5 DB",  # Invalid, case doesn't match
        }
        expected_results = {
            "correctUnit": True,
            "correctUnitScientific": True,
            "correctPluralUnit": True,
            "correctNoPluralUnit": True,
            "correctNonSymbolCapitalizedUnit": True,
            "correctSymbolCapitalizedUnit": True,
            "incorrectUnit": False,
            "incorrectSiUsage": False,
            "incorrectPluralUnit": False,
            "incorrectSymbolCapitalizedUnit": False,
            "incorrectSymbolCapitalizedUnitModifier": False,
            "notRequiredNumber": True,
            "notRequiredScientific": True,
            "specialAllowedCharBadUnit": False,
            "specialAllowedCharUnit": True,
            "voltsTest1": True,
            "voltsTest2": True,
            "voltsTest3": True,
            "voltsTest4": True,
            "voltsTest5": True,
            "voltsTest6": True,
            "voltsTest7": True,
            "volumeTest1": True,
            "volumeTest2": False,
            "volumeTest3": True,
            "volumeTest4": True,
            "volumeTest5": True,
            "volumeTest6": True,
            "volumeTest7": False,
        }
        legal_time_units = ["s", "second", "day", "minute", "hour"]
        legal_freq_units = ["Hz", "hertz"]
        legal_intensity_units = ["candela", "cd", "dB"]

        expected_issues = {
            "correctUnit": [],
            "correctUnitScientific": [],
            "correctPluralUnit": [],
            "correctNoPluralUnit": [],
            "correctNonSymbolCapitalizedUnit": [],
            "correctSymbolCapitalizedUnit": [],
            "incorrectUnit": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=legal_time_units),
            "incorrectSiUsage": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=legal_time_units),
            "incorrectPluralUnit": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=legal_freq_units),
            "incorrectSymbolCapitalizedUnit": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=legal_freq_units),
            "incorrectSymbolCapitalizedUnitModifier": self.format_error(
                ValidationErrors.UNITS_INVALID, tag=0, units=legal_freq_units
            ),
            "notRequiredNumber": [],
            "notRequiredScientific": [],
            "specialAllowedCharBadUnit": self.format_error(
                ValidationErrors.INVALID_VALUE_CLASS_VALUE,
                tag=0,
                index_in_tag=0,
                index_in_tag_end=16,
                value_class="dateTimeClass",
                actual_error=ValidationErrors.VALUE_INVALID,
            ),
            "specialAllowedCharUnit": [],
            "voltsTest1": [],
            "voltsTest2": [],
            "voltsTest3": [],
            "voltsTest4": [],
            "voltsTest5": [],
            "voltsTest6": [],
            "voltsTest7": [],
            "volumeTest1": [],
            "volumeTest2": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=legal_intensity_units),
            "volumeTest3": [],
            "volumeTest4": [],
            "volumeTest5": [],
            "volumeTest6": [],
            "volumeTest7": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=legal_intensity_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_extensions(self):
        test_strings = {
            "invalidExtension": "Experiment-control/Animal-agent",
        }
        expected_results = {
            "invalidExtension": False,
        }
        expected_issues = {
            "invalidExtension": self.format_error(
                ValidationErrors.INVALID_PARENT_NODE,
                tag=0,
                index_in_tag=19,
                index_in_tag_end=31,
                expected_parent_tag="Agent/Animal-agent",
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_extension_warning(self):
        test_strings = {"noWarning": "Condition-variable/ValidExt", "warning": "Task-property/WarningExt"}
        expected_results = {
            "noWarning": True,
            "warning": False,
        }
        expected_issues = {
            "noWarning": [],
            "warning": self.format_error(ValidationErrors.TAG_EXTENDED, tag=0, index_in_tag=13, index_in_tag_end=None),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_invalid_placeholder_in_normal_string(self):
        test_strings = {
            "invalidPlaceholder": "Duration/# ms",
            "invalidMiscPoundSign": "Du#ation/20 ms",
            "invalidAfterBaseTag": "Action/Invalid#/InvalidExtension",
        }
        expected_results = {
            "invalidPlaceholder": False,
            "invalidMiscPoundSign": False,
            "invalidAfterBaseTag": False,
        }
        expected_issues = {
            "invalidPlaceholder": self.format_error(
                ValidationErrors.INVALID_TAG_CHARACTER,
                tag=0,
                index_in_tag=9,
                index_in_tag_end=10,
                actual_error=ValidationErrors.PLACEHOLDER_INVALID,
            )
            + self.format_error(
                ValidationErrors.INVALID_VALUE_CLASS_VALUE,
                tag=0,
                index_in_tag=0,
                index_in_tag_end=13,
                value_class="numericClass",
                actual_error=ValidationErrors.VALUE_INVALID,
            ),
            "invalidMiscPoundSign": self.format_error(
                ValidationErrors.NO_VALID_TAG_FOUND, tag=0, index_in_tag=0, index_in_tag_end=8
            ),
            "invalidAfterBaseTag": self.format_error(
                ValidationErrors.INVALID_TAG_CHARACTER,
                tag=0,
                index_in_tag=14,
                index_in_tag_end=15,
                actual_error=ValidationErrors.PLACEHOLDER_INVALID,
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_span_reporting(self):
        test_strings = {
            "orgTagDifferent": "Duration/23 hz",
            "orgTagDifferent2": "Duration/23 hz, Duration/23 hz",
        }
        expected_results = {
            "orgTagDifferent": False,
            "orgTagDifferent2": False,
        }
        tag_unit_class_units = ["day", "hour", "minute", "s", "second"]
        expected_issues = {
            "orgTagDifferent": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=tag_unit_class_units),
            "orgTagDifferent2": self.format_error(ValidationErrors.UNITS_INVALID, tag=0, units=tag_unit_class_units)
            + self.format_error(ValidationErrors.UNITS_INVALID, tag=1, units=tag_unit_class_units),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class TestTagLevels(TestHed):
    @staticmethod
    def string_obj_func(validator):
        return validator._group_validator.run_tag_level_validators

    def test_no_duplicates(self):
        test_strings = {
            "topLevelDuplicate": "Event/Sensory-event,Event/Sensory-event",
            "groupDuplicate": "Item/Object/Man-made-object/VehicleTrain,(Event/Sensory-event,"
            "Purple-color/Purple,Event/Sensory-event)",
            "noDuplicate": "Event/Sensory-event," "Item/Object/Man-made-object/VehicleTrain," "Purple-color/Purple",
            "legalDuplicate": "Item/Object/Man-made-object/VehicleTrain,(Item/Object/Man-made-object/VehicleTrain,"
            "Event/Sensory-event)",
            "duplicateGroup": "Sensory-event, (Sensory-event, Man-made-object/VehicleTrain),"
            "(Man-made-object/VehicleTrain, Sensory-event)",
            "duplicateSubGroup": "Sensory-event, (Event, (Sensory-event, Man-made-object/VehicleTrain)),"
            "(Event, (Man-made-object/VehicleTrain, Sensory-event))",
            "duplicateSubGroupF": "Sensory-event, ((Sensory-event, Man-made-object/VehicleTrain), Event),"
            "((Man-made-object/VehicleTrain, Sensory-event), Event)",
        }
        expected_results = {
            "topLevelDuplicate": False,
            "groupDuplicate": False,
            "legalDuplicate": True,
            "noDuplicate": True,
            "duplicateGroup": False,
            "duplicateSubGroup": False,
            "duplicateSubGroupF": False,
        }

        expected_issues = {
            "topLevelDuplicate": [
                {"code": "TAG_EXPRESSION_REPEATED", "message": 'Repeated tag - "Event/Sensory-event"', "severity": 1}
            ],
            "groupDuplicate": [
                {"code": "TAG_EXPRESSION_REPEATED", "message": 'Repeated tag - "Event/Sensory-event"', "severity": 1}
            ],
            "legalDuplicate": [],
            "noDuplicate": [],
            "duplicateGroup": [
                {
                    "code": "TAG_EXPRESSION_REPEATED",
                    "message": 'Repeated group - "(Man-made-object/VehicleTrain,Sensory-event)"',
                    "severity": 1,
                }
            ],
            "duplicateSubGroup": [
                {
                    "code": "TAG_EXPRESSION_REPEATED",
                    "message": 'Repeated group - "(Event,(Man-made-object/VehicleTrain,Sensory-event))"',
                    "severity": 1,
                }
            ],
            "duplicateSubGroupF": [
                {
                    "code": "TAG_EXPRESSION_REPEATED",
                    "message": 'Repeated group - "((Man-made-object/VehicleTrain,Sensory-event),Event)"',
                    "severity": 1,
                }
            ],
        }
        self.validator_semantic_new(test_strings, expected_results, expected_issues, False)

    def test_no_duplicates_semantic(self):
        test_strings = {
            "mixedLevelDuplicates": "Man-made-object/Vehicle/Boat, Vehicle/Boat",
            "mixedLevelDuplicates2": "Man-made-object/Vehicle/Boat, Boat",
        }
        expected_results = {
            "mixedLevelDuplicates": False,
            "mixedLevelDuplicates2": False,
        }
        expected_issues = {
            "mixedLevelDuplicates": self.format_error(ValidationErrors.HED_TAG_REPEATED, tag=1),
            "mixedLevelDuplicates2": self.format_error(ValidationErrors.HED_TAG_REPEATED, tag=1),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_temp_validation(self):
        test_strings = {
            "valid1": "Event, (Event)",
        }
        expected_results = {
            "valid1": True,
        }
        expected_issues = {"valid1": []}
        self.validator_semantic_new(test_strings, expected_results, expected_issues, False)

    def test_topLevelTagGroup_validation_new(self):
        test_strings = {
            "valid1": "(Definition/ValidDef)",
            "valid2": "(Definition/ValidDef), (Definition/ValidDef2)",
            "invalid2": "(Event, (Definition/InvalidDef2))",
            "invalidTwoInOne": "(Definition/InvalidDef2, Definition/InvalidDef3)",
            "invalid2TwoInOne": "(Definition/InvalidDef2, Onset)",
            "valid2TwoInOne": "(Duration/5.0 s, Delay, (Event))",
            "invalid3InOne": "(Duration/5.0 s, Delay, Onset, (Event))",
            "invalidDuration": "(Duration/5.0 s, Onset, (Event))",
            "invalidDelay": "(Delay, Onset, (Event))",
            "invalidDurationPair": "(Duration/5.0 s, Duration/3.0 s, (Event))",
            "invalidDelayPair": "(Delay/3.0 s, Delay/2.0 s, (Event))",
        }
        expected_results = {
            "valid1": True,
            "valid2": True,
            "invalid2": False,
            "invalidTwoInOne": False,
            "invalid2TwoInOne": False,
            "valid2TwoInOne": True,
            "invalid3InOne": False,
            "invalidDuration": False,
            "invalidDelay": False,
            "invalidDurationPair": False,
            "invalidDelayPair": False,
        }
        expected_issues = {
            "valid1": [],
            "valid2": [],
            "invalid2": [
                {
                    "code": "DEFINITION_INVALID",
                    "message": 'Tag "Definition/InvalidDef2" must be in a top level group but was found in another location.',
                    "severity": 1,
                }
            ],
            "invalidTwoInOne": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Repeated reserved tag "Definition/InvalidDef3" or multiple reserved tags in group "(Definition/InvalidDef2,Definition/InvalidDef3)"',
                    "severity": 1,
                }
            ],
            "invalid2TwoInOne": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Tag "Onset" is not allowed with the other tag(s) or Def-expand sub-group in group "(Definition/InvalidDef2,Onset)"',
                    "severity": 1,
                }
            ],
            "valid2TwoInOne": [],
            "invalid3InOne": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Tag "Onset" is not allowed with the other tag(s) or Def-expand sub-group in group "(Duration/5.0 s,Delay,Onset,(Event))"',
                    "severity": 1,
                }
            ],
            "invalidDuration": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Tag "Onset" is not allowed with the other tag(s) or Def-expand sub-group in group "(Duration/5.0 s,Onset,(Event))"',
                    "severity": 1,
                }
            ],
            "invalidDelay": [
                {
                    "code": "TEMPORAL_TAG_ERROR",
                    "message": "'Onset' tag has no def tag or def-expand group or too many when 1 is required in string.",
                    "severity": 1,
                }
            ],
            "invalidDurationPair": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Repeated reserved tag "Duration/3.0 s" or multiple reserved tags in group "(Duration/5.0 s,Duration/3.0 s,(Event))"',
                    "severity": 1,
                }
            ],
            "invalidDelayPair": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Repeated reserved tag "Delay/2.0 s" or multiple reserved tags in group "(Delay/3.0 s,Delay/2.0 s,(Event))"',
                    "severity": 1,
                }
            ],
        }
        self.validator_semantic_new(test_strings, expected_results, expected_issues, False)

    def test_taggroup_validation(self):
        test_strings = {
            "invalid1": "Def-Expand/InvalidDef",
            "invalid2": "Def-Expand/InvalidDef, Event, (Event)",
            "invalid3": "Event, (Event), Def-Expand/InvalidDef",
            "valid1": "(Def-Expand/ValidDef)",
            "valid2": "(Def-Expand/ValidDef), (Def-Expand/ValidDef2)",
            "valid3": "(Event, (Def-Expand/InvalidDef2))",
            # This case should possibly be flagged as invalid
            "semivalid1": "(Def-Expand/InvalidDef2, Def-Expand/InvalidDef3)",
            "semivalid2": "(Def-Expand/InvalidDef2, Onset)",
        }
        expected_results = {
            "invalid1": False,
            "invalid2": False,
            "invalid3": False,
            "valid1": True,
            "valid2": True,
            "valid3": True,
            "semivalid1": True,
            "semivalid2": True,
        }
        expected_issues = {
            "invalid1": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Tag "Def-Expand/InvalidDef" that must be in a group was found in another location.',
                    "severity": 1,
                }
            ],
            "invalid2": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Tag "Def-Expand/InvalidDef" that must be in a group was found in another location.',
                    "severity": 1,
                }
            ],
            "invalid3": [
                {
                    "code": "TAG_GROUP_ERROR",
                    "message": 'Tag "Def-Expand/InvalidDef" that must be in a group was found in another location.',
                    "severity": 1,
                }
            ],
            "valid1": [],
            "valid2": [],
            "valid3": [],
            "semivalid1": [],
            "semivalid2": [
                {
                    "code": "TEMPORAL_TAG_ERROR",
                    "message": "'Onset' tag has no def tag or def-expand group or too many when 1 is required in string.",
                    "severity": 1,
                }
            ],
        }
        self.validator_semantic_new(test_strings, expected_results, expected_issues, False)

    def test_empty_groups(self):
        test_strings = {"emptyGroup": "Event, ()"}
        expected_results = {"emptyGroup": False}
        expected_issues = {"emptyGroup": self.format_error(ValidationErrors.HED_GROUP_EMPTY, tag=1000 + 1)}
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class FullHedString(TestHed):
    compute_forms = False

    @staticmethod
    def string_obj_func(validator):
        return validator._run_hed_string_validators

    def test_invalid_placeholders(self):
        # We might want these to be banned later as invalid characters.
        test_strings = {
            "invalidPlaceholder": "Duration/# ms",
            "invalidMiscPoundSign": "Du#ation/20 ms",
        }
        expected_results = {
            "invalidPlaceholder": True,
            "invalidMiscPoundSign": True,
        }
        expected_issues = {
            "invalidPlaceholder": [],
            "invalidMiscPoundSign": [],
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_mismatched_parentheses(self):
        test_strings = {
            "extraOpening": "Action/Reach/To touch,((Attribute/Object side/Left,Participant/Effect/Body part/Arm),"
            "Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px",
            "extraClosing": "Action/Reach/To touch,(Attribute/Object side/Left,Participant/Effect/Body part/Arm),),"
            "Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px",
            "valid": "Action/Reach/To touch,(Attribute/Object side/Left,Participant/Effect/Body part/Arm),"
            "Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px",
        }
        expected_results = {"extraOpening": False, "extraClosing": False, "valid": True}
        expected_issues = {
            "extraOpening": self.format_error(
                ValidationErrors.PARENTHESES_MISMATCH, opening_parentheses_count=2, closing_parentheses_count=1
            ),
            "extraClosing": self.format_error(
                ValidationErrors.PARENTHESES_MISMATCH, opening_parentheses_count=1, closing_parentheses_count=2
            )
            + self.format_error(ValidationErrors.TAG_EMPTY, source_string=test_strings["extraClosing"], char_index=84),
            "valid": [],
        }

        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_malformed_delimiters(self):
        test_strings = {
            "missingOpeningComma": "Action/Reach/To touch(Attribute/Object side/Left,Participant/Effect/Body part/Arm),"
            "Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px",
            "missingClosingComma": "Action/Reach/To touch,"
            "(Attribute/Object side/Left,Participant/Effect/Body part/Arm)Attribute/Location/Screen/Top/70 px,"
            "Attribute/Location/Screen/Left/23 px",
            "extraOpeningComma": ",Action/Reach/To touch,"
            "(Attribute/Object side/Left,Participant/Effect/Body part/Arm),"
            "Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px",
            "extraClosingComma": "Action/Reach/To touch,"
            "(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,"
            "Attribute/Location/Screen/Left/23 px,",
            "multipleExtraOpeningDelimiters": ",,,Action/Reach/To touch,"
            "(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,"
            "Attribute/Location/Screen/Left/23 px",
            "multipleExtraClosingDelimiters": "Action/Reach/To touch,"
            "(Attribute/Object side/Left,Participant/Effect/Body part/Arm),"
            "Attribute/Location/Screen/Top/70 px,Attribute/Location/Screen/Left/23 px,,,,",
            "multipleExtraMiddleDelimiters": "Action/Reach/To touch,"
            ",(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,"
            ",,Attribute/Location/Screen/Left/23 px",
            "valid": "Action/Reach/To touch,"
            "(Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,"
            "Attribute/Location/Screen/Left/23 px",
            "validNestedParentheses": "Action/Reach/To touch,"
            "((Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,"
            "Attribute/Location/Screen/Left/23 px),Event/Duration/3 ms",
            "validNestedParentheses2": "Action/Reach/To touch,"
            "(((Attribute/Object side/Left,Participant/Effect/Body part/Arm),Attribute/Location/Screen/Top/70 px,"
            "Attribute/Location/Screen/Left/23 px)),Event/Duration/3 ms",
            "validNestedParentheses3": "Thing, (Thing, (Thing))",
            "validNestedParentheses4": "Thing, ((Thing, (Thing)), Thing)",
            "invalidNestedParentheses": "Thing, ((Thing, (Thing)) Thing)",
        }

        expected_results = {
            "missingOpeningComma": False,
            "missingClosingComma": False,
            "extraOpeningComma": False,
            "extraClosingComma": False,
            "extraOpeningParen": False,
            "extraClosingParen": False,
            "multipleExtraOpeningDelimiters": False,
            "multipleExtraClosingDelimiters": False,
            "multipleExtraMiddleDelimiters": False,
            "valid": True,
            "validNestedParentheses": True,
            "validNestedParentheses2": True,
            "validNestedParentheses3": True,
            "validNestedParentheses4": True,
            "invalidNestedParentheses": False,
        }
        expected_issues = {
            "missingOpeningComma": self.format_error(ValidationErrors.COMMA_MISSING, tag="Action/Reach/To touch("),
            "missingClosingComma": self.format_error(ValidationErrors.COMMA_MISSING, tag="Participant/Effect/Body part/Arm)"),
            "extraOpeningComma": self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["extraOpeningComma"], char_index=0
            ),
            "extraClosingComma": self.format_error(
                ValidationErrors.TAG_EMPTY,
                source_string=test_strings["extraClosingComma"],
                char_index=len(test_strings["extraClosingComma"]) - 1,
            ),
            "extraOpeningParen": self.format_error(
                ValidationErrors.PARENTHESES_MISMATCH, opening_parentheses_count=2, closing_parentheses_count=1
            ),
            "extraClosingParen": self.format_error(
                ValidationErrors.PARENTHESES_MISMATCH, opening_parentheses_count=1, closing_parentheses_count=2
            ),
            "multipleExtraOpeningDelimiters": self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["multipleExtraOpeningDelimiters"], char_index=0
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["multipleExtraOpeningDelimiters"], char_index=1
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["multipleExtraOpeningDelimiters"], char_index=2
            ),
            "multipleExtraClosingDelimiters": self.format_error(
                ValidationErrors.TAG_EMPTY,
                source_string=test_strings["multipleExtraClosingDelimiters"],
                char_index=len(test_strings["multipleExtraClosingDelimiters"]) - 1,
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY,
                source_string=test_strings["multipleExtraClosingDelimiters"],
                char_index=len(test_strings["multipleExtraClosingDelimiters"]) - 2,
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY,
                source_string=test_strings["multipleExtraClosingDelimiters"],
                char_index=len(test_strings["multipleExtraClosingDelimiters"]) - 3,
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY,
                source_string=test_strings["multipleExtraClosingDelimiters"],
                char_index=len(test_strings["multipleExtraClosingDelimiters"]) - 4,
            ),
            "multipleExtraMiddleDelimiters": self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["multipleExtraMiddleDelimiters"], char_index=22
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["multipleExtraMiddleDelimiters"], char_index=121
            )
            + self.format_error(
                ValidationErrors.TAG_EMPTY, source_string=test_strings["multipleExtraMiddleDelimiters"], char_index=122
            ),
            "valid": [],
            "validNestedParentheses": [],
            "validNestedParentheses2": [],
            "validNestedParentheses3": [],
            "validNestedParentheses4": [],
            "invalidNestedParentheses": self.format_error(ValidationErrors.COMMA_MISSING, tag="Thing)) "),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_invalid_characters(self):
        test_strings = {
            "openingBrace": "Attribute/Object side/Left,Participant/Effect{/Body part/Arm",
            "closingBrace": "Attribute/Object side/Left,Participant/Effect}/Body part/Arm",
            "openingBracket": "Attribute/Object side/Left,Participant/Effect[/Body part/Arm",
            "closingBracket": "Attribute/Object side/Left,Participant/Effect]/Body part/Arm",
        }
        expected_results = {"openingBrace": False, "closingBrace": False, "openingBracket": False, "closingBracket": False}
        expected_issues = {
            "openingBrace": self.format_error(
                ValidationErrors.CHARACTER_INVALID, char_index=45, source_string=test_strings["openingBrace"]
            ),
            "closingBrace": self.format_error(
                ValidationErrors.CHARACTER_INVALID, char_index=45, source_string=test_strings["closingBrace"]
            ),
            "openingBracket": self.format_error(
                ValidationErrors.CHARACTER_INVALID, char_index=45, source_string=test_strings["openingBracket"]
            ),
            "closingBracket": self.format_error(
                ValidationErrors.CHARACTER_INVALID, char_index=45, source_string=test_strings["closingBracket"]
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    def test_string_extra_slash_space(self):
        test_strings = {
            "twoLevelDoubleSlash": "Event//Extension",
            "threeLevelDoubleSlash": "Vehicle//Boat//Tanker",
            "tripleSlashes": "Vehicle///Boat///Tanker",
            "mixedSingleAndDoubleSlashes": "Vehicle//Boat/Tanker",
            "singleSlashWithSpace": "Event/ Extension",
            "doubleSlashSurroundingSpace": "Event/ /Extension",
            "doubleSlashThenSpace": "Event// Extension",
            "sosPattern": "Event///   ///Extension",
            "alternatingSlashSpace": "Vehicle/ / Boat/ / Tanker",
            "leadingDoubleSlash": "//Event/Extension",
            "trailingDoubleSlash": "Event/Extension//",
            "leadingDoubleSlashWithSpace": "/ /Event/Extension",
            "trailingDoubleSlashWithSpace": "Event/Extension/ /",
        }
        expected_results = {
            "twoLevelDoubleSlash": False,
            "threeLevelDoubleSlash": False,
            "tripleSlashes": False,
            "mixedSingleAndDoubleSlashes": False,
            "singleSlashWithSpace": False,
            "doubleSlashSurroundingSpace": False,
            "doubleSlashThenSpace": False,
            "sosPattern": False,
            "alternatingSlashSpace": False,
            "leadingDoubleSlash": False,
            "trailingDoubleSlash": False,
            "leadingDoubleSlashWithSpace": False,
            "trailingDoubleSlashWithSpace": False,
        }
        expected_errors = {
            "twoLevelDoubleSlash": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=5, index_in_tag_end=7, tag=0
            ),
            "threeLevelDoubleSlash": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=7, index_in_tag_end=9, tag=0
            )
            + self.format_error(ValidationErrors.NODE_NAME_EMPTY, index_in_tag=13, index_in_tag_end=15, tag=0),
            "tripleSlashes": self.format_error(ValidationErrors.NODE_NAME_EMPTY, index_in_tag=7, index_in_tag_end=10, tag=0)
            + self.format_error(ValidationErrors.NODE_NAME_EMPTY, index_in_tag=14, index_in_tag_end=17, tag=0),
            "mixedSingleAndDoubleSlashes": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=7, index_in_tag_end=9, tag=0
            ),
            "singleSlashWithSpace": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=5, index_in_tag_end=7, tag=0
            ),
            "doubleSlashSurroundingSpace": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=5, index_in_tag_end=8, tag=0
            ),
            "doubleSlashThenSpace": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=5, index_in_tag_end=8, tag=0
            ),
            "sosPattern": self.format_error(ValidationErrors.NODE_NAME_EMPTY, index_in_tag=5, index_in_tag_end=14, tag=0),
            "alternatingSlashSpace": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=7, index_in_tag_end=11, tag=0
            )
            + self.format_error(ValidationErrors.NODE_NAME_EMPTY, index_in_tag=15, index_in_tag_end=19, tag=0),
            "leadingDoubleSlash": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=0, index_in_tag_end=2, tag=0
            ),
            "trailingDoubleSlash": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=15, index_in_tag_end=17, tag=0
            ),
            "leadingDoubleSlashWithSpace": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=0, index_in_tag_end=3, tag=0
            ),
            "trailingDoubleSlashWithSpace": self.format_error(
                ValidationErrors.NODE_NAME_EMPTY, index_in_tag=15, index_in_tag_end=18, tag=0
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_errors, False)

    def test_no_more_than_two_tildes(self):
        test_strings = {
            "noTildeGroup": "Event/Category/Initial context," "(Item/Object/Vehicle/Train,Event/Category/Initial context)",
            "oneTildeGroup": "Event/Category/Initial context," "(Item/Object/Vehicle/Car ~ Attribute/Object control/Perturb)",
            "twoTildeGroup": "Event/Category/Initial context,"
            "(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car, Item/ID/RedCar,"
            " Attribute/Visual/Color/Red)",
            "invalidTildeGroup": "Event/Category/Initial context,"
            "(Participant/ID 1 ~ Participant/Effect/Visual ~ Item/Object/Vehicle/Car,"
            " Item/ID/RedCar, Attribute/Visual/Color/Red ~ Attribute/Object control/Perturb)",
        }
        expected_results = {"noTildeGroup": True, "oneTildeGroup": False, "twoTildeGroup": False, "invalidTildeGroup": False}
        expected_issues = {
            "noTildeGroup": [],
            "oneTildeGroup": self.format_error(
                ValidationErrors.TILDES_UNSUPPORTED, source_string=test_strings["oneTildeGroup"], char_index=56
            ),
            "twoTildeGroup": self.format_error(
                ValidationErrors.TILDES_UNSUPPORTED, source_string=test_strings["twoTildeGroup"], char_index=49
            )
            + self.format_error(
                ValidationErrors.TILDES_UNSUPPORTED, source_string=test_strings["twoTildeGroup"], char_index=77
            ),
            "invalidTildeGroup": self.format_error(
                ValidationErrors.TILDES_UNSUPPORTED, source_string=test_strings["invalidTildeGroup"], char_index=49
            )
            + self.format_error(
                ValidationErrors.TILDES_UNSUPPORTED, source_string=test_strings["invalidTildeGroup"], char_index=77
            )
            + self.format_error(
                ValidationErrors.TILDES_UNSUPPORTED, source_string=test_strings["invalidTildeGroup"], char_index=147
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class RequiredTags(TestHed):
    schema_file = "../data/validator_tests/HED8.0.0_added_tests.mediawiki"

    @staticmethod
    def string_obj_func(validator):
        return partial(validator._group_validator.run_all_tags_validators)

    def test_includes_all_required_tags(self):
        test_strings = {
            "complete": "Animal-agent, Action",
            "missingAgent": "Action",
            "missingAction": "Animal-agent",
            "inSubGroup": "Animal-agent, (Action)",
            "missingAll": "Event",
        }
        expected_results = {
            "complete": True,
            "missingAgent": False,
            "missingAction": False,
            "inSubGroup": True,
            "missingAll": False,
        }
        expected_issues = {
            "complete": [],
            "missingAgent": self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace="Agent/Animal-agent"),
            "missingAction": self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace="Action"),
            "inSubGroup": [],
            "missingAll": self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace="Action")
            + self.format_error(ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace="Agent/Animal-agent"),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)

    def test_multiple_copies_unique_tags(self):
        test_strings = {
            "legal": "Event-context," "(Vehicle,Event), Animal-agent, Action",
            "multipleDesc": "Event-context," "Event-context," "Vehicle,(Vehicle,Event-context), Animal-agent, Action",
            # I think this is illegal in hed2 style schema now.
            "multipleDescIncShort": "Event-context," "Organizational-property/Event-context, Animal-agent, Action",
        }
        expected_results = {"legal": True, "multipleDesc": False, "multipleDescIncShort": False}
        expected_issues = {
            "legal": [],
            "multipleDesc": self.format_error(
                ValidationErrors.TAG_NOT_UNIQUE, tag_namespace="Property/Organizational-property/Event-context"
            ),
            "multipleDescIncShort": self.format_error(
                ValidationErrors.TAG_NOT_UNIQUE, tag_namespace="Property/Organizational-property/Event-context"
            ),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class RequiredTagInDefinition(TestHed):
    schema_file = "../data/validator_tests/HED8.0.0_added_tests.mediawiki"

    @staticmethod
    def string_obj_func(validator):
        from hed.validator import DefValidator

        def_dict = DefValidator()
        return partial(def_dict.check_for_definitions)

    def test_includes_all_required_tags(self):
        test_strings = {
            "complete": "Animal-agent, Action, (Definition/labelWithRequired, (Action))",
        }
        expected_results = {
            "complete": False,
        }
        expected_issues = {
            "complete": self.format_error(DefinitionErrors.BAD_PROP_IN_DEFINITION, tag=3, def_name="labelWithRequired"),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


class TestHedSpecialUnits(TestHed):
    compute_forms = True
    schema_file = "../data/validator_tests/HED8.0.0_added_tests.mediawiki"

    @staticmethod
    def string_obj_func(validator):
        return partial(validator._validate_individual_tags_in_hed_string)


class TestHedAllowedCharacters(TestHed):
    compute_forms = True
    schema_file = "../data/schema_tests/schema_utf8.mediawiki"

    @staticmethod
    def string_obj_func(validator):
        return partial(validator._validate_individual_tags_in_hed_string)

    def test_special_units(self):
        test_strings = {
            "ascii": "Ascii/bad-date",
            "illegalTab": "Ascii/bad-dat\t",
            "allowTab": "Nonascii/Cafe\t",
        }
        expected_results = {"ascii": True, "illegalTab": False, "allowTab": True}

        expected_issues = {
            "ascii": [],
            "illegalTab": self.format_error(
                ValidationErrors.INVALID_VALUE_CLASS_CHARACTER, tag=0, problem_tag="\t", value_class="textClass"
            ),
            "allowTab": [],
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, True)


if __name__ == "__main__":
    unittest.main()
