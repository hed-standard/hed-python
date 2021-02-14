import unittest
import os

from hed import schema


class TestHedSchema(unittest.TestCase):
    schema_file = '../data/HED7.1.1.xml'
    schema_file_3g = '../data/HED8.0.0-alpha.1.xml'

    @classmethod
    def setUpClass(cls):
        cls.hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(cls.hed_xml)
        cls.hed_xml_3g = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file_3g)
        cls.hed_schema_3g = schema.load_schema(cls.hed_xml_3g)

    def test_schema2xml(self):
        saved_filename = self.hed_schema.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema)

        saved_filename = self.hed_schema_3g.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_3g)

    def test_schema2wiki(self):
        saved_filename = self.hed_schema.save_as_mediawiki()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema)

        saved_filename = self.hed_schema_3g.save_as_mediawiki()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_3g)