import copy
import unittest
import os

from hed import schema
from hed.schema.hed_schema_constants import HedKey


class TestConverterBase(unittest.TestCase):
    xml_file = '../data/legacy_xml/HED8.0.0-alpha.2.xml'
    wiki_file = '../data/HED8.0.0-alpha.2.mediawiki'
    can_compare = True
    can_legacy = True
    @classmethod
    def setUpClass(cls):
        cls.xml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.xml_file)
        cls.hed_schema_xml = schema.load_schema(cls.xml_file)
        cls.wiki_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.wiki_file)
        cls.hed_schema_wiki = schema.load_schema(cls.wiki_file)
        cls._remove_unknown_attributes(cls.hed_schema_wiki)
        cls._remove_unknown_attributes(cls.hed_schema_xml)

    @staticmethod
    def _remove_unknown_attributes(hed_schema):
        for attribute_name in hed_schema.dictionaries['unknownAttributes']:
            del hed_schema.dictionaries[attribute_name]
        hed_schema.dictionaries['unknownAttributes'] = {}

    @staticmethod
    def _remove_units_descriptions(hed_schema, skip="posixPath"):
        # Remove units descriptions, as that is unsupported in old XML
        desc_dict = hed_schema.dictionaries['descriptions']
        units_removed_dict = {key: value for key, value in desc_dict.items() if
                              not key.startswith(HedKey.UnitClasses + "_") or skip in key}
        units_removed_dict = {key: value for key, value in units_removed_dict.items() if
                              not key.startswith(HedKey.Units + "_") or skip in key}
        hed_schema.dictionaries['descriptions'] = units_removed_dict

    def test_schema2xml(self):
        saved_filename = self.hed_schema_xml.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_xml)

    def test_schema2wiki(self):
        saved_filename = self.hed_schema_xml.save_as_mediawiki()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_xml)

    def test_schema_as_string_xml(self):
        with open(self.xml_file) as file:
            hed_schema_as_string = "".join([line for line in file])

            string_schema = schema.from_string(hed_schema_as_string)
            self._remove_unknown_attributes(string_schema)

            self.assertEqual(string_schema, self.hed_schema_xml)

    def test_schema_as_string_wiki(self):
        with open(self.wiki_file) as file:
            hed_schema_as_string = "".join([line for line in file])

            string_schema = schema.from_string(hed_schema_as_string, file_type=".mediawiki")
            self._remove_unknown_attributes(string_schema)

            self.assertEqual(string_schema, self.hed_schema_wiki)

    def test_wikischema2xml(self):
        saved_filename = self.hed_schema_wiki.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki)

        self.assertEqual(loaded_schema, wiki_schema_copy)

    def test_wikischema2legacyxml(self):
        if self.can_legacy:
            saved_filename = self.hed_schema_wiki.save_as_xml(save_as_legacy_format=True)
            try:
                loaded_schema = schema.load_schema(saved_filename)
            finally:
                os.remove(saved_filename)

            wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki)
            self._remove_units_descriptions(wiki_schema_copy)
            wiki_schema_copy.add_hed2_attributes(only_add_if_none_present=False)
            self._remove_unknown_attributes(loaded_schema)

            self.assertEqual(loaded_schema, wiki_schema_copy)

    def test_wikischema2wiki(self):
        saved_filename = self.hed_schema_wiki.save_as_mediawiki()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_wiki)

    def test_compare_readers(self):
        if self.can_compare:
            identical = self.hed_schema_wiki == self.hed_schema_xml
            if identical:
                self.assertTrue(identical)
                return

            self.assertNotEqual(self.hed_schema_wiki, self.hed_schema_xml)

            hed_schema_3g_wiki_modified = copy.deepcopy(self.hed_schema_wiki)

            if "legacy_xml" in self.xml_file:
                # Modify the wiki version of the dict to match XML now, as legacy XML doesn't match wiki perfectly
                hed_schema_3g_wiki_modified.add_hed2_attributes(only_add_if_none_present=False)
                self._remove_units_descriptions(hed_schema_3g_wiki_modified)

            self.assertEqual(hed_schema_3g_wiki_modified, self.hed_schema_xml)


class TestConverterOld(TestConverterBase):
    xml_file = '../data/legacy_xml/HED7.1.1.xml'
    wiki_file = '../data/HED7.2.0.mediawiki'
    can_compare = False


class TestConverterBeta(TestConverterBase):
    xml_file = '../data/hed_pairs/HED8.0.0-beta.1a.xml'
    wiki_file = '../data/hed_pairs/HED8.0.0-beta.1a.mediawiki'
    can_compare = True


class TestPropertyAdded(TestConverterBase):
    xml_file = '../data/hed_pairs/added_prop.xml'
    wiki_file = '../data/hed_pairs/added_prop.mediawiki'
    can_compare = True
    can_legacy = False

class TestPropertyAddedUsage(TestConverterBase):
    xml_file = '../data/hed_pairs/added_prop_with_usage.xml'
    wiki_file = '../data/hed_pairs/added_prop_with_usage.mediawiki'
    can_compare = True
    can_legacy = False
