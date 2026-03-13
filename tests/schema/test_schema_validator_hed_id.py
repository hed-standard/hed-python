import unittest
import copy

from hed.schema.schema_validation.hed_id_validator import HedIDValidator
from hed.schema import hed_schema_constants
from hed import load_schema_version
from hed.schema import HedKey

# tests needed:
# 1. Verify HED id(HARDEST, MAY SKIP)
# 4. Json tests


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hed_schema = load_schema_version("8.3.0")
        cls.test_schema = load_schema_version("testlib_3.0.0")
        cls.hed_schema84 = copy.deepcopy(cls.hed_schema)
        cls.hed_schema84.header_attributes[hed_schema_constants.VERSION_ATTRIBUTE] = "8.4.0"

    def test_constructor(self):
        id_validator = HedIDValidator(self.hed_schema)

        self.assertTrue(id_validator._previous_schemas[""])
        self.assertTrue(id_validator.library_data[""])
        self.assertEqual(id_validator._previous_schemas[""].version_number, "8.2.0")

        id_validator = HedIDValidator(self.test_schema)

        self.assertTrue(id_validator._previous_schemas[""])
        self.assertTrue(id_validator.library_data[""])
        self.assertTrue(id_validator._previous_schemas["testlib"])
        self.assertEqual(id_validator.library_data.get("testlib"), None)
        self.assertEqual(id_validator._previous_schemas["testlib"].version_number, "2.1.0")
        self.assertEqual(id_validator._previous_schemas[""].version_number, "8.1.0")

    def test_get_previous_version(self):
        self.assertEqual(HedIDValidator._get_previous_version("8.3.0", ""), "8.2.0")
        self.assertEqual(HedIDValidator._get_previous_version("8.2.0", ""), "8.1.0")
        self.assertEqual(HedIDValidator._get_previous_version("8.0.0", ""), None)
        self.assertEqual(HedIDValidator._get_previous_version("3.0.0", "testlib"), "testlib_2.1.0")

    def test_verify_tag_id(self):
        event_entry = self.hed_schema84.tags["Event"]
        event_entry.attributes[HedKey.HedID] = "HED_0000000"

        id_validator = HedIDValidator(self.hed_schema84)

        issues = id_validator.verify_tag_id(self.hed_schema84, event_entry, HedKey.HedID)
        self.assertGreater(len(issues), 0)
        messages = [i["message"] for i in issues]
        self.assertTrue(any("It has changed" in m for m in messages))
        self.assertTrue(any("between 10000" in m for m in messages))

    def test_verify_tag_id_invalid_format(self):
        """A non-integer hedId should produce an INVALID format error."""
        schema84 = copy.deepcopy(self.hed_schema)
        schema84.header_attributes[hed_schema_constants.VERSION_ATTRIBUTE] = "8.4.0"
        event_entry = schema84.tags["Event"]
        event_entry.attributes[HedKey.HedID] = "HED_XXXXXXX"

        id_validator = HedIDValidator(schema84)
        issues = id_validator.verify_tag_id(schema84, event_entry, HedKey.HedID)
        self.assertGreater(len(issues), 0)
        self.assertIn("It must be an integer in the format", issues[0]["message"])
