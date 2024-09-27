import unittest
import os

from hed.schema.schema_io import schema_util
from hed.schema import HedSchemaGroup
from hed import load_schema_version
from hed import load_schema


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_test_url = \
            """https://raw.githubusercontent.com/hed-standard/hed-schemas/master/standard_schema/hedxml/HED8.0.0.xml"""
        cls.hed_xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        '../schema_tests/HED8.0.0t.xml')

    def test_url_to_file(self):
        downloaded_file = schema_util.url_to_file(self.default_test_url)
        self.assertTrue(downloaded_file)
        os.remove(downloaded_file)

    def test_schema_version_greater_equal(self):
        schema1 = load_schema_version("8.0.0")
        self.assertFalse(schema_util.schema_version_greater_equal(schema1, "8.3.0"))

        schema2 = load_schema_version("v:8.2.0")
        self.assertFalse(schema_util.schema_version_greater_equal(schema2, "8.3.0"))

        schema_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   '../data/schema_tests/schema_utf8.mediawiki')
        schema3 = load_schema(schema_path, schema_namespace="tl:")
        self.assertTrue(schema_util.schema_version_greater_equal(schema3, "8.3.0"))

        schema_group = HedSchemaGroup([schema1, schema2])
        self.assertFalse(schema_util.schema_version_greater_equal(schema_group, "8.3.0"))

        schema_group = HedSchemaGroup([schema2, schema3])
        self.assertTrue(schema_util.schema_version_greater_equal(schema_group, "8.3.0"))


if __name__ == '__main__':
    unittest.main()
