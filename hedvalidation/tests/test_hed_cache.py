import random
import unittest
import os

from hed.validator import hed_cache

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hed_cache_test/')
        cls.hed_base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/')
        cls.default_xml_base_filename = "HED.xml"
        cls.default_hed_xml = os.path.join(cls.hed_base_dir, cls.default_xml_base_filename)
        cls.hed_test_version = '4.0.5'
        cls.hed_invalid_version = '4.6.7'

        cls.semantic_version_one = '1.2.3'
        cls.semantic_version_two = '1.2.4'
        cls.semantic_version_three = '1.2.5'
        cls.semantic_version_list = ['1.2.3', '1.2.4', '1.2.5']
        cls.hed_directory_version = '4.0.5'

        cls.specific_hed_url = """https://raw.githubusercontent.com/hed-standard/hed-specification/HED-restructure/hedxml/HED7.1.1.xml"""
        cls.base_api_url = """https://api.github.com/repos/hed-standard/hed-specification/contents/hedxml"""

    def test_get_latest_hed_version_path(self):
        latest_hed_version_path = hed_cache.get_latest_hed_version_path()
        self.assertIsInstance(latest_hed_version_path, str)

    def test_get_latest_semantic_version_in_list(self):
        latest_version = hed_cache._get_latest_semantic_version_in_list(self.semantic_version_list)
        self.assertIsInstance(latest_version, str)
        self.assertEqual(latest_version, self.semantic_version_three)

    def test_compare_semantic_versions(self):
        latest_version = hed_cache._compare_semantic_versions(self.semantic_version_one, self.semantic_version_two)
        self.assertIsInstance(latest_version, str)
        self.assertEqual(latest_version, self.semantic_version_two)

    def test_get_path_from_hed_version(self):
        hed_version_path = hed_cache.get_path_from_hed_version(self.hed_test_version)
        self.assertIsInstance(hed_version_path, str)

    def test_set_cache_directory(self):
        hed_cache_dir = "TEST_HED_CACHE"
        saved_cache_dir = hed_cache.HED_CACHE_DIRECTORY
        hed_cache.set_cache_directory(hed_cache_dir)
        self.assertTrue(hed_cache.HED_CACHE_DIRECTORY == hed_cache_dir)
        hed_cache.set_cache_directory(saved_cache_dir)
        self.assertTrue(hed_cache.HED_CACHE_DIRECTORY == saved_cache_dir)

    def test_get_local_file(self):
        hed_xml_filename = hed_cache.get_local_file(self.hed_base_dir, self.hed_test_version)
        self.assertTrue(hed_xml_filename)
        hed_xml_filename = hed_cache.get_local_file(self.hed_base_dir, self.hed_invalid_version)
        self.assertFalse(hed_xml_filename)
        hed_xml_filename = hed_cache.get_local_file(self.default_hed_xml)
        self.assertTrue(hed_xml_filename)

    def test_cache_specific_url(self):
        local_filename = hed_cache.cache_specific_url(self.specific_hed_url, None, self.hed_cache_dir)
        self.assertTrue(local_filename)

    def test_cache_all_hed_xml_versions(self):
        hed_cache.cache_all_hed_xml_versions(self.base_api_url, self.hed_cache_dir)
        cached_versions = hed_cache.get_all_hed_versions(self.hed_cache_dir)
        self.assertIsInstance(cached_versions, list)
        self.assertTrue(len(cached_versions) > 0)

    def test_get_all_hed_versions(self):
        cached_versions = hed_cache.get_all_hed_versions(self.hed_cache_dir)
        self.assertIsInstance(cached_versions, list)
        self.assertTrue(len(cached_versions) > 0)

if __name__ == '__main__':
    unittest.main()
