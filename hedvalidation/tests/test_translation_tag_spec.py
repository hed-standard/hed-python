import unittest

from tests.test_translation_hed import TestHed


class StringUtilityFunctions(TestHed):
    def test_replace_tag_values_with_pound(self):
        slash_string = 'Event/Duration/4 ms'
        no_slash_string = 'something'
        replaced_slash_string = self.syntactic_tag_validator.replace_tag_name_with_pound(slash_string)
        replaced_no_slash_string = self.syntactic_tag_validator.replace_tag_name_with_pound(no_slash_string)
        self.assertEqual(replaced_slash_string, 'Event/Duration/#')
        self.assertEqual(replaced_no_slash_string, '#')

    def test_detecting_slash_location(self):
        string1 = 'Event/Description/Something'
        string2 = 'Attribute/Direction/Left'
        slash_indices1 = self.syntactic_tag_validator.get_tag_slash_indices(string1)
        slash_indices2 = self.syntactic_tag_validator.get_tag_slash_indices(string2)
        self.assertEqual(slash_indices1, [5, 17])
        self.assertEqual(slash_indices2, [9, 19])

    def test_extract_last_part_of_tag(self):
        string1 = 'Event/Description/Something'
        string2 = 'Attribute/Direction/Left'
        no_slash_string = 'Participant'
        name1 = self.syntactic_tag_validator.get_tag_name(string1)
        name2 = self.syntactic_tag_validator.get_tag_name(string2)
        no_slash_name = self.syntactic_tag_validator.get_tag_name(no_slash_string)
        self.assertEqual(name1, 'Something')
        self.assertEqual(name2, 'Left')
        self.assertEqual(no_slash_name, 'Participant')


class TestSchemaUtilityFunctions(TestHed):
    def test_if_tag_exists(self):
        valid_tag1 = 'attribute/direction/left'
        valid_tag2 = 'item/object/person'
        valid_tag3 = 'event/duration/#'
        invalid_tag1 = 'something'
        invalid_tag2 = 'attribute/nothing'
        invalid_tag3 = 'participant/#'
        valid_tag1_results = self.semantic_tag_validator.tag_exists_in_schema(valid_tag1)
        valid_tag2_results = self.semantic_tag_validator.tag_exists_in_schema(valid_tag2)
        valid_tag3_results = self.semantic_tag_validator.tag_exists_in_schema(valid_tag3)
        invalid_tag1_results = self.semantic_tag_validator.tag_exists_in_schema(invalid_tag1)
        invalid_tag2_results = self.semantic_tag_validator.tag_exists_in_schema(invalid_tag2)
        invalid_tag3_results = self.semantic_tag_validator.tag_exists_in_schema(invalid_tag3)
        self.assertEqual(valid_tag1_results, True)
        self.assertEqual(valid_tag2_results, True)
        self.assertEqual(valid_tag3_results, True)
        self.assertEqual(invalid_tag1_results, False)
        self.assertEqual(invalid_tag2_results, False)
        self.assertEqual(invalid_tag3_results, False)

    def test_correctly_determine_tag_takes_value(self):
        value_tag1 = 'attribute/direction/left/35 px'
        value_tag2 = 'item/id/35'
        value_tag3 = 'event/duration/#'
        no_value_tag1 = 'something'
        no_value_tag2 = 'attribute/color/black'
        no_value_tag3 = 'participant/#'
        value_tag1_result = self.semantic_tag_validator.tag_takes_value(value_tag1)
        value_tag2_result = self.semantic_tag_validator.tag_takes_value(value_tag2)
        value_tag3_result = self.semantic_tag_validator.tag_takes_value(value_tag3)
        no_value_tag1_result = self.semantic_tag_validator.tag_takes_value(no_value_tag1)
        no_value_tag2_result = self.semantic_tag_validator.tag_takes_value(no_value_tag2)
        no_value_tag3_result = self.semantic_tag_validator.tag_takes_value(no_value_tag3)
        self.assertEqual(value_tag1_result, True)
        self.assertEqual(value_tag2_result, True)
        self.assertEqual(value_tag3_result, True)
        self.assertEqual(no_value_tag1_result, False)
        self.assertEqual(no_value_tag2_result, False)
        self.assertEqual(no_value_tag3_result, False)

    def test_should_determine_default_unit(self):
        unit_class_tag1 = 'attribute/blink/duration/35 ms'
        unit_class_tag2 = 'participant/effect/cognitive/reward/11 dollars'
        no_unit_class_tag = 'attribute/color/red/0.5'
        no_value_tag = 'attribute/color/black'
        unit_class_tag1_result = self.semantic_tag_validator.get_unit_class_default_unit(unit_class_tag1)
        unit_class_tag2_result = self.semantic_tag_validator.get_unit_class_default_unit(unit_class_tag2)
        no_unit_class_tag_result = self.semantic_tag_validator.get_unit_class_default_unit(no_unit_class_tag)
        no_value_tag_result = self.semantic_tag_validator.get_unit_class_default_unit(no_value_tag)
        self.assertEqual(unit_class_tag1_result, 's')
        self.assertEqual(unit_class_tag2_result, '$')
        self.assertEqual(no_unit_class_tag_result, '')
        self.assertEqual(no_value_tag_result, '')

    def test_correctly_determine_tag_unit_classes(self):
        unit_class_tag1 = 'attribute/direction/left/35 px'
        unit_class_tag2 = 'participant/effect/cognitive/reward/$10.55'
        unit_class_tag3 = 'event/duration/#'
        no_unit_class_tag = 'attribute/color/red/0.5'
        unit_class_tag1_result = self.semantic_tag_validator.get_tag_unit_classes(unit_class_tag1)
        unit_class_tag2_result = self.semantic_tag_validator.get_tag_unit_classes(unit_class_tag2)
        unit_class_tag3_result = self.semantic_tag_validator.get_tag_unit_classes(unit_class_tag3)
        no_unit_class_tag_result = self.semantic_tag_validator.get_tag_unit_classes(no_unit_class_tag)
        self.assertCountEqual(unit_class_tag1_result, ['angle', 'physicalLength', 'pixels'])
        self.assertCountEqual(unit_class_tag2_result, ['currency'])
        self.assertCountEqual(unit_class_tag3_result, ['time'])
        self.assertEqual(no_unit_class_tag_result, [])

    def test_determine_tags_legal_units(self):
        unit_class_tag1 = 'attribute/direction/left/35 px'
        unit_class_tag2 = 'participant/effect/cognitive/reward/$10.55'
        no_unit_class_tag = 'attribute/color/red/0.5'
        unit_class_tag1_result = self.semantic_tag_validator.get_tag_unit_class_units(unit_class_tag1)
        unit_class_tag2_result = self.semantic_tag_validator.get_tag_unit_class_units(unit_class_tag2)
        no_unit_class_tag_result = self.semantic_tag_validator.get_tag_unit_class_units(no_unit_class_tag)
        self.assertCountEqual(unit_class_tag1_result, [
            'degree',
            'radian',
            'rad',
            'm',
            'foot',
            'metre',
            'mile',
            'px',
            'pixel',
        ])
        self.assertCountEqual(unit_class_tag2_result, [
            'dollar',
            '$',
            'point',
            'fraction',
        ])
        self.assertEqual(no_unit_class_tag_result, [])

    def test_strip_off_units_from_value(self):
        dollars_string = '$25.99'
        volume_string = '100 m^3'
        prefixed_volume_string = '100 cm^3'
        invalid_volume_string = '200 cm'
        currency_units = ['dollar', '$', 'point', 'fraction']
        volume_units = ['m^3']
        stripped_dollars_string = self.semantic_tag_validator. \
            validate_units(dollars_string, dollars_string, currency_units)
        stripped_volume_string = self.semantic_tag_validator. \
            validate_units(volume_string, volume_string, volume_units)
        stripped_prefixed_volume_string = self.semantic_tag_validator. \
            validate_units(prefixed_volume_string, prefixed_volume_string, volume_units)
        # stripped_invalid_volume_string = self.semantic_tag_validator. \
        #    validate_units(invalid_volume_string, invalid_volume_string, volume_units)
        self.assertEqual(stripped_dollars_string, '25.99')
        self.assertEqual(stripped_volume_string, '100')
        self.assertEqual(stripped_prefixed_volume_string, '100')
        self.assertEqual(invalid_volume_string, '200 cm')

    def test_determine_allows_extensions(self):
        extension_tag1 = 'item/object/vehicle/boat'
        extension_tag2 = 'attribute/color/red/0.5'
        no_extension_tag1 = 'event/duration/22 s'
        no_extension_tag2 = 'participant/id/45'
        extension_tag1_result = self.semantic_tag_validator.is_extension_allowed_tag(extension_tag1)
        extension_tag2_result = self.semantic_tag_validator.is_extension_allowed_tag(extension_tag2)
        no_extension_tag1_result = self.semantic_tag_validator.is_extension_allowed_tag(no_extension_tag1)
        no_extension_tag2_result = self.semantic_tag_validator.is_extension_allowed_tag(no_extension_tag2)
        self.assertEqual(extension_tag1_result, True)
        self.assertEqual(extension_tag2_result, True)
        self.assertEqual(no_extension_tag1_result, False)
        self.assertEqual(no_extension_tag2_result, False)


if __name__ == '__main__':
    unittest.main()