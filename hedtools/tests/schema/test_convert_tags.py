import unittest

from hed import HedString
from hed.errors import ValidationErrors, ErrorContext, ErrorHandler
from tests.validator.test_tag_validator_base import TestHedBase


class TestTagFormat(TestHedBase):
    schema_file = '../data/legacy_xml/reduced_no_dupe.xml'


class TestConvertTag(TestTagFormat):
    def converter_base(self, test_strings, expected_results, expected_errors, convert_to_short=True):
        for test_key in test_strings:
            test_string_obj = HedString(test_strings[test_key])
            error_handler = ErrorHandler()
            error_handler.push_error_context(ErrorContext.HED_STRING, test_string_obj, increment_depth_after=False)
            test_issues = test_string_obj.convert_to_canonical_forms(self.hed_schema)
            if convert_to_short:
                string_result = test_string_obj.get_as_short()
            else:
                string_result = test_string_obj.get_as_long()
            expected_params = expected_errors[test_key]
            expected_result = expected_results[test_key]

            expected_issue = self.really_format_errors(error_handler, hed_string=test_string_obj,
                                                       params=expected_params)
            error_handler.add_context_to_issues(test_issues)

            # print(test_key)
            # print(expected_issue)
            # print(test_issues)
            self.assertEqual(string_result, expected_result, test_strings[test_key])
            self.assertCountEqual(test_issues, expected_issue, test_strings[test_key])


class TestConvertToLongTag(TestConvertTag):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertToLongTag, self).converter_base(test_strings,
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
            'uniqueValue': 'Label/Unique Value',
            'multiLevel': 'Label/Long Unique Value With/Slash Marks',
            'partialPath': 'Informational/Label/Unique Value',
        }
        expected_results = {
            'uniqueValue': 'Attribute/Informational/Label/Unique Value',
            'multiLevel': 'Attribute/Informational/Label/Long Unique Value With/Slash Marks',
            'partialPath': 'Attribute/Informational/Label/Unique Value',
        }
        expected_errors = {
            'uniqueValue': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Label/Unique Value',
            'trailingSpace': 'Label/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Attribute/Informational/Label/Unique Value',
            'trailingSpace': 'Attribute/Informational/Label/Unique Value',
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
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                 index_in_tag=55, index_in_tag_end=60, expected_parent_tag='Event'),
            'singleLevel':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                 index_in_tag=19, index_in_tag_end=28,
                                                 expected_parent_tag='Item/Object/Geometric'),
            'singleLevelAlreadyLong':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                 index_in_tag=25, index_in_tag_end=34,
                                                 expected_parent_tag='Item/Object/Geometric'),
            'twoLevels':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                 index_in_tag=19, index_in_tag_end=28,
                                                 expected_parent_tag='Item/Object/Geometric'),
            'partialDuplicate':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE, tag=0,
                                                 index_in_tag=10, index_in_tag_end=14, expected_parent_tag='Item'),
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
            'single': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=0, index_in_tag=0, index_in_tag_end=12),
            'invalidChild': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                             tag=0, index_in_tag=0, index_in_tag_end=12),

            'validChild': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                           tag=0, index_in_tag=0, index_in_tag_end=12),
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


class TestConvertToShortTag(TestConvertTag):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertToShortTag, self).converter_base(test_strings,
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
            'uniqueValue': 'Attribute/Informational/Label/Unique Value',
            'multiLevel': 'Attribute/Informational/Label/Long Unique Value With/Slash Marks',
            'partialPath': 'Informational/Label/Unique Value',
        }
        expected_results = {
            'uniqueValue': 'Label/Unique Value',
            'multiLevel': 'Label/Long Unique Value With/Slash Marks',
            'partialPath': 'Label/Unique Value',
        }
        expected_errors = {
            'uniqueValue': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_takes_value_invalid(self):
        test_strings = {
            'singleLevel': 'Attribute/Informational/Label/Event',
            'multiLevel': 'Attribute/Informational/Label/Event/Sensory-event',
            'mixed': 'Item/Sound/Event/Sensory-event/Environmental-sound',
        }
        expected_results = {
            'singleLevel': 'Attribute/Informational/Label/Event',
            'multiLevel': 'Attribute/Informational/Label/Event/Sensory-event',
            'mixed': 'Item/Sound/Event/Sensory-event/Environmental-sound',
        }
        expected_errors = {
            'singleLevel':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                 tag=0, index_in_tag=30, index_in_tag_end=35,
                                                 expected_parent_tag='Event'),
            'multiLevel':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                 tag=0, index_in_tag=30, index_in_tag_end=35,
                                                 expected_parent_tag='Event'),
            'mixed':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                 tag=0, index_in_tag=11, index_in_tag_end=16,
                                                 expected_parent_tag='Event'),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_tag_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Attribute/Informational/Label/Unique Value',
            'trailingSpace': 'Attribute/Informational/Label/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Label/Unique Value',
            'trailingSpace': 'Label/Unique Value',
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
            'validThenInvalid': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                                 tag=0, index_in_tag=61, index_in_tag_end=66,
                                                                 expected_parent_tag='Event'),
            'singleLevel': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                            tag=0, index_in_tag=25, index_in_tag_end=34,
                                                            expected_parent_tag='Item/Object/Geometric'),
            'singleLevelAlreadyShort':
                self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                 tag=0, index_in_tag=19, index_in_tag_end=28,
                                                 expected_parent_tag='Item/Object/Geometric'),
            'twoLevels': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                          tag=0, index_in_tag=25, index_in_tag_end=34,
                                                          expected_parent_tag='Item/Object/Geometric'),
            'duplicate': self.format_error_but_not_really(ValidationErrors.INVALID_PARENT_NODE,
                                                          tag=0, index_in_tag=22, index_in_tag_end=26,
                                                          expected_parent_tag='Item')
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
            'invalidParentWithExistingGrandchild': self.format_error_but_not_really(
                ValidationErrors.NO_VALID_TAG_FOUND, tag=0, index_in_tag=0, index_in_tag_end=12),
            'invalidChildWithExistingGrandchild': self.format_error_but_not_really(
                ValidationErrors.INVALID_PARENT_NODE, tag=0, index_in_tag=19, index_in_tag_end=28,
                expected_parent_tag="Item/Object/Geometric"),
            'invalidParentWithExistingChild': self.format_error_but_not_really(
                ValidationErrors.NO_VALID_TAG_FOUND, tag=0, index_in_tag=0, index_in_tag_end=12),
            'invalidSingle': self.format_error_but_not_really(
                ValidationErrors.NO_VALID_TAG_FOUND, tag=0, index_in_tag=0, index_in_tag_end=12),
            'invalidWithExtension': self.format_error_but_not_really(
                ValidationErrors.NO_VALID_TAG_FOUND, tag=0, index_in_tag=0, index_in_tag_end=12),
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


class TestConvertHedStringToShort(TestConvertTag):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertHedStringToShort, self).converter_base(test_strings, expected_results, expected_errors,
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
            'threeMulti': 'Event/Sensory-event,Item/Object/Man-made/Vehicle/Train,\
            Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5',
            'simpleGroup': '(Item/Object/Man-made/Vehicle/Train,\
            Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5)',
            'groupAndTag': '(Item/Object/Man-made/Vehicle/Train,\
            Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),\
            Item/Object/Man-made/Vehicle/Car',
            'nestedGroup': '((Item/Object/Man-made/Vehicle/Train,\
            Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),\
            Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors)',
            'nestedGroup2': '(Item/Object/Man-made/Vehicle/Car,'
                            'Attribute/Environmental/Indoors,(Item/Object/Man-made/Vehicle/Train,\
                            Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5))'
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
            'single': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=0, index_in_tag=0, index_in_tag_end=12),
            'double': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=0, index_in_tag=0, index_in_tag_end=12),
            'both': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                     tag=0, index_in_tag=0, index_in_tag_end=12)
                    + self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=1, index_in_tag=0, index_in_tag_end=12),
            'singleWithTwoValid': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                   tag=1, index_in_tag=0, index_in_tag_end=12),
            'doubleWithValid': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                tag=0, index_in_tag=0, index_in_tag_end=12),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Attribute/Informational/Label/Unique Value',
            'trailingSpace': 'Attribute/Informational/Label/Unique Value ',
            'bothSpace': ' Attribute/Informational/Label/Unique Value ',
            'leadingSpaceTwo': ' Attribute/Informational/Label/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Attribute/Informational/Label/Unique Value ',
            'bothSpaceTwo': ' Event,Attribute/Informational/Label/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Label/Unique Value',
            'trailingSpace': 'Label/Unique Value',
            'bothSpace': 'Label/Unique Value',
            'leadingSpaceTwo': 'Label/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Label/Unique Value',
            'bothSpaceTwo': 'Event,Label/Unique Value',
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


class TestConvertHedStringToLong(TestConvertTag):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertHedStringToLong, self).converter_base(test_strings, expected_results, expected_errors,
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
            'threeMulti': 'Event/Sensory-event,Item/Object/Man-made/Vehicle/Train,' +
            'Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5',
            'simpleGroup': '(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5)',
            'groupAndTag': '(Item/Object/Man-made/Vehicle/Train,' +
            'Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),Item/Object/Man-made/Vehicle/Car',
            'nestedGroup': '((Item/Object/Man-made/Vehicle/Train,' +
                           'Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5),' +
                           'Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors)',
            'nestedGroup2': '(Item/Object/Man-made/Vehicle/Car,Attribute/Environmental/Indoors,' +
                            '(Item/Object/Man-made/Vehicle/Train,Attribute/Sensory/Visual/Color/RGB-color/RGB-red/0.5))'
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
            'single': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=0, index_in_tag=0, index_in_tag_end=12),
            'double': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=0, index_in_tag=0, index_in_tag_end=12),
            'both': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                     tag=0, index_in_tag=0, index_in_tag_end=12)
                    + self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                       tag=1, index_in_tag=0, index_in_tag_end=12),
            'singleWithTwoValid': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                   tag=1, index_in_tag=0, index_in_tag_end=12),
            'doubleWithValid': self.format_error_but_not_really(ValidationErrors.NO_VALID_TAG_FOUND,
                                                                tag=0, index_in_tag=0, index_in_tag_end=12),
        }
        self.validator(test_strings, expected_results, expected_errors)

    def test_string_spaces_start_end(self):
        test_strings = {
            'leadingSpace': ' Label/Unique Value',
            'trailingSpace': 'Label/Unique Value ',
            'bothSpace': ' Label/Unique Value ',
            'leadingSpaceTwo': ' Label/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Label/Unique Value ',
            'bothSpaceTwo': ' Event,Label/Unique Value ',
        }
        expected_results = {
            'leadingSpace': 'Attribute/Informational/Label/Unique Value',
            'trailingSpace': 'Attribute/Informational/Label/Unique Value',
            'bothSpace': 'Attribute/Informational/Label/Unique Value',
            'leadingSpaceTwo': 'Attribute/Informational/Label/Unique Value,Event',
            'trailingSpaceTwo': 'Event,Attribute/Informational/Label/Unique Value',
            'bothSpaceTwo': 'Event,Attribute/Informational/Label/Unique Value',
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
