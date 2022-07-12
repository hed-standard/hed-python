import unittest
from hed.models.hed_string import HedStringFrozen, HedString
from hed.models.hed_string_group import HedStringGroup
from hed.models.expression_parser import TagExpressionParser
import os
from hed import schema


class TestParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/')
        hed_xml_file = os.path.join(cls.base_data_dir, "schema_test_data/HED8.0.0t.xml")
        cls.hed_schema = schema.load_schema(hed_xml_file)

    def base_test(self, parse_expr, search_strings):
        expression = TagExpressionParser(parse_expr)

        # print(f"Search Pattern: {expression._org_string}")
        for string, expected_result in search_strings.items():
            hed_string_frozen = HedStringFrozen(string, self.hed_schema)
            result1 = expression.search_hed_string(hed_string_frozen)
            # print(f"\tSearching string '{str(hed_string)}'")
            # if result:
            #    print(f"\t\tFound as group(s) {str([str(r) for r in result])}")
            self.assertEqual(bool(result1), expected_result)

            # Same test with HedString
            hed_string = HedString(string, self.hed_schema)
            result2 = expression.search_hed_string(hed_string)
            # print(f"\tSearching string '{str(hed_string)}'")
            # if result:
            #    print(f"\t\tFound as group(s) {str([str(r) for r in result])}")
            self.assertEqual(bool(result2), expected_result)

            # Same test with HedStringGroupined
            hed_string_comb = HedStringGroup([hed_string])
            result3 = expression.search_hed_string(hed_string_comb)
            # print(f"\tSearching string '{str(hed_string)}'")
            # if result:
            #    print(f"\t\tFound as group(s) {str([str(r) for r in result])}")
            self.assertEqual(bool(result3), expected_result)

            for r1, r2, r3 in zip(result1, result2, result3):
                # Ensure r2 is only a HedString if r3 is.
                if isinstance(r3, HedStringGroup):
                    self.assertIsInstance(r2, HedString)
                else:
                    self.assertNotIsInstance(r2, HedString)
                self.assertEqual(r2, r3)
            if len(hed_string_frozen.get_all_tags()) == len(hed_string_comb.get_all_tags()):
                self.assertEqual(len(result1), len(result2))

    def test_broken_search_strings(self):
        test_search_strings = [
            "A and",
            "(A and B",
            "and B",
            "A, ",
            ", A",
            "A)"
        ]
        for string in test_search_strings:
            try:
                parser = TagExpressionParser(string)
                self.assertFalse(True)
            except ValueError:
                continue

    def test_finding_tags(self):
        test_strings = {
            "Item, (Clear-throat)": True,
            "(Item, (Clear-throat))": True,
            "Item, Clear-throat": True,
            "Agent, Clear-throat": True,
            "Agent, Event": False,
        }
        self.base_test("(Item or Agent) and Action", test_strings)

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
        self.base_test("(Item or Agent) and [[Action or Event]]", test_strings)

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
        self.base_test("[[a, b]]", test_strings)

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
        self.base_test("[[a, [[c]] ]]", test_strings)

    def test_exact_group_complex(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": True,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": True,
        }
        self.base_test("[[a, b, [[c, d]] ]]", test_strings)

    def test_exact_group_complex_split(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B, C, D)": False,
            "((A, B, C, D))": True,  # todo: should this be true?  Probably not.
            "(A, B, (C, D))": False,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": False,
            "((A, B), (C, D))": True,
        }
        self.base_test("[[ [[a, b]], [[c, d]] ]]", test_strings)

    def test_mixed_group_split(self):
        test_strings = {
            "(A, D)": False,
            "((A), (D))": True,
            "((A), ((D)))": True,
            "((A, D))": True,  # TODO: should this be true?  Probably not.
        }
        self.base_test("[[ [a], [d] ]]", test_strings)

    def test_exact_group_split(self):
        test_strings = {
            "(A, D)": False,
            "((A), (D))": True,
            "((A), ((D)))": False,
            "((A, D))": True,  # TODO: should this be true?  Probably not.
        }
        self.base_test("[[ [[a]], [[d]] ]]", test_strings)

    def test_exact_group_split_or(self):
        test_strings = {
            "(A, D)": False,
            "((A), (D))": True,
            "((A), ((D)))": True,
            "((A, D))": True,
        }
        self.base_test("[[ [[a]] or [[d]] ]]", test_strings)

    def test_exact_group_split_or_negation(self):
        test_strings = {
            "(A, D)": False,
            "((A), (D))": True,
            "((A))": False,
            "((A), ((D)))": True,
            "((A, D))": False,
        }
        self.base_test("[[ [[~a]] ]]", test_strings)

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
        self.base_test("[[ [[~a and ~b]] ]]", test_strings)

    def test_exact_group_split_or_negation_dual2(self):
        test_strings = {
            "(A, B)": False,
            "((A), (B))": False,
            "((A))": False,
            "((A), ((B)))": True, # TODO: must all result groups have tags?  True because of ((B)) group with no tags.
            "((A, B))": False,
            "((A), (C))": True,
            "((A), (B, C))": False,
            "((A), ((B), C))": True,
        }
        self.base_test("[[ [[~(a or b)]] ]]", test_strings)

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
        self.base_test("[[ [[~(a or b)]] ]] and [[D or ~F]]", test_strings)

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
        self.base_test("[[ ~[[a]] ]]", test_strings)

    def test_exact_group_negation2(self):
        test_strings = {
            "(A, D, B)": True,
            "((A), (D), B)": False,
            "((A))": False,
            "((A), ((D, B)))": True,
            "((A, D))": False,
            "(B, (D))": True,
            "(B)": True
        }
        self.base_test("[[ ~[[a]], b]]", test_strings)

    def test_mixed_group_complex_split(self):
        test_strings = {
            "A, B, C, D": False,
            "(A, B), (C, D)": False,
            "(A, B, C, D)": False,
            "(A, B, (C, D))": False,
            "(A, B, ((C, D)))": False,
            "(E, F, (A, B, (C, D)))": True,
            "((A, B), (C, D))": True,
            "((A, B, C, D))": True,  # TODO: should this be true?  Probably not.
        }
        self.base_test("[[ [a, b], [c, d] ]]", test_strings)

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
        self.base_test("[[a, b, [[c]] ]]", test_strings)

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
        self.base_test("[[a]], [[ [[e, f]] ]]", test_strings)

        # This example works because it finds the group containing (c, d, (e, f)), rather than the ef group
        self.base_test("[[a]], [e, [[f]] ]", test_strings)

    def test_and_or(self):
        test_strings = {
            "A": False,
            "B": False,
            "C": True,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a and b or c", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": True,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("(a and b) or c", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": False
        }
        self.base_test("a and (b or c)", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a or b and c", test_strings)

        test_strings = {
            "A": True,
            "B": False,
            "C": False,
            "A, B": True,
            "A, C": True,
            "B, C": True
        }
        self.base_test("a or (b and c)", test_strings)

        test_strings = {
            "A": False,
            "B": False,
            "C": False,
            "A, B": False,
            "A, C": True,
            "B, C": True
        }
        self.base_test("(a or b) and c", test_strings)

    def test_logical_negation(self):
        expression = TagExpressionParser("~a")
        hed_string = HedStringFrozen("A")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), False)
        hed_string = HedStringFrozen("B")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), True)

        expression = TagExpressionParser("~a and b")
        hed_string = HedStringFrozen("A")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), False)
        hed_string = HedStringFrozen("B")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), True)
        hed_string = HedStringFrozen("A, B")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), False)

        expression = TagExpressionParser("~( (a or b) and c)")
        hed_string = HedStringFrozen("A")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), True)
        hed_string = HedStringFrozen("B")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), True)
        hed_string = HedStringFrozen("C")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), True)
        hed_string = HedStringFrozen("A, B")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), True)
        hed_string = HedStringFrozen("A, C")
        self.assertEqual(bool(expression.search_hed_string(hed_string)), False)
