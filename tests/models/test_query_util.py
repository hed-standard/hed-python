"""Tests for query_util module, particularly SearchResult class.

SearchResult represents a query match result consisting of:
- group: The containing HedGroup where matches were found
- children: The specific matched elements (tags/groups) within that group
             (NOT all children - only the ones that satisfied the query)

For example, when searching for "Red" in "(Red, Blue, Green)":
- group = the containing group (Red, Blue, Green)
- children = [Red] (only the matched tag)
"""

import os
import unittest
from hed.models.query_util import SearchResult
from hed.models.hed_string import HedString
from hed import schema
from unittest.mock import Mock


class TestSearchResult(unittest.TestCase):
    """Test SearchResult class functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_group = Mock()
        self.mock_group.__str__ = Mock(return_value="MockGroup")

        self.mock_child1 = Mock()
        self.mock_child1.__str__ = Mock(return_value="Child1")

        self.mock_child2 = Mock()
        self.mock_child2.__str__ = Mock(return_value="Child2")

        self.mock_child3 = Mock()
        self.mock_child3.__str__ = Mock(return_value="Child3")

    def test_init_single_child(self):
        """Test initialization with a single matched child (not a list)."""
        result = SearchResult(self.mock_group, self.mock_child1)
        self.assertEqual(result.group, self.mock_group)
        self.assertEqual(len(result.children), 1)
        self.assertIs(result.children[0], self.mock_child1)

    def test_init_list_of_children(self):
        """Test initialization with multiple matched children."""
        children = [self.mock_child1, self.mock_child2]
        result = SearchResult(self.mock_group, children)
        self.assertEqual(result.group, self.mock_group)
        self.assertEqual(len(result.children), 2)
        self.assertIs(result.children[0], self.mock_child1)
        self.assertIs(result.children[1], self.mock_child2)

    def test_init_empty_list(self):
        """Test initialization with empty list (e.g., negation case)."""
        result = SearchResult(self.mock_group, [])
        self.assertEqual(result.group, self.mock_group)
        self.assertEqual(len(result.children), 0)

    def test_merge_and_result_unique_children(self):
        """Test merging results adds unique matched children from both."""
        result1 = SearchResult(self.mock_group, [self.mock_child1])
        result2 = SearchResult(self.mock_group, [self.mock_child2])

        merged = result1.merge_and_result(result2)

        self.assertEqual(merged.group, self.mock_group)
        self.assertEqual(len(merged.children), 2)
        self.assertIn(self.mock_child1, merged.children)
        self.assertIn(self.mock_child2, merged.children)

    def test_merge_and_result_duplicate_children(self):
        """Test merging deduplicates children by identity (same object)."""
        result1 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])
        result2 = SearchResult(self.mock_group, [self.mock_child2, self.mock_child3])

        merged = result1.merge_and_result(result2)

        # Should only have unique children (by identity)
        self.assertEqual(len(merged.children), 3)
        self.assertIn(self.mock_child1, merged.children)
        self.assertIn(self.mock_child2, merged.children)
        self.assertIn(self.mock_child3, merged.children)

    def test_merge_and_result_different_groups_raises(self):
        """Test that merging results with different groups raises ValueError."""
        other_group = Mock()
        result1 = SearchResult(self.mock_group, [self.mock_child1])
        result2 = SearchResult(other_group, [self.mock_child2])

        with self.assertRaises(ValueError) as cm:
            result1.merge_and_result(result2)
        self.assertIn("Internal error", str(cm.exception))

    def test_has_same_children_identical(self):
        """Test has_same_children returns True for identical results."""
        result1 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])
        result2 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])

        self.assertTrue(result1.has_same_children(result2))
        self.assertTrue(result2.has_same_children(result1))

    def test_has_same_children_different_groups(self):
        """Test has_same_children returns False for different groups."""
        other_group = Mock()
        result1 = SearchResult(self.mock_group, [self.mock_child1])
        result2 = SearchResult(other_group, [self.mock_child1])

        self.assertFalse(result1.has_same_children(result2))

    def test_has_same_children_different_count(self):
        """Test has_same_children returns False for different child counts."""
        result1 = SearchResult(self.mock_group, [self.mock_child1])
        result2 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])

        self.assertFalse(result1.has_same_children(result2))

    def test_has_same_children_different_children(self):
        """Test has_same_children returns False for different children."""
        result1 = SearchResult(self.mock_group, [self.mock_child1])
        result2 = SearchResult(self.mock_group, [self.mock_child2])

        self.assertFalse(result1.has_same_children(result2))

    def test_has_same_children_different_order(self):
        """Test has_same_children compares by position (order matters)."""
        result1 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])
        result2 = SearchResult(self.mock_group, [self.mock_child2, self.mock_child1])

        # Should be False because order/position differs
        self.assertFalse(result1.has_same_children(result2))

    def test_backward_compatibility_has_same_tags(self):
        """Test that has_same_tags is a backward-compatible alias for has_same_children."""
        result1 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])
        result2 = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])
        result3 = SearchResult(self.mock_group, [self.mock_child3])

        # Both method names should work
        self.assertTrue(result1.has_same_tags(result2))
        self.assertTrue(result1.has_same_children(result2))

        self.assertFalse(result1.has_same_tags(result3))
        self.assertFalse(result1.has_same_children(result3))

        # Verify they are literally the same function (not a wrapper)
        self.assertIs(result1.has_same_tags.__func__, result1.has_same_children.__func__)

        # Both should produce identical results
        self.assertEqual(result1.has_same_tags(result2), result1.has_same_children(result2))

    def test_str_representation(self):
        """Test string representation uses 'Children' label."""
        result = SearchResult(self.mock_group, [self.mock_child1, self.mock_child2])
        str_repr = str(result)

        # Should contain group and children
        self.assertIn("MockGroup", str_repr)
        self.assertIn("Children:", str_repr)
        self.assertIn("Child1", str_repr)
        self.assertIn("Child2", str_repr)


class TestSearchResultHashEquality(unittest.TestCase):
    """Tests for SearchResult.__hash__ and __eq__, added with Plan 1 Phase A."""

    def setUp(self):
        self.group = Mock()
        self.group.__str__ = Mock(return_value="Group")
        self.other_group = Mock()
        self.c1 = Mock()
        self.c2 = Mock()
        self.c3 = Mock()
        self.c1.__str__ = Mock(return_value="c1")
        self.c2.__str__ = Mock(return_value="c2")
        self.c3.__str__ = Mock(return_value="c3")

    # --- __eq__ ---

    def test_eq_reflexive(self):
        r = SearchResult(self.group, [self.c1])
        self.assertEqual(r, r)

    def test_eq_same_group_and_children_by_identity(self):
        """Two results backed by the same group object and same child objects are equal."""
        r1 = SearchResult(self.group, [self.c1, self.c2])
        r2 = SearchResult(self.group, [self.c1, self.c2])
        self.assertEqual(r1, r2)

    def test_eq_different_group_same_children(self):
        """Different group objects → not equal, even if children are the same objects."""
        r1 = SearchResult(self.group, [self.c1])
        r2 = SearchResult(self.other_group, [self.c1])
        self.assertNotEqual(r1, r2)

    def test_eq_same_group_different_child_by_identity(self):
        """Same group but children are different objects → not equal."""
        r1 = SearchResult(self.group, [self.c1])
        r2 = SearchResult(self.group, [self.c2])
        self.assertNotEqual(r1, r2)

    def test_eq_different_child_count(self):
        r1 = SearchResult(self.group, [self.c1])
        r2 = SearchResult(self.group, [self.c1, self.c2])
        self.assertNotEqual(r1, r2)

    def test_eq_empty_children(self):
        r1 = SearchResult(self.group, [])
        r2 = SearchResult(self.group, [])
        self.assertEqual(r1, r2)

    def test_eq_child_order_matters(self):
        """Children [c1, c2] and [c2, c1] are not equal because position matters."""
        r1 = SearchResult(self.group, [self.c1, self.c2])
        r2 = SearchResult(self.group, [self.c2, self.c1])
        self.assertNotEqual(r1, r2)

    def test_eq_non_searchresult_returns_not_implemented(self):
        r = SearchResult(self.group, [self.c1])
        self.assertIs(r.__eq__("not a SearchResult"), NotImplemented)
        self.assertIs(r.__eq__(42), NotImplemented)
        self.assertIs(r.__eq__(None), NotImplemented)

    # --- __hash__ ---

    def test_hash_equal_objects_same_hash(self):
        """Equal objects must have the same hash (required by Python's data model)."""
        r1 = SearchResult(self.group, [self.c1, self.c2])
        r2 = SearchResult(self.group, [self.c1, self.c2])
        self.assertEqual(r1, r2)
        self.assertEqual(hash(r1), hash(r2))

    def test_hash_empty_children_consistent(self):
        r1 = SearchResult(self.group, [])
        r2 = SearchResult(self.group, [])
        self.assertEqual(hash(r1), hash(r2))

    def test_hashable_usable_in_set(self):
        """SearchResult can be added to a set; equal objects collapse to one entry."""
        r1 = SearchResult(self.group, [self.c1])
        r2 = SearchResult(self.group, [self.c1])  # equal to r1
        r3 = SearchResult(self.group, [self.c2])  # distinct child
        r4 = SearchResult(self.other_group, [self.c1])  # distinct group
        s = {r1, r2, r3, r4}
        self.assertEqual(len(s), 3)  # r1 and r2 collapse; r3 and r4 are distinct

    def test_hashable_usable_in_set_empty_children(self):
        r1 = SearchResult(self.group, [])
        r2 = SearchResult(self.group, [])
        s = {r1, r2}
        self.assertEqual(len(s), 1)

    # --- Integration: set-based dedup as used by merge_and_groups ---

    def test_merge_and_groups_deduplicates_equal_merged_results(self):
        """merge_and_groups should not return the same merged result twice.

        When two entries in groups1 are equal (produce the same merged result
        when combined with a shared groups2 entry), only one should appear in
        the output.
        """
        from hed.models.query_expressions import ExpressionAnd

        g = self.group
        # Two groups1 entries that are identical (same group, same child c1)
        r1a = SearchResult(g, [self.c1])
        r1b = SearchResult(g, [self.c1])  # equal to r1a under __eq__
        r2 = SearchResult(g, [self.c2])  # groups2 entry

        # r1a merged with r2 → SR(g, [c1, c2])
        # r1b merged with r2 → SR(g, [c1, c2]) ← duplicate; should be suppressed
        result = ExpressionAnd.merge_and_groups([r1a, r1b], [r2])
        self.assertEqual(len(result), 1, "duplicate merged result should be suppressed")

    def test_merge_and_groups_preserves_distinct_results(self):
        """merge_and_groups must not drop results that are genuinely different."""
        from hed.models.query_expressions import ExpressionAnd

        g = self.group
        r1a = SearchResult(g, [self.c1])
        r1b = SearchResult(g, [self.c2])  # different child: produces different merged result
        r2 = SearchResult(g, [self.c3])

        result = ExpressionAnd.merge_and_groups([r1a, r1b], [r2])
        self.assertEqual(len(result), 2, "two distinct merged results should both be returned")


class TestSearchResultGroupIdentitySemantics(unittest.TestCase):
    """Tests that merge_and_result and has_same_children use object identity
    (is/is not) for group comparison, consistent with __eq__ and __hash__.

    The key invariant: two distinct HedGroup objects that happen to have equal
    content must be treated as *different* groups throughout the API.

    Uses two HedString objects parsed from identical content with a real schema:
    HedGroup.__eq__ is content-based, so hs_a == hs_b is True while hs_a is not hs_b
    is also True — exactly the condition a buggy content-equality check would miss.
    """

    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/"))
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)

    def setUp(self):
        # Two HedStrings with identical content parsed independently.
        # HedGroup.__eq__ compares children structurally, so hs_a == hs_b,
        # but they are distinct objects: hs_a is not hs_b.
        hs_a = HedString("Red, Blue", self.hed_schema)
        hs_b = HedString("Red, Blue", self.hed_schema)
        self.group_a = hs_a
        self.group_b = hs_b
        # Use a real tag from group_a as the matched child
        self.child = list(hs_a.get_all_tags())[0]

    def test_merge_and_result_raises_for_content_equal_but_distinct_groups(self):
        """merge_and_result must raise ValueError when groups are distinct objects
        even if those objects compare as content-equal.
        """
        r1 = SearchResult(self.group_a, [self.child])
        r2 = SearchResult(self.group_b, [self.child])

        # group_a == group_b is True (content equality), so a buggy == check
        # would NOT raise.  The correct identity check (is not) MUST raise.
        with self.assertRaises(ValueError):
            r1.merge_and_result(r2)

    def test_has_same_children_false_for_content_equal_but_distinct_groups(self):
        """has_same_children must return False when groups are distinct objects
        even if those objects compare as content-equal.
        """
        r1 = SearchResult(self.group_a, [self.child])
        r2 = SearchResult(self.group_b, [self.child])

        # A buggy content-equality check would return True; identity check must return False.
        self.assertFalse(r1.has_same_children(r2))

    def test_eq_false_for_content_equal_but_distinct_groups(self):
        """__eq__ must return False when groups are distinct objects
        even if those objects compare as content-equal.
        """
        r1 = SearchResult(self.group_a, [self.child])
        r2 = SearchResult(self.group_b, [self.child])

        self.assertNotEqual(r1, r2)

    def test_same_group_object_all_apis_agree(self):
        """When both results share the exact same group object, all three
        APIs must consistently treat them as same-group.
        """
        r1 = SearchResult(self.group_a, [self.child])
        r2 = SearchResult(self.group_a, [self.child])

        self.assertTrue(r1.has_same_children(r2))
        self.assertEqual(r1, r2)
        merged = r1.merge_and_result(r2)  # must not raise
        self.assertIs(merged.group, self.group_a)


if __name__ == "__main__":
    unittest.main()
