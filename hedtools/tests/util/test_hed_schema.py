import unittest
import os

from hed.util.hed_schema import HedSchema
from hed.util.exceptions import HedFileError


class TestHedSchema(unittest.TestCase):
    schema_file = '../data/HED7.1.1.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = HedSchema(hed_xml)
        cls.hed_schema_dictionaries = cls.hed_schema.dictionaries

    def test_invalid_schema(self):
        # Handle missing or invalid files.
        invalid_xml_file = "invalidxmlfile.xml"
        hed_schema = None
        try:
            hed_schema = HedSchema(invalid_xml_file)
        except HedFileError as e:
            pass

        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = HedSchema(None)
        except HedFileError as e:
            pass
        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = HedSchema("")
        except HedFileError as e:
            pass
        self.assertFalse(hed_schema)

    def test_display_filename(self):
        invalid_xml_file = "invalidxmlfile.xml"
        display_filename = "PrettyDisplayName.xml"
        try:
            hed_schema = HedSchema(invalid_xml_file)
            # We should have an error before we reach here.
            self.assertTrue(False)
        except HedFileError as e:
            self.assertTrue(display_filename in e.format_error_message(return_string_only=True,
                                                                       display_filename=display_filename))

    def test_attribute_keys(self):
        tag_dictionary_keys = ['default', 'extensionAllowed', 'isNumeric', 'position', 'predicateType', 'recommended',
                               'required', 'requireChild', 'tags', 'takesValue', 'unique', 'unitClass']
        for key in tag_dictionary_keys:
            self.assertIn(key, self.hed_schema_dictionaries, key + ' not found.')
            self.assertIsInstance(self.hed_schema_dictionaries[key], dict, key + ' not a dictionary.')

    def test_required_tags(self):
        expected_tags = ['event/category', 'event/description', 'event/label']
        actual_tags_dictionary = self.hed_schema_dictionaries['required']
        self.assertCountEqual(actual_tags_dictionary.keys(), expected_tags)

    def test_positioned_tags(self):
        expected_tags = ['event/category', 'event/description', 'event/label', 'event/long name']
        actual_tags_dictionary = self.hed_schema_dictionaries['position']
        self.assertCountEqual(actual_tags_dictionary.keys(), expected_tags)

    def test_unique_tags(self):
        expected_tags = ['event/description', 'event/label', 'event/long name']
        actual_tags_dictionary = self.hed_schema_dictionaries['unique']
        self.assertCountEqual(actual_tags_dictionary.keys(), expected_tags)

    def test_default_unit_tags(self):
        default_unit_tags = {
            'attribute/blink/time shut/#': 's',
            'attribute/blink/duration/#': 's',
            'attribute/blink/pavr/#': 'centiseconds',
            'attribute/blink/navr/#': 'centiseconds',
        }
        actual_tags_dictionary = self.hed_schema_dictionaries['default']
        self.assertDictEqual(actual_tags_dictionary, default_unit_tags)

    def test_unit_classes(self):
        default_units = {
            'acceleration': 'm-per-s^2',
            'currency': '$',
            'angle': 'radian',
            'frequency': 'Hz',
            'intensity': 'dB',
            'jerk': 'm-per-s^3',
            'luminousIntensity': 'cd',
            'memorySize': 'B',
            'physicalLength': 'm',
            'pixels': 'px',
            'speed': 'm-per-s',
            'time': 's',
            'clockTime': 'hour:min',
            'dateTime': 'YYYY-MM-DDThh:mm:ss',
            'area': 'm^2',
            'volume': 'm^3',
        }
        all_units = {
            'acceleration': ['m-per-s^2'],
            'currency': ['dollar', '$', 'point', 'fraction'],
            'angle': ['radian', 'rad', 'degree'],
            'frequency': ['hertz', 'Hz'],
            'intensity': ['dB'],
            'jerk': ['m-per-s^3'],
            'luminousIntensity': ['candela', 'cd'],
            'memorySize': ['byte', 'B'],
            'physicalLength': ['metre', 'm', 'foot', 'mile'],
            'pixels': ['pixel', 'px'],
            'speed': ['m-per-s', 'mph', 'kph'],
            'time': ['second', 's', 'day', 'minute', 'hour'],
            'clockTime': ['hour:min', 'hour:min:sec'],
            'dateTime': ['YYYY-MM-DDThh:mm:ss'],
            'area': ['m^2', 'px^2', 'pixel^2'],
            'volume': ['m^3'],
        }
        actual_default_units_dictionary = self.hed_schema_dictionaries['defaultUnits']
        actual_all_units_dictionary = self.hed_schema_dictionaries['units']
        self.assertDictEqual(actual_default_units_dictionary, default_units)
        self.assertDictEqual(actual_all_units_dictionary, all_units)

    def test_large_dictionaries(self):
        expected_tag_count = {
            'isNumeric': 80,
            'predicateType': 20,
            'recommended': 0,
            'requireChild': 64,
            'tags': 1116,
            'takesValue': 119,
            'unitClass': 63,
        }
        for key, number in expected_tag_count.items():
            self.assertEqual(len(self.hed_schema_dictionaries[key]), number, 'Mismatch on attribute ' + key)

    def test_tag_attribute(self):
        test_strings = {
            'value':
                'Attribute/Location/Reference frame/Relative to participant/Azimuth/#',
            'valueParent':
                'Attribute/Location/Reference frame/Relative to participant/Azimuth',
            'allowedExtension': 'Item/Object/Road sign',
        }
        expected_results = {
            'value': {
                'default': False,
                'extensionAllowed': False,
                'isNumeric': True,
                'position': False,
                'predicateType': False,
                'recommended': False,
                'required': False,
                'requireChild': False,
                'tags': True,
                'takesValue': True,
                'unique': False,
                'unitClass': True,
            },
            'valueParent': {
                'default': False,
                'extensionAllowed': True,
                'isNumeric': False,
                'position': False,
                'predicateType': False,
                'recommended': False,
                'required': False,
                'requireChild': True,
                'tags': True,
                'takesValue': False,
                'unique': False,
                'unitClass': False,
            },
            'allowedExtension': {
                'default': False,
                'extensionAllowed': True,
                'isNumeric': False,
                'position': False,
                'predicateType': False,
                'recommended': False,
                'required': False,
                'requireChild': False,
                'tags': True,
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

    def test_get_all_descriptions(self):
        descriptions = self.hed_schema.get_all_descriptions()
        self.assertTrue(isinstance(descriptions, dict))
        self.assertTrue(len(descriptions) > 0)

    def test_get_all_terms(self):
        terms = self.hed_schema.get_all_terms()
        self.assertTrue(isinstance(terms, list))
        self.assertTrue(len(terms) > 0)
