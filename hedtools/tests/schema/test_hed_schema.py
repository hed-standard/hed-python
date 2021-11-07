import unittest
import os

from hed import schema, HedFileError, HedString
from hed.schema import HedKey, HedSectionKey, HedTag
from tests.validator.test_tag_validator_2g import TestHed


class TestHedSchema(unittest.TestCase):
    schema_file = '../data/legacy_xml/HED7.1.1.xml'
    schema_file_3g_xml = '../data/hed_pairs/HED8.0.0.xml'
    schema_file_3g = '../data/hed_pairs/HED8.0.0.mediawiki'
    smoke_test_dir = '../data/hed_smoke_test/'

    @classmethod
    def setUpClass(cls):
        cls.hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(cls.hed_xml)
        cls.hed_xml_3g = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file_3g_xml)
        cls.hed_wiki_3g = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file_3g)
        cls.hed_schema_3g = schema.load_schema(cls.hed_wiki_3g)
        cls.smoke_test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.smoke_test_dir)

    def test_invalid_schema(self):
        # Handle missing or invalid files.
        invalid_xml_file = "invalidxmlfile.xml"
        hed_schema = None
        try:
            hed_schema = schema.load_schema(invalid_xml_file)
        except HedFileError:
            pass

        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = schema.load_schema(None)
        except HedFileError:
            pass
        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = schema.load_schema("")
        except HedFileError:
            pass
        self.assertFalse(hed_schema)

    def test_name(self):
        invalid_xml_file = "invalidxmlfile.xml"
        name = "PrettyDisplayName.xml"
        try:
            schema.load_schema(invalid_xml_file)
            # We should have an error before we reach here.
            self.assertTrue(False)
        except HedFileError as e:
            self.assertTrue(name in e.format_error_message(return_string_only=True, name=name))

    def test_tag_attribute(self):
        test_strings = {
            'value': 'Attribute/Location/Reference frame/Relative to participant/Azimuth/#',
            'valueParent': 'Attribute/Location/Reference frame/Relative to participant/Azimuth',
            'allowedExtension': 'Item/Object/Road sign',
        }
        expected_results = {
            'value': {
                'defaultUnits': False,
                'extensionAllowed': False,
                'isNumeric': True,
                'position': False,
                'predicateType': False,
                'recommended': False,
                'required': False,
                'requireChild': False,
                'takesValue': True,
                'unique': False,
                'unitClass': True,
            },
            'valueParent': {
                'defaultUnits': False,
                'extensionAllowed': False,
                'isNumeric': False,
                'position': False,
                'predicateType': False,
                'recommended': False,
                'required': False,
                'requireChild': True,
                'takesValue': False,
                'unique': False,
                'unitClass': False,
            },
            'allowedExtension': {
                'defaultUnits': False,
                'extensionAllowed': False,
                'isNumeric': False,
                'position': False,
                'predicateType': False,
                'recommended': False,
                'required': False,
                'requireChild': False,
                'takesValue': False,
                'unique': False,
                'unitClass': False,
            },
        }
        for key, test_string in test_strings.items():
            expected_dict = expected_results[key]
            for attribute, expected_value in expected_dict.items():
                self.assertEqual(self.hed_schema.tag_has_attribute(test_string, attribute), expected_value,
                                 'Test string: %s. Attribute: %s.' % (test_string, attribute))

    def test_get_all_tags(self):
        terms = self.hed_schema.get_all_schema_tags(True)
        self.assertTrue(isinstance(terms, list))
        self.assertTrue(len(terms) > 0)

    def test_find_duplicate_tags(self):
        dupe_tags = self.hed_schema.find_duplicate_tags()
        self.assertEqual(len(dupe_tags), 81)

        dupe_tags = self.hed_schema_3g.find_duplicate_tags()
        self.assertEqual(len(dupe_tags), 0)

    def test_get_desc_dict(self):
        desc_dict = self.hed_schema.get_desc_iter()
        self.assertEqual(len(list(desc_dict)), 385)

        desc_dict = self.hed_schema_3g.get_desc_iter()
        self.assertEqual(len(list(desc_dict)), 1117)

    def test_get_tag_description(self):
        # Test known tag
        desc = self.hed_schema.get_tag_description("Event/Category")
        self.assertEqual(desc, "This is meant to designate the reason this event was recorded")
        # Test known unit modifier
        desc = self.hed_schema.get_tag_description("deca", HedSectionKey.UnitModifiers)
        self.assertEqual(desc, "SI unit multiple representing 10^1")

        # test unknown tag.
        desc = self.hed_schema.get_tag_description("This/Is/Not/A/Real/Tag")
        self.assertEqual(desc, None)

    def test_get_all_tag_attributes(self):
        test_string = HedString("Jerk-rate/#")
        test_string.convert_to_canonical_forms(self.hed_schema_3g)
        tag_props = self.hed_schema_3g.get_all_tag_attributes(test_string)
        expected_props = {
            "takesValue": "true",
            "valueClass": "numericClass",
            "unitClass": 'jerkUnits'
        }
        self.assertCountEqual(tag_props, expected_props)

        tag_props = self.hed_schema.get_all_tag_attributes("This/Is/Not/A/Tag")
        expected_props = {
        }
        self.assertCountEqual(tag_props, expected_props)

        test_string = HedString("Statistical-value")
        test_string.convert_to_canonical_forms(self.hed_schema_3g)
        tag_props = self.hed_schema_3g.get_all_tag_attributes(test_string)
        expected_props = {
            HedKey.ExtensionAllowed: "true",
        }
        self.assertCountEqual(tag_props, expected_props)
        # also test long form.
        tag_props = self.hed_schema_3g.get_all_tag_attributes("Property/Data-property/Data-value/Statistical-value")
        self.assertCountEqual(tag_props, expected_props)

    def test_get_hed_xml_version(self):
        self.assertEqual(schema.get_hed_xml_version(self.hed_xml), "7.1.1")
        self.assertEqual(schema.get_hed_xml_version(self.hed_xml_3g), "8.0.0")

    def test_has_duplicate_tags(self):
        self.assertTrue(self.hed_schema.has_duplicate_tags)
        self.assertFalse(self.hed_schema_3g.has_duplicate_tags)

    def test_short_tag_mapping(self):
        self.assertEqual(len(self.hed_schema.short_tag_mapping), 993)
        self.assertEqual(len(self.hed_schema_3g.short_tag_mapping), 1110)

    def test_loading_all_schemas(self):
        files = os.listdir(self.smoke_test_dir)
        for file in files:
            _ = schema.load_schema(os.path.join(self.smoke_test_dir, file))

        self.assertTrue(True)

class TestSchemaUtilityFunctions(TestHed):
    def test_correctly_determine_tag_takes_value(self):
        value_tag1 = HedTag('attribute/direction/left/35 px', extension_index=len('attribute/direction/left'))
        value_tag2 = HedTag('item/id/35', extension_index=len('item/id'))
        value_tag3 = HedTag('event/duration/#', extension_index=len('event/duration'))
        no_value_tag1 = HedTag('something', extension_index=len('something'))
        no_value_tag2 = HedTag('attribute/color/black', extension_index=len('attribute/color/black'))
        no_value_tag3 = HedTag('participant/#', extension_index=len('participant'))
        value_tag1_result = self.hed_schema.is_takes_value_tag(value_tag1)
        value_tag2_result = self.hed_schema.is_takes_value_tag(value_tag2)
        value_tag3_result = self.hed_schema.is_takes_value_tag(value_tag3)
        no_value_tag1_result = self.hed_schema.is_takes_value_tag(no_value_tag1)
        no_value_tag2_result = self.hed_schema.is_takes_value_tag(no_value_tag2)
        no_value_tag3_result = self.hed_schema.is_takes_value_tag(no_value_tag3)
        self.assertEqual(value_tag1_result, True)
        self.assertEqual(value_tag2_result, True)
        self.assertEqual(value_tag3_result, True)
        self.assertEqual(no_value_tag1_result, False)
        self.assertEqual(no_value_tag2_result, False)
        self.assertEqual(no_value_tag3_result, False)

    def test_should_determine_default_unit(self):
        unit_class_tag1 = HedTag('attribute/blink/duration/35 ms', extension_index=len('attribute/blink/duration'))
        unit_class_tag2 = HedTag('participant/effect/cognitive/reward/11 dollars',
                                 extension_index=len('participant/effect/cognitive/reward'))
        no_unit_class_tag = HedTag('attribute/color/red/0.5', extension_index=len('attribute/color/red'))
        no_value_tag = HedTag('attribute/color/black', extension_index=len('attribute/color/black'))
        unit_class_tag1_result = self.hed_schema.get_unit_class_default_unit(unit_class_tag1)
        unit_class_tag2_result = self.hed_schema.get_unit_class_default_unit(unit_class_tag2)
        no_unit_class_tag_result = self.hed_schema.get_unit_class_default_unit(no_unit_class_tag)
        no_value_tag_result = self.hed_schema.get_unit_class_default_unit(no_value_tag)
        self.assertEqual(unit_class_tag1_result, 's')
        self.assertEqual(unit_class_tag2_result, '$')
        self.assertEqual(no_unit_class_tag_result, '')
        self.assertEqual(no_value_tag_result, '')

    def test_correctly_determine_tag_unit_classes(self):
        unit_class_tag1 = HedTag('attribute/direction/left/35 px', extension_index=len('attribute/direction/left'))
        unit_class_tag2 = HedTag('participant/effect/cognitive/reward/$10.55',
                                 extension_index=len('participant/effect/cognitive/reward'))
        unit_class_tag3 = HedTag('event/duration/#', extension_index=len('event/duration'))
        no_unit_class_tag = HedTag('attribute/color/red/0.5', extension_index=len('attribute/color/red'))
        unit_class_tag1_result = self.hed_schema.get_tag_unit_classes(unit_class_tag1)
        unit_class_tag2_result = self.hed_schema.get_tag_unit_classes(unit_class_tag2)
        unit_class_tag3_result = self.hed_schema.get_tag_unit_classes(unit_class_tag3)
        no_unit_class_tag_result = self.hed_schema.get_tag_unit_classes(no_unit_class_tag)
        self.assertCountEqual(unit_class_tag1_result, ['angle', 'physicalLength', 'pixels'])
        self.assertCountEqual(unit_class_tag2_result, ['currency'])
        self.assertCountEqual(unit_class_tag3_result, ['time'])
        self.assertEqual(no_unit_class_tag_result, [])

    def test_determine_tags_legal_units(self):
        unit_class_tag1 = HedTag('attribute/direction/left/35 px', extension_index=len('attribute/direction/left'))
        unit_class_tag2 = HedTag('participant/effect/cognitive/reward/$10.55',
                                 extension_index=len('participant/effect/cognitive/reward'))
        no_unit_class_tag = HedTag('attribute/color/red/0.5', extension_index=len('attribute/color/red'))
        unit_class_tag1_result = self.hed_schema.get_tag_unit_class_units(unit_class_tag1)
        unit_class_tag2_result = self.hed_schema.get_tag_unit_class_units(unit_class_tag2)
        no_unit_class_tag_result = self.hed_schema.get_tag_unit_class_units(no_unit_class_tag)
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
        dollars_string_invalid = '25.99$'
        volume_string = '100 m^3'
        prefixed_volume_string = '100 cm^3'
        invalid_volume_string = '200 cm'
        currency_units = ['dollar', '$', 'point', 'fraction']
        volume_units = ['m^3']
        stripped_dollars_string = \
            self.hed_schema._get_tag_units_portion(dollars_string, dollars_string, currency_units)
        stripped_dollars_string_invalid = \
            self.hed_schema._get_tag_units_portion(dollars_string_invalid, dollars_string_invalid, currency_units)
        stripped_volume_string = \
            self.hed_schema._get_tag_units_portion(volume_string, volume_string, volume_units)
        stripped_prefixed_volume_string = \
            self.hed_schema._get_tag_units_portion(prefixed_volume_string, prefixed_volume_string, volume_units)
        stripped_invalid_volume_string = \
            self.hed_schema._get_tag_units_portion(invalid_volume_string, invalid_volume_string, volume_units)
        self.assertEqual(stripped_dollars_string, '25.99')
        self.assertEqual(stripped_dollars_string_invalid, None)
        self.assertEqual(stripped_volume_string, '100')
        self.assertEqual(stripped_prefixed_volume_string, '100')
        self.assertEqual(stripped_invalid_volume_string, None)

    def test_determine_allows_extensions(self):
        extension_tag1 = HedTag('item/object/vehicle/boat', extension_index=len('item/object/vehicle/boat'))
        no_extension_tag1 = HedTag('event/duration/22 s', extension_index=len('event/duration'))
        no_extension_tag2 = HedTag('participant/id/45', extension_index=len('participant/id'))
        no_extension_tag3 = HedTag('attribute/visual/color/red/0.5', extension_index=len('attribute/visual/color/red'))
        extension_tag1_result = self.hed_schema.is_extension_allowed_tag(extension_tag1)
        no_extension_tag1_result = self.hed_schema.is_extension_allowed_tag(no_extension_tag1)
        no_extension_tag2_result = self.hed_schema.is_extension_allowed_tag(no_extension_tag2)
        no_extension_tag3_result = self.hed_schema.is_extension_allowed_tag(no_extension_tag3)
        self.assertEqual(extension_tag1_result, True)
        self.assertEqual(no_extension_tag1_result, False)
        self.assertEqual(no_extension_tag2_result, False)
        self.assertEqual(no_extension_tag3_result, False)
