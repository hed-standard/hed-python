from hed.errors import HedFileError
from hed.schema import load_schema_version

import unittest
import os
import itertools
import urllib.error

from hed.schema import hed_cache
from hed import schema
import shutil


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_cache_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../schema_cache_test/')
        cls.saved_cache_folder = hed_cache.HED_CACHE_DIRECTORY
        schema.set_cache_directory(cls.hed_cache_dir)

        cls.default_xml_base_filename = "HED8.0.0t.xml"
        cls.hed_test_version = '7.1.1'
        cls.hed_invalid_version = '4.6.7'

        cls.semantic_version_one = '1.2.3'
        cls.semantic_version_two = '1.2.4'
        cls.semantic_version_three = '1.2.5'
        cls.semantic_version_list = ['1.2.3', '1.2.4', '1.2.5']
        cls.specific_base_url = "https://api.github.com/repos/hed-standard/hed-specification/contents/hedxml"
        try:
            cls.specific_hed_url = \
                """https://raw.githubusercontent.com/hed-standard/hed-specification/master/hedxml/HED8.0.0.xml"""
            hed_cache.cache_xml_versions(cache_folder=cls.hed_cache_dir)
        except urllib.error.HTTPError as e:
            schema.set_cache_directory(cls.saved_cache_folder)
            raise e

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.hed_cache_dir)
        schema.set_cache_directory(cls.saved_cache_folder)

    def test_cache_again(self):
        time_since_update = hed_cache.cache_xml_versions(cache_folder=self.hed_cache_dir)
        self.assertGreater(time_since_update, 0)

    def test_cache_specific_urls(self):
        filename = hed_cache.cache_specific_url(self.specific_base_url)
        self.assertTrue(os.path.exists(filename))

    def test_get_cache_directory(self):
        from hed.schema import get_cache_directory
        cache_dir = get_cache_directory()
        self.assertTrue(cache_dir, "get_cache_directory gives a non-blank element")
        # print(f"\nCache directory is {os.path.realpath(cache_dir)}\n")
        self.assertEqual(cache_dir, self.hed_cache_dir)

    def test_get_hed_version_path(self):
        latest_hed_version_path = hed_cache.get_hed_version_path()
        self.assertIsInstance(latest_hed_version_path, str)

    def test_get_latest_semantic_version_in_list(self):
        latest_version = hed_cache._get_latest_semantic_version_in_list(self.semantic_version_list)
        self.assertIsInstance(latest_version, str)
        self.assertEqual(latest_version, self.semantic_version_three)

    def test_compare_semantic_versions(self):
        latest_version = hed_cache._compare_semantic_versions(self.semantic_version_one, self.semantic_version_two)
        self.assertIsInstance(latest_version, str)
        self.assertEqual(latest_version, self.semantic_version_two)

    def test_set_cache_directory(self):
        hed_cache_dir = "TEST_SCHEMA_CACHE"
        saved_cache_dir = hed_cache.HED_CACHE_DIRECTORY
        hed_cache.set_cache_directory(hed_cache_dir)
        self.assertTrue(hed_cache.HED_CACHE_DIRECTORY == hed_cache_dir)
        hed_cache.set_cache_directory(saved_cache_dir)
        self.assertTrue(hed_cache.HED_CACHE_DIRECTORY == saved_cache_dir)
        os.rmdir(hed_cache_dir)

    def test_cache_specific_url(self):
        local_filename = hed_cache.cache_specific_url(self.specific_hed_url, None, cache_folder=self.hed_cache_dir)
        self.assertTrue(local_filename)

    def test_get_hed_versions_all(self):
        cached_versions = hed_cache.get_hed_versions(self.hed_cache_dir, get_libraries=True)
        self.assertIsInstance(cached_versions, dict)
        self.assertTrue(len(cached_versions) > 1)

    def test_get_hed_versions(self):
        cached_versions = hed_cache.get_hed_versions(self.hed_cache_dir)
        self.assertIsInstance(cached_versions, list)
        self.assertTrue(len(cached_versions) > 0)

    def test_get_hed_versions_library(self):
        cached_versions = hed_cache.get_hed_versions(self.hed_cache_dir, library_name="score")
        self.assertIsInstance(cached_versions, list)
        self.assertTrue(len(cached_versions) > 0)

    def test_sort_version_list(self):
        valid_versions = ["8.1.0", "8.0.0", "8.0.0-alpha.1", "7.1.1", "1.0.0"]
        for shuffled_versions in itertools.permutations(valid_versions):
            sorted_versions = hed_cache._sort_version_list(shuffled_versions)
            self.assertEqual(valid_versions, sorted_versions)

    def test_find_hed_expression(self):
        valid_versions = ["8.1.0", "8.0.0", "8.0.0-alpha.1", "7.1.1", "1.0.0"]
        invalid_versions = ["01.1.1", "0", "0.0.0.0.1.1"]
        for version in valid_versions:
            final_version = f"HED{version}.xml"
            self.assertTrue(hed_cache.version_pattern.match(final_version))
        for version in invalid_versions:
            final_version = f"HED{version}.xml"
            self.assertFalse(hed_cache.version_pattern.match(final_version))

class TestLocal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        hed_cache_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../schema_cache_test_local/')
        if os.path.exists(hed_cache_dir) and os.path.isdir(hed_cache_dir):
            shutil.rmtree(hed_cache_dir)
        cls.hed_cache_dir = hed_cache_dir
        cls.saved_cache_folder = hed_cache.HED_CACHE_DIRECTORY
        schema.set_cache_directory(cls.hed_cache_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.hed_cache_dir)
        schema.set_cache_directory(cls.saved_cache_folder)

    def test_local_cache(self):
        final_hed_xml_file = hed_cache.get_hed_version_path("8.0.0", None, local_hed_directory=self.hed_cache_dir)
        self.assertFalse(final_hed_xml_file)
        hed_cache.cache_local_versions(self.hed_cache_dir)
        final_hed_xml_file = hed_cache.get_hed_version_path("8.0.0", None, local_hed_directory=self.hed_cache_dir)
        self.assertTrue(final_hed_xml_file)

    def test_schema_load_schema_version_invalid(self):
        # This test was moved here from schema io as it will throw errors on github rate limiting like the cache tests.
        with self.assertRaises(HedFileError) as context1:
            load_schema_version("x.0.1")
        self.assertEqual(context1.exception.args[0], 'fileNotFound')

        with self.assertRaises(HedFileError) as context2:
            load_schema_version("base:score_x.0.1")
        self.assertEqual(context2.exception.args[0], 'fileNotFound')

        with self.assertRaises(HedFileError) as context3:
            load_schema_version(["", None])
        self.assertEqual(context3.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context4:
            load_schema_version(["8.0.0", "score_1.0.0"])
        self.assertEqual(context4.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context5:
            load_schema_version(["sc:8.0.0", "sc:score_1.0.0"])
        self.assertEqual(context5.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context6:
            load_schema_version(["", "score_1.0.0"])
        self.assertEqual(context6.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context7:
            load_schema_version(["", "score_"])
        self.assertEqual(context7.exception.args[0], 'schemaDuplicatePrefix')

        with self.assertRaises(HedFileError) as context8:
            load_schema_version(["", "notreallibrary"])
        self.assertEqual(context8.exception.args[0], 'fileNotFound')

if __name__ == '__main__':
    unittest.main()

