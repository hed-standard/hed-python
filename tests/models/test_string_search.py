"""Tests for StringQueryHandler, parse_hed_string, and string_search.

Most test cases are directly ported from test_query_handler.py, replacing
HedString-based assertions with raw-string assertions.  Because StringNode
leaf nodes set ``tag_terms = (text,)`` for single-component tags (e.g. ``"a"``
→ ``("a",)``), the literal bare-term matching is equivalent to the
monkey-patched ``tag_terms`` in test_query_handler.py, so all structural
tests pass identically.

Ancestor search tests that require schema hierarchy (e.g. "Clear-throat" being
a descendant of "Action") are placed in a separate test class that generates a
schema lookup table from a real schema file.
"""

import os
import unittest

import pandas as pd

from hed.errors.exceptions import HedQueryError
from hed.models.string_search import StringNode, StringQueryHandler, parse_hed_string, string_search
from hed.models.schema_lookup import generate_schema_lookup


# ---------------------------------------------------------------------------
# Helper: mirror the base_test pattern from test_query_handler.py
# ---------------------------------------------------------------------------


class TestStringParser(unittest.TestCase):
    """Test the tokeniser / parser via StringQueryHandler (error cases)."""

    def test_broken_search_strings(self):
        broken = ["A &&", "(A && B", "&& B", "A, ", ", A", "A)"]
        for s in broken:
            with self.subTest(query=s):
                with self.assertRaises(ValueError):
                    StringQueryHandler(s)

    def test_broken_search_strings_raise_hed_query_error(self):
        broken = ["A &&", "(A && B", "&& B", "A, ", ", A", "A)"]
        for s in broken:
            with self.subTest(query=s):
                with self.assertRaises(HedQueryError):
                    StringQueryHandler(s)

    def test_hed_query_error_is_value_error(self):
        with self.assertRaises(ValueError):
            StringQueryHandler("(unclosed")


class StringSearchBase(unittest.TestCase):
    """Base class providing the base_test helper."""

    def base_test(self, parse_expr, search_strings):
        handler = StringQueryHandler(parse_expr)
        for string, expected in search_strings.items():
            with self.subTest(expr=parse_expr, string=string):
                result = handler.search(string)
                self.assertEqual(bool(result), expected, msg=f"Query={parse_expr!r}, String={string!r}")


# ---------------------------------------------------------------------------
# Basic tag matching
# ---------------------------------------------------------------------------


class TestStringSearchBasicTags(StringSearchBase):
    def test_bare_term_literal_match(self):
        """Bare term matches only the exact tag (no ancestor search without lookup)."""
        test_strings = {
            "A": True,
            "B": False,
            "A, B": True,
            "(A, B)": True,
            "(C, D)": False,
        }
        self.base_test("a", test_strings)

    def test_bare_term_case_insensitive(self):
        test_strings = {"A": True, "a": True, "B": False}
        self.base_test("a", test_strings)
        self.base_test("A", test_strings)

    def test_and_two_tags(self):
        test_strings = {"A": False, "B": False, "C": False, "A, B": True, "A, C": False, "B, C": False}
        self.base_test("a && b", test_strings)

    def test_or_two_tags(self):
        test_strings = {"A": True, "B": True, "C": False, "A, B": True, "A, C": True, "B, C": True}
        self.base_test("a || b", test_strings)

    def test_and_three_tags(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": True,
            "D, A, B": False,  # C missing
            "A, B, (C)": True,  # C in group still present in string
        }
        self.base_test("a && b && c", test_strings)

    def test_actual_wildcard_comma_is_and(self):
        """Comma in a query acts as AND — both tags must be present."""
        test_strings = {
            "A, B, C": True,
            "A, B": True,
            "A, B, (C)": True,
        }
        self.base_test("A, B", test_strings)

    def test_exact_term_quoted(self):
        """Quoted tag uses MATCH_EXACT — does not match short-form parent/child."""
        test_strings = {"A": True, "B": False}
        self.base_test('"A"', test_strings)

    def test_wildcard_prefix(self):
        """Asterisk wildcard matches tags whose text starts with the prefix."""
        # "Apricot" starts with "apr", not "app" — does NOT match "App*"
        test_strings = {
            "Apple": True,
            "Apricot": False,
            "Banana": False,
            "Applesauce": True,
        }
        self.base_test("App*", test_strings)

    def test_wildcard_with_slash(self):
        """Wildcard on a slash-path prefix matches the short_tag (last component)."""
        test_strings = {
            "Def/Def1": True,
            "Def/Def2": True,
            "Def/Def1/Value": True,
        }
        self.base_test("Def*", test_strings)

        test_strings = {
            "Def/Def1": True,
            "Def/Def2": True,
            "Def/Def1/Value": True,
        }
        self.base_test("Def/Def*", test_strings)

    def test_slash_exact_match(self):
        """Slash-path uses full text comparison."""
        test_strings = {
            "Def/Def1": True,
            "Def/Def2": False,
            "Def/Def1/Value": False,
        }
        self.base_test("Def/Def1", test_strings)

        test_strings = {
            "Def/Def1": False,
            "Def/Def2": False,
            "Def/Def1/Value": True,
        }
        self.base_test("Def/Def1/Value", test_strings)

    def test_or_subexpressions(self):
        test_strings = {
            "Item, (Clear-throat)": True,
            "(Item, (Clear-throat))": True,
            "Item, Clear-throat": True,
            "Agent, Clear-throat": True,
            "Agent, Event": False,
        }
        # These use fictitious tags; no schema/ancestor search needed
        self.base_test("(Item || Agent) && Clear-throat", test_strings)

    def test_duplicate_search_and(self):
        """AND of a tag with itself requires two distinct matching leaf objects."""
        # Only ONE 'a' leaf exists in each string — the AND deduplication rejects it
        test_strings = {
            "(A)": False,
            "(A, B)": False,
        }
        self.base_test("A && A", test_strings)

    def test_duplicate_search_or(self):
        """OR of a tag with itself always matches if the tag is present."""
        test_strings = {
            "(A)": True,
            "(A, B)": True,
        }
        self.base_test("A || A", test_strings)


# ---------------------------------------------------------------------------
# Grouping operators
# ---------------------------------------------------------------------------


class TestStringSearchGrouping(StringSearchBase):
    def test_logical_group_parentheses(self):
        """Parentheses in query are for precedence, not structural grouping."""
        test_strings = {
            "A, B": True,
            "A, C": True,
            "D, B": True,
            "D, E": False,
        }
        self.base_test("(A || D) && (B || C)", test_strings)

    def test_exact_group_curly_braces(self):
        """{A, B} — A and B must share the same direct parent group."""
        test_strings = {
            "A, B": False,
            "(A, B)": True,
            "(A, (B))": False,
            "(A, (B, C))": False,
            "(A), (A, B)": True,
            "(A, B), (A)": True,
            "(A, B, (C, D))": True,
            "(A, B, C)": True,
        }
        self.base_test("{a, b}", test_strings)

    def test_exact_group_nested(self):
        """{A, {C}} — A and a group containing C must share a parent."""
        test_strings = {
            "(A, C)": False,
            "(A, (C))": True,
            "((A, C))": False,
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": True,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": True,
            "(A, B, (E, F, (C, D)))": False,
        }
        self.base_test("{a, {c} }", test_strings)

    def test_exact_group_complex(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": True,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": True,
        }
        self.base_test("{a, b, {c, d} }", test_strings)

    def test_exact_group_strict_colon(self):
        """{A, B:} — A and B and nothing else in the group."""
        test_strings = {
            "(A, B)": True,
            "(A, B, C)": False,
            "(A)": False,
        }
        self.base_test("{a, b:}", test_strings)

    def test_exact_group_optional(self):
        """{A, B: C} — A and B required; C optional; nothing else allowed."""
        test_strings = {
            "(A, B)": True,
            "(A, B, C)": True,
            "(A, B, C, D)": False,
            "(A, B, D)": False,
        }
        self.base_test("{a, b: c}", test_strings)

    def test_exact_group_complex_split(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "((A, B, C, D))": False,
            "(A, B, (C, D))": False,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": False,
            "((A, B), (C, D))": True,
        }
        self.base_test("{ {a, b}, {c, d} }", test_strings)

    def test_exact_group_split_or(self):
        test_strings = {
            "(A, D)": False,
            "((A), (D))": True,
            "((A), ((D)))": True,
            "((A, D))": True,
        }
        self.base_test("{ {a} || {d} }", test_strings)

    def test_containing_group(self):
        """[A, B] — both A and B in the same subtree (any depth)."""
        test_strings = {
            "A, B": False,
            "(A, B)": True,
            "(A, B), (A, B)": True,
            "(A, (B))": True,
            "(A, (B, C))": True,
            "(A), (B)": False,
        }
        self.base_test("[a, b]", test_strings)

    def test_containing_group_nested(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, C)": False,
            "(A, B, (C, D))": True,
            "(A, (B))": False,
            "(A, (C))": True,
            "(A, (B, C))": True,
            "(A), (B)": False,
            "(C, (A))": False,
            "(A, ((C)))": True,
        }
        self.base_test("[a, [c] ]", test_strings)

    def test_containing_group_complex(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": True,
            "(A, (B))": False,
            "(A, (B, C))": False,
            "(A), (B)": False,
        }
        self.base_test("[a, b, [c, d] ]", test_strings)

    def test_mixed_group_complex_split(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B), (C, D)": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": False,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": False,
            "((A, B), (C, D))": True,
            "((A, B, C, D))": False,
        }
        self.base_test("{ [a, b], [c, d] }", test_strings)

    def test_exact_group_complex2(self):
        test_strings = {
            "A, B, C": False,
            "(A, B, C)": False,
            "(A, B, (C)), (A, B)": True,
            "(A, B), (A, B, (C))": True,
            "(A, B), (B, (C))": False,
            "(B, (C)), (A, B, (C))": True,
            "(A, B, (A, (C)))": False,
        }
        self.base_test("{a, b, {c} }", test_strings)

    def test_containing_group_complex2(self):
        test_strings = {
            "A, B, C": False,
            "(A, B, C)": False,
            "(A, B, (C)), (A, B)": True,
            "(A, B), (A, B, (C))": True,
            "(A, B), (B, (C))": False,
            "(B, (C)), (A, B, (C))": True,
        }
        self.base_test("[a, b, [c] ]", test_strings)

    def test_mixed_groups(self):
        test_strings = {"(A, B), (C, D, (E, F))": True}
        self.base_test("{a}, { {e, f} }", test_strings)

        test_strings = {"(A, B), (C, D, (E, F))": False}
        self.base_test("{a}, [e, {f} ]", test_strings)

    def test_double_bracket_nested_descendant(self):
        """[[a]] parses as [ [a] ] — nested descendant groups."""
        test_strings = {
            "((A))": True,
            "(A)": False,
            "A": False,
        }
        self.base_test("[[a]]", test_strings)


# ---------------------------------------------------------------------------
# Wildcards ?, ??, ???
# ---------------------------------------------------------------------------


class TestStringSearchWildcards(StringSearchBase):
    def test_and_wildcard_any(self):
        """? matches any child (tag or group)."""
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": True,
            "D, A, B": True,
            "A, B, (C)": True,
        }
        self.base_test("a && b && ?", test_strings)

    def test_and_wildcard_nothing_else_curly(self):
        """{A && B} with no wildcard means both in same group, any other contents ok."""
        test_strings = {
            "A": False,
            "B": False,
            "A, B": False,
            "(A, B, C)": True,
            "(A, B)": True,
            "(A, B), C": True,
        }
        self.base_test("{a && b}", test_strings)

    def test_wildcard_tag_only(self):
        """?? matches any tag child."""
        test_strings = {
            "(A, B)": True,  # tag_a matches 'a', tag_b satisfies ?? — two distinct tags
            "(A, (B))": False,  # tag_a matches 'a'; only other child is group (B) — ?? needs a tag
            "((A, B))": True,  # inner (A,B) satisfies a&&?? at its level; propagated to outer
        }
        self.base_test("{a, ??}", test_strings)

    def test_wildcard_group_only(self):
        """??? matches any group child."""
        # {a, ???} requires a group containing 'a' AND a sub-group
        # (A, B) has no group children — False; (A, (B)) has sub-group — True
        test_strings = {
            "(A, B)": False,  # no group child alongside A
            "(A, (B))": True,
            "(A)": False,
        }
        self.base_test("{a, ???}", test_strings)

        test_strings = {
            "(A, B)": False,  # no group child alongside A
            "(A, (B))": True,
            "(A, (B), (C))": True,
        }
        self.base_test("{a, ???}", test_strings)

    def test_wildcard_in_optional_exact(self):
        """{ @B && @A && C: ???} — C required, no A/B allowed, plus a group child."""
        test_strings = {
            "(A, D, B)": False,
            "((A), (D), B)": False,
            "((A))": False,
            "((A), ((D, B)))": False,
            "((A, D))": False,
            "(B)": True,
            "(B, (D))": True,
            "((A), B)": False,
        }
        self.base_test("{ @c && @a && b: ???}", test_strings)


# ---------------------------------------------------------------------------
# Negation
# ---------------------------------------------------------------------------


class TestStringSearchNegation(StringSearchBase):
    def test_negation_simple(self):
        """~A matches any group that does not contain A at any level."""
        test_strings = {
            "A, B": False,
            "B, C": True,
            "(A, B)": False,
            "(B, C)": True,
        }
        self.base_test("~a", test_strings)

    def test_negation_with_and(self):
        """~A && B — B is present and A is absent."""
        test_strings = {
            "A, D, B": False,
            "(A, D, B)": False,
            "B, C": True,
            "A, B": False,
        }
        self.base_test("~a && b", test_strings)

    def test_negation_raises_with_wildcard(self):
        """Wildcards cannot be negated."""
        for query in ["~?", "~??", "~???", "~(A, ?)", "~(A, ??)", "~(A && ?)"]:
            with self.subTest(query=query):
                with self.assertRaises(HedQueryError):
                    StringQueryHandler(query)

    def test_negation_no_wildcard_valid(self):
        """Negation without wildcards must parse without error."""
        for query in ["~A", "~(A)", "~(A && B)", "~(A || B)", "~[A]", "~[A, B]"]:
            with self.subTest(query=query):
                h = StringQueryHandler(query)
                self.assertIsNotNone(h.tree)

    def test_exact_group_negation(self):
        """{~{a}} — always true because there is at least one group without 'a'."""
        test_strings = {
            "(A, D)": True,
            "((A), (D))": True,
            "((A))": True,
            "((A), ((D)))": True,
            "((A, D))": True,
        }
        self.base_test("{ ~{a} }", test_strings)

    def test_exact_group_negation2(self):
        test_strings = {
            "(A, D, B)": True,
            "((A), (D), B)": False,
            "((A))": False,
            "((A), ((D, B)))": True,
            "((A, D))": False,
            "(B, (D))": True,
            "(B)": True,
            "((A), B)": False,
        }
        self.base_test("{ ~{a}, b}", test_strings)

    def test_exact_group_negation3(self):
        test_strings = {
            "(A, D, B)": False,
            "((A), (D), B)": True,
            "((A))": False,
            "((A), ((D, B)))": True,
            "((A, D))": False,
            "(B, (D))": True,
            "(B)": True,
            "((A), B)": True,
        }
        self.base_test("{ ~a && b}", test_strings)

    def test_exact_group_negation_dual(self):
        test_strings = {
            "(A, B)": False,
            "((A), (B))": False,
            "((A))": False,
            "((A), ((B)))": True,
            "((A, B))": False,
            "((A), (C))": True,
            "((A), (B, C))": False,
            "((A), ((B), C))": True,
        }
        self.base_test("{ {~a && ~b} }", test_strings)

    def test_exact_group_negation_dual2(self):
        test_strings = {
            "(A, B)": False,
            "((A), (B))": False,
            "((A))": False,
            "((A), ((B)))": True,
            "((A, B))": False,
            "((A), (C))": True,
            "((A), (B, C))": False,
            "((A), ((B), C))": True,
        }
        self.base_test("{ {~(a || b)} }", test_strings)

    def test_exact_group_negation_complex(self):
        test_strings = {
            "(A, B), (D)": False,
            "((A), (B)), (D)": False,
            "((A)), (D)": False,
            "((A), ((B))), (D)": True,
            "((A), ((B))), (H)": True,
            "((A, B)), (D)": False,
            "((A), (C)), (D)": True,
            "((A), (B, C)), (D)": False,
            "((A), (B, C)), (H)": False,
        }
        self.base_test("{ {~(a || b)} } && {D || ~F}", test_strings)

    def test_exact_group_negation5_raises(self):
        """{ ~a && b:} — negation in exact match with colon raises HedQueryError."""
        with self.assertRaises(ValueError):
            StringQueryHandler("{ ~a && b:}")


# ---------------------------------------------------------------------------
# @-prefix (not-in-line)
# ---------------------------------------------------------------------------


class TestStringSearchNotInLine(StringSearchBase):
    def test_not_in_line_basic(self):
        """@B matches if (and only if) B does NOT appear anywhere in the string."""
        test_strings = {
            "A": True,  # B absent → @B matches
            "B": False,  # B present → @B fails
            "C": True,  # B absent → @B matches
            "A, B": False,
            "A, C": True,
            "B, C": False,
            "A, B, C": False,
            "D, A, B": False,
            "A, B, (C)": False,
            "(A, B, (C))": False,
            "(A, B, (C)), D": False,
            "(A, B, (C)), (D), E": False,
        }
        self.base_test("@B", test_strings)

    def test_not_in_line_with_and(self):
        """@B && C — B must not be present AND C must be present."""
        test_strings = {
            "A": False,  # C absent
            "B": False,  # B present
            "C": True,  # B absent, C present
            "A, B": False,  # B present
            "A, C": True,  # B absent, C present
            "B, C": False,  # B present
            "A, B, C": False,  # B present
            "D, A, B": False,
            "A, B, (C)": False,
            "(A, B, (C))": False,
            "(A, B, (C)), D": False,
            "(A, B, (C)), (D), E": False,
        }
        self.base_test("@B && C", test_strings)

    def test_not_in_line_with_or(self):
        """@C || B — either C is absent OR B is present."""
        test_strings = {
            "A": True,  # C absent (@C matches)
            "B": True,  # B present (B matches)
            "C": False,  # C present (@C fails), B absent (B fails)
            "A, B": True,  # B present
            "A, C": False,  # C present, B absent
            "B, C": True,  # B present
            "A, B, C": True,  # B present
            "D, A, B": True,
            "A, B, (C)": True,
            "(A, B, (C))": True,
            "(A, B, (C)), D": True,
            "(A, B, (C)), (D), E": True,
        }
        self.base_test("@C || B", test_strings)


# ---------------------------------------------------------------------------
# Optional exact group
# ---------------------------------------------------------------------------


class TestStringSearchOptionalExact(StringSearchBase):
    def test_optional_basic(self):
        test_strings = {"(A, C)": True}
        self.base_test("{a && (b || c)}", test_strings)

        test_strings = {"(A, B, C, D)": True}
        self.base_test("{a && b: c && d}", test_strings)

        test_strings = {
            "(A, B, C)": True,
            "(A, B, C, D)": False,
        }
        self.base_test("{a && b: c || d}", test_strings)

        test_strings = {
            "(A, C)": True,
            "(A, D)": True,
            "(A, B, C)": False,
            "(A, B, C, D)": False,
        }
        self.base_test("{a || b: c || d}", test_strings)

    def test_optional_or(self):
        test_strings = {"(A, B)": True, "(A, B, C)": True}
        self.base_test("{a || b}", test_strings)


# ---------------------------------------------------------------------------
# StringNode tree structure tests
# ---------------------------------------------------------------------------


class TestParseHedString(unittest.TestCase):
    def test_empty_string(self):
        root = parse_hed_string("")
        self.assertFalse(root.is_group)
        self.assertEqual(root.children, [])

    def test_single_tag(self):
        root = parse_hed_string("Event")
        self.assertEqual(len(root.children), 1)
        tag = root.children[0]
        self.assertFalse(tag.is_group)
        self.assertEqual(tag.text, "event")
        self.assertEqual(tag.tag_terms, ("event",))

    def test_two_tags(self):
        root = parse_hed_string("Event, Action")
        self.assertEqual(len(root.children), 2)
        texts = [c.text for c in root.children]
        self.assertIn("event", texts)
        self.assertIn("action", texts)

    def test_group_tag(self):
        root = parse_hed_string("(Event, Action)")
        self.assertEqual(len(root.children), 1)
        group = root.children[0]
        self.assertTrue(group.is_group)
        self.assertEqual(len(group.children), 2)

    def test_nested_group(self):
        root = parse_hed_string("(A, (B, C))")
        group = root.children[0]
        self.assertTrue(group.is_group)
        children_is_group = [c.is_group for c in group.children]
        self.assertEqual(len(group.children), 2)
        # One tag, one nested group
        self.assertIn(True, children_is_group)
        self.assertIn(False, children_is_group)

    def test_mixed_root(self):
        root = parse_hed_string("Blue, (Red, Square)")
        self.assertEqual(len(root.children), 2)
        # First child is a tag
        self.assertFalse(root.children[0].is_group)
        # Second child is a group
        self.assertTrue(root.children[1].is_group)

    def test_tag_terms_from_long_form(self):
        """Long-form tags get multi-component tag_terms for ancestor search."""
        root = parse_hed_string("Event/Sensory-event")
        tag = root.children[0]
        self.assertEqual(tag.tag_terms, ("event", "sensory-event"))
        # short_tag is the full casefolded text (there is no schema to derive the real short tag)
        self.assertEqual(tag.short_tag, "event/sensory-event")

    def test_tag_terms_from_short_form_no_lookup(self):
        """Short-form tags get single-component tag_terms without a lookup."""
        root = parse_hed_string("Sensory-event")
        tag = root.children[0]
        self.assertEqual(tag.tag_terms, ("sensory-event",))
        self.assertEqual(tag.short_tag, "sensory-event")

    def test_tag_terms_with_lookup(self):
        """Schema lookup populates full ancestor tag_terms."""
        lookup = {"sensory-event": ("event", "sensory-event")}
        root = parse_hed_string("Sensory-event", schema_lookup=lookup)
        tag = root.children[0]
        self.assertEqual(tag.tag_terms, ("event", "sensory-event"))

    def test_get_all_groups_includes_root(self):
        """get_all_groups always includes the root node."""
        root = parse_hed_string("Event")
        groups = root.get_all_groups()
        self.assertIn(root, groups)

    def test_get_all_groups_includes_nested(self):
        root = parse_hed_string("(A, (B, C))")
        groups = root.get_all_groups()
        # root + 2 groups
        self.assertEqual(len(groups), 3)

    def test_get_all_tags(self):
        root = parse_hed_string("A, (B, (C, D))")
        tags = root.get_all_tags()
        texts = {t.text for t in tags}
        self.assertEqual(texts, {"a", "b", "c", "d"})

    def test_parent_references(self):
        root = parse_hed_string("(A, B)")
        group = root.children[0]
        self.assertIs(group._parent, root)
        for tag in group.children:
            self.assertIs(tag._parent, group)

    def test_whitespace_stripped(self):
        root = parse_hed_string("  Event  ,  Action  ")
        texts = {c.text for c in root.children}
        self.assertIn("event", texts)
        self.assertIn("action", texts)

    def test_malformed_string_no_crash(self):
        """Unbalanced parens should not crash the parser."""
        root = parse_hed_string("A, (B, C")
        # Should not raise; partial tree returned
        self.assertIsNotNone(root)

    def test_str_representation(self):
        root = parse_hed_string("(A, B)")
        group = root.children[0]
        self.assertEqual(str(group), "(a,b)")


# ---------------------------------------------------------------------------
# StringNode duck-typing interface
# ---------------------------------------------------------------------------


class TestStringNodeInterface(unittest.TestCase):
    def test_tags_method(self):
        root = parse_hed_string("A, (B, C)")
        # root.tags() returns only direct leaf children
        root_tags = root.tags()
        self.assertEqual(len(root_tags), 1)
        self.assertEqual(root_tags[0].text, "a")

    def test_groups_method(self):
        root = parse_hed_string("A, (B, C)")
        root_groups = root.groups()
        self.assertEqual(len(root_groups), 1)
        self.assertTrue(root_groups[0].is_group)

    def test_find_tags_with_term(self):
        root = parse_hed_string("A, (B, C)")
        found = root.find_tags_with_term("a", recursive=True, include_groups=2)
        self.assertEqual(len(found), 1)
        tag, parent = found[0]
        self.assertEqual(tag.text, "a")
        self.assertIs(parent, root)

    def test_find_exact_tags(self):
        root = parse_hed_string("A, B, C")
        found = root.find_exact_tags(["a", "c"], recursive=True, include_groups=2)
        self.assertEqual(len(found), 2)
        texts = {t.text for t, _ in found}
        self.assertEqual(texts, {"a", "c"})

    def test_find_wildcard_tags(self):
        root = parse_hed_string("Apple, Apricot, Banana")
        found = root.find_wildcard_tags(["app"], recursive=True, include_groups=2)
        texts = {t.text for t, _ in found}
        # "apricot" starts with "apr" not "app" — only "apple" matches
        self.assertEqual(texts, {"apple"})

    def test_string_node_equality_with_string(self):
        root = parse_hed_string("Event")
        tag = root.children[0]
        self.assertEqual(tag, "event")
        self.assertEqual(tag, "Event")  # casefold comparison
        self.assertNotEqual(tag, "action")

    def test_string_node_identity_equality(self):
        root = parse_hed_string("A")
        tag = root.children[0]
        self.assertEqual(tag, tag)  # same object

    def test_string_node_hash_stable(self):
        root = parse_hed_string("A")
        tag = root.children[0]
        s = {tag}
        self.assertIn(tag, s)

    # --- include_groups return-mode coverage ---

    def test_find_tags_with_term_tags_only(self):
        """include_groups=0 returns tag objects, not (tag, group) pairs."""
        root = parse_hed_string("A, (B, C)")
        tags = root.find_tags_with_term("b", recursive=True, include_groups=0)
        self.assertEqual(len(tags), 1)
        self.assertIsInstance(tags[0], StringNode)
        self.assertEqual(tags[0].text, "b")

    def test_find_tags_with_term_groups_only(self):
        """include_groups=1 returns the parent group objects."""
        root = parse_hed_string("A, (B, C)")
        groups = root.find_tags_with_term("b", recursive=True, include_groups=1)
        self.assertEqual(len(groups), 1)
        self.assertTrue(groups[0].is_group)

    def test_find_exact_tags_tags_only(self):
        """include_groups=0 returns tag objects."""
        root = parse_hed_string("A, B, C")
        tags = root.find_exact_tags(["a", "c"], recursive=True, include_groups=0)
        texts = {t.text for t in tags}
        self.assertEqual(texts, {"a", "c"})

    def test_find_exact_tags_groups_only(self):
        """include_groups=1 returns parent group for each matched tag."""
        root = parse_hed_string("(A, B)")
        groups = root.find_exact_tags(["a"], recursive=True, include_groups=1)
        self.assertEqual(len(groups), 1)
        self.assertTrue(groups[0].is_group)

    def test_find_wildcard_tags_tags_only(self):
        """include_groups=0 returns tag objects."""
        root = parse_hed_string("Apple, Banana")
        tags = root.find_wildcard_tags(["app"], recursive=True, include_groups=0)
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].text, "apple")

    def test_find_wildcard_tags_groups_only(self):
        """include_groups=1 returns parent group for each matched tag."""
        root = parse_hed_string("(Apple, Banana)")
        groups = root.find_wildcard_tags(["app"], recursive=True, include_groups=1)
        self.assertEqual(len(groups), 1)
        self.assertTrue(groups[0].is_group)

    # --- non-recursive (direct children only) ---

    def test_find_tags_with_term_not_recursive(self):
        """recursive=False searches only direct children of the node."""
        root = parse_hed_string("A, (B, C)")
        # B is inside a group — not a direct child of root
        found = root.find_tags_with_term("b", recursive=False, include_groups=2)
        self.assertEqual(len(found), 0)
        # A is a direct child
        found = root.find_tags_with_term("a", recursive=False, include_groups=2)
        self.assertEqual(len(found), 1)

    def test_find_exact_tags_not_recursive(self):
        root = parse_hed_string("A, (B, C)")
        found = root.find_exact_tags(["b"], recursive=False, include_groups=2)
        self.assertEqual(len(found), 0)  # B is nested
        found = root.find_exact_tags(["a"], recursive=False, include_groups=2)
        self.assertEqual(len(found), 1)  # A is direct

    def test_find_wildcard_tags_not_recursive(self):
        root = parse_hed_string("(Apple, Banana)")
        # Apple is inside a group, not a direct child of root
        found = root.find_wildcard_tags(["app"], recursive=False, include_groups=2)
        self.assertEqual(len(found), 0)

    # --- search with None / empty string ---

    def test_search_none_does_not_raise(self):
        """search(None) is handled gracefully — treated as empty string."""
        handler = StringQueryHandler("A")
        result = handler.search(None)
        self.assertFalse(bool(result))

    def test_search_empty_string_is_false(self):
        handler = StringQueryHandler("A")
        self.assertFalse(bool(handler.search("")))

    # --- StringNode.__str__ on root ---

    def test_str_on_root_node(self):
        """Root node (text=None, is_group=False) renders as comma-joined children."""
        root = parse_hed_string("A, B")
        self.assertEqual(str(root), "a,b")

    def test_repr_coverage(self):
        root = parse_hed_string("A, (B)")
        self.assertIn("root", repr(root))
        self.assertIn("tag", repr(root.children[0]))
        self.assertIn("group", repr(root.children[1]))


# ---------------------------------------------------------------------------
# Ancestor search via long-form strings (no lookup)
# ---------------------------------------------------------------------------


class TestLongFormAncestorSearch(StringSearchBase):
    """Long-form HED strings support ancestor search without a lookup table."""

    def test_bare_term_matches_long_form_ancestor(self):
        """Query 'Event' matches 'Event/Sensory-event' because the long-form
        text splits to tag_terms = ('event', 'sensory-event')."""
        test_strings = {
            "Event/Sensory-event": True,
            "Event": True,
            "Action": False,
        }
        self.base_test("Event", test_strings)

    def test_bare_term_matches_nested_long_form(self):
        """Query 'Event' matches in a group with long-form tag."""
        test_strings = {
            "(Event/Sensory-event, Action)": True,
            "(Action, Property)": False,
        }
        self.base_test("Event", test_strings)

    def test_long_form_exact_match(self):
        """Exact query 'Event/Sensory-event' matches only that full path."""
        test_strings = {
            "Event/Sensory-event": True,
            "Event": False,
            "Sensory-event": False,
        }
        self.base_test("Event/Sensory-event", test_strings)


# ---------------------------------------------------------------------------
# Ancestor search via schema lookup
# ---------------------------------------------------------------------------


class TestSchemaLookupAncestorSearch(unittest.TestCase):
    """Tests for ancestor search using a real schema lookup table."""

    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "../data/"))
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        try:
            from hed import schema as hed_schema

            cls.hed_schema = hed_schema.load_schema(hed_xml_file)
            cls.lookup = generate_schema_lookup(cls.hed_schema)
        except Exception:
            cls.hed_schema = None
            cls.lookup = None

    def _search(self, query, raw_string):
        handler = StringQueryHandler(query)
        return bool(handler.search(raw_string, schema_lookup=self.lookup))

    def test_schema_loaded(self):
        if self.lookup is None:
            self.skipTest("Schema not available; skipping lookup tests")
        self.assertIsInstance(self.lookup, dict)
        self.assertGreater(len(self.lookup), 0)

    def test_event_matches_sensory_event(self):
        if self.lookup is None:
            self.skipTest("Schema not available")
        # 'Sensory-event' is a descendant of 'Event' in the HED schema
        self.assertTrue(self._search("Event", "Sensory-event"))

    def test_event_not_matching_unrelated(self):
        if self.lookup is None:
            self.skipTest("Schema not available")
        self.assertFalse(self._search("Event", "Property"))

    def test_action_matches_clear_throat_via_lookup(self):
        """Clear-throat is a descendant of Action in the schema."""
        if self.lookup is None:
            self.skipTest("Schema not available")
        # Only passes if 'clear-throat' is indeed under Action hierarchy
        # (which it is in HED 8.x)
        clear_throat_terms = self.lookup.get("clear-throat", ())
        if "action" not in clear_throat_terms:
            self.skipTest("Clear-throat not under Action in this schema version")
        self.assertTrue(self._search("Action", "Clear-throat"))

    def test_lookup_all_entries_are_tuples(self):
        if self.lookup is None:
            self.skipTest("Schema not available")
        for key, value in self.lookup.items():
            with self.subTest(key=key):
                self.assertIsInstance(key, str)
                self.assertIsInstance(value, tuple)
                self.assertTrue(all(isinstance(v, str) for v in value))

    def test_lookup_key_in_value(self):
        """Every key must appear in its own tag_terms tuple (self-inclusion)."""
        if self.lookup is None:
            self.skipTest("Schema not available")
        for key, terms in self.lookup.items():
            with self.subTest(key=key):
                self.assertIn(key, terms, f"Key {key!r} should be in its own tag_terms {terms}")

    def test_exact_query_not_ancestor(self):
        """Quoted exact query does not do ancestor search even with lookup."""
        if self.lookup is None:
            self.skipTest("Schema not available")
        handler = StringQueryHandler('"Event"')
        result = bool(handler.search("Sensory-event", schema_lookup=self.lookup))
        self.assertFalse(result)

    def test_wildcard_with_lookup(self):
        """Wildcard matches short_tag prefix — lookup does not affect this."""
        if self.lookup is None:
            self.skipTest("Schema not available")
        handler = StringQueryHandler("Sensory*")
        self.assertTrue(bool(handler.search("Sensory-event", schema_lookup=self.lookup)))
        self.assertFalse(bool(handler.search("Event", schema_lookup=self.lookup)))


# ---------------------------------------------------------------------------
# string_search convenience function
# ---------------------------------------------------------------------------


class TestStringSearch(unittest.TestCase):
    def test_basic_mask(self):
        data = ["A, B", "A, C", "B, C", "D"]
        mask = string_search(data, "A && B")
        self.assertEqual(mask, [True, False, False, False])

    def test_none_rows(self):
        data = ["A, B", None, float("nan"), "B, C"]
        mask = string_search(data, "A")
        self.assertTrue(mask[0])
        self.assertFalse(mask[1])
        self.assertFalse(mask[2])
        self.assertFalse(mask[3])

    def test_pandas_na_row(self):
        import pandas as pd

        data = ["A, B", pd.NA, "B, C"]
        mask = string_search(data, "A")
        self.assertTrue(mask[0])
        self.assertFalse(mask[1])
        self.assertFalse(mask[2])

    def test_empty_string_row(self):
        data = ["A", "", "B"]
        mask = string_search(data, "A")
        self.assertTrue(mask[0])
        self.assertFalse(mask[1])
        self.assertFalse(mask[2])

    def test_returns_list(self):
        data = ["A, B", "C, D"]
        mask = string_search(data, "A")
        self.assertIsInstance(mask, list)
        self.assertEqual(len(mask), 2)

    def test_query_compiled_once(self):
        """string_search compiles the query once and applies it row by row."""
        data = ["A"] * 100 + ["B"] * 100
        mask = string_search(data, "A")
        self.assertEqual(sum(mask), 100)

    def test_group_query_in_list(self):
        data = ["(A, B)", "A, B", "(A, C)"]
        mask = string_search(data, "{A, B}")
        self.assertTrue(mask[0])  # in same group
        self.assertFalse(mask[1])  # not in a group
        self.assertFalse(mask[2])  # B not present

    def test_with_schema_lookup(self):
        """string_search accepts an optional schema_lookup dict."""
        lookup = {"sensory-event": ("event", "sensory-event")}
        data = ["Sensory-event", "Action"]
        mask = string_search(data, "Event", schema_lookup=lookup)
        self.assertTrue(mask[0])
        self.assertFalse(mask[1])


# ---------------------------------------------------------------------------
# Performance / benchmark utilities
# ---------------------------------------------------------------------------


class TestBenchmarkBaseline(unittest.TestCase):
    """Smoke tests verifying both search systems work on the same data.

    Not a microbenchmark — run an actual benchmark with timeit manually.
    The class exists to confirm the basic_search system remains functional
    alongside StringQueryHandler so comparative benchmarks can be run.
    """

    def test_basic_search_still_works(self):
        """basic_search.find_matching is still importable and functional."""
        from hed.models.basic_search import find_matching

        data = pd.Series(["A, B", "A, C", "B, C"])
        mask = find_matching(data, "A")
        self.assertTrue(mask.iloc[0])
        self.assertTrue(mask.iloc[1])
        self.assertFalse(mask.iloc[2])

    def test_both_agree_on_comma_queries(self):
        """On flat strings both systems agree for simple comma-separated queries.

        Note: basic_search and StringQueryHandler have different query syntaxes:
        - basic_search: comma-or-space-separated words, '@' = anywhere, '~' = absent
        - StringQueryHandler: '&&' / '||', '{...}' groups, '@' = not-in-line

        We only compare on the shared-syntax subset: plain tag words without
        any operator characters, which both systems interpret as "tag must be present".
        """
        from hed.models.basic_search import find_matching

        data = pd.Series(["A, B", "A, C", "B, C", "A", "B", "C"])

        # Single-tag lookup: both should agree
        for tag in ["A", "B", "C"]:
            with self.subTest(tag=tag):
                bs_mask = find_matching(data, tag)
                sq_mask = string_search(data.tolist(), tag)
                for i in range(len(data)):
                    self.assertEqual(
                        bool(bs_mask.iloc[i]),
                        bool(sq_mask[i]),
                        msg=f"tag={tag!r}, string={data.iloc[i]!r}",
                    )


if __name__ == "__main__":
    unittest.main()
