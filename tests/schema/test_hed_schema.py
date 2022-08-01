import unittest
import os

from hed.errors import HedFileError
from hed.models import HedString, HedTag
from hed.schema import HedKey, HedSectionKey, get_hed_xml_version, load_schema, HedSchemaGroup, load_schema_version, HedSchema


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
        hed_schema2 = load_schema(hed_xml, schema_prefix="tl:")
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

    def test_load_schema_version_tags(self):
        schema = load_schema_version(xml_version="st:8.0.0")
        schema2 = load_schema_version(xml_version="8.0.0")
        self.assertNotEqual(schema, schema2)
        schema2.set_schema_prefix("st")
        self.assertEqual(schema, schema2)

        score_lib = load_schema_version(xml_version="score_0.0.1")
        self.assertEqual(score_lib._schema_prefix, "")
        self.assertTrue(score_lib.get_tag_entry("Modulators"))

        score_lib = load_schema_version(xml_version="sc:score_0.0.1")
        self.assertEqual(score_lib._schema_prefix, "sc:")
        self.assertTrue(score_lib.get_tag_entry("Modulators", schema_prefix="sc:"))

    def test_bad_prefixes(self):
        schema = load_schema_version(xml_version="8.0.0")

        self.assertTrue(schema.get_tag_entry("Event"))
        self.assertFalse(schema.get_tag_entry("sc:Event"))
        self.assertFalse(schema.get_tag_entry("unknown:Event"))
        self.assertFalse(schema.get_tag_entry(":Event"))
        self.assertFalse(schema.get_tag_entry("Event", schema_prefix=None))
        self.assertTrue(schema.get_tag_entry("Event", schema_prefix=''))
        self.assertFalse(schema.get_tag_entry("Event", schema_prefix='unknown'))

    def test_bad_prefixes_library(self):
        schema = load_schema_version(xml_version="tl:8.0.0")

        self.assertTrue(schema.get_tag_entry("tl:Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("sc:Event", schema_prefix="tl:"))
        self.assertTrue(schema.get_tag_entry("Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("unknown:Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry(":Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("Event", schema_prefix=None))
        self.assertFalse(schema.get_tag_entry("Event", schema_prefix=''))
        self.assertFalse(schema.get_tag_entry("Event", schema_prefix='unknown'))

    def test_load_schema_version(self):
        ver1 = "8.0.0"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version, "8.0.0", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, None, "load_schema_version standard schema has no library")
        ver2 = "base:8.0.0"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertEqual(schemas2.version, "8.0.0", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas2._schema_prefix, "base:", "load_schema_version has the right version with prefix")
        ver3 = ["base:8.0.0"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertEqual(schemas3.version, "8.0.0", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas3._schema_prefix, "base:", "load_schema_version has the right version with prefix")
        ver3 = ["base:"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertTrue(schemas3.version, "load_schema_version has the right version with prefix")
        self.assertEqual(schemas3._schema_prefix, "base:", "load_schema_version has the right version with prefix")

    def test_load_schema_version_libraries(self):
        ver1 = "score_0.0.1"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertEqual(schemas1.version, "0.0.1", "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no prefix")
        ver1 = "score_"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertTrue(schemas1.version, "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no prefix")
        ver1 = "score"
        schemas1 = load_schema_version(ver1)
        self.assertIsInstance(schemas1, HedSchema, "load_schema_version returns a HedSchema if a string version")
        self.assertTrue(schemas1.version, "load_schema_version has the right version")
        self.assertEqual(schemas1.library, "score", "load_schema_version works with single library no prefix")

        ver2 = "base:score_0.0.1"
        schemas2 = load_schema_version(ver2)
        self.assertIsInstance(schemas2, HedSchema, "load_schema_version returns HedSchema version+prefix")
        self.assertEqual(schemas2.version, "0.0.1", "load_schema_version has the right version with prefix")
        self.assertEqual(schemas2._schema_prefix, "base:", "load_schema_version has the right version with prefix")
        ver3 = ["8.0.0", "sc:score_0.0.1"]
        schemas3 = load_schema_version(ver3)
        self.assertIsInstance(schemas3, HedSchemaGroup, "load_schema_version returns HedSchema version+prefix")
        self.assertIsInstance(schemas3._schemas, dict, "load_schema_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas3._schemas), 2, "load_schema_version group dictionary is right length")
        s = schemas3._schemas[""]
        self.assertEqual(s.version, "8.0.0", "load_schema_version has the right version with prefix")

        ver4 = ["ts:8.0.0", "sc:score_0.0.1"]
        schemas4 = load_schema_version(ver4)
        self.assertIsInstance(schemas4, HedSchemaGroup, "load_schema_version returns HedSchema version+prefix")
        self.assertIsInstance(schemas4._schemas, dict, "load_schema_version group keeps dictionary of hed versions")
        self.assertEqual(len(schemas4._schemas), 2, "load_schema_version group dictionary is right length")
        s = schemas4._schemas["ts:"]
        self.assertEqual(s.version, "8.0.0", "load_schema_version has the right version with prefix")
        with self.assertRaises(KeyError):
            s = schemas4._schemas[""]

    def test_load_schema_version_empty(self):
        schemas = load_schema_version("")
        self.assertIsInstance(schemas, HedSchema, "load_schema_version for empty string returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
        schemas = load_schema_version(None)
        self.assertIsInstance(schemas, HedSchema, "load_schema_version for None returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
        schemas = load_schema_version([""])
        self.assertIsInstance(schemas, HedSchema, "load_schema_version list with blank entry returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")
        schemas = load_schema_version([])
        self.assertIsInstance(schemas, HedSchema, "load_schema_version list with blank entry returns latest version")
        self.assertTrue(schemas.version, "load_schema_version for empty string has a version")
        self.assertFalse(schemas.library, "load_schema_version for empty string is not a library")

    def test_schema_load_schema_version_invalid(self):
        with self.assertRaises(HedFileError):
            load_schema_version("x.0.1")

        with self.assertRaises(HedFileError):
            load_schema_version("base:score_x.0.1")

        with self.assertRaises(HedFileError):
            load_schema_version(["", None])

        with self.assertRaises(HedFileError):
            load_schema_version(["8.0.0", "score_0.0.1"])

        with self.assertRaises(HedFileError):
            load_schema_version(["sc:8.0.0", "sc:score_0.0.1"])

        with self.assertRaises(HedFileError):
            load_schema_version(["", "score_0.0.1"])

        with self.assertRaises(HedFileError):
            load_schema_version(["", "score_"])

        with self.assertRaises(HedFileError):
            load_schema_version(["", "notreallibrary"])