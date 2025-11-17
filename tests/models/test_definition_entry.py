import unittest
import os
from hed.schema import load_schema_version
from hed.models.definition_entry import DefinitionEntry
from hed.models.hed_string import HedString


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/")
        hed_schema = load_schema_version("8.4.0")
        cls.contents1 = HedString("(Sensory-event)", hed_schema)
        cls.contents2 = HedString("(Agent-action)", hed_schema)
        cls.contents3 = HedString("(Sensory-event)", hed_schema)
        cls.hed_schema = hed_schema

    def test_definition_entry_init(self):
        """Test basic initialization of DefinitionEntry."""
        name = "TestDef"
        takes_value = True
        source_context = [{"line": 1}]

        entry = DefinitionEntry(name, self.contents1, True, source_context)
        self.assertEqual(entry.name, name.casefold())
        self.assertIsNotNone(entry.contents)
        self.assertEqual(entry.takes_value, takes_value)
        self.assertEqual(entry.source_context, source_context)
        self.assertEqual(str(entry), str(self.contents1))

    def test_none_contents(self):
        """Test with None contents."""
        entry = DefinitionEntry("TestDef", None, False, None)
        self.assertIsNone(entry.contents)
        self.assertFalse(entry.takes_value)
        self.assertEqual(str(entry), "None")

    def test_eq_method(self):
        """Test __eq__ method"""
        name = "TestDef"
        takes_value = True
        source_context1 = [{"line": 1}]
        source_context2 = [{"line": 2}]  # Different source context

        entry1 = DefinitionEntry(name, self.contents1, takes_value, source_context1)
        entry2 = DefinitionEntry(name, self.contents1, takes_value, source_context2)
        entry3 = DefinitionEntry(name, self.contents3, takes_value, source_context2)
        entry4 = DefinitionEntry("TESTDEF", self.contents3, takes_value, source_context1)
        # Should be equal despite different source contexts
        self.assertEqual(entry1, entry2)
        self.assertTrue(entry1 == entry2)
        # Should be equal as contents are the same
        self.assertEqual(entry1, entry3)
        self.assertTrue(entry1 == entry3)
        # Should be equal with different cased names
        self.assertEqual(entry1, entry4)
        self.assertTrue(entry1 == entry4)

        # Not equal with different contents
        entry5 = DefinitionEntry(name, self.contents2, takes_value, None)
        self.assertNotEqual(entry1, entry5)
        self.assertFalse(entry1 == entry5)

        # Not equal with different takes value
        entry6 = DefinitionEntry(name, self.contents2, True, None)
        self.assertNotEqual(entry1, entry6)
        self.assertFalse(entry1 == entry6)

        # Not equal with different contents
        entry7 = DefinitionEntry(name, None, False, None)
        self.assertNotEqual(entry1, entry7)
        self.assertFalse(entry1 == entry7)


if __name__ == "__main__":
    unittest.main()
