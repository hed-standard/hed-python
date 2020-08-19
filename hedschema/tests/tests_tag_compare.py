import unittest
import os
from hed.converter.tag_compare import TagCompare


class Test(unittest.TestCase):
    schema_file = 'data/reduced_no_dupe.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.tag_compare = TagCompare(hed_xml)
        cls.tag_compare.print_tag_dict()

    def compare_base(self, input_tags, output_tags, test_function):
        for input_tag, output_tag in zip(input_tags, output_tags):
            converted_tag = test_function(input_tag)

            self.assertEqual(output_tag, converted_tag)

    def test_basic_strings(self):
        test_strings = [
            'Event',
            'Sensory event',
        ]
        expected_results = [
            'Event',
            'Event/Sensory event',
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_long_tag)

    def test_basic_long_to_short(self):
        test_strings = [
            'Event',
            'Event/Sensory event',
        ]
        expected_results = [
            'Event',
            'Sensory event',
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_takes_value(self):
        test_strings = [
            'Environmental sound/Unique Value'
        ]
        expected_results = [
            'Item/Sound/Environmental sound/Unique Value'
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_long_tag)

    def test_takes_value2(self):
        test_strings = [
            'Item/Sound/Environmental sound/Unique Value'
        ]
        expected_results = [
            'Environmental sound/Unique Value'
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_invalid_takes_value(self):
        # Note these are cases where we produce invalid tags as there is no validation
        # This is expected behavior.
        test_strings = [
            'Item/Sound/Environmental sound/Event',
            'Item/Sound/Environmental sound/Long Unique Value With/Slash Marks'
        ]
        expected_results = [
            'Environmental sound/Event',
            'Environmental sound/Long Unique Value With/Slash Marks'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_short_to_long(self):
        test_strings = [
            'Item/Object/Geometric',
            'Object/Geometric'
        ]
        expected_results = [
            'Item/Object/Geometric',
            'Item/Object/Geometric'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_long_tag)

    def test_long_to_short(self):
        test_strings = [
            'Item/Object/Geometric',
            'Object/Geometric'
        ]
        expected_results = [
            'Geometric',
            'Geometric'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_extension_allowed(self):
        test_strings = [
            'Event/Experiment control/extended lvl1',
        ]
        expected_results = [
            'Experiment control/extended lvl1',
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_extension_allowed_2_levels(self):
        test_strings = [
            'Event/Experiment control/extended lvl1/Extension2',
        ]
        expected_results = [
            'Experiment control/extended lvl1/Extension2',
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_invalid_extension(self):
        # Note these are cases where we produce invalid tags as there is no validation
        # This is expected behavior.
        test_strings = [
            'Event/Experiment control/Geometric',
            'Event/Experiment control/Geometric/Event',
        ]
        expected_results = [
            'Experiment control/Geometric',
            'Experiment control/Geometric/Event'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_extension_allowed_cascade(self):
        """Note we now assume all nodes are extension allowed.
        """
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
        self.compare_base(test_strings, expected_results, self.tag_compare.convert_to_short_tag)

    def test_groups_short_to_long(self):
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
                                         '(Participant/Cognitive state/Awake ~ Participant/Trait/Age/15 ~ Item/Sound/Siren, Item/Object/Manmade/Vehicle,'
                                         ' Attribute/Sensory/Visual/Color/RGB color/RGB Red/100)',
                        'singleTag': 'Event/Sensory event',
                        'nestedTag': 'Event, Event/Sensory event, Event/Sensory event'
                        }

        test_strings = test_strings.values()
        expected_results = expected_results.values()

        self.compare_base(test_strings, expected_results, self.tag_compare.convert_hed_string_to_long)

    def test_groups_long_to_short(self):
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
                                             '(Awake ~ Age/15 ~ Siren, Vehicle,'
                                             ' RGB Red/100)',
                            'singleTag': 'Sensory event',
                            'nestedTag': 'Event, Sensory event, Sensory event',
                            'nestedTag2': 'Event, Sensory event, Sensory event'
                            }

        test_strings = test_strings.values()
        expected_results = expected_results.values()

        self.compare_base(test_strings, expected_results, self.tag_compare.convert_hed_string_to_short)


if __name__ == "__main__":
    unittest.main()
