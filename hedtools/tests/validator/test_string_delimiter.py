from hed.util.hed_string import HedString, HedTag, HedGroup

from tests.validator.test_tag_validator import TestHed


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


class TestHedString(TestHed):
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
            try:
                hed_string = HedString(string)
            except ValueError:
                self.assertEqual(False, expected_result[name])
                continue

            self.assertEqual(True, expected_result[name])
            # Make sure it parses each section
            _ = hed_string.get_all_groups()
            _ = hed_string.get_all_tags()


class HedTagLists(HedStrings):
    def test_type(self):
        hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
        result = HedString.split_hed_string_into_groups(hed_string)
        self.assertIsInstance(result, HedGroup)

    # def test_top_level_tags(self):
    #     hed_string = 'Event/Category/Experimental stimulus,Item/Object/Vehicle/Train,Attribute/Visual/Color/Purple'
    #     result = HedString.split_hed_string_into_groups(hed_string)
    #     tags_as_strings = [str(tag) for tag in result.get_all_tags()]
    #     self.assertCountEqual(tags_as_strings, ['Event/Category/Experimental stimulus', 'Item/Object/Vehicle/Train',
    #                                    'Attribute/Visual/Color/Purple'])

    def test_group_tags(self):
        hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
        result = HedString.split_hed_string_into_groups(hed_string)
        tags_as_strings = [str(tag) for tag in result.get_direct_children()]
        self.assertCountEqual(tags_as_strings, ['/Action/Reach/To touch',
                                       '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)',
                                       '/Attribute/Location/Screen/Top/70 px',
                                       '/Attribute/Location/Screen/Left/23 px'])

    # Update test - verify how double quote should be handled
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


class ProcessedHedTags(HedStrings):
    # Update Test - These are mostly no longer relevant
    # def test_formatted_tags(self):
    #     formatted_hed_tag = 'event/category/experimental stimulus'
    #     test_strings = {
    #         'formatted': 'event/category/experimental stimulus',
    #         'openingDoubleQuote': '"Event/Category/Experimental stimulus',
    #         'closingDoubleQuote': 'Event/Category/Experimental stimulus"',
    #         'openingAndClosingDoubleQuote': '"Event/Category/Experimental stimulus"',
    #         'openingSlash': '/Event/Category/Experimental stimulus',
    #         'closingSlash': 'Event/Category/Experimental stimulus/',
    #         'openingAndClosingSlash': '/Event/Category/Experimental stimulus/',
    #         'openingDoubleQuotedSlash': '"/Event/Category/Experimental stimulus',
    #         'closingDoubleQuotedSlash': 'Event/Category/Experimental stimulus/"',
    #         'openingSlashClosingDoubleQuote':
    #             '/Event/Category/Experimental stimulus"',
    #         'closingSlashOpeningDoubleQuote':
    #             '"Event/Category/Experimental stimulus/',
    #         'openingAndClosingDoubleQuotedSlash':
    #             '"/Event/Category/Experimental stimulus/"',
    #     }
    #     expected_results = {
    #         'formatted': formatted_hed_tag,
    #         'openingDoubleQuote': formatted_hed_tag,
    #         'closingDoubleQuote': formatted_hed_tag,
    #         'openingAndClosingDoubleQuote': formatted_hed_tag,
    #         'openingSlash': formatted_hed_tag,
    #         'closingSlash': formatted_hed_tag,
    #         'openingAndClosingSlash': formatted_hed_tag,
    #         'openingDoubleQuotedSlash': formatted_hed_tag,
    #         'closingDoubleQuotedSlash': formatted_hed_tag,
    #         'openingSlashClosingDoubleQuote': formatted_hed_tag,
    #         'closingSlashOpeningDoubleQuote': formatted_hed_tag,
    #         'openingAndClosingDoubleQuotedSlash': formatted_hed_tag,
    #     }
    #
    #     def test_function(string):
    #         return HedString.format_hed_tag(string)
    #
    #     self.validator_scalar(test_strings, expected_results, test_function)

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
        self.assertCountEqual([str(group) for group in parsed_string.get_all_groups()], [
            '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),'
                     '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px',
            '(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm)',
        ])

    # Update Test - These are mostly no longer relevant
    # def test_parsed_formatted_tags(self):
    #     hed_string = '/Action/Reach/To touch,(/Attribute/Object side/Left,/Participant/Effect/Body part/Arm),' \
    #                  '/Attribute/Location/Screen/Top/70 px,/Attribute/Location/Screen/Left/23 px '
    #     formatted_hed_string = 'action/reach/to touch,(attribute/object side/left,participant/effect/body part/arm),' \
    #                            'attribute/location/screen/top/70 px,attribute/location/screen/left/23 px '
    #     parsed_string = HedString(hed_string)
    #     parsed_formatted_string = HedString(formatted_hed_string)
    #     self.assertCountEqual(
    #         parsed_string.lower_tags(),
    #         parsed_formatted_string.get_tags(),
    #     )
    #     self.assertCountEqual(
    #         parsed_string.lower_tag_group_lists(),
    #         parsed_formatted_string.get_tag_groups_lists(),
    #     )
    #     self.assertCountEqual(
    #         parsed_string.lower_top_level_tags(),
    #         parsed_formatted_string.get_top_level_tags(),
    #     )
