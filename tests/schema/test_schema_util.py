import unittest
import os

from hed.schema.schema_io import schema_util


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


if __name__ == '__main__':
    unittest.main()
