import unittest
import os

from hed.errors import HedFileError
from hed.models import HedString, HedTag
from hed.schema import HedKey, HedSectionKey, get_hed_xml_version, load_schema, HedSchemaGroup, load_schema_version


class TestHedSchema(unittest.TestCase):
    schema_file_3g_xml = '../data/schema_test_data/HED8.0.0t.xml'
    schema_file_3g = '../data/schema_test_data/HED8.0.0.mediawiki'

    @classmethod
    def setUpClass(cls):
        cls.hed_xml_3g = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.schema_file_3g_xml)
        cls.hed_wiki_3g = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.schema_file_3g)
        cls.hed_schema_3g_wiki = load_schema(cls.hed_wiki_3g)
        cls.hed_schema_3g = load_schema(cls.hed_xml_3g)

        schema_file = '../data/validator_tests/HED8.0.0_added_tests.mediawiki'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = load_schema(hed_xml)
        hed_schema2 = load_schema(hed_xml, library_prefix="tl:")
        cls.hed_schema_group = HedSchemaGroup([hed_schema1, hed_schema2])


    def test_invalid_schema(self):
        # Handle missing or invalid files.
        invalid_xml_file = "invalidxmlfile.xml"
        hed_schema = None
        try:
            hed_schema = load_schema(invalid_xml_file)
        except HedFileError:
            pass

        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = load_schema(None)
        except HedFileError:
            pass
        self.assertFalse(hed_schema)

        hed_schema = None
        try:
            hed_schema = load_schema("")
        except HedFileError:
            pass
        self.assertFalse(hed_schema)

    def test_name(self):
        invalid_xml_file = "invalidxmlfile.xml"
        name = "PrettyDisplayName.xml"
        try:
            load_schema(invalid_xml_file)
            # We should have an error before we reach here.
            self.assertTrue(False)
        except HedFileError as e:
            self.assertTrue(name in e.format_error_message(return_string_only=True, name=name))

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

    def test_get_all_tags(self):
        terms = self.hed_schema_3g.get_all_schema_tags(True)
        self.assertTrue(isinstance(terms, list))
        self.assertTrue(len(terms) > 0)

    def test_find_duplicate_tags(self):
        dupe_tags = self.hed_schema_3g.find_duplicate_tags()
        self.assertEqual(len(dupe_tags), 0)

    def test_get_desc_dict(self):
        desc_dict = self.hed_schema_3g.get_desc_iter()
        self.assertEqual(len(list(desc_dict)), 1117)

    def test_get_tag_description(self):
        # Test known tag
        desc = self.hed_schema_3g.get_tag_description("Event/Sensory-event")
        self.assertEqual(desc, "Something perceivable by the participant. An event meant to be an experimental"
                               " stimulus should include the tag Task-property/Task-event-role/Experimental-stimulus.")
        # Test known unit modifier
        desc = self.hed_schema_3g.get_tag_description("deca", HedSectionKey.UnitModifiers)
        self.assertEqual(desc, "SI unit multiple representing 10^1")

        # test unknown tag.
        desc = self.hed_schema_3g.get_tag_description("This/Is/Not/A/Real/Tag")
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

        tag_props = self.hed_schema_3g.get_all_tag_attributes("This/Is/Not/A/Tag")
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
        self.assertEqual(get_hed_xml_version(self.hed_xml_3g), "8.0.0")

    def test_has_duplicate_tags(self):
        self.assertFalse(self.hed_schema_3g.has_duplicate_tags)

    def test_short_tag_mapping(self):
        self.assertEqual(len(self.hed_schema_3g.all_tags.keys()), 1110)

    def test_schema_complicance(self):
        warnings = self.hed_schema_group.check_compliance(True)
        self.assertEqual(len(warnings), 10)

    def test_load_schema_version(self):
        schema = load_schema_version(xml_version="st:8.0.0")
        schema2 = load_schema_version(xml_version="8.0.0")
        self.assertNotEqual(schema, schema2)
        schema2.set_library_prefix("st")
        self.assertEqual(schema, schema2)

        score_lib = load_schema_version(xml_version="score_0.0.1")
        self.assertEqual(score_lib._library_prefix, "")
        self.assertTrue(score_lib.get_tag_entry("Modulators"))

        score_lib = load_schema_version(xml_version="sc:score_0.0.1")
        self.assertEqual(score_lib._library_prefix, "sc:")
        self.assertTrue(score_lib.get_tag_entry("Modulators", library_prefix="sc:"))

    def test_bad_prefixes(self):
        schema = load_schema_version(xml_version="8.0.0")

        self.assertTrue(schema.get_tag_entry("Event"))
        self.assertFalse(schema.get_tag_entry("sc:Event"))
        self.assertFalse(schema.get_tag_entry("unknown:Event"))
        self.assertFalse(schema.get_tag_entry(":Event"))
        self.assertFalse(schema.get_tag_entry("Event", library_prefix=None))
        self.assertTrue(schema.get_tag_entry("Event", library_prefix=''))
        self.assertFalse(schema.get_tag_entry("Event", library_prefix='unknown'))

    def test_bad_prefixes_library(self):
        schema = load_schema_version(xml_version="tl:8.0.0")

        self.assertTrue(schema.get_tag_entry("tl:Event", library_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("sc:Event", library_prefix="tl:"))
        self.assertTrue(schema.get_tag_entry("Event", library_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("unknown:Event", library_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry(":Event", library_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("Event", library_prefix=None))
        self.assertFalse(schema.get_tag_entry("Event", library_prefix=''))
        self.assertFalse(schema.get_tag_entry("Event", library_prefix='unknown'))