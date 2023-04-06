from hed.models.hed_tag import HedTag
from tests.validator.test_tag_validator_base import TestHedBase


class TestValidatorUtilityFunctions(TestHedBase):
    schema_file = '../data/schema_tests/HED8.0.0t.xml'

    def test_if_tag_exists(self):
        valid_tag1 = HedTag('Left-handed', hed_schema=self.hed_schema)
        hash1 = hash(valid_tag1)
        hash2 = hash(valid_tag1)
        self.assertEqual(hash1, hash2)
        valid_tag2 = HedTag('Geometric-object', hed_schema=self.hed_schema)
        valid_tag3 = HedTag('duration/#', hed_schema=self.hed_schema)
        invalid_tag1 = HedTag('something', hed_schema=self.hed_schema)
        invalid_tag2 = HedTag('Participant/nothing', hed_schema=self.hed_schema)
        invalid_tag3 = HedTag('participant/#', hed_schema=self.hed_schema)
        valid_tag1_results = valid_tag1.tag_exists_in_schema()
        valid_tag2_results = valid_tag2.tag_exists_in_schema()
        valid_tag3_results = valid_tag3.tag_exists_in_schema()
        invalid_tag1_results = invalid_tag1.tag_exists_in_schema()
        invalid_tag2_results = invalid_tag2.tag_exists_in_schema()
        invalid_tag3_results = invalid_tag3.tag_exists_in_schema()
        # valid_tag1_results = self.semantic_tag_validator.check_tag_exists_in_schema(valid_tag1)
        # valid_tag2_results = self.semantic_tag_validator.check_tag_exists_in_schema(valid_tag2)
        # valid_tag3_results = self.semantic_tag_validator.check_tag_exists_in_schema(valid_tag3)
        # invalid_tag1_results = self.semantic_tag_validator.check_tag_exists_in_schema(invalid_tag1)
        # invalid_tag2_results = self.semantic_tag_validator.check_tag_exists_in_schema(invalid_tag2)
        # invalid_tag3_results = self.semantic_tag_validator.check_tag_exists_in_schema(invalid_tag3)
        self.assertEqual(valid_tag1_results, True)
        self.assertEqual(valid_tag2_results, True)
        self.assertEqual(valid_tag3_results, True)
        self.assertEqual(invalid_tag1_results, False)
        self.assertEqual(invalid_tag2_results, False)
        self.assertEqual(invalid_tag3_results, False)


class TestSchemaUtilityFunctions(TestHedBase):
    schema_file = '../data/schema_tests/HED8.0.0t.xml'

    def test_correctly_determine_tag_takes_value(self):
        value_tag1 = HedTag('Distance/35 px', hed_schema=self.hed_schema)
        value_tag2 = HedTag('id/35', hed_schema=self.hed_schema)
        value_tag3 = HedTag('duration/#', hed_schema=self.hed_schema)
        no_value_tag1 = HedTag('something', hed_schema=self.hed_schema)
        no_value_tag2 = HedTag('attribute/color/black', hed_schema=self.hed_schema)
        no_value_tag3 = HedTag('participant/#', hed_schema=self.hed_schema)
        value_tag1_result = value_tag1.is_takes_value_tag()
        value_tag2_result = value_tag2.is_takes_value_tag()
        value_tag3_result = value_tag3.is_takes_value_tag()
        no_value_tag1_result = no_value_tag1.is_takes_value_tag()
        no_value_tag2_result = no_value_tag2.is_takes_value_tag()
        no_value_tag3_result = no_value_tag3.is_takes_value_tag()
        self.assertEqual(value_tag1_result, True)
        self.assertEqual(value_tag2_result, True)
        self.assertEqual(value_tag3_result, True)
        self.assertEqual(no_value_tag1_result, False)
        self.assertEqual(no_value_tag2_result, False)
        self.assertEqual(no_value_tag3_result, False)

    def test_should_determine_default_unit(self):
        unit_class_tag1 = HedTag('duration/35 ms', hed_schema=self.hed_schema)
        # unit_class_tag2 = HedTag('participant/effect/cognitive/reward/11 dollars',
        #                          schema=self.schema)
        no_unit_class_tag = HedTag('RGB-red/0.5', hed_schema=self.hed_schema)
        no_value_tag = HedTag('Black', hed_schema=self.hed_schema)
        unit_class_tag1_result = unit_class_tag1.get_unit_class_default_unit()
        # unit_class_tag2_result = unit_class_tag2.get_unit_class_default_unit()
        no_unit_class_tag_result = no_unit_class_tag.get_unit_class_default_unit()
        no_value_tag_result = no_value_tag.get_unit_class_default_unit()
        self.assertEqual(unit_class_tag1_result, 's')
        # self.assertEqual(unit_class_tag2_result, '$')
        self.assertEqual(no_unit_class_tag_result, '')
        self.assertEqual(no_value_tag_result, '')

    def test_correctly_determine_tag_unit_classes(self):
        unit_class_tag1 = HedTag('distance/35 px', hed_schema=self.hed_schema)
        # Todo: Make a schema with a currency unit to test this
        # unit_class_tag2 = HedTag('reward/$10.55', schema=self.schema)
        unit_class_tag3 = HedTag('duration/#', hed_schema=self.hed_schema)
        no_unit_class_tag = HedTag('RGB-red/0.5', hed_schema=self.hed_schema)
        unit_class_tag1_result = list(unit_class_tag1.unit_classes.keys())
        # unit_class_tag2_result = list(unit_class_tag2.get_tag_unit_class_units())
        unit_class_tag3_result = list(unit_class_tag3.unit_classes.keys())
        no_unit_class_tag_result = list(no_unit_class_tag.unit_classes.keys())
        self.assertCountEqual(unit_class_tag1_result, ['physicalLengthUnits'])
        # self.assertCountEqual(unit_class_tag2_result, ['currency'])
        self.assertCountEqual(unit_class_tag3_result, ['timeUnits'])
        self.assertEqual(no_unit_class_tag_result, [])

    def test_determine_tags_legal_units(self):
        unit_class_tag1 = HedTag('distance/35 px', hed_schema=self.hed_schema)
        # todo: add this back in when we have a currency unit or make a test for one.
        # unit_class_tag2 = HedTag('reward/$10.55', schema=self.schema)
        no_unit_class_tag = HedTag('RGB-red/0.5', hed_schema=self.hed_schema)
        unit_class_tag1_result = unit_class_tag1.get_tag_unit_class_units()
        # unit_class_tag2_result = unit_class_tag2.get_tag_unit_class_units()
        no_unit_class_tag_result = no_unit_class_tag.get_tag_unit_class_units()
        self.assertCountEqual(unit_class_tag1_result, [
            'inch',
            'm',
            'foot',
            'metre',
            'mile',
        ])
        # self.assertCountEqual(unit_class_tag2_result, [
        #     'dollar',
        #     '$',
        #     'point',
        #     'fraction',
        # ])
        self.assertEqual(no_unit_class_tag_result, [])

    def test_strip_off_units_from_value(self):
        # todo: add this back in when we have a currency unit or make a test for one.
        # dollars_string_no_space = HedTag('Participant/Effect/Cognitive/Reward/$25.99', schema=self.schema)
        # dollars_string = HedTag('Participant/Effect/Cognitive/Reward/$ 25.99', schema=self.schema)
        # dollars_string_invalid = HedTag('Participant/Effect/Cognitive/Reward/25.99$', schema=self.schema)
        volume_string_no_space = HedTag('Volume/100m^3', hed_schema=self.hed_schema)
        volume_string = HedTag('Volume/100 m^3', hed_schema=self.hed_schema)
        prefixed_volume_string = HedTag('Volume/100 cm^3', hed_schema=self.hed_schema)
        invalid_volume_string = HedTag('Volume/200 cm', hed_schema=self.hed_schema)
        # currency_units = {
        #     'currency':self.schema.unit_classes['currency']
        # }
        volume_units = {
            'volume': self.hed_schema.unit_classes['volumeUnits']
        }
        # stripped_dollars_string_no_space = dollars_string_no_space._get_tag_units_portion(currency_units)
        # stripped_dollars_string = dollars_string._get_tag_units_portion(currency_units)
        # stripped_dollars_string_invalid = dollars_string_invalid._get_tag_units_portion(currency_units)
        stripped_volume_string, _ = volume_string._get_tag_units_portion(volume_units)
        stripped_volume_string_no_space, _ = volume_string_no_space._get_tag_units_portion(volume_units)
        stripped_prefixed_volume_string, _ = prefixed_volume_string._get_tag_units_portion(volume_units)
        stripped_invalid_volume_string, _ = invalid_volume_string._get_tag_units_portion(volume_units)
        # self.assertEqual(stripped_dollars_string_no_space, None)
        # self.assertEqual(stripped_dollars_string, '25.99')
        # self.assertEqual(stripped_dollars_string_invalid, None)
        self.assertEqual(stripped_volume_string, '100')
        self.assertEqual(stripped_volume_string_no_space, None)
        self.assertEqual(stripped_prefixed_volume_string, '100')
        self.assertEqual(stripped_invalid_volume_string, None)

    def test_determine_allows_extensions(self):
        extension_tag1 = HedTag('boat', hed_schema=self.hed_schema)
        no_extension_tag1 = HedTag('duration/22 s', hed_schema=self.hed_schema)
        no_extension_tag2 = HedTag('id/45', hed_schema=self.hed_schema)
        no_extension_tag3 = HedTag('RGB-red/0.5', hed_schema=self.hed_schema)
        extension_tag1_result = extension_tag1.is_extension_allowed_tag()
        no_extension_tag1_result = no_extension_tag1.is_extension_allowed_tag()
        no_extension_tag2_result = no_extension_tag2.is_extension_allowed_tag()
        no_extension_tag3_result = no_extension_tag3.is_extension_allowed_tag()
        self.assertEqual(extension_tag1_result, True)
        self.assertEqual(no_extension_tag1_result, False)
        self.assertEqual(no_extension_tag2_result, False)
        self.assertEqual(no_extension_tag3_result, False)