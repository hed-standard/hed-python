import unittest
import os

from hed.errors import error_reporter
from hed.models.hed_string import HedString
from hed.schema.hed_schema_file import load_schema


class TestBaseTag(unittest.TestCase):
    schema_file = '../data/legacy_xml/reduced_no_dupe.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = load_schema(hed_xml)
        cls.error_handler = error_reporter.ErrorHandler()


class TestCanonicalForms(TestBaseTag):
    def tag_form_base(self, test_strings, expected_results, expected_errors):
        for test_key in test_strings:
            test_string_obj = HedString(test_strings[test_key])
            test_errors = test_string_obj.convert_to_canonical_forms(hed_schema=self.hed_schema, error_handler=self.error_handler)
            expected_error = expected_errors[test_key]
            expected_result = expected_results[test_key]
            for tag in test_string_obj.tags():
                self.assertEqual(tag.base_tag, expected_result, test_strings[test_key])
                self.assertCountEqual(test_errors, expected_error, test_strings[test_key])


class TestConvertToLongTag(TestCanonicalForms):
    def validator(self, test_strings, expected_results, expected_errors):
        super(TestConvertToLongTag, self).tag_form_base(test_strings,
                                                         expected_results, expected_errors)

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
            'uniqueValue': 'Attribute/Informational/Label',
            'multiLevel': 'Attribute/Informational/Label',
            'partialPath': 'Attribute/Informational/Label',
        }
        expected_errors = {
            'uniqueValue': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    # def test_tag_spaces_start_end(self):
    #     test_strings = {
    #         'leadingSpace': ' Environmental-sound/Unique Value',
    #         'trailingSpace': 'Environmental-sound/Unique Value ',
    #     }
    #     expected_results = {
    #         'leadingSpace': 'Item/Sound/Environmental-sound/Unique Value',
    #         'trailingSpace': 'Item/Sound/Environmental-sound/Unique Value',
    #     }
    #     expected_errors = {
    #         'leadingSpace': [],
    #         'trailingSpace': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)
    #
    def test_tag_extension_allowed(self):
        test_strings = {
            'singleLevel': 'Experiment-control/extended lvl1',
            'multiLevel': 'Experiment-control/extended lvl1/Extension2',
            'partialPath': 'Vehicle/Boat/Yacht',
        }
        expected_results = {
            'singleLevel': 'Event/Experiment-control',
            'multiLevel': 'Event/Experiment-control',
            'partialPath': 'Item/Object/Man-made/Vehicle/Boat',
        }
        expected_errors = {
            'singleLevel': [],
            'multiLevel': [],
            'partialPath': [],
        }
        self.validator(test_strings, expected_results, expected_errors)

    # def test_tag_invalid_extension(self):
    #     test_strings = {
    #         'validThenInvalid': 'Experiment-control/valid extension followed by invalid/Event',
    #         'singleLevel': 'Experiment-control/Geometric',
    #         'singleLevelAlreadyLong': 'Event/Experiment-control/Geometric',
    #         'twoLevels': 'Experiment-control/Geometric/Event',
    #         'partialDuplicate': 'Geometric/Item/Object/Geometric',
    #     }
    #     expected_results = {
    #         'validThenInvalid': 'Experiment-control/valid extension followed by invalid/Event',
    #         'singleLevel': 'Experiment-control/Geometric',
    #         'singleLevelAlreadyLong': 'Event/Experiment-control/Geometric',
    #         'twoLevels': 'Experiment-control/Geometric/Event',
    #         'partialDuplicate': 'Geometric/Item/Object/Geometric',
    #     }
    #     expected_errors = {
    #         'validThenInvalid':
    #             self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, test_strings['validThenInvalid'],
    #                                             55, 60, 'Event', hed_string=test_strings['validThenInvalid']),
    #         'singleLevel':
    #             self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, test_strings['singleLevel'],
    #                                             19, 28, 'Item/Object/Geometric',
    #                                             hed_string=test_strings['singleLevel']),
    #         'singleLevelAlreadyLong':
    #             self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE,
    #                                             test_strings['singleLevelAlreadyLong'],
    #                                             25, 34, 'Item/Object/Geometric',
    #                                             hed_string=test_strings['singleLevelAlreadyLong']),
    #         'twoLevels':
    #             self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE, test_strings['twoLevels'],
    #                                             19, 28, 'Item/Object/Geometric',
    #                                             hed_string=test_strings['twoLevels']),
    #         'partialDuplicate':
    #             self.error_handler.format_error(ValidationErrors.INVALID_PARENT_NODE,
    #                                             test_strings['partialDuplicate'], 10, 14, 'Item',
    #                                             hed_string=test_strings['partialDuplicate']),
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)
    #
    # def test_tag_invalid(self):
    #     test_strings = {
    #         'single': 'InvalidEvent',
    #         'invalidChild': 'InvalidEvent/InvalidExtension',
    #         'validChild': 'InvalidEvent/Event',
    #     }
    #     expected_results = {
    #         'single': 'InvalidEvent',
    #         'invalidChild': 'InvalidEvent/InvalidExtension',
    #         'validChild': 'InvalidEvent/Event',
    #     }
    #     expected_errors = {
    #         'single': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
    #                                                   test_strings['single'], 0, 12,
    #                                                   hed_string=test_strings['single']),
    #         'invalidChild': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
    #                                                         test_strings['invalidChild'], 0, 12,
    #                                                         hed_string=test_strings['invalidChild']),
    #
    #         'validChild': self.error_handler.format_error(ValidationErrors.NO_VALID_TAG_FOUND,
    #                                                       test_strings['validChild'], 0, 12,
    #                                                       hed_string=test_strings['validChild']),
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)
    #
    # def test_tag_extension_cascade(self):
    #     """Note we now assume all nodes are extension allowed."""
    #     test_strings = {
    #         'validTakesValue': 'Age/15',
    #         'cascadeExtension': 'Awed/Cascade Extension',
    #         'invalidExtension': 'Agent-action/Good/Time',
    #     }
    #     expected_results = {
    #         'validTakesValue': 'Attribute/Agent-related/Trait/Age/15',
    #         'cascadeExtension': 'Attribute/Agent-related/Emotional-state/Awed/Cascade Extension',
    #         'invalidExtension': 'Event/Agent-action/Good/Time',
    #     }
    #     expected_errors = {
    #         'validTakesValue': [],
    #         'cascadeExtension': [],
    #         'invalidExtension': [],
    #     }
    #     self.validator(test_strings, expected_results, expected_errors)


if __name__ == "__main__":
    unittest.main()
