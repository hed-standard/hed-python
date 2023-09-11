import unittest
import copy

from hed.schema import schema_attribute_validators
from hed import schema


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = schema.load_schema_version("8.1.0")

    def test_util_placeholder(self):
        tag_entry = self.hed_schema.tags["Event"]
        attribute_name = "unitClass"
        self.assertTrue(schema_attribute_validators.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name))
        attribute_name = "unitClass"
        tag_entry = self.hed_schema.tags["Age/#"]
        self.assertFalse(schema_attribute_validators.tag_is_placeholder_check(self.hed_schema, tag_entry, attribute_name))

    def test_util_suggested(self):
        tag_entry = self.hed_schema.tags["Event/Sensory-event"]
        attribute_name = "suggestedTag"
        self.assertFalse(schema_attribute_validators.tag_exists_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = self.hed_schema.tags["Property"]
        self.assertFalse(schema_attribute_validators.tag_exists_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["suggestedTag"] = "InvalidSuggestedTag"
        self.assertTrue(schema_attribute_validators.tag_exists_check(self.hed_schema, tag_entry, attribute_name))

    def test_util_rooted(self):
        tag_entry = self.hed_schema.tags["Event"]
        attribute_name = "rooted"
        self.assertFalse(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = self.hed_schema.tags["Property"]
        self.assertFalse(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "Event"
        self.assertFalse(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))
        tag_entry = copy.deepcopy(tag_entry)
        tag_entry.attributes["rooted"] = "NotRealTag"
        self.assertTrue(schema_attribute_validators.tag_exists_base_schema_check(self.hed_schema, tag_entry, attribute_name))