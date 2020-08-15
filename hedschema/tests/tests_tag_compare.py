import unittest
import os
from hed.converter.tag_compare import TagCompare


class Test(unittest.TestCase):
    #schema_file = 'data/HED7.1.1.xml'
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

        self.compare_base(test_strings, expected_results, self.tag_compare.short_to_long_tag)

    def test_basic_long_to_short(self):
        test_strings = [
            'Event',
            'Event/Sensory event',
        ]
        expected_results = [
            'Event',
            'Sensory event',
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_takes_value(self):
        test_strings = [
            'Environmental sound/Unique Value'
        ]
        expected_results = [
            'Item/Sound/Environmental sound/Unique Value'
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.short_to_long_tag)

    def test_takes_value2(self):
        test_strings = [
            'Item/Sound/Environmental sound/Unique Value'
        ]
        expected_results = [
            'Environmental sound/Unique Value'
        ]

        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_invalid_takes_value(self):
        test_strings = [
            'Item/Sound/Environmental sound/Event',
            'Item/Sound/Environmental sound/Long Unique Value With/Slash Marks'
        ]
        expected_results = [
            None,
            None
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_short_to_long(self):
        test_strings = [
            'Item/Object/Geometric',
            'Object/Geometric'
        ]
        expected_results = [
            'Item/Object/Geometric',
            'Item/Object/Geometric'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.short_to_long_tag)

    def test_long_to_short(self):
        test_strings = [
            'Item/Object/Geometric',
            'Object/Geometric'
        ]
        expected_results = [
            'Geometric',
            'Geometric'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_extension_allowed(self):
        test_strings = [
            'Event/Experiment control/extended lvl1',
        ]
        expected_results = [
            'Experiment control/extended lvl1',
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_extension_allowed_2_levels(self):
        test_strings = [
            'Event/Experiment control/extended lvl1/Extension2',
        ]
        expected_results = [
            'Experiment control/extended lvl1/Extension2',
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_invalid_extension(self):
        test_strings = [
            'Event/Experiment control/Geometric',
            'Event/Experiment control/Geometric/Event',
        ]
        expected_results = [
            None,
            None
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)

    def test_extension_allowed_cascade(self):
        """Note extension allowed short_to_long behavior does NOT depend on which node(s) are marked extension_allowed,
            the results will be the same regardless.  long_to_short varies.
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
            None,
            'Siren',
            'Trait/NewTraitTest'
        ]
        self.compare_base(test_strings, expected_results, self.tag_compare.long_to_short_tag)



if __name__ == "__main__":
    unittest.main()
