"""Tests for JSON schema format explicit attributes handling."""

import unittest
import json
from hed.schema import load_schema_version


class TestJSONExplicitAttributes(unittest.TestCase):
    """Test that explicitAttributes field correctly distinguishes inherited from explicit attributes."""

    @classmethod
    def setUpClass(cls):
        """Load schema once for all tests."""
        cls.schema = load_schema_version("8.4.0")

    def _get_json_output(self):
        """Get JSON output as dict."""
        json_string = self.schema.get_as_json_string(save_merged=True)
        return json.loads(json_string)

    def test_explicit_attributes_key_exists(self):
        """Test that explicitAttributes key is present in JSON output."""
        json_data = self._get_json_output()

        # Check that tags have explicitAttributes
        tags = json_data["tags"]
        self.assertIn("Event", tags)
        self.assertIn("explicitAttributes", tags["Event"])

    def test_item_has_explicit_extension_allowed(self):
        """Test that Item has extensionAllowed in both attributes and explicitAttributes."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        item = tags["Item"]
        self.assertIn("extensionAllowed", item["attributes"])
        self.assertTrue(item["attributes"]["extensionAllowed"])
        self.assertIn("extensionAllowed", item["explicitAttributes"])
        self.assertTrue(item["explicitAttributes"]["extensionAllowed"])

    def test_object_inherits_extension_allowed(self):
        """Test that Object has extensionAllowed in attributes but NOT in explicitAttributes."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        obj = tags["Object"]
        # Should have extensionAllowed in attributes (inherited from Item)
        self.assertIn("extensionAllowed", obj["attributes"])
        self.assertTrue(obj["attributes"]["extensionAllowed"])

        # Should NOT have extensionAllowed in explicitAttributes (it's inherited)
        self.assertNotIn("extensionAllowed", obj["explicitAttributes"])

    def test_event_has_explicit_suggested_tag(self):
        """Test that Event has suggestedTag in both dicts."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        event = tags["Event"]
        self.assertIn("suggestedTag", event["attributes"])
        self.assertIn("Task-property", event["attributes"]["suggestedTag"])

        self.assertIn("suggestedTag", event["explicitAttributes"])
        self.assertIn("Task-property", event["explicitAttributes"]["suggestedTag"])

    def test_sensory_event_inherits_and_adds_suggested_tag(self):
        """Test that Sensory-event shows both inherited and explicit suggestedTag values."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        sensory = tags["Sensory-event"]

        # attributes should have all values (inherited + explicit)
        self.assertIn("suggestedTag", sensory["attributes"])
        all_tags = sensory["attributes"]["suggestedTag"]
        self.assertIn("Task-property", all_tags)  # inherited from Event
        self.assertIn("Task-event-role", all_tags)  # explicit
        self.assertIn("Sensory-presentation", all_tags)  # explicit

        # explicitAttributes should only have explicit values
        self.assertIn("suggestedTag", sensory["explicitAttributes"])
        explicit_tags = sensory["explicitAttributes"]["suggestedTag"]
        self.assertNotIn("Task-property", explicit_tags)  # NOT explicit
        self.assertIn("Task-event-role", explicit_tags)  # explicit
        self.assertIn("Sensory-presentation", explicit_tags)  # explicit

    def test_hed_id_is_always_explicit(self):
        """Test that hedId (non-inheritable) appears in both dicts."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        event = tags["Event"]
        self.assertIn("hedId", event["attributes"])
        self.assertIn("hedId", event["explicitAttributes"])
        self.assertEqual(event["attributes"]["hedId"], event["explicitAttributes"]["hedId"])

    def test_false_boolean_omitted(self):
        """Test that boolean attributes with false value are omitted."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        # Event should not have requireChild, unique, etc. since they're false
        event = tags["Event"]
        self.assertNotIn("requireChild", event["attributes"])
        self.assertNotIn("unique", event["attributes"])
        self.assertNotIn("required", event["attributes"])

        # Same for explicitAttributes
        self.assertNotIn("requireChild", event["explicitAttributes"])
        self.assertNotIn("unique", event["explicitAttributes"])

    def test_biological_item_inherits_from_item(self):
        """Test that Biological-item inherits extensionAllowed from Item."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        bio = tags["Biological-item"]
        # Should have extensionAllowed in attributes (inherited)
        self.assertIn("extensionAllowed", bio["attributes"])
        self.assertTrue(bio["attributes"]["extensionAllowed"])

        # Should NOT have it in explicitAttributes
        self.assertNotIn("extensionAllowed", bio["explicitAttributes"])

    def test_roundtrip_preserves_explicit_vs_inherited(self):
        """Test that JSON -> Schema -> JSON roundtrip preserves explicit/inherited distinction."""
        # Get original JSON
        original_json_str = self.schema.get_as_json_string(save_merged=True)
        json.loads(original_json_str)

        # Load from JSON string
        from hed.schema.schema_io import json2schema

        reloaded_schema = json2schema.SchemaLoaderJSON.load(schema_as_string=original_json_str)

        # Convert back to JSON
        roundtrip_json_str = reloaded_schema.get_as_json_string(save_merged=True)
        roundtrip_json = json.loads(roundtrip_json_str)

        # Check that Object still doesn't have explicit extensionAllowed
        self.assertNotIn("extensionAllowed", roundtrip_json["tags"]["Object"]["explicitAttributes"])
        self.assertIn("extensionAllowed", roundtrip_json["tags"]["Object"]["attributes"])

    def test_language_item_inherits_suggested_tag(self):
        """Test multi-level inheritance of suggestedTag."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        # Language-item has explicit suggestedTag
        lang = tags["Language-item"]
        self.assertIn("suggestedTag", lang["attributes"])
        self.assertIn("Sensory-presentation", lang["attributes"]["suggestedTag"])
        self.assertIn("suggestedTag", lang["explicitAttributes"])
        self.assertIn("Sensory-presentation", lang["explicitAttributes"]["suggestedTag"])

    def test_empty_lists_omitted(self):
        """Test that empty lists are omitted from JSON output (not written as empty arrays)."""
        json_data = self._get_json_output()
        tags = json_data["tags"]

        # Tags without relatedTag/valueClass/unitClass should not have these keys at all
        event = tags["Event"]
        # Event has suggestedTag, so it should be present
        self.assertIn("suggestedTag", event["attributes"])
        # But if Event doesn't have relatedTag, it should be omitted entirely
        if "relatedTag" in event["attributes"]:
            # If present, it must be non-empty
            self.assertNotEqual(
                event["attributes"]["relatedTag"], [], "relatedTag should be omitted entirely, not present as empty list"
            )

        # Check that tags without certain attributes don't have empty lists
        item = tags.get("Item", {})
        if "relatedTag" in item.get("attributes", {}):
            self.assertNotEqual(item["attributes"]["relatedTag"], [], "Empty relatedTag should be omitted, not present as []")


class TestJSONBackwardsCompatibility(unittest.TestCase):
    """Test that old JSON format (without explicitAttributes) still loads correctly."""

    def test_load_old_format_without_explicit_attributes(self):
        """Test loading JSON that doesn't have explicitAttributes field."""
        old_format_json = {
            "version": "8.4.0",
            "tags": {
                "Item": {
                    "short_form": "Item",
                    "long_form": "Item",
                    "description": "An independently existing thing",
                    "parent": None,
                    "children": ["Object"],
                    "attributes": {"extensionAllowed": True, "hedId": "HED_0012171"},
                },
                "Object": {
                    "short_form": "Object",
                    "long_form": "Item/Object",
                    "description": "A material thing",
                    "parent": "Item",
                    "children": [],
                    "attributes": {"extensionAllowed": True, "hedId": "HED_0012247"},  # Old format had this wrong
                },
            },
            "units": {},
            "unit_classes": {},
            "unit_modifiers": {},
            "value_classes": {},
            "schema_attributes": {},
            "properties": {},
        }

        from hed.schema.schema_io import json2schema
        import json

        schema = json2schema.SchemaLoaderJSON.load(schema_as_string=json.dumps(old_format_json))

        # Verify schema loaded
        self.assertIsNotNone(schema)
        item = schema.get_tag_entry("Item")
        self.assertIsNotNone(item)

        # Item should have explicit extensionAllowed
        self.assertIn("extensionAllowed", item.attributes)

        # Object should also have explicit extensionAllowed (from old format)
        obj = schema.get_tag_entry("Item/Object")
        self.assertIn("extensionAllowed", obj.attributes)


if __name__ == "__main__":
    unittest.main()
