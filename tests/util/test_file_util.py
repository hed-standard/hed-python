import unittest
import os

import hed.util.io_util
from hed.util import file_util


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_test_url = \
            """https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml"""
        cls.hed_xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../schema_test_data/HED8.0.0t.xml')

    def test_url_to_file(self):
        downloaded_file = file_util.url_to_file(self.default_test_url)
        self.assertTrue(downloaded_file)
        os.remove(downloaded_file)

if __name__ == '__main__':
    unittest.main()
