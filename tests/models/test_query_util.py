"""Tests for query_util module, particularly SearchResult class.

SearchResult represents a query match result consisting of:
- group: The containing HedGroup where matches were found
- children: The specific matched elements (tags/groups) within that group
             (NOT all children - only the ones that satisfied the query)

For example, when searching for "Red" in "(Red, Blue, Green)":
- group = the containing group (Red, Blue, Green)
- children = [Red] (only the matched tag)
"""

import unittest
from hed.models.query_util import SearchResult
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


if __name__ == "__main__":
    unittest.main()
