import copy
import unittest
import os

from hed import schema
from hed.schema.hed_schema_constants import HedSectionKey


class TestConverterBase(unittest.TestCase):
    xml_file = '../data/hed_pairs/HED8.0.0t.xml'
    wiki_file = '../data/hed_pairs/HED8.0.0.mediawiki'
    can_compare = True
    can_legacy = False

    @classmethod
    def setUpClass(cls):
        cls.xml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.xml_file)
        cls.hed_schema_xml = schema.load_schema(cls.xml_file)
        cls.wiki_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.wiki_file)
        cls.hed_schema_wiki = schema.load_schema(cls.wiki_file)

    @staticmethod
    def _remove_units_descriptions(hed_schema, skip="posixPath"):
        for tag_entry in hed_schema[HedSectionKey.Units].values():
            tag_entry.description = None

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

            self.assertEqual(string_schema, self.hed_schema_xml)

    def test_schema_as_string_wiki(self):
        with open(self.wiki_file) as file:
            hed_schema_as_string = "".join([line for line in file])
            with open("/tmp/test_string_saving.mediawiki", "w") as f:
                f.write(hed_schema_as_string)

            string_schema = schema.from_string(hed_schema_as_string, file_type=".mediawiki")

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
    wiki_file = '../data/legacy_xml/HED7.2.0.mediawiki'
    can_compare = False


class TestConverterOld2(TestConverterBase):
    xml_file = '../data/legacy_xml/HED7.1.1.xml'
    wiki_file = '../data/legacy_xml/HED7.3.0.mediawiki'
    can_compare = False


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


class TestHedUnknownAttr(TestConverterBase):
    xml_file = '../data/hed_pairs/unknown_attribute.xml'
    wiki_file = '../data/hed_pairs/unknown_attribute.mediawiki'
    can_compare = True
    can_legacy = False


class TestHedMultiValueClass(TestConverterBase):
    xml_file = '../data/hed_pairs/HED8.0.0_2_value_classes.xml'
    wiki_file = '../data/hed_pairs/HED8.0.0_2_value_classes.mediawiki'
    can_compare = True
    can_legacy = False


class TestPrologue_issues1(TestConverterBase):
    xml_file = '../data/hed_pairs/prologue_tests/test_extra_blank_line_end.xml'
    wiki_file = '../data/hed_pairs/prologue_tests/test_extra_blank_line_end.mediawiki'
    can_compare = True
    can_legacy = False


class TestPrologue_issues2(TestConverterBase):
    xml_file = '../data/hed_pairs/prologue_tests/test_extra_blank_line_middle.xml'
    wiki_file = '../data/hed_pairs/prologue_tests/test_extra_blank_line_middle.mediawiki'
    can_compare = True
    can_legacy = False


class TestPrologue_issues3(TestConverterBase):
    xml_file = '../data/hed_pairs/prologue_tests/test_extra_blank_line_start.xml'
    wiki_file = '../data/hed_pairs/prologue_tests/test_extra_blank_line_start.mediawiki'
    can_compare = True
    can_legacy = False


class TestPrologue_issues4(TestConverterBase):
    xml_file = '../data/hed_pairs/prologue_tests/test_no_blank_line.xml'
    wiki_file = '../data/hed_pairs/prologue_tests/test_no_blank_line.mediawiki'
    can_compare = True
    can_legacy = False


class TestConverterSavingPrefix(unittest.TestCase):
    xml_file = '../data/hed_pairs/HED8.0.0t.xml'

    @classmethod
    def setUpClass(cls):
        cls.xml_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), cls.xml_file)
        cls.hed_schema_xml = schema.load_schema(cls.xml_file)
        cls.hed_schema_xml_prefix = schema.load_schema(cls.xml_file, library_prefix="tl:")

    def test_saving_prefix(self):
        saved_filename = self.hed_schema_xml_prefix.save_as_xml()
        try:
            loaded_schema = schema.load_schema(saved_filename)
        finally:
            os.remove(saved_filename)

        self.assertEqual(loaded_schema, self.hed_schema_xml)
