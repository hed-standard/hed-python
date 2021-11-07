import unittest
import os
from hed.util import file_util


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_test_url = \
            """https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml"""
        cls.hed_xml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../hed_pairs/HED8.0.0.xml')

    def test_url_to_file(self):
        downloaded_file = file_util.url_to_file(self.default_test_url)
        self.assertTrue(downloaded_file)
        file_util.delete_file_if_it_exists(downloaded_file)

    def test_delete_file_if_it_exist(self):
        some_file = '3k32j23kj.txt'
        deleted = file_util.delete_file_if_it_exists(some_file)
        self.assertFalse(deleted)

        deleted = file_util.delete_file_if_it_exists(None)
        self.assertFalse(deleted)

        deleted = file_util.delete_file_if_it_exists("")
        self.assertFalse(deleted)

        some_file = "folder_that_does_not_exist/3k32j23kj.txt"
        deleted = file_util.delete_file_if_it_exists(some_file)
        self.assertFalse(deleted)

    def test_get_file_extension(self):
        expected_extension = '.xml'
        file_extension = file_util.get_file_extension(self.hed_xml_file)
        self.assertTrue(file_extension)
        self.assertEqual(expected_extension, file_extension)


if __name__ == '__main__':
    unittest.main()
