import unittest
import os

from hed.errors import HedFileError, get_printable_issue_string
from hed.models import HedString, HedTag
from hed.schema import HedKey, HedSectionKey, get_hed_xml_version, load_schema, HedSchemaGroup, load_schema_version, HedSchema


class TestHedSchema(unittest.TestCase):
    schema_file_3g_xml = '../data/schema_tests/HED8.0.0t.xml'
    schema_file_3g = '../data/schema_tests/HED8.2.0.mediawiki'

    @classmethod
    def setUpClass(cls):
        cls.hed_xml_3g = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.schema_file_3g_xml)
        cls.hed_wiki_3g = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.schema_file_3g)
        cls.hed_schema_3g_wiki = load_schema(cls.hed_wiki_3g)
        cls.hed_schema_3g = load_schema(cls.hed_xml_3g)

        schema_file = '../data/validator_tests/HED8.0.0_added_tests.mediawiki'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = load_schema(hed_xml)
        hed_schema2 = load_schema(hed_xml, schema_namespace="tl:")
        cls.hed_schema_group = HedSchemaGroup([hed_schema1, hed_schema2])

    def test_name(self):
        invalid_xml_file = "invalidxmlfile.xml"
        try:
            load_schema(invalid_xml_file)
            # We should have an error before we reach here.
            self.assertTrue(False)
        except HedFileError as e:
            self.assertTrue(invalid_xml_file in e.filename)

    def test_tag_attribute(self):
        test_strings = {
            'value': 'Weight/#',
            'valueParent': 'Label',
            'allowedExtension': 'Experiment-structure',
        }
        expected_results = {
            'value': {
                'defaultUnits': False,
                'extensionAllowed': False,
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
            tag = HedTag(test_string, hed_schema=self.hed_schema_3g)
            for attribute, expected_value in expected_dict.items():
                self.assertEqual(tag.has_attribute(attribute), expected_value,
                                 'Test string: %s. Attribute: %s.' % (test_string, attribute))

    def test_get_all_tag_attributes(self):
        tag_props = self.hed_schema_3g._get_tag_entry("Jerk-rate/#").attributes
        expected_props = {
            "takesValue": "true",
            "valueClass": "numericClass",
            "unitClass": 'jerkUnits'
        }
        self.assertCountEqual(tag_props, expected_props)

        tag_props = self.hed_schema_3g._get_tag_entry("Statistical-value").attributes
        expected_props = {
            HedKey.ExtensionAllowed: "true",
        }
        self.assertCountEqual(tag_props, expected_props)
        # also test long form.
        tag_props = self.hed_schema_3g._get_tag_entry("Property/Data-property/Data-value/Statistical-value").attributes
        self.assertCountEqual(tag_props, expected_props)

    def test_get_hed_xml_version(self):
        self.assertEqual(get_hed_xml_version(self.hed_xml_3g), "8.0.0")

    def test_has_duplicate_tags(self):
        self.assertFalse(self.hed_schema_3g.has_duplicates())

    def test_short_tag_mapping(self):
        self.assertEqual(len(self.hed_schema_3g.tags.keys()), 1110)

    def test_schema_compliance(self):
        warnings = self.hed_schema_group.check_compliance(True)
        self.assertEqual(len(warnings), 18)

    def test_bad_prefixes(self):
        schema = load_schema_version(xml_version="8.3.0")

        self.assertTrue(schema.get_tag_entry("Event"))
        self.assertFalse(schema.get_tag_entry("sc:Event"))
        self.assertFalse(schema.get_tag_entry("unknown:Event"))
        self.assertFalse(schema.get_tag_entry(":Event"))
        self.assertFalse(schema.get_tag_entry("Event", schema_namespace=None))
        self.assertTrue(schema.get_tag_entry("Event", schema_namespace=''))
        self.assertFalse(schema.get_tag_entry("Event", schema_namespace='unknown'))

    def test_bad_prefixes_library(self):
        schema = load_schema_version(xml_version="tl:8.3.0")

        self.assertTrue(schema.get_tag_entry("tl:Event", schema_namespace="tl:"))
        self.assertFalse(schema.get_tag_entry("sc:Event", schema_namespace="tl:"))
        self.assertTrue(schema.get_tag_entry("Event", schema_namespace="tl:"))
        self.assertFalse(schema.get_tag_entry("unknown:Event", schema_namespace="tl:"))
        self.assertFalse(schema.get_tag_entry(":Event", schema_namespace="tl:"))
        self.assertFalse(schema.get_tag_entry("Event", schema_namespace=None))
        self.assertFalse(schema.get_tag_entry("Event", schema_namespace=''))
        self.assertFalse(schema.get_tag_entry("Event", schema_namespace='unknown'))

