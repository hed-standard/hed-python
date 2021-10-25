from hed import HedString
import unittest


class TestHedStrings(unittest.TestCase):
    def validator_scalar(self, test_strings, expected_results, test_function):
        for test_key in test_strings:
            test_result = test_function(test_strings[test_key])
            expected_result = expected_results[test_key]
            self.assertEqual(test_result, expected_result, test_strings[test_key])

    def validator_list(self, test_strings, expected_results, test_function):
        for test_key in test_strings:
            test_result = test_function(test_strings[test_key])
            expected_result = expected_results[test_key]
            self.assertCountEqual(test_result, expected_result, test_strings[test_key])


class TestHedString(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_constructor(self):
        test_strings = {
            'normal': "Tag1,Tag2",
            'normalParen': "(Tag1,Tag2)",
            'normalDoubleParen': "(Tag1,Tag2,(Tag3,Tag4))",
            'extraOpeningParen': "((Tag1,Tag2,(Tag3,Tag4))",
            'extra2OpeningParen': "(((Tag1,Tag2,(Tag3,Tag4))",
            'extraClosingParen': "(Tag1,Tag2,(Tag3,Tag4)))",
            'extra2ClosingParen': "(Tag1,Tag2,(Tag3,Tag4))))"
        }
        expected_result = {
            'normal': True,
            'normalParen': True,
            'normalDoubleParen': True,
            'extraOpeningParen': False,
            'extra2OpeningParen': False,
            'extraClosingParen': False,
            'extra2ClosingParen': False
        }

        # Just make sure it doesn't crash while parsing super invalid strings.
        for name, string in test_strings.items():
            hed_string = HedString(string)

            self.assertEqual(bool(hed_string), expected_result[name])
            if bool(hed_string):
                _ = hed_string.get_all_groups()
                _ = hed_string.get_all_tags()


class HedTagLists(TestHedStrings):
    def test_type(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = HedString.split_hed_string_into_groups(hed_string)
        self.assertIsInstance(result, list)

    def test_top_level_tags(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = HedString.split_hed_string_into_groups(hed_string)
        tags_as_strings = [str(tag) for tag in result]
        self.assertCountEqual(tags_as_strings, ['Event/Category/Experimental stimulus', 'Item/Object/Vehicle/Train',
                                       'Attribute/Visual/Color/Purple'])

    def test_group_tags(self):
        hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
        string_obj = HedString(hed_string)
        # result = HedString.split_hed_string_into_groups(hed_string)
        tags_as_strings = [str(tag) for tag in string_obj.get_direct_children()]
        self.assertCountEqual(tags_as_strings,
                              ['/Action/Reach/To touch',
                               '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)',
                               '/Attribute/Location/Screen/Top/70 px', '/Attribute/Location/Screen/Left/23 px'])

    # Potentially restore some similar behavior later if desired.
    # We no longer automatically remove things like quotes.
    # def test_double_quotes(self):
    #     double_quote_string = 'Event/Category/Experimental stimulus,"Item/Object/Vehicle/Train",' \
    #                           'Attribute/Visual/Color/Purple '
    #     normal_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
    #     double_quote_result = HedString.split_hed_string_into_groups(double_quote_string)
    #     normal_result = HedString.split_hed_string_into_groups(normal_string)
    #     self.assertEqual(double_quote_result, normal_result)

    def test_blanks(self):
        test_strings = {
            'doubleTilde':
                '/Item/Object/Vehicle/Car~~/Attribute/Object control/Perturb',
            'doubleComma':
                '/Item/Object/Vehicle/Car,,/Attribute/Object control/Perturb',
            'doubleInvalidCharacter':
                '/Item/Object/Vehicle/Car[]/Attribute/Object control/Perturb',
            'trailingBlank':
                '/Item/Object/Vehicle/Car,/Attribute/Object control/Perturb,',
        }
        expected_list = [
            '/Item/Object/Vehicle/Car',
            '/Attribute/Object control/Perturb',
        ]
        expected_results = {
            'doubleTilde': [
                '/Item/Object/Vehicle/Car~~/Attribute/Object control/Perturb',
            ],
            'doubleComma': expected_list,
            'doubleInvalidCharacter': ['/Item/Object/Vehicle/Car[]/Attribute/Object control/Perturb'],
            'trailingBlank': expected_list,
        }

        def test_function(string):
            return [str(child) for child in HedString.split_hed_string_into_groups(string)]

        self.validator_list(test_strings, expected_results, test_function)


class ProcessedHedTags(TestHedStrings):
    def test_parsed_tags(self):
        hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
        parsed_string = HedString(hed_string)
        self.assertCountEqual([str(tag) for tag in parsed_string.get_all_tags()], [
            '/Action/Reach/To touch',
            '/Attribute/Object side/Left',
            '/Participant/Effect/Body part/Arm',
            '/Attribute/Location/Screen/Top/70 px',
            '/Attribute/Location/Screen/Left/23 px',
        ])
        self.assertCountEqual([str(group) for group in parsed_string.get_all_groups()],
                              ['/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                               '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
                               '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)'])


class TestHedStringUtil(unittest.TestCase):
    def compare_split_results(self, test_strings, expected_results):
        for test_key in test_strings:
            test_string = test_strings[test_key]
            expected_result = expected_results[test_key]
            actual_results = HedString.split_hed_string(test_string)
            decoded_results = [test_string[start:end] for (is_tag, (start, end)) in actual_results]
            self.assertEqual(decoded_results, expected_result)

    def test_split_hed_string(self):
        test_strings = {
            'single': 'Event',
            'double': 'Event, Event/Extension',
            'singleAndGroup': 'Event/Extension, (Event/Extension2, Event/Extension3)',
            'singleAndGroupWithBlank': 'Event/Extension, (Event, ,Event/Extension3)',
            'manyParens': 'Event/Extension,(((Event/Extension2, )(Event)',
            'manyParensEndingSpace': 'Event/Extension,(((Event/Extension2, )(Event) ',
            'manyParensOpeningSpace': ' Event/Extension,(((Event/Extension2, )(Event)',
            'manyParensBothSpace': ' Event/Extension,(((Event/Extension2, )(Event ',
            'manyClosingParens': 'Event/Extension, (Event/Extension2, ))(Event)',
        }
        expected_results = {
            'single': ['Event'],
            'double': ['Event', ', ', 'Event/Extension'],
            'singleAndGroup': ['Event/Extension', ', ', '(', 'Event/Extension2', ', ', 'Event/Extension3', ')'],
            'singleAndGroupWithBlank': ['Event/Extension', ', ', '(', 'Event', ', ', ',', 'Event/Extension3', ')'],
            'manyParens': ['Event/Extension', ',', '(', '(', '(', 'Event/Extension2', ', ', ')', '(', 'Event', ')'],
            'manyParensEndingSpace':
                ['Event/Extension', ',', '(', '(', '(', 'Event/Extension2', ', ', ')', '(', 'Event', ') '],
            'manyParensOpeningSpace':
                [' ', 'Event/Extension', ',', '(', '(', '(', 'Event/Extension2', ', ', ')', '(', 'Event', ')'],
            'manyParensBothSpace':
                [' ', 'Event/Extension', ',', '(', '(', '(', 'Event/Extension2', ', ', ')', '(', 'Event', ' '],
            'manyClosingParens': ['Event/Extension', ', ', '(', 'Event/Extension2', ', ', ')', ')', '(', 'Event', ')']
        }

        self.compare_split_results(test_strings, expected_results)
