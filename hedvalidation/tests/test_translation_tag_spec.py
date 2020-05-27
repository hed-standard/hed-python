from tests.test_translation_hed import TestHed


class StringUtilityFunctions(TestHed):
    def validator(self, test_strings, expected_results, test_function):
        for key in test_strings:
            test_result = test_function(test_strings[key])
            self.assertEqual(test_result, expected_results[key])

    def test_replace_tag_values_with_pound(self):
        test_strings = {'slash': 'Event/Duration/4 ms',
                        'no_slash': 'something'}
        expected_results = {'slash': 'Event/Duration/#',
                            'no_slash': '#'}
        self.validator(test_strings, expected_results,
                       lambda tag: self.syntactic_tag_validator.replace_tag_name_with_pound(tag))

    def test_detecting_slash_location(self):
        test_strings = {'description': 'Event/Description/Something',
                        'direction': 'Attribute/Direction/Left',
                        'no_slash': 'something'}
        expected_results = {'description': [5, 17],
                            'direction': [9, 19],
                            'no_slash': [], }
        self.validator(test_strings, expected_results,
                       lambda tag: self.syntactic_tag_validator.get_tag_slash_indices(tag))

    def test_extract_last_part_of_tag(self):
        test_strings = {'description': 'Event/Description/Something',
                        'direction': 'Attribute/Direction/Left',
                        'no_slash': 'Participant'}
        expected_results = {'description': 'Something',
                            'direction': 'Left',
                            'no_slash': 'Participant'}
        self.validator(test_strings, expected_results, lambda tag: self.syntactic_tag_validator.get_tag_name(tag))


class TestSchemaUtilityFunctions(TestHed):
    def validator(self, test_strings, expected_results, test_function):
        for key in test_strings:
            test_result = test_function(test_strings[key])
            self.assertEqual(test_result, expected_results[key])

    def validator_list(self, test_strings, expected_results, test_function):
        for key in test_strings:
            test_result = test_function(test_strings[key])
            self.assertCountEqual(test_result, expected_results[key])

    # does not work
    def test_if_tag_exists(self):
        test_strings = {'direction': 'attribute/direction/left',
                        'person': 'item/object/person',
                        'valid_pound': 'event/duration/#',
                        'missing_top_level': 'something',
                        'missing_sub': 'attribute/nothing',
                        'missing_value': 'participant/#'}
        expected_results = {'direction': True,
                            'person': True,
                            'valid_pound': True,
                            'missing_top_level': False,
                            'missing_sub': False,
                            'missing_value': False}
        self.validator(test_strings, expected_results,
                       lambda tag: self.semantic_tag_validator.tag_exists_in_schema(tag))

    def test_correctly_determine_tag_takes_value(self):
        test_string = {'direction': 'attribute/direction/left/35 px',
                       'event_id': 'event/id/35',
                       'valid_pound': 'event/duration/#',
                       'top_level': 'something',
                       'no_value_sub': 'attribute/color/black',
                       'no_value_pound': 'participant/#'}
        expected_results = {'direction': True,
                            'event_id': True,
                            'valid_pound': True,
                            'top_level': False,
                            'no_value_sub': False,
                            'no_value_pound': False}
        self.validator(test_string, expected_results, lambda tag: self.semantic_tag_validator.tag_takes_value(tag))

    # does not work
    def test_should_determine_default_unit(self):
        test_strings = {'suffixed': 'attribute/blink/duration/35 ms',
                        'prefixed': 'participant/effect/cognitive/reward/$10.55',
                        'suffixed_ith_prefix_default': 'participant/effect/cognitive/reward/11 dollars',
                        'unit_class_pound': 'event/duration/#',
                        'no_unit_class_value': 'attribute/color/red/0.5',
                        'no_value': 'attribute/color/black',
                        'no_value_pound': 'participant/#'}
        expected_results = {'suffixed': 's',
                            'prefixed': '$',
                            'suffixed_ith_prefix_default': '$',
                            'unit_class_pound': 's',
                            'no_unit_class_value': '',
                            'no_value': '',
                            'no_value_pound': ''}
        self.validator(test_strings, expected_results,
                       lambda tag: self.semantic_tag_validator.get_unit_class_default_unit(tag))

    # does not work
    def test_correctly_determine_tag_unit_classes(self):
        test_strings = {'suffixed': 'attribute/direction/left/35 px',
                        'prefixed': 'participant/effect/cognitive/reward/$10.55',
                        'suffixed_with_prefix_default': 'participant/effect/cognitive/reward/11 dollars',
                        'unit_class_pound': 'event/duration/#',
                        'no_unit_class_value': 'attribute/color/red/0.5',
                        'no_value': 'attribute/color/black',
                        'no_value_pound': 'participant/#'}
        expected_results = {'suffixed': ['angle', 'physicalLength', 'pixels'],
                            'prefixed': ['currency'],
                            'suffixed_with_prefix_default': ['currency'],
                            'unit_class_pound': ['time'],
                            'no_unit_class_value': [],
                            'no_value': [],
                            'no_value_pound': []}
        self.validator_list(test_strings, expected_results,
                            lambda tag: self.semantic_tag_validator.get_tag_unit_classes(tag))

    # does not work
    def test_determine_tags_legal_units(self):
        test_strings = {'suffixed': 'attribute/direction/left/35 px',
                        'prefixed': 'participant/effect/cognitive/reward/$10.55',
                        'suffixed_with_prefix_default': 'participant/effect/cognitive/reward/11 dollars',
                        'unit_class_pound': 'event/duration/#',
                        'no_unit_class_value': 'attribute/color/red/0.5',
                        'no_value': 'attribute/color/black',
                        'no_value_pound': 'participant/#'}
        direction_units = [
            'degree',
            'radian',
            'rad',
            'm',
            'foot',
            'metre',
            'mile',
            'px',
            'pixel',
        ]
        currency_units = ['dollar', '$', 'point', 'fraction']
        time_units = ['second', 's', 'hour:min', 'day', 'minute', 'hour']
        expected_results = {'suffixed': direction_units,
                            'prefixed': currency_units,
                            'suffixed_with_prefix_default': currency_units,
                            'unit_class_pound': time_units,
                            'no_unit_class_value': [],
                            'no_value': [],
                            'no_value_pound': []}
        self.validator_list(test_strings, expected_results,
                            lambda tag: self.semantic_tag_validator.get_tag_unit_class_units(tag))

    def test_strip_off_units_from_value(self):
        dollars_string = '$25.99'
        volume_string = '100 m^3'
        prefixed_volume_string = '100 cm^3'
        invalid_volume_string = '200 cm'

        currency_units = ['dollars', '$', 'points', 'fraction']
        volume_units = ['m^3']

        stripped_dollars_string = self.semantic_tag_validator. \
            validate_units(dollars_string, dollars_string, currency_units)
        stripped_volume_string = self.semantic_tag_validator. \
            validate_units(volume_string, volume_string, volume_units)
        stripped_prefixed_volume_string = self.semantic_tag_validator. \
            validate_units(prefixed_volume_string, prefixed_volume_string, volume_units)
        stripped_invalid_volume_string = self.semantic_tag_validator. \
            validate_units(invalid_volume_string, invalid_volume_string, volume_units)

        self.assertEqual(stripped_dollars_string, '25.99')
        self.assertEqual(stripped_volume_string, '100')
        self.assertEqual(stripped_prefixed_volume_string, '100')
        self.assertEqual(stripped_invalid_volume_string, '200 cm')


    def test_determine_allows_extensions(self):
        test_strings = {'vehicle': 'item/object/vehicle/boat',
                        'color': 'attribute/color/red/0.5',
                        'no_extension': 'event/nonsense'}
        expected_results = {'vehicle': True,
                            'color': True,
                            'no_extension': False}
        self.validator(test_strings, expected_results,
                       lambda tag: self.semantic_tag_validator.is_extension_allowed_tag(tag))
