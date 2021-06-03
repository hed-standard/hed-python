import copy
import unittest
import os

from hed import schema
from hed.schema.hed_schema_constants import HedKey

class TestHedSchema(unittest.TestCase):
    schema_file = '../data/legacy_xml/HED7.1.1.xml'
    schema_file_3g = '../data/legacy_xml/HED8.0.0-alpha.2.xml'
    schema_wiki_file = '../data/HED7.2.0.mediawiki'
    schema_wiki_file_3g = '../data/HED8.0.0-alpha.2.mediawiki'

    @classmethod
    def setUpClass(cls):
        cls.hed_xml = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file)
        cls.hed_schema = schema.load_schema(cls.hed_xml)
        cls.hed_xml_3g = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_file_3g)
        cls.hed_schema_3g = schema.load_schema(cls.hed_xml_3g)

        # Unknown attributes are not saved, so remove them after loading
        cls._remove_unknown_attributes(cls.hed_schema)
        cls._remove_unknown_attributes(cls.hed_schema_3g)

        cls.hed_wiki = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_wiki_file)
        cls.hed_schema_wiki = schema.load_schema(cls.hed_wiki)
        cls.hed_wiki_3g = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.schema_wiki_file_3g)
        cls.hed_schema_wiki_3g = schema.load_schema(cls.hed_wiki_3g)

        # Unknown attributes are not saved, so remove them after loading
        cls._remove_unknown_attributes(cls.hed_schema_wiki)
        cls._remove_unknown_attributes(cls.hed_schema_wiki_3g)

        with open(cls.hed_xml_3g) as file:
            cls.hed_schema_as_string = "".join([line for line in file])
        with open(cls.hed_wiki_3g) as file:
            cls.hed_wiki_schema_as_string = "".join([line for line in file])

    @staticmethod
    def _remove_units_descriptions(hed_schema, skip="posixPath"):
        # Remove units descriptions, as that is unsupported in old XML
        desc_dict = hed_schema.dictionaries['descriptions']
        units_removed_dict = {key: value for key, value in desc_dict.items() if not key.startswith(HedKey.UnitClasses + "_") or skip in key}
        units_removed_dict = {key: value for key, value in units_removed_dict.items() if
                              not key.startswith(HedKey.Units + "_") or skip in key}
        hed_schema.dictionaries['descriptions'] = units_removed_dict

    @staticmethod
    def _remove_unknown_attributes(hed_schema):
        for attribute_name in hed_schema.dictionaries['unknownAttributes']:
            del hed_schema.dictionaries[attribute_name]
        hed_schema.dictionaries['unknownAttributes'] = {}

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

    def test_schema_as_string(self):
        string_schema = schema.from_string(self.hed_schema_as_string)

        self.assertEqual(string_schema, self.hed_schema_3g)

    def test_schema_as_string_wiki(self):
        string_schema = schema.from_string(self.hed_wiki_schema_as_string, file_type=".mediawiki")

        self.assertEqual(string_schema, self.hed_schema_wiki_3g)

    def test_wikischema2xml(self):
        saved_filename = self.hed_schema_wiki.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki)

        self.assertEqual(loaded_schema, wiki_schema_copy)

        saved_filename = self.hed_schema_wiki_3g.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki_3g)

        self.assertEqual(loaded_schema, wiki_schema_copy)

    def test_wikischema2legacyxml(self):
        saved_filename = self.hed_schema_wiki.save_as_xml(save_as_legacy_format=True)
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki)
        self._remove_units_descriptions(wiki_schema_copy)

        self.assertEqual(loaded_schema, wiki_schema_copy)

        saved_filename = self.hed_schema_wiki_3g.save_as_xml(save_as_legacy_format=True)
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki_3g)
        self._remove_units_descriptions(wiki_schema_copy, skip="posixPath")
        wiki_schema_copy.add_hed2_attributes(only_add_if_none_present=False)

        self.assertEqual(loaded_schema, wiki_schema_copy)

    def test_wikischema2wiki(self):
        saved_filename = self.hed_schema_wiki.save_as_mediawiki()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_wiki)

        saved_filename = self.hed_schema_wiki_3g.save_as_mediawiki()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_wiki_3g)

    def test_legacy_xml_reader(self):
        self.assertNotEqual(self.hed_schema_wiki_3g, self.hed_schema_3g)

        hed_schema_3g_wiki_modified = copy.deepcopy(self.hed_schema_wiki_3g)

        # Modify the wiki version of the dict to match XML now, as legacy XML doesn't match wiki perfectly
        hed_schema_3g_wiki_modified.add_hed2_attributes(only_add_if_none_present=False)
        self._remove_units_descriptions(hed_schema_3g_wiki_modified)

        self.assertEqual(hed_schema_3g_wiki_modified, self.hed_schema_3g)
