import unittest
from hed.models.hed_string import HedString
from hed.models.query_handler import QueryHandler
import os
from hed import schema
from hed import HedTag


# Override the tag terms function for testing purposes when we don't have a schema
def new_init(self, *args, **kwargs):
    old_tag_init(self, *args, **kwargs)
    if not self.tag_terms:
        self.tag_terms = (str(self).lower(),)


old_tag_init = HedTag.__init__
HedTag.__init__ = new_init


class TestParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_data_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '../data/'))
        cls.base_data_dir = base_data_dir
        hed_xml_file = os.path.join(base_data_dir, "schema_tests/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)

    def base_test(self, parse_expr, search_strings):
        expression = QueryHandler(parse_expr)

        # print(f"Search Pattern: {expression._org_string} - {str(expression.tree)}")
        for string, expected_result in search_strings.items():
            hed_string = HedString(string, self.hed_schema)
            result2 = expression.search(hed_string)
            # print(f"\tSearching string '{str(hed_string)}'")
            # if result2:
            #    print(f"\t\tFound as group(s) {str([str(r) for r in result2])}")
            self.assertEqual(bool(result2), expected_result)

    def test_broken_search_strings(self):
        test_search_strings = [
            "A &&",
            "(A && B",
            "&& B",
            "A, ",
            ", A",
            "A)"
        ]
        for string in test_search_strings:
            with self.assertRaises(ValueError) as context:
                QueryHandler(string)
            self.assertTrue(context.exception.args[0])

    def test_finding_tags(self):
        test_strings = {
            "Item, (Clear-throat)": True,
            "(Item, (Clear-throat))": True,
            "Item, Clear-throat": True,
            "Agent, Clear-throat": True,
            "Agent, Event": False,
        }
        self.base_test("(Item || Agent) && Action", test_strings)

    def test_finding_tags_wildcards(self):
        test_strings = {
            "Def/Def1": True,
            "Def/Def2": True,
            "Def/Def1/Value": True,
        }
        self.base_test("Def", test_strings)
        test_strings = {
            "Def/Def1": True,
            "Def/Def2": True,
            "Def/Def1/Value": True,
        }
        self.base_test("Def/Def*", test_strings)
        test_strings = {
            "Def/Def1": True,
            "Def/Def2": False,
            "Def/Def1/Value": False,
        }
        self.base_test("Def/Def1", test_strings)
        test_strings = {
            "Def/Def1": True,
            "Def/Def2": False,
            "Def/Def1/Value": True,
        }
        self.base_test("Def/Def1*", test_strings)
        test_strings = {
            "Def/Def1": False,
            "Def/Def2": False,
            "Def/Def1/Value": True,
        }
        self.base_test("Def/Def1/*", test_strings)

    def test_exact_term(self):
        test_strings = {
            "Event": True,
            "Sensory-event": False,
            "Event/ext": False
        }
        self.base_test('"Event"', test_strings)

    def test_actual_wildcard(self):
        test_strings = {
            "A, B, C": True,
            "A, B": True,
            "A, B, (C)": True,
        }
        self.base_test("A, B", test_strings)

    def test_finding_tags2(self):
        test_strings = {
            "Item, (Clear-throat)": True,
            "(Item, (Clear-throat))": True,
            "Item, Clear-throat": False,
            "Agent, Clear-throat": False,
            "Agent, Event": False,
            "Agent, (Event)": True,
            "(Item), (Event)": True
        }
        self.base_test("(Item || Agent) && {Action || Event}", test_strings)

    def test_exact_group(self):
        test_strings = {
            "A, B": False,
            "(A, B)": True,
            "(A, (B))": False,
            "(A, (B, C))": False,
            "(A), (A, B)": True,
            "(A, B), (A)": True,
            "(A, B, (C, D))": True,
            "(A, B, C)": True
        }
        self.base_test("{a, b}", test_strings)

    def test_exact_group_simple_complex(self):
        test_strings = {
            "(A, C)": False,
            "(A, (C))": True,
            "((A, C))": False,
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": True,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": True,
            "(A, B, (E, F, (C, D)))": False,  # TODO: Should this be True?  [[c]] isn't directly inside an a group.
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

    def test_duplicate_search(self):
        test_strings = {
            "(Event)": False,
            "(Event, Agent-action)": True,

        }
        self.base_test("Event && Event", test_strings)

    def test_duplicate_search_or(self):
        test_strings = {
            "(Event)": True,
            "(Event, Agent-action)": True,

        }
        self.base_test("Event || Event", test_strings)

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

    def test_mixed_group_split(self):
        test_strings = {
            "(Event, Clear-throat)": False,
            "((Event), (Clear-throat))": True,
            "((Event), ((Clear-throat)))": True,
            "((Event, Clear-throat))": False,
        }
        self.base_test("{ [Event], [Action] }", test_strings)

    def test_exact_group_split(self):
        test_strings = {
            "(Event, Clear-throat)": False,
            "((Event), (Clear-throat))": True,
            "((Event), ((Clear-throat)))": False,
            "((Event, Clear-throat))": False,
        }
        self.base_test("{ {Event}, {Action} }", test_strings)

    def test_exact_group_split_or(self):
        test_strings = {
            "(A, D)": False,
            "((A), (D))": True,
            "((A), ((D)))": True,
            "((A, D))": True,
        }
        self.base_test("{ {a} || {d} }", test_strings)

    def test_exact_group_split_or_negation(self):
        test_strings = {
            # "(Event, Clear-throat)": False,
            "((Event), (Clear-throat))": True,
            "((Event))": False,
            "((Event), ((Clear-throat)))": True,
            "((Event, Clear-throat))": False,
        }
        # Need to think this through more.  How do you exact match a negative tag?
        self.base_test("{ {~Event} }", test_strings)

    def test_exact_group_split_or_negation_dual(self):
        test_strings = {
            "(A, B)": False,
            "((A), (B))": False,
            "((A))": False,
            "((A), ((B)))": True,  # TODO: must all result groups have tags?  True because of ((B)) group with no tags.
            "((A, B))": False,
            "((A), (C))": True,
            "((A), (B, C))": False,
            "((A), ((B), C))": True,
        }
        self.base_test("{ {~a && ~b} }", test_strings)

    def test_exact_group_split_or_negation_dual2(self):
        test_strings = {
            "(A, B)": False,
            "((A), (B))": False,
            "((A))": False,
            "((A), ((B)))": True,  # TODO: must all result groups have tags?  True because of ((B)) group with no tags.
            "((A, B))": False,
            "((A), (C))": True,
            "((A), (B, C))": False,
            "((A), ((B), C))": True,
        }
        self.base_test("{ {~(a || b)} }", test_strings)

    def test_exact_group_split_or_negation_complex(self):
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

    # TODO: Should this work, and what should it mean?
    # Right now this is always true, since there is at least one group without ", (a)" in every string.
    def test_exact_group_negation(self):
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
            "((A), B)": False
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
            "((A), B)": True
        }
        self.base_test("{ ~a && b}", test_strings)

    def test_exact_group_negation4(self):
        test_strings = {
            "(A, D, B)": False,
            "((A), (D), B)": False,
            "((A))": False,
            "((A), ((D, B)))": False,
            "((A, D))": False,
            "(B)": True,
            "(B, (D))": True,
            "((A), B)": False
        }
        self.base_test("{ @c && @a && b: ???}", test_strings)

    def test_exact_group_negation5(self):
        test_string = "{ ~a && b:}"
        with self.assertRaises(ValueError) as context:
            QueryHandler(test_string)
        self.assertTrue(context.exception.args[0])

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
            "(A, B, (A, (C)))": False
        }
        self.base_test("{a, b, {c} }", test_strings)

    def test_containing_group_complex2(self):
        test_strings = {
            "A, B, C": False,
            "(A, B, C)": False,
            "(A, B, (C)), (A, B)": True,
            "(A, B), (A, B, (C))": True,
            "(A, B), (B, (C))": False,
            "(B, (C)), (A, B, (C))": True
        }
        self.base_test("[a, b, [c] ]", test_strings)

    def test_containing_group(self):
        test_strings = {
            "A, B": False,
            "(A, B)": True,
            "(A, B), (A, B)": True,
            "(A, (B))": True,
            "(A, (B, C))": True,
            "(A), (B)": False
        }
        self.base_test("[a, b]", test_strings)

    def test_containing_group_simple_complex(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, C)": False,
            "(A, B, (C, D))": True,
            "(A, (B))": False,
            "(A, (C))": True,
            "(A, (B, C))": True,
            "(A), (B)": False,
            "(C, (A))": False,
            "(A, ((C)))": True
        }
        self.base_test("[a, [c] ]", test_strings)

    def test_containing_group_complex(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": True,
            "(A, (B))": False,
            "(A, (B, C))": False,
            "(A), (B)": False
        }
        self.base_test("[a, b, [c, d] ]", test_strings)

    def test_mixed_groups(self):
        test_strings = {
            "(A, B), (C, D, (E, F))": True
        }
        self.base_test("{a}, { {e, f} }", test_strings)

        test_strings = {
            "(A, B), (C, D, (E, F))": False
        }
        # This example works because it finds the group containing (c, d, (e, f)), rather than the ef group
        self.base_test("{a}, [e, {f} ]", test_strings)

    def test_and(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": False,
            "B, C": False
        }
        self.base_test("a && b", test_strings)

    def test_or(self):
        test_strings = {
            "A": True,
            "B": True,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a || b", test_strings)

    def test_and_wildcard(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": True,
            "D, A, B": True,
            "A, B, (C)": True
        }
        self.base_test("a && b && ?", test_strings)

    def test_and_wildcard_nothing_else(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": False,
            "D, A, B": False,
            "A, B, (C)": False,
            "(A, B), C": True,
            "(A, B, C)": True,
        }
        self.base_test("{a && b}", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": False,
            "D, A, B": False,
            "A, B, (C)": False,
            "(A, B), C": True,
            "(A, B, C)": False,
        }
        self.base_test("{a && b:}", test_strings)

    def test_and_logical_wildcard(self):
        test_strings = {
            "A": False,
            "A, B": False,
            "A, B, (C)": True,
            "A, B, C": True,
        }
        self.base_test("(A, B) && ?", test_strings)
        self.base_test("A, B && ?", test_strings)

        test_strings = {
            "A": True,
            "A, C": True,
            "A, B, C": True,
            "B, C": False,
            "B, C, D, E": True
        }
        self.base_test("(a || (b && c) && ?)", test_strings)

        self.base_test("(a || (b && c && ?) && ?)", test_strings)

    def test_double_wildcard(self):
        test_strings = {
            "A": False,
            "A, B, (C)": True,
            "A, B, C": True,
            "A, (B), (C)": False,
        }
        self.base_test("A && ? && ??", test_strings)

    def test_or_wildcard(self):
        test_strings = {
            "A": True,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": True,
            "A, B, C": True,
            "D, A, B": True,
            "A, B, (C)": True
        }
        self.base_test("a || b, ?", test_strings)

    def test_and_wildcard_tags(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": True,
            "D, A, B": True,
            "A, B, (C)": False
        }
        self.base_test("a && b, ??", test_strings)

    def test_and_wildcard_groups(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": False,
            "D, A, B": False,
            "A, B, (C)": True
        }
        self.base_test("a && b, ???", test_strings)

    def test_complex_wildcard_groups(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": False,
            "D, A, B": False,
            "A, B, (C)": False,
            "(A, B, (C))": False,
            "(A, B, (C)), D": True,
            "(A, B, (C)), (D)": True,
            "((A, B), (C)), E": False,  # todo: should discuss this case.  Is this correct to be False?
            "((A, B), C), E": False,
        }
        self.base_test("[a && b, ???], ?", test_strings)

    def test_wildcard_new(self):
        # todo: does it make sense this behavior varies?  I think so
        test_strings = {
            "((A, B), C)": False,
        }
        self.base_test("[a && b, ???]", test_strings)

        test_strings = {
            "((A, B), C)": False,
        }
        self.base_test("[a && b && c]", test_strings)

    def test_complex_wildcard_groups2(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": False,
            "B, C": False,
            "A, B, C": False,
            "D, A, B": False,
            "A, B, (C)": False,
            "(A, B, (C))": False,
            "(A, B, (C)), D": False,
            "(A, B, (C)), (D), E": True,
        }
        self.base_test("[a && b, ???], E, ?", test_strings)

    def test_and_or(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": True,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a && b || c", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": True,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("(a && b) || c", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": False
        }
        self.base_test("a && (b || c)", test_strings)

        test_strings = {
            "A": True,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a || b && c", test_strings)

        test_strings = {
            "A": True,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a || (b && c)", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": True,
            "B, C": True
        }
        self.base_test("(a || b) && c", test_strings)

    def test_logical_negation(self):
        expression = QueryHandler("~a")
        hed_string = HedString("A", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), False)
        hed_string = HedString("B", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), True)

        expression = QueryHandler("~a && b")
        hed_string = HedString("A", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), False)
        hed_string = HedString("B", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), True)
        hed_string = HedString("A, B", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), False)

        expression = QueryHandler("~( (a || b) && c)")
        hed_string = HedString("A", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), True)
        hed_string = HedString("B", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), True)
        hed_string = HedString("C", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), True)
        hed_string = HedString("A, B", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), True)
        hed_string = HedString("A, C", self.hed_schema)
        self.assertEqual(bool(expression.search(hed_string)), False)

    def test_not_in_line(self):
        test_strings = {
            "A": True,
            "B": False,
            "C": True,
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

    def test_not_in_line2(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": True,
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
        self.base_test("@B && C", test_strings)

    def test_not_in_line3(self):
        test_strings = {
            "A": True,
            "B": True,
            "C": False,
            "A, B": True,
            "A, C": False,
            "B, C": True,
            "A, B, C": True,
            "D, A, B": True,
            "A, B, (C)": True,
            "(A, B, (C))": True,
            "(A, B, (C)), D": True,
            "(A, B, (C)), (D), E": True,
        }
        self.base_test("@C || B", test_strings)

    def test_optional_exact_group(self):
        test_strings = {
            "(A, C)": True,
        }
        self.base_test("{a && (b || c)}", test_strings)

        test_strings = {
            "(A, B, C, D)": True,
        }
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

        test_strings = {
            "(Onset, (Def-expand/taco))": True,
            "(Onset, Def-expand/taco)": False,
            "(Onset, Def/taco, (Def-expand/taco))": True,  # this one validates
            "(Onset, (Def/taco))": False,
            "(Onset, (Def-expand/taco, (Label/DefContents)))": True,
            "(Onset, (Def-expand/taco), (Label/OnsetContents))": True,
            "(Onset, (Def-expand/taco), (Label/OnsetContents, Description/MoreContents))": True,
            "Onset, (Def-expand/taco), (Label/OnsetContents)": False,
            "(Onset, (Def-expand/taco), Label/OnsetContents)": False,
        }
        self.base_test("{(Onset || Offset), (Def || {Def-expand}): ???}", test_strings)
        test_strings = {
            "(A, B)": True,
            "(A, B, C)": True
        }
        self.base_test("{a || b}", test_strings)
