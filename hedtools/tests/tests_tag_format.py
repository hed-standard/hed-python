import unittest
import os
from hed.utilities.tag_format import TagFormat
from hed.utilities.util import error_reporter, format_util


class Test(unittest.TestCase):
    schema_file = 'data/reduced_no_dupe.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.tag_compare = TagFormat(hed_xml)
        cls.tag_compare.map_schema.print_tag_dict()

    def compare_base_new(self, test_function, input_strings, expected_results, errors_list=None):
        # Assume there are no errors if none provided.
        check_errors = True
        if errors_list is None:
            errors_list = []
        while len(errors_list) < len(input_strings):
            check_errors = False
            errors_list.append(None)

        for input_tag, output_tag, errors in zip(input_strings, expected_results, errors_list):
            converted_tag, actual_errors = test_function(input_tag)

            self.assertEqual(output_tag, converted_tag)
            if check_errors:
                self.assertEqual(errors, actual_errors)
            else:
                self.assertFalse(actual_errors)

    def compare_split_results(self, input_strings, expected_results):
        for input_tag, result in zip(input_strings, expected_results):
            actual_results = format_util.split_hed_string(input_tag)
            decoded_results = [input_tag[start:end] for (is_tag, (start, end)) in actual_results]
            self.assertEqual(result, decoded_results)

    def test_tag_long(self):
        test_strings = [
            'Event',
            'Sensory event',
            'Item/Object/Geometric',
            'Object/Geometric'
        ]
        expected_results = [
            'Event',
            'Event/Sensory event',
            'Item/Object/Geometric',
            'Item/Object/Geometric'
        ]
        errors_list = [
            None,
            None,
            None,
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short(self):
        test_strings = [
            'Event',
            'Event/Sensory event',
            'Item/Object/Geometric',
            'Object/Geometric'
        ]
        expected_results = [
            'Event',
            'Sensory event',
            'Geometric',
            'Geometric'
        ]
        errors_list = [
            None,
            None,
            None,
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_takes_value(self):
        test_strings = [
            'Environmental sound/Unique Value'
        ]
        expected_results = [
            'Item/Sound/Environmental sound/Unique Value'
        ]

        errors_list = [
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_takes_value(self):
        test_strings = [
            'Item/Sound/Environmental sound/Unique Value',
            'Sound/Environmental sound/Long Unique Value With/Slash Marks',

        ]
        expected_results = [
            'Environmental sound/Unique Value',
            'Environmental sound/Long Unique Value With/Slash Marks'
        ]

        errors_list = [
            None,
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_short_takes_value_invalid(self):
        test_strings = [
            'Item/Sound/Environmental sound/Event'
        ]
        expected_results = [
            'Item/Sound/Environmental sound/Event'
        ]
        errors_list = [
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, 'Item/Sound/Environmental sound/Event', 31, 36,
                                             'Event')
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_short_spaces_start_end(self):
        test_strings = [
            ' Environmental sound/Unique Value',
            'Environmental sound/Unique Value ',
        ]
        expected_results = [
            ' Environmental sound/Unique Value',
            'Item/Sound/Environmental sound/Unique Value '
        ]

        errors_list = [
            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND, ' Environmental sound/Unique Value',
                                             0, 20),
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_extension_allowed(self):
        test_strings = [
            'Event/Experiment control/extended lvl1',
            'Event/Experiment control/extended lvl1/Extension2',
        ]
        expected_results = [
            'Experiment control/extended lvl1',
            'Experiment control/extended lvl1/Extension2',
        ]
        errors_list = [
            None,
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_extension_allowed(self):
        test_strings = [
            'Experiment control/extended lvl1',
            'Experiment control/extended lvl1/Extension2',
        ]
        expected_results = [
            'Event/Experiment control/extended lvl1',
            'Event/Experiment control/extended lvl1/Extension2',
        ]
        errors_list = [
            None,
            None
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_invalid_extension(self):
        test_strings = [
            'Event/Experiment control/Geometric',
            'Event/Experiment control/Geometric/Event',
            'Event/Experiment control/valid extension',
            'Event/Experiment control/valid extension followed by invalid/Event',
            'Item/Object/Geometric/Item/Object/Geometric'
        ]
        expected_results = [
            'Event/Experiment control/Geometric',
            'Event/Experiment control/Geometric/Event',
            'Experiment control/valid extension',
            'Event/Experiment control/valid extension followed by invalid/Event',
            'Item/Object/Geometric/Item/Object/Geometric'
        ]
        errors_list = [
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'Event/Experiment control/Geometric',
                                             25, 34, 'Item/Object/Geometric'),
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'Event/Experiment control/Geometric/Event',
                                             35, 40, 'Event'),
            None,
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'Event/Experiment control/valid extension followed by invalid/Event',
                                             61, 66, 'Event'),
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'Item/Object/Geometric/Item/Object/Geometric',
                                             34, 43, 'Item/Object/Geometric'),
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_invalid_extension(self):
        test_strings = [
            'Experiment control/Geometric',
            'Experiment control/Geometric/Event',
            'Event/Experiment control/valid extension',
            'Experiment control/valid extension followed by invalid/Event',
            'Item/Object/Geometric/Item/Object/Geometric'
        ]
        expected_results = [
            'Experiment control/Geometric',
            'Experiment control/Geometric/Event',
            'Event/Experiment control/valid extension',
            'Experiment control/valid extension followed by invalid/Event',
            'Item/Object/Geometric/Item/Object/Geometric'
        ]
        errors_list = [
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, 'Experiment control/Geometric',
                                             19, 28,
                                             'Item/Object/Geometric'),
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, 'Experiment control/Geometric/Event',
                                             19, 28,
                                             'Item/Object/Geometric'),
            None,
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE, 'Experiment control/valid extension followed by invalid/Event',
                                             55, 60,
                                             'Event'),
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'Item/Object/Geometric/Item/Object/Geometric',
                                             22, 26, 'Item'),
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_invalid(self):
        test_strings = [
            'InvalidEvent/Experiment control/Geometric',
            'Event/InvalidEvent/Geometric',
            'InvalidEvent',
            'InvalidEvent/InvalidExtension'
        ]
        expected_results = [
            'InvalidEvent/Experiment control/Geometric',
            'Event/InvalidEvent/Geometric',
            'InvalidEvent',
            'InvalidEvent/InvalidExtension'
        ]
        errors_list = [
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'InvalidEvent/Experiment control/Geometric', 32, 41,
                                             'Item/Object/Geometric'),
            error_reporter.report_error_type(error_reporter.INVALID_PARENT_NODE,
                                             'Event/InvalidEvent/Geometric', 19, 28,
                                             'Item/Object/Geometric'),
            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent', 0, 12),
            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent/InvalidExtension', 0, 12),
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_invalid(self):
        test_strings = [
            'InvalidEvent',
            'InvalidEvent/InvalidExtension',
            'InvalidEvent/Event'
        ]
        expected_results = [
            'InvalidEvent',
            'InvalidEvent/InvalidExtension',
            'InvalidEvent/Event'
        ]
        errors_list = [
            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent', 0, 12),
            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent/InvalidExtension', 0, 12),

            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent/Event', 0, 12),
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_extension_cascade(self):
        """Note we now assume all nodes are extension allowed."""
        test_strings = [
            'Participant/Trait/Age/15',
            'Participant/Emotional state/Awed/Invalid Non Cascade Extension',
            'Item/Sound/Siren/Invalid Extension',
            'Item/Sound/Siren',
            'Participant/Trait/NewTraitTest'
        ]
        expected_results = [
            'Age/15',
            'Awed/Invalid Non Cascade Extension',
            'Siren/Invalid Extension',
            'Siren',
            'Trait/NewTraitTest'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_extension_cascade(self):
        """Note we now assume all nodes are extension allowed."""
        test_strings = [
            'Age/15',
            'Awed/Cascade Extension',
            'Siren/Extension',
            'Siren',
            'Trait/NewTraitTest'

        ]
        expected_results = [
            'Participant/Trait/Age/15',
            'Participant/Emotional state/Awed/Cascade Extension',
            'Item/Sound/Siren/Extension',
            'Item/Sound/Siren',
            'Participant/Trait/NewTraitTest'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_slash_at_start(self):
        test_strings = [
            '/Event/Extension',
            '/Item/Sound/Siren',
            '/Item/Sound/Siren/Extension'
        ]
        expected_results = [
            'Event/Extension',
            'Siren',
            'Siren/Extension'
        ]
        errors_list = [
        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_slash_at_start(self):
        test_strings = [
            '/Event/Extension',
            '/Item/Sound/Siren',
            '/Item/Sound/Siren/Extension'
        ]
        expected_results = [
            'Event/Extension',
            'Item/Sound/Siren',
            'Item/Sound/Siren/Extension'
        ]
        errors_list = [
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_tag_short_slash_at_end(self):
        test_strings = [
            'Event/Extension/',
            'Item/Sound/Siren/',
            'Item/Sound/Siren/Extension/'
        ]
        expected_results = [
            'Event/Extension',
            'Siren',
            'Siren/Extension'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare._convert_to_short_tag, test_strings, expected_results, errors_list)

    def test_tag_long_slash_at_end(self):
        test_strings = [
            'Event/Extension/',
            'Item/Sound/Siren/',
            'Item/Sound/Siren/Extension/'
        ]
        expected_results = [
            'Event/Extension',
            'Item/Sound/Siren',
            'Item/Sound/Siren/Extension'
        ]
        errors_list = [
        ]
        self.compare_base_new(self.tag_compare._convert_to_long_tag, test_strings, expected_results, errors_list)

    def test_empty_strings(self):
        test_strings = [
            ''
        ]
        expected_results = [
            ''
        ]
        errors_list = [
            [error_reporter.report_error_type(error_reporter.EMPTY_TAG_FOUND, "")]
        ]

        self.compare_base_new(self.tag_compare.convert_hed_string_to_short, test_strings, expected_results, errors_list)
        self.compare_base_new(self.tag_compare.convert_hed_string_to_long, test_strings, expected_results, errors_list)

    # Tests below here test the string functions.  We probably will want more.
    def test_string_long(self):
        test_strings = {'noTildeGroup': 'Sensory event,'
                                            '(Siren,Sensory event)',
                            'oneTildeGroup': 'Sensory event,'
                                             '(Siren ~ Indoors)',
                            'twoTildeGroup': 'Sensory event,'
                                             '(Awake ~ Age/15 ~ Siren, Vehicle,'
                                             ' RGB Red/100)',
                            'singleTag': 'Sensory event',
                            'nestedTag': 'Event, Sensory event, Sensory event'
                            }

        expected_results = {'noTildeGroup': 'Event/Sensory event,'
                                        '(Item/Sound/Siren,Event/Sensory event)',
                        'oneTildeGroup': 'Event/Sensory event,'
                                         '(Item/Sound/Siren ~ Attribute/Environmental/Indoors)',
                        'twoTildeGroup': 'Event/Sensory event,'
                                         '(Participant/Cognitive state/Awake ~ Participant/Trait/Age/15 ~ Item/Sound/Siren, Item/Object/Manmade/Vehicle, '
                                         'Attribute/Sensory/Visual/Color/RGB color/RGB Red/100)',
                        'singleTag': 'Event/Sensory event',
                        'nestedTag': 'Event, Event/Sensory event, Event/Sensory event'
                        }

        test_strings = test_strings.values()
        expected_results = expected_results.values()

        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_long, test_strings, expected_results, errors_list)

    def test_string_short(self):
        test_strings = {
                        'noTildeGroup': 'Event/Sensory event,'
                                        '(Item/Sound/Siren,Event/Sensory event)',
                        'oneTildeGroup': 'Event/Sensory event,'
                                         '(Item/Sound/Siren ~ Attribute/Environmental/Indoors)',
                        'twoTildeGroup': 'Event/Sensory event,'
                                         '(Participant/Cognitive state/Awake ~ Participant/Trait/Age/15 ~ Item/Sound/Siren, Item/Object/Manmade/Vehicle,'
                                         ' Attribute/Sensory/Visual/Color/RGB color/RGB Red/100)',
                        'singleTag': 'Event/Sensory event',
                        'nestedTag': 'Event, Sensory event, Event/Sensory event',
                        'nestedTag2': 'event, Sensory event, event/Sensory event'
                        }
        expected_results = {
                            'noTildeGroup': 'Sensory event,'
                                            '(Siren,Sensory event)',
                            'oneTildeGroup': 'Sensory event,'
                                             '(Siren ~ Indoors)',
                            'twoTildeGroup': 'Sensory event,'
                                             '(Awake ~ Age/15 ~ Siren, Vehicle, '
                                             'RGB Red/100)',
                            'singleTag': 'Sensory event',
                            'nestedTag': 'Event, Sensory event, Sensory event',
                            'nestedTag2': 'Event, Sensory event, Sensory event'
                            }

        test_strings = test_strings.values()
        expected_results = expected_results.values()

        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_short, test_strings, expected_results, errors_list)

    def test_string_short_invalid(self):
        test_strings = [
            'InvalidEvent',
            'InvalidEvent/InvalidExtension',
            'InvalidEvent, InvalidEvent/InvalidExtension',
        ]
        expected_results = [
            'InvalidEvent',
            'InvalidEvent/InvalidExtension',
            'InvalidEvent, InvalidEvent/InvalidExtension'
        ]

        errors_list = [
            [error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent', 0, 12),],
            [error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                              'InvalidEvent/InvalidExtension', 0, 12), ],

            [error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                             'InvalidEvent', 0, 12),
            error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                              'InvalidEvent/InvalidExtension', 0, 12), ]
        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_short, test_strings, expected_results, errors_list)

    def test_string_long_invalid(self):
        test_strings = [
            'InvalidEvent',
            'InvalidEvent/InvalidExtension',
            'InvalidEvent, InvalidEvent/InvalidExtension'
        ]
        expected_results = [
            'InvalidEvent',
            'InvalidEvent/InvalidExtension',
            'InvalidEvent, InvalidEvent/InvalidExtension'
        ]

        errors_list = [
            [error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                              'InvalidEvent', 0, 12), ],
            [error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                              'InvalidEvent/InvalidExtension', 0, 12), ],

            [error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                              'InvalidEvent', 0, 12),
             error_reporter.report_error_type(error_reporter.NO_VALID_TAG_FOUND,
                                              'InvalidEvent/InvalidExtension', 0, 12), ]
        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_long, test_strings, expected_results, errors_list)

    def test_string_short_slash_all(self):
        test_strings = [
            '/Event//Extension/',
            '/Item//Sound//Siren/',
            '/Item//Sound//Siren//Extension/'
        ]
        expected_results = [
            'Event/Extension',
            'Siren',
            'Siren/Extension'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_short, test_strings, expected_results, errors_list)

    def test_string_long_slash_all(self):
        test_strings = [
            '/Event//Extension/',
            '/Item//Sound//Siren/',
            '/Item//Sound//Siren//Extension/'
        ]
        expected_results = [
            'Event/Extension',
            'Item/Sound/Siren',
            'Item/Sound/Siren/Extension'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_long, test_strings, expected_results, errors_list)


    def test_string_long_spaces_start_end(self):
        test_strings = [
            ' Environmental sound/Unique Value',
            'Environmental sound/Unique Value ',
        ]
        expected_results = [
            ' Item/Sound/Environmental sound/Unique Value',
            'Item/Sound/Environmental sound/Unique Value '
        ]

        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_long, test_strings, expected_results, errors_list)

    def test_string_short_spaces_start_end(self):
        test_strings = [
            ' Item/Sound/Environmental sound/Unique Value',
            'Item/Sound/Environmental sound/Unique Value '
        ]
        expected_results = [
            ' Environmental sound/Unique Value',
            'Environmental sound/Unique Value ',
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_short, test_strings, expected_results, errors_list)

    def test_string_short_doubleslash(self):
        test_strings = [
            'Event//Extension',
            'Item//Sound/Siren',
            'Item/Sound//Siren/Extension',
            'Item/Sound/Siren//Extension'
        ]
        expected_results = [
            'Event/Extension',
            'Siren',
            'Siren/Extension',
            'Siren/Extension'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_short, test_strings, expected_results, errors_list)

    def test_string_long_doubleslash_spaces(self):
        test_strings = [
            'Event//Extension',
            'Item//Sound/Siren',
            'Item/Sound//Siren/Extension',
            'Item/Sound/Siren//Extension'
            'Event// Extension',
            'Item// Sound/Siren',
            'Item/ Sound// Siren/Extension',
            'Item/Sound/ Siren//Extension',
            'Event/ / Extension',
            'Item//  Sound/ Siren',
            'Item/ Sound/ /Siren/Extension',
            'Item/Sound///Siren//Extension'
        ]
        expected_results = [
            'Event/Extension',
            'Item/Sound/Siren',
            'Item/Sound/Siren/Extension',
            'Item/Sound/Siren/Extension'
            'Event/Extension',
            'Item/Sound/Siren',
            'Item/Sound/Siren/Extension',
            'Item/Sound/Siren/Extension',
            'Event/Extension',
            'Item/Sound/Siren',
            'Item/Sound/Siren/Extension',
            'Item/Sound/Siren/Extension'
        ]
        errors_list = [

        ]
        self.compare_base_new(self.tag_compare.convert_hed_string_to_long, test_strings, expected_results, errors_list)

    def test_split_hed_string(self):
        test_strings = [
            'Event',
            'Event, Event/Extension',
            'Event/Extension, (Event/Extension2, Event/Extension3)',
            'Event/Extension, (Event, ,Event/Extension3)',
            'Event/Extension,(((((Event/Extension2, )(Event)',
            'Event/Extension,(((((Event/Extension2, )(Event) ',
            ' Event/Extension,(((((Event/Extension2, )(Event)',
            ' Event/Extension,(((((Event/Extension2, )(Event ',
        ]
        expected_results = [
            ['Event'],
            ['Event', ', ', 'Event/Extension'],
            ['Event/Extension', ', (', 'Event/Extension2', ', ', 'Event/Extension3', ')'],
            ['Event/Extension', ', (', 'Event', ', ,', 'Event/Extension3', ')'],
            ['Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ')'],
            ['Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ') '],
            [' ', 'Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ')'],
            [' ', 'Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ' '],
        ]

        self.compare_split_results(test_strings, expected_results)

if __name__ == "__main__":
    unittest.main()
