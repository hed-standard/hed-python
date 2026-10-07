import copy
import unittest

from hed import load_schema_version
from hed.schema import HedKey, hed_schema_constants
from hed.schema.schema_validation.hed_id_validator import HedIDValidator

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
        self.assertEqual(id_validator._previous_schemas["testlib"].version_number, "2.2.0")
        self.assertEqual(id_validator._previous_schemas[""].version_number, "8.3.0")

    def test_get_previous_version(self):
        self.assertEqual(HedIDValidator._get_previous_version("8.3.0", ""), "8.2.0")
        self.assertEqual(HedIDValidator._get_previous_version("8.2.0", ""), "8.1.0")
        self.assertEqual(HedIDValidator._get_previous_version("8.0.0", ""), None)
        self.assertEqual(HedIDValidator._get_previous_version("3.0.0", "testlib"), "testlib_2.2.0")
        # Regression guard: the previous version must come from the full (manifest) version list,
        # not just whatever happens to be in the local cache. This reaches deeper into testlib's
        # history than the case above, so it fails if the list is ever truncated/incomplete again
        # (the bug that surfaced on a fresh CI runner). testlib releases: 1.0.2, 2.0.0, 2.1.0, ...
        self.assertEqual(HedIDValidator._get_previous_version("2.0.0", "testlib"), "testlib_1.0.2")

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


class TestUnpartneredLibrary(unittest.TestCase):
    """An unpartnered library's entries carry no inLibrary, so the validator falls back to the schema's library
    name for the previous-version lookup and the id range (PR #1448)."""

    W = "'''"

    @classmethod
    def setUpClass(cls):
        from hed.schema import from_string  # noqa: PLC0415

        w = cls.W
        lines = [
            'HED library="score" version="1.1.0"',
            f"{w}Prologue{w}",
            "!# start schema",
            f"{w}Modulator{w} <nowiki>{{hedId=HED_0045000}}</nowiki>",
            f"{w}Sleep-modulator{w} <nowiki>{{hedId=HED_0012345}}</nowiki>",
            "!# end schema",
            f"{w}Unit classes{w}",
            f"{w}Unit modifiers{w}",
            f"{w}Value classes{w}",
            f"{w}Schema attributes{w}",
            "* hedId <nowiki>{elementProperty, stringRange}</nowiki>",
            f"{w}Properties{w}",
            "* elementProperty",
            "* stringRange",
            f"{w}Epilogue{w}",
            "!# end hed",
        ]
        cls.unpartnered = from_string("\n".join(lines), schema_format=".mediawiki")
        cls.id_validator = HedIDValidator(cls.unpartnered)

    def test_library_name_comes_from_the_schema(self):
        self.assertFalse(self.unpartnered.tags["Modulator"].has_attribute(HedKey.InLibrary))
        self.assertEqual(self.id_validator._previous_schemas["score"].version_number, "1.0.0")
        self.assertEqual(self.id_validator.library_data["score"]["id_range"], [40000, 59999])

    def test_id_in_the_library_range_is_accepted(self):
        entry = self.unpartnered.tags["Modulator"]
        self.assertEqual(self.id_validator.verify_tag_id(self.unpartnered, entry, HedKey.HedID), [])

    def test_id_outside_the_library_range_is_reported(self):
        entry = self.unpartnered.tags["Sleep-modulator"]
        issues = self.id_validator.verify_tag_id(self.unpartnered, entry, HedKey.HedID)
        self.assertEqual(len(issues), 1, issues)
        self.assertIn("between 40000", issues[0]["message"])
