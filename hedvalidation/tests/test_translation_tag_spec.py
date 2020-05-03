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

    def test_strip_off_units_from_value(self):
        dollars_string = '$25.99'
        volume_string = '100 m3'
        invalid_volume_string = '200 cm'
        currency_units = ['dollars', '$', 'points', 'fraction']
        volume_units = ['m3', 'cm3', 'mm3', 'km3']
        stripped_dollars_string = self.syntactic_tag_validator.\
            _strip_off_units_if_valid(dollars_string, currency_units, True)
        stripped_volume_string = self.syntactic_tag_validator.\
            _strip_off_units_if_valid(volume_string, volume_units, True)
        stripped_invalid_volume_string = self.syntactic_tag_validator.\
            _strip_off_units_if_valid(invalid_volume_string, volume_units, True)
        self.assertEqual(stripped_dollars_string, '25.99')
        self.assertEqual(stripped_volume_string, '100')
        self.assertEqual(invalid_volume_string, '200 cm')

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
        self.assertEqual(valid_tag1_results, False)
        self.assertEqual(valid_tag3_results, False)
        self.assertEqual(valid_tag3_results, False)