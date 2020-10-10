from hed.validator.hed_string_delimiter import HedStringDelimiter
from tests.test_tag_validator import TestHed


class HedStrings(TestHed):
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


class HedTagGroups(HedStrings):
    def test_surround_parentheses(self):
        test_strings = {
            'group': '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)',
            'nonGroup': '/Attribute/Object side/Left,/Participant/Effect/Body part/Arm',
        }
        expected_results = {
            'group': True,
            'nonGroup': False,
        }

        def test_function(string):
            return HedStringDelimiter.hed_string_is_a_group(string)

        self.validator_scalar(test_strings, expected_results, test_function)

    def test_remove_parentheses(self):
        group_string = '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)'
        formatted_string = '/Attribute/Object side/Left,/Participant/Effect/Body part/Arm'
        result = HedStringDelimiter.remove_group_parentheses(group_string)
        self.assertEqual(result, formatted_string, 'Remove parentheses from group string.')


class HedTagLists(HedStrings):
    def test_type(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = HedStringDelimiter.split_hed_string_into_list(hed_string)
        self.assertIsInstance(result, list)

    def test_top_level_tags(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = HedStringDelimiter.split_hed_string_into_list(hed_string)
        self.assertCountEqual(result, ['Event/Category/Experimental stimulus', 'Item/Object/Vehicle/Train',
                                       'Attribute/Visual/Color/Purple'])

    def test_group_tags(self):
        hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
        result = HedStringDelimiter.split_hed_string_into_list(hed_string)
        self.assertCountEqual(result, ['/Action/Reach/To touch',
                                       '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)',
                                       '/Attribute/Location/Screen/Top/70 px',
                                       '/Attribute/Location/Screen/Left/23 px'])

    def test_tildes(self):
        hed_string = '/Item/Object/Vehicle/Car ~ /Attribute/Object control/Perturb'
        result = HedStringDelimiter.split_hed_string_into_list(hed_string)
        self.assertCountEqual(result, ['/Item/Object/Vehicle/Car', '~', '/Attribute/Object control/Perturb'])

    def test_double_quotes(self):
        double_quote_string = 'Event/Category/Experimental stimulus,"Item/Object/Vehicle/Train",' \
                              'Attribute/Visual/Color/Purple '
        normal_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        double_quote_result = HedStringDelimiter.split_hed_string_into_list(double_quote_string)
        normal_result = HedStringDelimiter.split_hed_string_into_list(normal_string)
        self.assertEqual(double_quote_result, normal_result)

    def test_blanks(self):
        test_strings = {
            'doubleTilde':
                '/Item/Object/Vehicle/Car~~/Attribute/Object control/Perturb',
            'doubleComma':
                '/Item/Object/Vehicle/Car,,/Attribute/Object control/Perturb',
            # !FIXME! Are square brackets invalid characters, and if so, how should we detect them?
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
                '/Item/Object/Vehicle/Car',
                '~',
                '~',
                '/Attribute/Object control/Perturb',
            ],
            'doubleComma': expected_list,
            'doubleInvalidCharacter': expected_list,
            'trailingBlank': expected_list,
        }

        def test_function(string):
            return HedStringDelimiter.split_hed_string_into_list(string)

        self.validator_list(test_strings, expected_results, test_function)


class ProcessedHedTags(HedStrings):
    def test_formatted_tags(self):
        formatted_hed_tag = 'event/category/experimental stimulus'
        test_strings = {
            'formatted': 'event/category/experimental stimulus',
            'openingDoubleQuote': '"Event/Category/Experimental stimulus',
            'closingDoubleQuote': 'Event/Category/Experimental stimulus"',
            'openingAndClosingDoubleQuote': '"Event/Category/Experimental stimulus"',
            'openingSlash': '/Event/Category/Experimental stimulus',
            'closingSlash': 'Event/Category/Experimental stimulus/',
            'openingAndClosingSlash': '/Event/Category/Experimental stimulus/',
            'openingDoubleQuotedSlash': '"/Event/Category/Experimental stimulus',
            'closingDoubleQuotedSlash': 'Event/Category/Experimental stimulus/"',
            'openingSlashClosingDoubleQuote':
                '/Event/Category/Experimental stimulus"',
            'closingSlashOpeningDoubleQuote':
                '"Event/Category/Experimental stimulus/',
            'openingAndClosingDoubleQuotedSlash':
                '"/Event/Category/Experimental stimulus/"',
        }
        expected_results = {
            'formatted': formatted_hed_tag,
            'openingDoubleQuote': formatted_hed_tag,
            'closingDoubleQuote': formatted_hed_tag,
            'openingAndClosingDoubleQuote': formatted_hed_tag,
            'openingSlash': formatted_hed_tag,
            'closingSlash': formatted_hed_tag,
            'openingAndClosingSlash': formatted_hed_tag,
            'openingDoubleQuotedSlash': formatted_hed_tag,
            'closingDoubleQuotedSlash': formatted_hed_tag,
            'openingSlashClosingDoubleQuote': formatted_hed_tag,
            'closingSlashOpeningDoubleQuote': formatted_hed_tag,
            'openingAndClosingDoubleQuotedSlash': formatted_hed_tag,
        }

        def test_function(string):
            return HedStringDelimiter.format_hed_tag(string)

        self.validator_scalar(test_strings, expected_results, test_function)

    def test_parsed_tags(self):
        hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
        parsed_string = HedStringDelimiter(hed_string)
        self.assertCountEqual(parsed_string.get_tags(), [
            '/Action/Reach/To touch',
            '/Attribute/Object side/Left',
            '/Participant/Effect/Body part/Arm',
            '/Attribute/Location/Screen/Top/70 px',
            '/Attribute/Location/Screen/Left/23 px',
        ])
        self.assertCountEqual(parsed_string.get_top_level_tags(), [
            '/Action/Reach/To touch',
            '/Attribute/Location/Screen/Top/70 px',
            '/Attribute/Location/Screen/Left/23 px',
        ])
        self.assertCountEqual(parsed_string.get_tag_groups(), [
            ['/Attribute/Object side/Left', '/Participant/Effect/Body part/Arm'],
        ])

    def test_parsed_formatted_tags(self):
        hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
        formatted_hed_string = 'action/reach/to touch,(attribute/object side/left,participant/effect/body part/arm),' \
                               'attribute/location/screen/top/70 px,attribute/location/screen/left/23 px '
        parsed_string = HedStringDelimiter(hed_string)
        parsed_formatted_string = HedStringDelimiter(formatted_hed_string)
        self.assertCountEqual(
            parsed_string.get_formatted_tags(),
            parsed_formatted_string.get_tags(),
        )
        self.assertCountEqual(
            parsed_string.get_formatted_tag_groups(),
            parsed_formatted_string.get_tag_groups(),
        )
        self.assertCountEqual(
            parsed_string.get_formatted_top_level_tags(),
            parsed_formatted_string.get_top_level_tags(),
        )
