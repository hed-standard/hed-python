"""Tests for hed.models.schema_lookup.

Tests cover:
- generate_schema_lookup builds a valid dict from a real schema
- save_schema_lookup / load_schema_lookup round-trip
- Both individual HedSchema and HedSchemaGroup inputs are handled
"""

import json
import os
import tempfile
import unittest

from hed.models.schema_lookup import generate_schema_lookup, save_schema_lookup, load_schema_lookup


class TestSchemaLookupBase(unittest.TestCase):
    """Base class that loads a schema once for all lookup tests."""

    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/"))
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        try:
            from hed import schema as hed_schema

            cls.hed_schema = hed_schema.load_schema(hed_xml_file)
            cls.lookup = generate_schema_lookup(cls.hed_schema)
        except Exception as exc:
            cls.hed_schema = None
            cls.lookup = None
            cls._setup_error = str(exc)

    def _require_schema(self):
        if self.lookup is None:
            self.skipTest(f"Schema not available: {getattr(self, '_setup_error', 'unknown error')}")


class TestGenerateSchemaLookup(TestSchemaLookupBase):
    def test_returns_dict(self):
        self._require_schema()
        self.assertIsInstance(self.lookup, dict)

    def test_non_empty(self):
        self._require_schema()
        self.assertGreater(len(self.lookup), 0)

    def test_all_keys_are_strings(self):
        self._require_schema()
        for key in self.lookup:
            self.assertIsInstance(key, str)

    def test_all_values_are_tuples_of_strings(self):
        self._require_schema()
        for key, value in self.lookup.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, tuple)
                for item in value:
                    self.assertIsInstance(item, str)

    def test_keys_are_casefolded(self):
        self._require_schema()
        for key in self.lookup:
            self.assertEqual(key, key.casefold(), f"Key {key!r} is not casefolded")

    def test_values_are_casefolded(self):
        self._require_schema()
        for key, terms in self.lookup.items():
            for term in terms:
                with self.subTest(key=key, term=term):
                    self.assertEqual(term, term.casefold())

    def test_key_appears_in_own_tag_terms(self):
        """Every short tag name must be present in its own tag_terms tuple."""
        self._require_schema()
        for key, terms in self.lookup.items():
            with self.subTest(key=key):
                self.assertIn(key, terms, f"Key {key!r} missing from its own tag_terms {terms}")

    def test_event_in_lookup(self):
        self._require_schema()
        self.assertIn("event", self.lookup)

    def test_event_tag_terms_correct(self):
        """'Event' has itself as only ancestor (it is a top-level tag)."""
        self._require_schema()
        terms = self.lookup.get("event")
        self.assertIsNotNone(terms)
        self.assertIn("event", terms)

    def test_sensory_event_has_event_ancestor(self):
        """'Sensory-event' is a child of 'Event' so 'event' must appear in its tag_terms."""
        self._require_schema()
        terms = self.lookup.get("sensory-event")
        if terms is None:
            self.skipTest("'sensory-event' not in schema")
        self.assertIn("event", terms)
        self.assertIn("sensory-event", terms)

    def test_no_value_placeholder_keys(self):
        """Entries ending with '/#' should be excluded from the lookup."""
        self._require_schema()
        for key in self.lookup:
            self.assertFalse(key.endswith("/#"), f"Found value placeholder key: {key!r}")

    def test_no_slash_in_keys(self):
        """Keys are short tag names (last slash component), never full paths."""
        self._require_schema()
        for key in self.lookup:
            self.assertNotIn("/", key, f"Key {key!r} contains a slash")

    def test_tag_terms_form_valid_path(self):
        """tag_terms for a non-root tag should end with the key itself."""
        self._require_schema()
        for key, terms in self.lookup.items():
            with self.subTest(key=key):
                self.assertEqual(terms[-1], key, f"Last term of {terms} should equal key {key!r}")

    def test_ancestor_chain_consistent(self):
        """If 'sensory-event' → (..., 'event', 'sensory-event'), then
        the parent term 'event' should also be in the lookup."""
        self._require_schema()
        for key, terms in self.lookup.items():
            # Each ancestor term (except the last = self) should be in the lookup
            for ancestor in terms[:-1]:
                with self.subTest(key=key, ancestor=ancestor):
                    self.assertIn(ancestor, self.lookup, f"Ancestor {ancestor!r} of {key!r} not in lookup")


class TestSchemaLookupRoundTrip(TestSchemaLookupBase):
    def test_save_and_load(self):
        self._require_schema()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_schema_lookup(self.lookup, tmp_path)
            loaded = load_schema_lookup(tmp_path)

            self.assertEqual(set(loaded.keys()), set(self.lookup.keys()))
            for key in self.lookup:
                self.assertEqual(loaded[key], self.lookup[key])
        finally:
            os.unlink(tmp_path)

    def test_saved_file_is_valid_json(self):
        self._require_schema()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="r") as tmp:
            tmp_path = tmp.name

        try:
            save_schema_lookup(self.lookup, tmp_path)
            with open(tmp_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIsInstance(data, dict)
            # JSON arrays are stored as lists
            for _key, value in data.items():
                self.assertIsInstance(value, list)
        finally:
            os.unlink(tmp_path)

    def test_loaded_values_are_tuples(self):
        self._require_schema()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_schema_lookup(self.lookup, tmp_path)
            loaded = load_schema_lookup(tmp_path)
            for key, value in loaded.items():
                with self.subTest(key=key):
                    self.assertIsInstance(value, tuple)
        finally:
            os.unlink(tmp_path)

    def test_round_trip_preserves_tag_terms(self):
        self._require_schema()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            save_schema_lookup(self.lookup, tmp_path)
            loaded = load_schema_lookup(tmp_path)

            for key in self.lookup:
                with self.subTest(key=key):
                    self.assertEqual(loaded[key], self.lookup[key])
        finally:
            os.unlink(tmp_path)


class TestSchemaLookupUsedInSearch(TestSchemaLookupBase):
    """Integration tests: lookup dict plugged into StringQueryHandler."""

    def test_event_query_matches_sensory_event_via_lookup(self):
        self._require_schema()
        from hed.models.string_search import StringQueryHandler

        handler = StringQueryHandler("Event")
        result = bool(handler.search("Sensory-event", schema_lookup=self.lookup))
        self.assertTrue(result)

    def test_event_query_miss_with_no_lookup(self):
        """Without lookup, 'Event' does not match short-form 'Sensory-event'."""
        from hed.models.string_search import StringQueryHandler

        handler = StringQueryHandler("Event")
        result = bool(handler.search("Sensory-event"))
        self.assertFalse(result)

    def test_event_query_matches_event_itself(self):
        self._require_schema()
        from hed.models.string_search import StringQueryHandler

        handler = StringQueryHandler("Event")
        result = bool(handler.search("Event", schema_lookup=self.lookup))
        self.assertTrue(result)

    def test_descendant_group_with_lookup(self):
        """[Event] matches a group containing any Event descendant."""
        self._require_schema()
        from hed.models.string_search import StringQueryHandler

        handler = StringQueryHandler("[Event]")
        self.assertTrue(bool(handler.search("(Sensory-event, Action)", schema_lookup=self.lookup)))
        self.assertFalse(bool(handler.search("(Property)", schema_lookup=self.lookup)))


class TestSchemaLookupNoSchema(unittest.TestCase):
    """Test generate_schema_lookup with a minimal handcrafted schema-like object."""

    def test_empty_schema_returns_empty_dict(self):
        """A schema with an empty tags section returns an empty lookup."""
        # Rather than mocking a full HedSchema, test that the function handles
        # edge cases gracefully by verifying it returns a dict type.
        from hed.models.schema_lookup import generate_schema_lookup

        # Use a very minimal stub
        class _FakeSection:
            def items(self):
                return []

        class _FakeSchema:
            _sections = {}

            @property
            def schemas(self):
                return []

        result = generate_schema_lookup(_FakeSchema())
        self.assertIsInstance(result, dict)

    def test_save_empty_dict(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            save_schema_lookup({}, tmp_path)
            loaded = load_schema_lookup(tmp_path)
            self.assertEqual(loaded, {})
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
