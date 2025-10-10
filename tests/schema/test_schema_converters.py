import copy
import unittest
import os

from hed import schema
import tempfile
import functools


def get_temp_filename(extension):
    with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
        filename = temp_file.name
    return filename


# Function wrapper to create and clean up a single schema for testing
def with_temp_file(extension):
    def decorator(test_func):
        @functools.wraps(test_func)
        def wrapper(*args, **kwargs):
            # Create a temporary file with the given extension
            filename = get_temp_filename(extension)
            try:
                # Call the test function with the filename
                return test_func(*args, filename=filename, **kwargs)
            finally:
                # Clean up: Remove the temporary file
                os.remove(filename)
        return wrapper
    return decorator


class TestConverterBase(unittest.TestCase):
    xml_file = '../data/schema_tests/HED8.2.0.xml'
    wiki_file = '../data/schema_tests/HED8.2.0.mediawiki'
    can_compare = True

    @classmethod
    def setUpClass(cls):
        cls.xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.xml_file)
        cls.hed_schema_xml = schema.load_schema(cls.xml_file)
        cls.wiki_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.wiki_file)
        cls.hed_schema_wiki = schema.load_schema(cls.wiki_file)

        # !BFK! - Delete default units as they aren't in the XML file.
        if "HED8.2.0" in cls.wiki_file:
            del cls.hed_schema_wiki.unit_classes["temperatureUnits"].attributes["defaultUnits"]

    @with_temp_file(".xml")
    def test_schema2xml(self, filename):
        self.hed_schema_xml.save_as_xml(filename)
        loaded_schema = schema.load_schema(filename)

        self.assertEqual(loaded_schema, self.hed_schema_xml)

    @with_temp_file(".mediawiki")
    def test_schema2wiki(self, filename):
        self.hed_schema_xml.save_as_mediawiki(filename)
        loaded_schema = schema.load_schema(filename)

        self.assertEqual(loaded_schema, self.hed_schema_xml)

    def test_schema_as_string_xml(self):
        with open(self.xml_file) as file:
            hed_schema_as_string = "".join(list(file))

            string_schema = schema.from_string(hed_schema_as_string)

            self.assertEqual(string_schema, self.hed_schema_xml)

    def test_schema_as_string_wiki(self):
        with open(self.wiki_file) as file:
            hed_schema_as_string = "".join(list(file))

        string_schema = schema.from_string(hed_schema_as_string, schema_format=".mediawiki")
        # !BFK! - Same as before, 8.2.0 has a difference
        if "HED8.2.0" in self.wiki_file:
            del string_schema.unit_classes["temperatureUnits"].attributes["defaultUnits"]

        self.assertEqual(string_schema, self.hed_schema_wiki)

    @with_temp_file(".xml")
    def test_wikischema2xml(self, filename):
        self.hed_schema_wiki.save_as_xml(filename)
        loaded_schema = schema.load_schema(filename)

        wiki_schema_copy = copy.deepcopy(self.hed_schema_wiki)

        self.assertEqual(loaded_schema, wiki_schema_copy)

    @with_temp_file(".mediawiki")
    def test_wikischema2wiki(self, filename):
        self.hed_schema_wiki.save_as_mediawiki(filename)
        loaded_schema = schema.load_schema(filename)

        self.assertEqual(loaded_schema, self.hed_schema_wiki)

    def test_compare_readers(self):
        if self.can_compare:
            self.assertEqual(self.hed_schema_wiki, self.hed_schema_xml)


class TestComplianceBase(unittest.TestCase):
    xml_file_old = '../data/schema_tests/HED8.0.0t.xml'
    xml_file = '../data/schema_tests/HED8.2.0.xml'
    wiki_file = '../data/schema_tests/HED8.2.0.mediawiki'
    can_compare = True
    expected_issues = 0

    @classmethod
    def setUpClass(cls):
        cls.xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.xml_file)
        cls.hed_schema_xml = schema.load_schema(cls.xml_file)
        cls.wiki_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.wiki_file)
        cls.hed_schema_wiki = schema.load_schema(cls.wiki_file)
        if "HED8.2.0" in cls.wiki_file:
            del cls.hed_schema_wiki.unit_classes["temperatureUnits"].attributes["defaultUnits"]
        cls.xml_file_old = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.xml_file_old)
        cls.hed_schema_xml_old = schema.load_schema(cls.xml_file_old)

    def test_compliance(self):
        issues = self.hed_schema_wiki.check_compliance()
        self.assertEqual(len(issues), self.expected_issues)
        issues_old = self.hed_schema_xml_old.check_compliance()
        self.assertGreater(len(issues_old), 0)

    def test_compare_readers(self):
        self.assertNotEqual(self.hed_schema_xml, self.hed_schema_xml_old)
        if self.can_compare:
            self.assertEqual(self.hed_schema_wiki, self.hed_schema_xml)


class TestPropertyAdded(TestConverterBase):
    xml_file = '../data/schema_tests/added_prop.xml'
    wiki_file = '../data/schema_tests/added_prop.mediawiki'
    can_compare = True


class TestPropertyAddedUsage(TestConverterBase):
    xml_file = '../data/schema_tests/added_prop_with_usage.xml'
    wiki_file = '../data/schema_tests/added_prop_with_usage.mediawiki'
    can_compare = True


class TestHedUnknownAttr(TestConverterBase):
    xml_file = '../data/schema_tests/unknown_attribute.xml'
    wiki_file = '../data/schema_tests/unknown_attribute.mediawiki'
    can_compare = True


class TestHedMultiValueClass(TestConverterBase):
    xml_file = '../data/schema_tests/HED8.0.0_2_value_classes.xml'
    wiki_file = '../data/schema_tests/HED8.0.0_2_value_classes.mediawiki'
    can_compare = True


class TestPrologueIssues1(TestConverterBase):
    xml_file = '../data/schema_tests/prologue_tests/test_extra_blank_line_end.xml'
    wiki_file = '../data/schema_tests/prologue_tests/test_extra_blank_line_end.mediawiki'
    can_compare = True


class TestPrologueIssues2(TestConverterBase):
    xml_file = '../data/schema_tests/prologue_tests/test_extra_blank_line_middle.xml'
    wiki_file = '../data/schema_tests/prologue_tests/test_extra_blank_line_middle.mediawiki'
    can_compare = True


class TestPrologueIssues3(TestConverterBase):
    xml_file = '../data/schema_tests/prologue_tests/test_extra_blank_line_start.xml'
    wiki_file = '../data/schema_tests/prologue_tests/test_extra_blank_line_start.mediawiki'
    can_compare = True


class TestPrologueIssues4(TestConverterBase):
    xml_file = '../data/schema_tests/prologue_tests/test_no_blank_line.xml'
    wiki_file = '../data/schema_tests/prologue_tests/test_no_blank_line.mediawiki'
    can_compare = True


class TestDuplicateUnitCompliance(TestComplianceBase):
    xml_file = '../data/schema_tests/duplicate_unit.xml'
    wiki_file = '../data/schema_tests/duplicate_unit.mediawiki'
    can_compare = True
    expected_issues = 1


class TestDuplicateUnitClass(TestComplianceBase):
    xml_file = '../data/schema_tests/duplicate_unit_class.xml'
    wiki_file = '../data/schema_tests/duplicate_unit_class.mediawiki'
    can_compare = True
    expected_issues = 1


class TestConverterSavingPrefix(unittest.TestCase):
    xml_file = '../data/schema_tests/HED8.0.0t.xml'

    @classmethod
    def setUpClass(cls):
        cls.xml_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), cls.xml_file)
        cls.hed_schema_xml = schema.load_schema(cls.xml_file)
        cls.hed_schema_xml_prefix = schema.load_schema(cls.xml_file, schema_namespace="tl:")

    @with_temp_file(".xml")
    def test_saving_prefix(self, filename):
        self.hed_schema_xml_prefix.save_as_xml(filename)
        loaded_schema = schema.load_schema(filename)

        self.assertEqual(loaded_schema, self.hed_schema_xml)
