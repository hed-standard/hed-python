import unittest

from hed.util import hed_string_util


class TestHedStringUtil(unittest.TestCase):
    def compare_split_results(self, test_strings, expected_results):
        for test_key in test_strings:
            test_string = test_strings[test_key]
            expected_result = expected_results[test_key]
            actual_results = hed_string_util.split_hed_string(test_string)
            decoded_results = [test_string[start:end] for (is_tag, (start, end)) in actual_results]
            self.assertEqual(decoded_results, expected_result)

    def test_split_hed_string(self):
        test_strings = {
            'single': 'Event',
            'double': 'Event, Event/Extension',
            'singleAndGroup': 'Event/Extension, (Event/Extension2, Event/Extension3)',
            'singleAndGroupWithBlank': 'Event/Extension, (Event, ,Event/Extension3)',
            'manyParens': 'Event/Extension,(((((Event/Extension2, )(Event)',
            'manyParensEndingSpace': 'Event/Extension,(((((Event/Extension2, )(Event) ',
            'manyParensOpeningSpace': ' Event/Extension,(((((Event/Extension2, )(Event)',
            'manyParensBothSpace': ' Event/Extension,(((((Event/Extension2, )(Event ',
        }
        expected_results = {
            'single': ['Event'],
            'double': ['Event', ', ', 'Event/Extension'],
            'singleAndGroup': ['Event/Extension', ', (', 'Event/Extension2', ', ', 'Event/Extension3', ')'],
            'singleAndGroupWithBlank': ['Event/Extension', ', (', 'Event', ', ,', 'Event/Extension3', ')'],
            'manyParens': ['Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ')'],
            'manyParensEndingSpace': ['Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ') '],
            'manyParensOpeningSpace': [' ', 'Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ')'],
            'manyParensBothSpace': [' ', 'Event/Extension', ',(((((', 'Event/Extension2', ', )(', 'Event', ' '],
        }

        self.compare_split_results(test_strings, expected_results)


if __name__ == '__main__':
    unittest.main()
