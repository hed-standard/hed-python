import unittest
import os

from hed.util import error_reporter
from hed.util.hed_string import HedString
from hed.schema.hed_schema_file import load_schema
from hed.util.error_types import ValidationErrors


class TestTagFormat(unittest.TestCase):
    schema_file = '../data/legacy_xml/reduced_no_dupe.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = load_schema(hed_xml)
        cls.error_handler = error_reporter.ErrorHandler()


class TestConvertTag(TestTagFormat):
    def validator_base(self, test_strings, expected_results, expected_errors, convert_to_short=True):
        for test_key in test_strings:
            test_string_obj = HedString(test_strings[test_key])
            if convert_to_short:
                test_errors = test_string_obj.convert_to_short(self.hed_schema)
            else:
                test_errors = test_string_obj.convert_to_long(self.hed_schema)
            expected_error = expected_errors[test_key]
            expected_result = expected_results[test_key]
            self.assertEqual(str(test_string_obj), expected_result, test_strings[test_key])
            self.assertCountEqual(test_errors, expected_error, test_strings[test_key])


class TestConvertString(TestTagFormat):
    def validator_base(self, test_strings, expected_results, expected_errors, convert_to_short=True):
        for test_key in test_strings:
            test_string_obj = HedString(test_strings[test_key])
            if convert_to_short:
                test_errors = test_string_obj.convert_to_short(self.hed_schema)
            else:
                test_errors = test_string_obj.convert_to_long(self.hed_schema)
            expected_error = expected_errors[test_key]
            expected_result = expected_results[test_key]
            self.assertEqual(str(test_string_obj), expected_result, test_strings[test_key])
            self.assertCountEqual(test_errors, expected_error, test_strings[test_key])


class TestConvertToLongTag(TestConvertTag):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertToLongTag, self).validator_base(test_strings,
                                                         expected_results, expected_errors,
                                                         convert_to_short=False)

    def test_tag(self):
        test_strings = {
            'singleLevel': 'Event',
            'twoLevel': 'Sensory-event',
            'alreadyLong': 'Item/Object/Geometric',
            'partialLong': 'Object/Geometric',
            'fullShort': 'Geometric',
        }
        expected_results = {
            'singleLevel': 'Event',
            'twoLevel': 'Event/Sensory-event',
            'alreadyLong': 'Item/Object/Geometric',
            'partialLong': 'Item/Object/Geometric',
            'fullShort': 'Item/Object/Geometric',
        }
        expected_errors = {
            'singleLevel': [],
            'twoLevel': [],
            'alreadyLong': [],
            'partialLong': [],
            'fullShort': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_takes_value(self):
        test_strings = {
            'uniqueValue': 'Environmental-sound/Unique Value',
            'multiLevel': 'Environmental-sound/Long Unique Value With/Slash Marks',
            'partialPath': 'Sound/Environmental-sound/Unique Value',
        }
        expected_results = {
            'uniqueValue': 'Item/Sound/Environmental-sound/Unique Value',
            'multiLevel': 'Item/Sound/Environmental-sound/Long Unique Value With/Slash Marks',
            'partialPath': 'Item/Sound/Environmental-sound/Unique Value',
        }
        expected_errors = {
            'uniqueValue': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Environmental-sound/Unique Value',
            'trailingSpace': 'Environmental-sound/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Item/Sound/Environmental-sound/Unique Value',
            'trailingSpace': 'Item/Sound/Environmental-sound/Unique Value',
        }
        expected_errors = {
            'leadingSpace': [],
            'trailingSpace': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_extension_allowed(self):
        test_strings = {
            'singleLevel': 'Experiment-control/extended lvl1',
            'multiLevel': 'Experiment-control/extended lvl1/Extension2',
            'partialPath': 'Vehicle/Boat/Yacht',
        }
        expected_results = {
            'singleLevel': 'Event/Experiment-control/extended lvl1',
            'multiLevel': 'Event/Experiment-control/extended lvl1/Extension2',
            'partialPath': 'Item/Object/Man-made/Vehicle/Boat/Yacht',
        }
        expected_errors = {
            'singleLevel': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_invalid_extension(self):
        test_strings = {
            'validThenInvalid': 'Experiment-control/valid extension followed by invalid/Event',
            'singleLevel': 'Experiment-control/Geometric',
            'singleLevelAlreadyLong': 'Event/Experiment-control/Geometric',
            'twoLevels': 'Experiment-control/Geometric/Event',
            'partialDuplicate': 'Geometric/Item/Object/Geometric',
        }
        expected_results = {
            'validThenInvalid': 'Experiment-control/valid extension followed by invalid/Event',
            'singleLevel': 'Experiment-control/Geometric',
            'singleLevelAlreadyLong': 'Event/Experiment-control/Geometric',
            'twoLevels': 'Experiment-control/Geometric/Event',
            'partialDuplicate': 'Geometric/Item/Object/Geometric',
        }
        expected_errors = {
            'validThenInvalid':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, test_strings['validThenInvalid'],
                                                55, 60, 'Event', hed_string=test_strings['validThenInvalid']),
            'singleLevel':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, test_strings['singleLevel'],
                                                19, 28, 'Item/Object/Geometric',
                                                hed_string=test_strings['singleLevel']),
            'singleLevelAlreadyLong':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                test_strings['singleLevelAlreadyLong'],
                                                25, 34, 'Item/Object/Geometric',
                                                hed_string=test_strings['singleLevelAlreadyLong']),
            'twoLevels':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, test_strings['twoLevels'],
                                                19, 28, 'Item/Object/Geometric',
                                                hed_string=test_strings['twoLevels']),
            'partialDuplicate':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                test_strings['partialDuplicate'], 10, 14, 'Item',
                                                hed_string=test_strings['partialDuplicate']),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_invalid(self):
        test_strings = {
            'single': 'InvalidEvent',
            'invalidChild': 'InvalidEvent/InvalidExtension',
            'validChild': 'InvalidEvent/Event',
        }
        expected_results = {
            'single': 'InvalidEvent',
            'invalidChild': 'InvalidEvent/InvalidExtension',
            'validChild': 'InvalidEvent/Event',
        }
        expected_errors = {
            'single': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                      test_strings['single'], 0, 12,
                                                      hed_string=test_strings['single']),
            'invalidChild': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                            test_strings['invalidChild'], 0, 12,
                                                            hed_string=test_strings['invalidChild']),

            'validChild': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                          test_strings['validChild'], 0, 12,
                                                          hed_string=test_strings['validChild']),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_extension_cascade(self):
        """Note we now assume all nodes are extension allowed."""
        test_strings = {
            'validTakesValue': 'Age/15',
            'cascadeExtension': 'Awed/Cascade Extension',
            'invalidExtension': 'Agent-action/Good/Time',
        }
        expected_results = {
            'validTakesValue': 'Attribute/Agent-related/Trait/Age/15',
            'cascadeExtension': 'Attribute/Agent-related/Emotional-state/Awed/Cascade Extension',
            'invalidExtension': 'Event/Agent-action/Good/Time',
        }
        expected_errors = {
            'validTakesValue': [],
            'cascadeExtension': [],
            'invalidExtension': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    # Deprecated tests
    # def test_tag_slash_at_edge(self):
    #     test_strings = {
    #         'leadingSingle': '/Event',
    #         'leadingExtension': '/Event/Extension',
    #         'leadingMultiLevel': '/Vehicle/Train',
    #         'leadingMultiLevelExtension': '/Vehicle/Train/Maglev',
    #         'trailingSingle': 'Event/',
    #         'trailingExtension': 'Event/Extension/',
    #         'trailingMultiLevel': 'Vehicle/Train/',
    #         'trailingMultiLevelExtension': 'Vehicle/Train/Maglev/',
    #         'bothSingle': '/Event/',
    #         'bothExtension': '/Event/Extension/',
    #         'bothMultiLevel': '/Vehicle/Train/',
    #         'bothMultiLevelExtension': '/Vehicle/Train/Maglev/',
    #     }
    #     expected_results = {
    #         'leadingSingle': 'Event',
    #         'leadingExtension': 'Event/Extension',
    #         'leadingMultiLevel': 'Item/Object/Man-made/Vehicle/Train',
    #         'leadingMultiLevelExtension': 'Item/Object/Man-made/Vehicle/Train/Maglev',
    #         'trailingSingle': 'Event',
    #         'trailingExtension': 'Event/Extension',
    #         'trailingMultiLevel': 'Item/Object/Man-made/Vehicle/Train',
    #         'trailingMultiLevelExtension': 'Item/Object/Man-made/Vehicle/Train/Maglev',
    #         'bothSingle': 'Event',
    #         'bothExtension': 'Event/Extension',
    #         'bothMultiLevel': 'Item/Object/Man-made/Vehicle/Train',
    #         'bothMultiLevelExtension': 'Item/Object/Man-made/Vehicle/Train/Maglev',
    #     }
    #     expected_errors = {
    #         'leadingSingle': [],
    #         'leadingExtension': [],
    #         'leadingMultiLevel': [],
    #         'leadingMultiLevelExtension': [],
    #         'trailingSingle': [],
    #         'trailingExtension': [],
    #         'trailingMultiLevel': [],
    #         'trailingMultiLevelExtension': [],
    #         'bothSingle': [],
    #         'bothExtension': [],
    #         'bothMultiLevel': [],
    #         'bothMultiLevelExtension': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)


class TestConvertToShortTag(TestConvertTag):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertToShortTag, self).validator_base(test_strings,
                                                          expected_results, expected_errors, convert_to_short=True)

    def test_tag(self):
        test_strings = {
            'singleLevel': 'Event',
            'twoLevel': 'Event/Sensory-event',
            'fullLong': 'Item/Object/Geometric',
            'partialShort': 'Object/Geometric',
            'alreadyShort': 'Geometric',
        }
        expected_results = {
            'singleLevel': 'Event',
            'twoLevel': 'Sensory-event',
            'fullLong': 'Geometric',
            'partialShort': 'Geometric',
            'alreadyShort': 'Geometric',
        }
        expected_errors = {
            'singleLevel': [],
            'twoLevel': [],
            'fullLong': [],
            'partialShort': [],
            'alreadyShort': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_takes_value(self):
        test_strings = {
            'uniqueValue': 'Item/Sound/Environmental-sound/Unique Value',
            'multiLevel': 'Item/Sound/Environmental-sound/Long Unique Value With/Slash Marks',
            'partialPath': 'Sound/Environmental-sound/Unique Value',
        }
        expected_results = {
            'uniqueValue': 'Environmental-sound/Unique Value',
            'multiLevel': 'Environmental-sound/Long Unique Value With/Slash Marks',
            'partialPath': 'Environmental-sound/Unique Value',
        }
        expected_errors = {
            'uniqueValue': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_takes_value_invalid(self):
        test_strings = {
            'singleLevel': 'Item/Sound/Environmental-sound/Event',
            'multiLevel': 'Item/Sound/Environmental-sound/Event/Sensory-event',
            'mixed': 'Item/Sound/Event/Sensory-event/Environmental-sound',
        }
        expected_results = {
            'singleLevel': 'Item/Sound/Environmental-sound/Event',
            'multiLevel': 'Item/Sound/Environmental-sound/Event/Sensory-event',
            'mixed': 'Item/Sound/Event/Sensory-event/Environmental-sound',
        }
        expected_errors = {
            'singleLevel':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                test_strings['singleLevel'], 31, 36, 'Event'),
            'multiLevel':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                test_strings['multiLevel'], 31, 36, 'Event'),
            'mixed':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                test_strings['mixed'], 11, 16, 'Event'),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Item/Sound/Environmental-sound/Unique Value',
            'trailingSpace': 'Item/Sound/Environmental-sound/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Environmental-sound/Unique Value',
            'trailingSpace': 'Environmental-sound/Unique Value',
        }
        expected_errors = {
            'leadingSpace': [],
            'trailingSpace': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_extension_allowed(self):
        test_strings = {
            'singleLevel': 'Event/Experiment-control/extended lvl1',
            'multiLevel': 'Event/Experiment-control/extended lvl1/Extension2',
            'partialPath': 'Object/Man-made/Vehicle/Boat/Yacht',
        }
        expected_results = {
            'singleLevel': 'Experiment-control/extended lvl1',
            'multiLevel': 'Experiment-control/extended lvl1/Extension2',
            'partialPath': 'Boat/Yacht',
        }
        expected_errors = {
            'singleLevel': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_invalid_extension(self):
        test_strings = {
            'validThenInvalid': 'Event/Experiment-control/valid extension followed by invalid/Event',
            'singleLevel': 'Event/Experiment-control/Geometric',
            'singleLevelAlreadyShort': 'Experiment-control/Geometric',
            'twoLevels': 'Event/Experiment-control/Geometric/Event',
            'duplicate': 'Item/Object/Geometric/Item/Object/Geometric',
        }
        expected_results = {
            'validThenInvalid': 'Event/Experiment-control/valid extension followed by invalid/Event',
            'singleLevel': 'Event/Experiment-control/Geometric',
            'singleLevelAlreadyShort': 'Experiment-control/Geometric',
            'twoLevels': 'Event/Experiment-control/Geometric/Event',
            'duplicate': 'Item/Object/Geometric/Item/Object/Geometric',
        }
        expected_errors = {
            'validThenInvalid': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                                test_strings['validThenInvalid'], 61, 66, 'Event'),
            'singleLevel': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                           test_strings['singleLevel'], 25, 34,
                                                           'Item/Object/Geometric'),
            'singleLevelAlreadyShort':
                self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                test_strings['singleLevelAlreadyShort'],
                                                19, 28, 'Item/Object/Geometric'),
            'twoLevels': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                         test_strings['twoLevels'], 25, 34, 'Item/Object/Geometric'),
            'duplicate': self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, 
                                                         test_strings['duplicate'], 22, 26, 'Item')
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_invalid(self):
        test_strings = {
            'invalidParentWithExistingGrandchild': 'InvalidEvent/Experiment-control/Geometric',
            'invalidChildWithExistingGrandchild': 'Event/InvalidEvent/Geometric',
            'invalidParentWithExistingChild': 'InvalidEvent/Geometric',
            'invalidSingle': 'InvalidEvent',
            'invalidWithExtension': 'InvalidEvent/InvalidExtension',
        }
        expected_results = {
            'invalidParentWithExistingGrandchild': 'InvalidEvent/Experiment-control/Geometric',
            'invalidChildWithExistingGrandchild': 'Event/InvalidEvent/Geometric',
            'invalidParentWithExistingChild': 'InvalidEvent/Geometric',
            'invalidSingle': 'InvalidEvent',
            'invalidWithExtension': 'InvalidEvent/InvalidExtension',
        }
        expected_errors = {
            'invalidParentWithExistingGrandchild': self.error_handler.format_error(
                ValidationErrors.NO_VALID_TAG_FOUND, test_strings['invalidParentWithExistingGrandchild'], 0, 12),
            'invalidChildWithExistingGrandchild': self.error_handler.format_error(
                ValidationErrors.INVALID_PARENT_NODE, test_strings['invalidChildWithExistingGrandchild'], 19, 28,
                "Item/Object/Geometric"),
            'invalidParentWithExistingChild': self.error_handler.format_error(
                ValidationErrors.NO_VALID_TAG_FOUND, test_strings['invalidParentWithExistingChild'], 0, 12),
            'invalidSingle': self.error_handler.format_error(
                ValidationErrors.NO_VALID_TAG_FOUND, test_strings['invalidSingle'], 0, 12),
            'invalidWithExtension': self.error_handler.format_error(
                ValidationErrors.NO_VALID_TAG_FOUND, test_strings['invalidWithExtension'], 0, 12),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_extension_cascade(self):
        """Note we now assume all nodes are extension allowed."""
        test_strings = {
            'validTakesValue': 'Attribute/Agent-related/Trait/Age/15',
            'cascadeExtension': 'Attribute/Agent-related/Emotional-state/Awed/Cascade Extension',
            'invalidExtension': 'Event/Agent-action/Good/Time',
        }
        expected_results = {
            'validTakesValue': 'Age/15',
            'cascadeExtension': 'Awed/Cascade Extension',
            'invalidExtension': 'Agent-action/Good/Time',
        }
        expected_errors = {
            'validTakesValue': [],
            'cascadeExtension': [],
            'invalidExtension': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    # Deprecated tests
    # def test_tag_slash_at_edge(self):
    #     test_strings = {
    #         'leadingSingle': '/Event',
    #         'leadingExtension': '/Event/Extension',
    #         'leadingMultiLevel': '/Item/Object/Man-made/Vehicle/Train',
    #         'leadingMultiLevelExtension': '/Item/Object/Man-made/Vehicle/Train/Maglev',
    #         'trailingSingle': 'Event/',
    #         'trailingExtension': 'Event/Extension/',
    #         'trailingMultiLevel': 'Item/Object/Man-made/Vehicle/Train/',
    #         'trailingMultiLevelExtension': 'Item/Object/Man-made/Vehicle/Train/Maglev/',
    #         'bothSingle': '/Event/',
    #         'bothExtension': '/Event/Extension/',
    #         'bothMultiLevel': '/Item/Object/Man-made/Vehicle/Train/',
    #         'bothMultiLevelExtension': '/Item/Object/Man-made/Vehicle/Train/Maglev/',
    #     }
    #     expected_results = {
    #         'leadingSingle': 'Event',
    #         'leadingExtension': 'Event/Extension',
    #         'leadingMultiLevel': 'Train',
    #         'leadingMultiLevelExtension': 'Train/Maglev',
    #         'trailingSingle': 'Event',
    #         'trailingExtension': 'Event/Extension',
    #         'trailingMultiLevel': 'Train',
    #         'trailingMultiLevelExtension': 'Train/Maglev',
    #         'bothSingle': 'Event',
    #         'bothExtension': 'Event/Extension',
    #         'bothMultiLevel': 'Train',
    #         'bothMultiLevelExtension': 'Train/Maglev',
    #     }
    #     expected_errors = {
    #         'leadingSingle': [],
    #         'leadingExtension': [],
    #         'leadingMultiLevel': [],
    #         'leadingMultiLevelExtension': [],
    #         'trailingSingle': [],
    #         'trailingExtension': [],
    #         'trailingMultiLevel': [],
    #         'trailingMultiLevelExtension': [],
    #         'bothSingle': [],
    #         'bothExtension': [],
    #         'bothMultiLevel': [],
    #         'bothMultiLevelExtension': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)


class TestConvertHedStringToShort(TestConvertString):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertHedStringToShort, self).validator_base(test_strings, expected_results, expected_errors,
                                                                convert_to_short=True)

    def test_empty_strings(self):
        test_strings = {
            'emptyString': '',
        }
        expected_results = {
            'emptyString': '',
        }
        expected_errors = {
            'emptyString': []
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string(self):
        test_strings = {
            'singleLevel': 'Event',
            'multiLevel': 'Event/Sensory-event',
            'twoSingle': 'Event,Attribute',
            'oneExtension': 'Event/Extension',
            'threeMulti': 'Event/Sensory-event,Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5',
            'simpleGroup': '(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5)',
            'groupAndTag': '(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),Item/Object/Man-made/Vehicle/Car',
            'nestedGroup': '((Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors)',
            'nestedGroup2': '(Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors,(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5))'
        }
        expected_results = {
            'singleLevel': 'Event',
            'multiLevel': 'Sensory-event',
            'twoSingle': 'Event,Attribute',
            'oneExtension': 'Event/Extension',
            'threeMulti': 'Sensory-event,Train,RGB-red/0.5',
            'simpleGroup': '(Train,RGB-red/0.5)',
            'groupAndTag': '(Train,RGB-red/0.5),Car',
            'nestedGroup': '((Train,RGB-red/0.5),Car,Indoors)',
            'nestedGroup2': '(Car,Indoors,(Train,RGB-red/0.5))'
        }
        expected_errors = {
            'singleLevel': [],
            'multiLevel': [],
            'twoSingle': [],
            'oneExtension': [],
            'threeMulti': [],
            'simpleGroup': [],
            'groupAndTag': [],
            'nestedGroup': [],
            'nestedGroup2': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string_invalid(self):
        single = 'InvalidEvent'
        double = 'InvalidEvent/InvalidExtension'
        test_strings = {
            'single': single,
            'double': double,
            'both': single + ',' + double,
            'singleWithTwoValid': 'Attribute,' + single + ',Event',
            'doubleWithValid': double + ',Item/Object/Man-made/Vehicle/Car/Minivan',
        }
        expected_results = {
            'single': single,
            'double': double,
            'both': single + ',' + double,
            'singleWithTwoValid': 'Attribute,' + single + ',Event',
            'doubleWithValid': double + ',Car/Minivan',
        }
        expected_errors = {
            'single': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                      test_strings['single'], 0, 12,
                                                      hed_string=test_strings['single']),
            'double': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                      test_strings['double'], 0, 12,
                                                      hed_string=test_strings['double']),
            'both': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                    single, 0, 12,
                                                    hed_string=test_strings['both'])
                  + self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
                                                    double, 0, 12,
                                                    hed_string=test_strings['both']),
            'singleWithTwoValid': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                                  single, 0, 12,
                                                                  hed_string=test_strings['singleWithTwoValid']),
            'doubleWithValid': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                               double, 0, 12,
                                                               hed_string=test_strings['doubleWithValid']),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Item/Sound/Environmental-sound/Unique Value',
            'trailingSpace': 'Item/Sound/Environmental-sound/Unique Value ',
            'bothSpace': ' Item/Sound/Environmental-sound/Unique Value ',
            'leadingSpaceTwo': ' Item/Sound/Environmental-sound/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Item/Sound/Environmental-sound/Unique Value ',
            'bothSpaceTwo': ' Event,Item/Sound/Environmental-sound/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Environmental-sound/Unique Value',
            'trailingSpace': 'Environmental-sound/Unique Value',
            'bothSpace': 'Environmental-sound/Unique Value',
            'leadingSpaceTwo': 'Environmental-sound/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Environmental-sound/Unique Value',
            'bothSpaceTwo': 'Event,Environmental-sound/Unique Value',
        }
        expected_errors = {
            'leadingSpace': [],
            'trailingSpace': [],
            'bothSpace': [],
            'leadingSpaceTwo': [],
            'trailingSpaceTwo': [],
            'bothSpaceTwo': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    # Deprecated tests
    # def test_string_slash_start_end(self):
    #     test_strings = {
    #         'leadingSingle': '/Event',
    #         'leadingMultiLevel': '/Object/Man-made/Vehicle/Train',
    #         'trailingSingle': 'Event/',
    #         'trailingMultiLevel': 'Object/Man-made/Vehicle/Train/',
    #         'bothSingle': '/Event/',
    #         'bothMultiLevel': '/Object/Man-made/Vehicle/Train/',
    #         'twoMixedOuter': '/Event,Object/Man-made/Vehicle/Train/',
    #         'twoMixedInner': 'Event/,/Object/Man-made/Vehicle/Train',
    #         'twoMixedBoth': '/Event/,/Object/Man-made/Vehicle/Train/',
    #         'twoMixedBothGroup': '(/Event/,/Object/Man-made/Vehicle/Train/)',
    #     }
    #     expected_event = 'Event'
    #     expected_train = 'Train'
    #     expected_mixed = expected_event + ',' + expected_train
    #     expected_results = {
    #         'leadingSingle': expected_event,
    #         'leadingMultiLevel': expected_train,
    #         'trailingSingle': expected_event,
    #         'trailingMultiLevel': expected_train,
    #         'bothSingle': expected_event,
    #         'bothMultiLevel': expected_train,
    #         'twoMixedOuter': expected_mixed,
    #         'twoMixedInner': expected_mixed,
    #         'twoMixedBoth': expected_mixed,
    #         'twoMixedBothGroup': '(' + expected_mixed + ')',
    #     }
    #     expected_errors = {
    #         'leadingSingle': [],
    #         'leadingMultiLevel': [],
    #         'trailingSingle': [],
    #         'trailingMultiLevel': [],
    #         'bothSingle': [],
    #         'bothMultiLevel': [],
    #         'twoMixedOuter': [],
    #         'twoMixedInner': [],
    #         'twoMixedBoth': [],
    #         'twoMixedBothGroup': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)

    # Deprecated tests
    # def test_string_extra_slash_space(self):
    #     test_strings = {
    #         'twoLevelDoubleSlash': 'Event//Extension',
    #         'threeLevelDoubleSlash': 'Item//Object//Geometric',
    #         'tripleSlashes': 'Item///Object///Geometric',
    #         'mixedSingleAndDoubleSlashes': 'Item///Object/Geometric',
    #         'singleSlashWithSpace': 'Event/ Extension',
    #         'doubleSlashSurroundingSpace': 'Event/ /Extension',
    #         'doubleSlashThenSpace': 'Event// Extension',
    #         'sosPattern': 'Event///   ///Extension',
    #         'alternatingSlashSpace': 'Item/ / Object/ / Geometric',
    #         'leadingDoubleSlash': '//Event/Extension',
    #         'trailingDoubleSlash': 'Event/Extension//',
    #         'leadingDoubleSlashWithSpace': '/ /Event/Extension',
    #         'trailingDoubleSlashWithSpace': 'Event/Extension/ /',
    #     }
    #     expected_event_extension = 'Event/Extension'
    #     expected_geometric = 'Geometric'
    #     expected_results = {
    #         'twoLevelDoubleSlash': expected_event_extension,
    #         'threeLevelDoubleSlash': expected_geometric,
    #         'tripleSlashes': expected_geometric,
    #         'mixedSingleAndDoubleSlashes': expected_geometric,
    #         'singleSlashWithSpace': expected_event_extension,
    #         'doubleSlashSurroundingSpace': expected_event_extension,
    #         'doubleSlashThenSpace': expected_event_extension,
    #         'sosPattern': expected_event_extension,
    #         'alternatingSlashSpace': expected_geometric,
    #         'leadingDoubleSlash': expected_event_extension,
    #         'trailingDoubleSlash': expected_event_extension,
    #         'leadingDoubleSlashWithSpace': expected_event_extension,
    #         'trailingDoubleSlashWithSpace': expected_event_extension,
    #     }
    #     expected_errors = {
    #         'twoLevelDoubleSlash': [],
    #         'threeLevelDoubleSlash': [],
    #         'tripleSlashes': [],
    #         'mixedSingleAndDoubleSlashes': [],
    #         'singleSlashWithSpace': [],
    #         'doubleSlashSurroundingSpace': [],
    #         'doubleSlashThenSpace': [],
    #         'sosPattern': [],
    #         'alternatingSlashSpace': [],
    #         'leadingDoubleSlash': [],
    #         'trailingDoubleSlash': [],
    #         'leadingDoubleSlashWithSpace': [],
    #         'trailingDoubleSlashWithSpace': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)


class TestConvertHedStringToLong(TestConvertString):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertHedStringToLong, self).validator_base(test_strings, expected_results, expected_errors,
                                                               convert_to_short=False)

    def test_empty_strings(self):
        test_strings = {
            'emptyString': '',
        }
        expected_results = {
            'emptyString': '',
        }
        expected_errors = {
            'emptyString': []
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string(self):
        test_strings = {
            'singleLevel': 'Event',
            'multiLevel': 'Sensory-event',
            'twoSingle': 'Event,Attribute',
            'oneExtension': 'Event/Extension',
            'threeMulti': 'Sensory-event,Train,RGB-red/0.5',
            'simpleGroup': '(Train,RGB-red/0.5)',
            'groupAndTag': '(Train,RGB-red/0.5),Car',
            'nestedGroup': '((Train,RGB-red/0.5),Car,Indoors)',
            'nestedGroup2': '(Car,Indoors,(Train,RGB-red/0.5))'
        }
        expected_results = {
            'singleLevel': 'Event',
            'multiLevel': 'Event/Sensory-event',
            'twoSingle': 'Event,Attribute',
            'oneExtension': 'Event/Extension',
            'threeMulti': 'Event/Sensory-event,Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5',
            'simpleGroup': '(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5)',
            'groupAndTag': '(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),Item/Object/Man-made/Vehicle/Car',
            'nestedGroup': '((Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors)',
            'nestedGroup2': '(Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors,(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5))'
        }
        expected_errors = {
            'singleLevel': [],
            'multiLevel': [],
            'twoSingle': [],
            'oneExtension': [],
            'threeMulti': [],
            'simpleGroup': [],
            'groupAndTag': [],
            'nestedGroup': [],
            'nestedGroup2': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string_invalid(self):
        single = 'InvalidEvent'
        double = 'InvalidEvent/InvalidExtension'
        test_strings = {
            'single': single,
            'double': double,
            'both': single + ',' + double,
            'singleWithTwoValid': 'Attribute,' + single + ',Event',
            'doubleWithValid': double + ',Car/Minivan',
        }
        expected_results = {
            'single': single,
            'double': double,
            'both': single + ',' + double,
            'singleWithTwoValid': 'Attribute,' + single + ',Event',
            'doubleWithValid': double + ',Item/Object/Man-made/Vehicle/Car/Minivan',
        }
        expected_errors = {
            'single': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                      test_strings['single'], 0, 12,
                                                      hed_string=test_strings['single']),
            'double': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                      test_strings['double'], 0, 12,
                                                      hed_string=test_strings['double']),
            'both': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                    single, 0, 12,
                                                    hed_string=test_strings['both'])
                     + self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                       double, 0, 12,
                                                       hed_string=test_strings['both']),
            'singleWithTwoValid': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                                  single, 0, 12,
                                                                  hed_string=test_strings['singleWithTwoValid']),
            'doubleWithValid': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND, 
                                                               double, 0, 12,
                                                               hed_string=test_strings['doubleWithValid']),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Environmental-sound/Unique Value',
            'trailingSpace': 'Environmental-sound/Unique Value ',
            'bothSpace': ' Environmental-sound/Unique Value ',
            'leadingSpaceTwo': ' Environmental-sound/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Environmental-sound/Unique Value ',
            'bothSpaceTwo': ' Event,Environmental-sound/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Item/Sound/Environmental-sound/Unique Value',
            'trailingSpace': 'Item/Sound/Environmental-sound/Unique Value',
            'bothSpace': 'Item/Sound/Environmental-sound/Unique Value',
            'leadingSpaceTwo': 'Item/Sound/Environmental-sound/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Item/Sound/Environmental-sound/Unique Value',
            'bothSpaceTwo': 'Event,Item/Sound/Environmental-sound/Unique Value',
        }
        expected_errors = {
            'leadingSpace': [],
            'trailingSpace': [],
            'bothSpace': [],
            'leadingSpaceTwo': [],
            'trailingSpaceTwo': [],
            'bothSpaceTwo': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    # Deprecated tests
    # def test_string_slash_start_end(self):
    #     test_strings = {
    #         'leadingSingle': '/Event',
    #         'leadingMultiLevel': '/Vehicle/Train',
    #         'trailingSingle': 'Event/',
    #         'trailingMultiLevel': 'Vehicle/Train/',
    #         'bothSingle': '/Event/',
    #         'bothMultiLevel': '/Vehicle/Train/',
    #         'twoMixedOuter': '/Event,Vehicle/Train/',
    #         'twoMixedInner': 'Event/,/Vehicle/Train',
    #         'twoMixedBoth': '/Event/,/Vehicle/Train/',
    #         'twoMixedBothGroup': '(/Event/,/Vehicle/Train/)',
    #     }
    #     expected_event = 'Event'
    #     expected_train = 'Item/Object/Man-made/Vehicle/Train'
    #     expected_mixed = expected_event + ',' + expected_train
    #     expected_results = {
    #         'leadingSingle': expected_event,
    #         'leadingMultiLevel': expected_train,
    #         'trailingSingle': expected_event,
    #         'trailingMultiLevel': expected_train,
    #         'bothSingle': expected_event,
    #         'bothMultiLevel': expected_train,
    #         'twoMixedOuter': expected_mixed,
    #         'twoMixedInner': expected_mixed,
    #         'twoMixedBoth': expected_mixed,
    #         'twoMixedBothGroup': '(' + expected_mixed + ')',
    #     }
    #     expected_errors = {
    #         'leadingSingle': [],
    #         'leadingMultiLevel': [],
    #         'trailingSingle': [],
    #         'trailingMultiLevel': [],
    #         'bothSingle': [],
    #         'bothMultiLevel': [],
    #         'twoMixedOuter': [],
    #         'twoMixedInner': [],
    #         'twoMixedBoth': [],
    #         'twoMixedBothGroup': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)

    # def test_string_extra_slash_space(self):
    #     test_strings = {
    #         'twoLevelDoubleSlash': 'Event//Extension',
    #         'threeLevelDoubleSlash': 'Vehicle//Boat//Tanker',
    #         'tripleSlashes': 'Vehicle///Boat///Tanker',
    #         'mixedSingleAndDoubleSlashes': 'Vehicle///Boat/Tanker',
    #         'singleSlashWithSpace': 'Event/ Extension',
    #         'doubleSlashSurroundingSpace': 'Event/ /Extension',
    #         'doubleSlashThenSpace': 'Event// Extension',
    #         'sosPattern': 'Event///   ///Extension',
    #         'alternatingSlashSpace': 'Vehicle/ / Boat/ / Tanker',
    #         'leadingDoubleSlash': '//Event/Extension',
    #         'trailingDoubleSlash': 'Event/Extension//',
    #         'leadingDoubleSlashWithSpace': '/ /Event/Extension',
    #         'trailingDoubleSlashWithSpace': 'Event/Extension/ /',
    #     }
    #     expected_event_extension = 'Event/Extension'
    #     expected_tanker = 'Item/Object/Man-made/Vehicle/Boat/Tanker'
    #     expected_results = {
    #         'twoLevelDoubleSlash': expected_event_extension,
    #         'threeLevelDoubleSlash': expected_tanker,
    #         'tripleSlashes': expected_tanker,
    #         'mixedSingleAndDoubleSlashes': expected_tanker,
    #         'singleSlashWithSpace': expected_event_extension,
    #         'doubleSlashSurroundingSpace': expected_event_extension,
    #         'doubleSlashThenSpace': expected_event_extension,
    #         'sosPattern': expected_event_extension,
    #         'alternatingSlashSpace': expected_tanker,
    #         'leadingDoubleSlash': expected_event_extension,
    #         'trailingDoubleSlash': expected_event_extension,
    #         'leadingDoubleSlashWithSpace': expected_event_extension,
    #         'trailingDoubleSlashWithSpace': expected_event_extension,
    #     }
    #     expected_errors = {
    #         'twoLevelDoubleSlash': [],
    #         'threeLevelDoubleSlash': [],
    #         'tripleSlashes': [],
    #         'mixedSingleAndDoubleSlashes': [],
    #         'singleSlashWithSpace': [],
    #         'doubleSlashSurroundingSpace': [],
    #         'doubleSlashThenSpace': [],
    #         'sosPattern': [],
    #         'alternatingSlashSpace': [],
    #         'leadingDoubleSlash': [],
    #         'trailingDoubleSlash': [],
    #         'leadingDoubleSlashWithSpace': [],
    #         'trailingDoubleSlashWithSpace': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)


if __name__ == "__main__":
    unittest.main()
