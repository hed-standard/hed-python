import unittest
import os

from hed.schema import load_schema, HedSchemaGroup


class TestHedSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema_file = '../data/validator_tests/HED8.0.0_added_tests.mediawiki'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = load_schema(hed_xml)
        hed_schema2 = load_schema(hed_xml, schema_prefix="tl:")
        cls.hed_schema_group = HedSchemaGroup([hed_schema1, hed_schema2])

    def test_schema_compliance(self):
        warnings = self.hed_schema_group.check_compliance(True)
        self.assertEqual(len(warnings), 10)

    def test_get_tag_entry(self):
        tag_entry = self.hed_schema_group.get_tag_entry("Event", schema_prefix="tl:")
        self.assertTrue(tag_entry)

    def test_bad_prefixes(self):
        schema = self.hed_schema_group

        self.assertTrue(schema.get_tag_entry("Event"))
        self.assertFalse(schema.get_tag_entry("sc:Event"))
        self.assertFalse(schema.get_tag_entry("unknown:Event"))
        self.assertFalse(schema.get_tag_entry(":Event"))

        self.assertTrue(schema.get_tag_entry("tl:Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("sc:Event", schema_prefix="tl:"))
        self.assertTrue(schema.get_tag_entry("Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry("unknown:Event", schema_prefix="tl:"))
        self.assertFalse(schema.get_tag_entry(":Event", schema_prefix="tl:"))

        self.assertFalse(schema.get_tag_entry("Event", schema_prefix=None))
        self.assertTrue(schema.get_tag_entry("Event", schema_prefix=""))
