import unittest
import os

from hed.schema import load_schema, HedSchemaGroup


class TestHedSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        schema_file = '../data/validator_tests/HED8.0.0_added_tests.mediawiki'
        hed_xml = os.path.join(os.path.dirname(os.path.realpath(__file__)), schema_file)
        hed_schema1 = load_schema(hed_xml)
        hed_schema2 = load_schema(hed_xml, library_prefix="tl:")
        cls.hed_schema_group = HedSchemaGroup([hed_schema1, hed_schema2])

    def test_schema_compliance(self):
        warnings = self.hed_schema_group.check_compliance(True)
        self.assertEqual(len(warnings), 10)

    def test_get_tag_entry(self):
        tag_entry = self.hed_schema_group.get_tag_entry("Event", library_prefix="tl:")
        self.assertTrue(tag_entry)
