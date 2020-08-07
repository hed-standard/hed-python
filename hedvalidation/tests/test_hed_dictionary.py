import unittest
import os

from hed.validator.hed_dictionary import HedDictionary


class TestHedDictionary(unittest.TestCase):
    schema_file = 'data/HED7.1.1.xml'

    @classmethod
    def setUpClass(cls):
        hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_dictionary = HedDictionary(hed_xml)
        cls.hed_dictionary_dictionaries = cls.hed_dictionary.dictionaries

    def test_attribute_keys(self):
        tag_dictionary_keys = ['default', 'extensionAllowed', 'isNumeric', 'position', 'predicateType', 'recommended',
                               'required', 'requireChild', 'tags', 'takesValue', 'unique', 'unitClass']
        for key in tag_dictionary_keys:
            self.assertIn(key, self.hed_dictionary_dictionaries, key + ' not found.')
            self.assertIsInstance(self.hed_dictionary_dictionaries[key], dict, key + ' not a dictionary.')

    def test_required_tags(self):
        expected_tags = ['event/category', 'event/description', 'event/label']
        actual_tags_dictionary = self.hed_dictionary_dictionaries['required']
        self.assertCountEqual(actual_tags_dictionary.keys(), expected_tags)

    def test_positioned_tags(self):
        expected_tags = ['event/category', 'event/description', 'event/label', 'event/long name']
        actual_tags_dictionary = self.hed_dictionary_dictionaries['position']
        self.assertCountEqual(actual_tags_dictionary.keys(), expected_tags)

    def test_unique_tags(self):
        expected_tags = ['event/description', 'event/label', 'event/long name']
        actual_tags_dictionary = self.hed_dictionary_dictionaries['unique']
        self.assertCountEqual(actual_tags_dictionary.keys(), expected_tags)

    def test_default_unit_tags(self):
        default_unit_tags = {
            'attribute/blink/time shut/#': 's',
            'attribute/blink/duration/#': 's',
            'attribute/blink/pavr/#': 'centiseconds',
            'attribute/blink/navr/#': 'centiseconds',
        }
        actual_tags_dictionary = self.hed_dictionary_dictionaries['default']
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
        actual_default_units_dictionary = self.hed_dictionary_dictionaries['defaultUnits']
        actual_all_units_dictionary = self.hed_dictionary_dictionaries['units']
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
            self.assertEqual(len(self.hed_dictionary_dictionaries[key]), number, 'Mismatch on attribute ' + key)

    def test_tag_attribute(self):
        test_strings = {
            'value':
                'Attribute/Location/Reference frame/Relative to participant/Azimuth/#',
            'allowedExtension': 'Item/Object/Road sign',
        }
        expected_results = {
            'value': {
                'default': False,
                'extensionAllowed': True,
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
                self.assertEqual(self.hed_dictionary.tag_has_attribute(test_string, attribute), expected_value,
                                 'Test string: %s. Attribute: %s.' % (test_string, attribute))
