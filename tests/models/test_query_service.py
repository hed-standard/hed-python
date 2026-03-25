"""Tests for query_service module: get_query_handlers and search_hed_objs."""

import os
import unittest

from hed import schema
from hed.models import HedString
from hed.models.query_handler import QueryHandler
from hed.models.query_service import get_query_handlers, search_hed_objs


class TestGetQueryHandlers(unittest.TestCase):
    """Tests for get_query_handlers."""

    def test_valid_queries(self):
        handlers, names, issues = get_query_handlers(["Event", "Action"])
        self.assertEqual(len(handlers), 2)
        self.assertTrue(all(isinstance(h, QueryHandler) for h in handlers))
        self.assertEqual(names, ["query_0", "query_1"])
        self.assertEqual(issues, [])

    def test_valid_queries_with_names(self):
        handlers, names, issues = get_query_handlers(["Event"], query_names=["my_col"])
        self.assertEqual(len(handlers), 1)
        self.assertEqual(names, ["my_col"])
        self.assertEqual(issues, [])

    def test_single_string_query(self):
        handlers, names, issues = get_query_handlers("Event")
        self.assertEqual(len(handlers), 1)
        self.assertIsInstance(handlers[0], QueryHandler)
        self.assertEqual(issues, [])

    def test_empty_queries(self):
        handlers, names, issues = get_query_handlers([])
        self.assertIsNone(handlers)
        self.assertIsNone(names)
        self.assertEqual(len(issues), 1)
        self.assertIn("EmptyQueries", issues[0])

    def test_none_queries(self):
        handlers, names, issues = get_query_handlers(None)
        self.assertIsNone(handlers)
        self.assertIsNone(names)
        self.assertEqual(len(issues), 1)

    def test_mismatched_names_length(self):
        handlers, names, issues = get_query_handlers(["Event", "Action"], query_names=["only_one"])
        self.assertEqual(len(issues), 1)
        self.assertIn("QueryNamesLengthBad", issues[0])

    def test_duplicate_names(self):
        handlers, names, issues = get_query_handlers(["Event", "Action"], query_names=["dup", "dup"])
        self.assertEqual(len(issues), 1)
        self.assertIn("DuplicateQueryNames", issues[0])

    def test_bad_query_includes_error_details(self):
        """Fix #5: Error messages should include the exception details, not just 'cannot be parsed'."""
        handlers, names, issues = get_query_handlers(["A &&", "Event"])
        self.assertIsNone(handlers[0])
        self.assertIsInstance(handlers[1], QueryHandler)
        self.assertEqual(len(issues), 1)
        self.assertIn("[BadQuery 0]", issues[0])
        # The fix ensures the original exception message is included
        self.assertIn("A &&", issues[0])
        # Should contain more than just "cannot be parsed" — the exception detail should be there
        self.assertNotEqual(issues[0], "[BadQuery 0]: A && cannot be parsed")

    def test_multiple_bad_queries(self):
        handlers, names, issues = get_query_handlers(["A &&", "(B", "Event"])
        self.assertIsNone(handlers[0])
        self.assertIsNone(handlers[1])
        self.assertIsInstance(handlers[2], QueryHandler)
        self.assertEqual(len(issues), 2)


class TestSearchHedObjs(unittest.TestCase):
    """Tests for search_hed_objs."""

    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/"))
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)

    def test_basic_search(self):
        hed_objs = [
            HedString("Event", self.hed_schema),
            HedString("Action", self.hed_schema),
            HedString("Event, Action", self.hed_schema),
        ]
        handlers, names, issues = get_query_handlers(["Event"], query_names=["has_event"])
        self.assertEqual(issues, [])
        df = search_hed_objs(hed_objs, handlers, names)
        self.assertEqual(df.at[0, "has_event"], 1)
        self.assertEqual(df.at[1, "has_event"], 0)
        self.assertEqual(df.at[2, "has_event"], 1)

    def test_search_with_none_entries(self):
        hed_objs = [
            HedString("Event", self.hed_schema),
            None,
            HedString("Action", self.hed_schema),
        ]
        handlers, names, issues = get_query_handlers(["Event"], query_names=["has_event"])
        df = search_hed_objs(hed_objs, handlers, names)
        self.assertEqual(df.at[0, "has_event"], 1)
        self.assertEqual(df.at[1, "has_event"], 0)
        self.assertEqual(df.at[2, "has_event"], 0)

    def test_search_multiple_queries(self):
        hed_objs = [
            HedString("Event, Action", self.hed_schema),
            HedString("Event", self.hed_schema),
        ]
        handlers, names, issues = get_query_handlers(["Event", "Action"], query_names=["ev", "act"])
        df = search_hed_objs(hed_objs, handlers, names)
        self.assertEqual(df.at[0, "ev"], 1)
        self.assertEqual(df.at[0, "act"], 1)
        self.assertEqual(df.at[1, "ev"], 1)
        self.assertEqual(df.at[1, "act"], 0)


if __name__ == "__main__":
    unittest.main()
