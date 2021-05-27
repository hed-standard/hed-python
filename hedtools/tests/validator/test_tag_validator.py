import unittest
import os

from hed.util.hed_string import HedString
from hed.validator.hed_validator import HedValidator
from hed.util import error_reporter
from hed.validator.tag_validator import TagValidator
from hed import schema
from hed.util.error_types import ValidationErrors, ValidationWarnings


class TestHed3(unittest.TestCase):
    schema_file = '../data/legacy_xml/HED8.0.0-alpha.1.xml'

    @classmethod
    def setUpClass(cls):
        cls.error_handler = error_reporter.ErrorHandler()
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(hed_xml)
        cls.syntactic_tag_validator = TagValidator(cls.hed_schema, check_for_warnings=False,
                                                   run_semantic_validation=False)
        cls.syntactic_warning_tag_validator = TagValidator(cls.hed_schema, check_for_warnings=True,
                                                           run_semantic_validation=False)
        cls.semantic_tag_validator = TagValidator(cls.hed_schema, check_for_warnings=False,
                                                  run_semantic_validation=True)
        cls.semantic_warning_tag_validator = TagValidator(cls.hed_schema, check_for_warnings=True,
                                                          run_semantic_validation=True)
        cls.syntactic_hed_input_reader = HedValidator()
        cls.syntactic_hed_input_reader._tag_validator = cls.syntactic_tag_validator
        cls.syntactic_warning_hed_input_reader = HedValidator()
        cls.syntactic_warning_hed_input_reader._tag_validator = cls.syntactic_warning_tag_validator
        cls.semantic_hed_input_reader = HedValidator()
        cls.semantic_hed_input_reader._tag_validator = cls.semantic_tag_validator
        cls.semantic_warning_hed_input_reader = HedValidator()
        cls.semantic_warning_hed_input_reader._tag_validator = cls.semantic_warning_tag_validator

    def validator_base(self, test_strings, expected_results, expected_issues, test_function, convert_tags):
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


class IndividualHedTagsShort(TestHed3):
    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.syntactic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), False)
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.syntactic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), False)

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), True)
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.semantic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), True)

    def test_exist_in_schema(self):
        test_strings = {
            'takesValue': 'Duration/3 ms',
            'full': 'Animal-agent',
            'extensionsAllowed': 'Experiment-control/Beaver',
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
            'leafExtension': self.error_handler.format_error(ValidationErrors.INVALID_EXTENSION, tag=test_strings['leafExtension']),
            'nonExtensionsAllowed': self.error_handler.format_error(ValidationErrors.INVALID_EXTENSION, tag=test_strings['nonExtensionsAllowed']),
            'invalidExtension': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, tag="Attribute/Red", index=10, index_end=13,
                                                                       expected_parent_tag="Attribute/Sensory/Visual/Color/CSS-color/Red-color/Red",
                                                                       hed_string="Attribute/Red"),
            'invalidExtension2': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, tag="Attribute/Red/Extension2", index=10, index_end=13,
                                                                       expected_parent_tag="Attribute/Sensory/Visual/Color/CSS-color/Red-color/Red",
                                                                       hed_string="Attribute/Red/Extension2"),
            'usedToBeIllegalComma':  self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, tag="This/Is/A/Tag", index=0, index_end=4,
                                                                       hed_string=test_strings['usedToBeIllegalComma']),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

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
            'hasChild': 'Experimental-stimulus',
            'missingChild': 'Label'
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
            'missingRequiredUnit': self.error_handler.format_error(ValidationWarnings.UNIT_CLASS_DEFAULT_USED, tag=test_strings['missingRequiredUnit'],
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
            # 'invalidTime': False
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
                                                                                          unit_class_units=
                                                                                                  legal_freq_units),
            'notRequiredNumber': [],
            'notRequiredScientific': [],
            # 'properTime': [],
            # 'invalidTime': self.error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT,  tag=test_strings['invalidTime'],
            #                                 unit_class_units=",".join(sorted(legal_clock_time_units)))
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
            'invalidExtension': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, tag='Experiment-control/Animal-agent',
                                                                       index=19, index_end=31, expected_parent_tag="Agent/Animal-agent",
                                                                       hed_string='Experiment-control/Animal-agent'),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)

    # Update test - this warning needs to be added, then this test will fail
    def test_invalid_placeholder_in_normal_string(self):
        test_strings = {
            'invalidPlaceholder': 'Duration/# ms',
        }
        expected_results = {
            'invalidPlaceholder': True,
        }
        expected_issues = {
            'invalidPlaceholder': [],
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class TestTagLevels3(TestHed3):
    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                hed_string_delimiter: self.syntactic_warning_hed_input_reader._validate_tag_levels_in_hed_string(
                                hed_string_delimiter), False)
        else:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                hed_string_delimiter:
                                self.syntactic_hed_input_reader._validate_tag_levels_in_hed_string(
                                hed_string_delimiter), False)

    def validator_semantic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                hed_string_delimiter: self.semantic_warning_hed_input_reader._validate_tag_levels_in_hed_string(
                                hed_string_delimiter), True)
        else:
            self.validator_base(test_strings, expected_results, expected_issues,
                                lambda
                                hed_string_delimiter: self.semantic_hed_input_reader._validate_tag_levels_in_hed_string(
                                hed_string_delimiter), True)

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
                                                                     hed_string=test_strings['topLevelDuplicate']),
            'groupDuplicate': self.error_handler.format_error(ValidationErrors.DUPLICATE, 
                                                                  tag='Event/Category/Sensory presentation',
                                                                  hed_string=test_strings['groupDuplicate']),
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
            'mixedLevelDuplicates': self.error_handler.format_error(ValidationErrors.DUPLICATE, 
                                                                        tag='Vehicle/Boat',
                                                                        hed_string=test_strings['mixedLevelDuplicates']),
            'mixedLevelDuplicates2': self.error_handler.format_error(ValidationErrors.DUPLICATE, 
                                                                        tag='Boat',
                                                                        hed_string=test_strings['mixedLevelDuplicates2']),
        }
        self.validator_semantic(test_strings, expected_results, expected_issues, False)


class IndividualHedTagFormatting(TestHed3):
    def validator_syntactic(self, test_strings, expected_results, expected_issues, check_for_warnings):
        if check_for_warnings is True:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.syntactic_warning_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), False)
        else:
            self.validator_base(test_strings, expected_results, expected_issues, lambda
                hed_string_delimiter: self.syntactic_hed_input_reader._validate_individual_tags_in_hed_string(
                hed_string_delimiter), False)

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
        expected_event_extension = 'Event/Extension'
        expected_tanker = 'Item/Object/Man-made/Vehicle/Boat/Tanker'
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
            'twoLevelDoubleSlash': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=5, index_end=7, tag=test_strings["twoLevelDoubleSlash"]),
            'threeLevelDoubleSlash': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=7, index_end=9, tag=test_strings["threeLevelDoubleSlash"])
                + self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=13, index_end=15, tag=test_strings["threeLevelDoubleSlash"]),
            'tripleSlashes': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=7, index_end=10, tag=test_strings["tripleSlashes"])
                + self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=14, index_end=17, tag=test_strings["tripleSlashes"]),
            'mixedSingleAndDoubleSlashes': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=7, index_end=9, tag=test_strings["mixedSingleAndDoubleSlashes"]),
            'singleSlashWithSpace': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=5, index_end=7, tag=test_strings["singleSlashWithSpace"]),
            'doubleSlashSurroundingSpace': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=5, index_end=8, tag=test_strings["doubleSlashSurroundingSpace"]),
            'doubleSlashThenSpace': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=5, index_end=8, tag=test_strings["doubleSlashThenSpace"]),
            'sosPattern': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=5, index_end=14, tag=test_strings["sosPattern"]),
            'alternatingSlashSpace': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=7, index_end=11, tag=test_strings["alternatingSlashSpace"])
                + self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=15, index_end=19, tag=test_strings["alternatingSlashSpace"]),
            'leadingDoubleSlash': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=0, index_end=2, tag=test_strings["leadingDoubleSlash"]),
            'trailingDoubleSlash': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=15, index_end=17, tag=test_strings["trailingDoubleSlash"]),
            'leadingDoubleSlashWithSpace': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=0, index_end=3, tag=test_strings["leadingDoubleSlashWithSpace"]),
            'trailingDoubleSlashWithSpace': self.error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES, index=15, index_end=18, tag=test_strings["trailingDoubleSlashWithSpace"]),
        }
        self.validator_syntactic(test_strings, expected_results, expected_errors, check_for_warnings=False)

if __name__ == '__main__':
    unittest.main()
