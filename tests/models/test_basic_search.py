import unittest
import pandas as pd
from hed import load_schema_version

import os
from hed import TabularInput
from hed.models import basic_search
from hed.models.basic_search import find_words, check_parentheses, reverse_and_flip_parentheses, \
    construct_delimiter_map, verify_search_delimiters, find_matching
import numpy as np
from hed.models.df_util import convert_to_form


class TestNewSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../data/bids_tests/eeg_ds003645s_hed'))
        sidecar1_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.events_path = os.path.realpath(
            os.path.join(bids_root_path, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        cls.base_input = TabularInput(cls.events_path, sidecar1_path)
        cls.schema = load_schema_version("8.3.0")
        cls.df = cls.base_input.series_filtered

    def test_find_matching_results(self):
        result1 = basic_search.find_matching(self.df, "(Face, Item-interval/1)")
        result2 = basic_search.find_matching(self.df, "(Face, Item-interval/1*)")

        self.assertTrue(np.sum(result1) > 0, "result1 should have some true values")
        self.assertTrue(np.sum(result2) > 0, "result2 should have some true values")
        self.assertTrue(np.sum(result1) < np.sum(result2), "result1 should have fewer true values than result2")

        # Verify we get the same results in both tag forms
        df_copy = self.df.copy()
        convert_to_form(df_copy, self.schema, "long_tag")

        result1b = basic_search.find_matching(self.df, "(Face, Item-interval/1)")
        result2b = basic_search.find_matching(self.df, "(Face, Item-interval/1*)")

        self.assertTrue(np.sum(result1b) > 0, "result1 should have some true values")
        self.assertTrue(np.sum(result2b) > 0, "result2 should have some true values")
        self.assertTrue(np.sum(result1b) < np.sum(result2b), "result1 should have fewer true values than result2")
        self.assertTrue(result1.equals(result1b))
        self.assertTrue(result2.equals(result2b))

        convert_to_form(df_copy, self.schema, "short_tag")

        result1b = basic_search.find_matching(self.df, "(Face, Item-interval/1)")
        result2b = basic_search.find_matching(self.df, "(Face, Item-interval/1*)")

        self.assertTrue(np.sum(result1b) > 0, "result1 should have some true values")
        self.assertTrue(np.sum(result2b) > 0, "result2 should have some true values")
        self.assertTrue(np.sum(result1b) < np.sum(result2b), "result1 should have fewer true values than result2")
        self.assertTrue(result1.equals(result1b))
        self.assertTrue(result2.equals(result2b))


class TestFindWords(unittest.TestCase):
    def test_basic(self):
        search_string = "@global (local1, local2)"
        anywhere_words, _, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['global'])
        self.assertEqual(specific_words, ['local1', 'local2'])

    def test_no_anywhere_words(self):
        search_string = "(local1, local2)"
        anywhere_words, _, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, [])
        self.assertEqual(specific_words, ['local1', 'local2'])

    def test_no_specific_words(self):
        search_string = "@global1, @global2"
        anywhere_words, _, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['global1', 'global2'])
        self.assertEqual(specific_words, [])

    def test_empty_string(self):
        search_string = ""
        anywhere_words, _, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, [])
        self.assertEqual(specific_words, [])

    def test_mixed_words(self):
        search_string = "@global (local1, local2), @another_global"
        anywhere_words, _, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['global', 'another_global'])
        self.assertEqual(specific_words, ['local1', 'local2'])

    def test_whitespace(self):
        search_string = " @Global ,  ( local1 , local2 ) "
        anywhere_words, _, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['Global'])
        self.assertEqual(specific_words, ['local1', 'local2'])


class TestCheckParentheses(unittest.TestCase):
    def test_balanced_parentheses(self):
        self.assertEqual(check_parentheses("(())"), "")
        self.assertEqual(check_parentheses("(someText())"), "")
        self.assertEqual(check_parentheses("((some)text())"), "")
        self.assertEqual(check_parentheses("()"), "")

    def test_unbalanced_parentheses(self):
        self.assertEqual(check_parentheses("(()"), "(")
        self.assertEqual(check_parentheses("()someText("), "(")
        self.assertEqual(check_parentheses("(text)text)"), ")")
        self.assertEqual(check_parentheses("text)"), ")")

    def test_mixed_parentheses(self):
        self.assertEqual(check_parentheses("(()(())"), "(")
        self.assertEqual(check_parentheses("(someText))((someText)"), ")(")
        self.assertEqual(check_parentheses("((someText))someText"), "")
        self.assertEqual(check_parentheses("(someText(someText))someText"), "")

    def test_special_cases(self):
        self.assertEqual(check_parentheses(""), "")
        self.assertEqual(check_parentheses("abc"), "")
        self.assertEqual(check_parentheses("((()))("), "(")
        self.assertEqual(check_parentheses("text"), "")

    def test_reverse_and_flip_parentheses(self):
        self.assertEqual(reverse_and_flip_parentheses("(abc)"), "(cba)")
        self.assertEqual(reverse_and_flip_parentheses("Hello()"), "()olleH")
        self.assertEqual(reverse_and_flip_parentheses(")("), ")(")
        self.assertEqual(reverse_and_flip_parentheses("((()))"), "((()))")
        self.assertEqual(reverse_and_flip_parentheses("()()()"), "()()()")
        self.assertEqual(reverse_and_flip_parentheses("abc"), "cba")
        self.assertEqual(reverse_and_flip_parentheses("123(abc)321"), "123(cba)321")
        self.assertEqual(reverse_and_flip_parentheses("a(bc)d"), "d(cb)a")


class TestConstructDelimiterMap(unittest.TestCase):
    def test_empty_text(self):
        self.assertEqual(construct_delimiter_map("", ["word1", "word2"]), {})

    def test_empty_words(self):
        self.assertEqual(construct_delimiter_map("word1,word2", []), {})

    def test_single_occurrence(self):
        text = "word1,word2"
        expected_result = {
            ("word1", "word2"): "",
            ("word2", "word1"): ""
        }
        self.assertEqual(construct_delimiter_map(text, ["word1", "word2"]), expected_result)

    def test_multiple_words(self):
        text = "word0,((word1),word2)"
        expected_result = {
            ("word0", "word1"): "((",
            ("word0", "word2"): "(",
            ("word1", "word0"): "))",
            ("word1", "word2"): ")",
            ("word2", "word1"): "(",
            ("word2", "word0"): ")"
        }
        self.assertEqual(construct_delimiter_map(text, ["word0", "word1", "word2"]), expected_result)

        text = "word0 , ( (word1 ), word2)"
        self.assertEqual(construct_delimiter_map(text, ["word0", "word1", "word2"]), expected_result)


class TestVerifyDelimiters(unittest.TestCase):
    def base_verify_func(self, query_text, text, specific_words, expected_result):
        delimiter_map = construct_delimiter_map(query_text, specific_words)
        actual_result = verify_search_delimiters(text, specific_words, delimiter_map)
        self.assertEqual(actual_result, expected_result)

    def test_all_conditions_met(self):
        query_text = "word0,((word1),word2)"
        specific_words = ["word0", "word1", "word2"]
        text = "word0,((word1),word2)"
        self.base_verify_func(query_text, text, specific_words, True)
        text = "((word1),word2), word0"
        self.base_verify_func(query_text, text, specific_words, True)
        text = "word0,(word2, (word1))"
        self.base_verify_func(query_text, text, specific_words, True)
        text = "word0,((word1),(ExtraGroup),word2)"
        self.base_verify_func(query_text, text, specific_words, True)
        text = "word0,((word2),word1)"
        self.base_verify_func(query_text, text, specific_words, False)
        text = "((word1),word0), word2"
        self.base_verify_func(query_text, text, specific_words, False)
        text = "word0,((word1))"
        self.base_verify_func(query_text, text, specific_words, False)
        text = "(word1),(ExtraGroup),word2)"
        self.base_verify_func(query_text, text, specific_words, False)

    def test_wildcard_matching_verify_delimiters(self):
        query_text = "word0, ((word1.*?)), word2.*?"
        delimiter_map = construct_delimiter_map(query_text, ["word0", "word1.*?", "word2.*?"])

        # Positive test cases
        text = "((word1)), word0, word2X"
        self.assertTrue(verify_search_delimiters(text, ["word0", "word1.*?", "word2.*?"], delimiter_map))

        text = "word0, ((word1Y)), word2Z"
        self.assertTrue(verify_search_delimiters(text, ["word0", "word1.*?", "word2.*?"], delimiter_map))

        # Negative test cases
        text = "word0, (word1), word2"
        self.assertFalse(verify_search_delimiters(text, ["word0", "word1.*?", "word2.*?"], delimiter_map))


class TestFindMatching(unittest.TestCase):
    def base_find_matching(self, series, search_string, expected):
        mask = find_matching(series, search_string)
        self.assertTrue(all(mask == expected), f"Expected {expected}, got {mask}")

    def test_basic_matching(self):
        series = pd.Series([
            "word0, word1, word2",
            "word0, (word1, word2)"
        ])
        search_string = "word0, word1"
        expected = pd.Series([True, True])
        self.base_find_matching(series, search_string, expected)
        search_string = "(word0, word1)"
        expected = pd.Series([True, False])
        self.base_find_matching(series, search_string, expected)

    def test_group_matching(self):
        series = pd.Series([
            "(word1), word0, ((word2))",
            "word0, ((word1)), word2",
            "(word1), word0, (word2)"
        ])
        search_string = "word0, ((word1)), word2"
        expected = pd.Series([False, True, False])
        self.base_find_matching(series, search_string, expected)

    def test_anywhere_words(self):
        series = pd.Series([
            "(word1), word0, ((word2))",
            "word0, ((word1)), word2",
            "word0, (word3), ((word1)), word2"
        ])
        search_string = "@word3, word0, ((word1)), word2"
        expected = pd.Series([False, False, True])
        self.base_find_matching(series, search_string, expected)

    def test_mismatched_parentheses(self):
        series = pd.Series([
            "(word1), word0, ((word2))",
            "word0, ((word1)), word2",
            "word0, (word1)), word2",
            "word0, ((word1), word2"
        ])
        search_string = "word0, ((word1)), word2"
        expected = pd.Series([False, True, False, False])
        self.base_find_matching(series, search_string, expected)

    def test_wildcard_matching(self):
        series = pd.Series([
            "word2, word0, ((word1X))",
            "word0, ((word1Y)), word2Z",
            "word0, ((word1)), word2",
            "word0, (word1), word2"
        ])
        search_string = "word0, ((word1*)), word2*"
        expected = pd.Series([True, True, True, False])
        self.base_find_matching(series, search_string, expected)

    def test_complex_case_with_word_identifiers(self):
        query_text = "word0, ((word1), @word2, @word3, word4)"
        series = pd.Series([
            "word0, ((word1), word2, word3, word4)",
            "word2, word0, ((word1), word3, word4)",
            "word3, ((word1), word2, word4), word0",
            "word0, ((word1), word4), word2, word3",
            "word0, word1, word4, word2",
            "word2, word3"
        ])
        expected = pd.Series([True, True, True, True, False, False])

        self.base_find_matching(series, query_text, expected)

    def test_very_complex_case_with_word_identifiers(self):
        query_text = "word0, (((word1, word2), @word3)), ((word4, word5)))"
        series = pd.Series([
            "word0, (((word1, word2), word3)), ((word4, word5)))",
            "word3, word0, (((word1, word2))), ((word4, word5)))",
            "word0, ((word1, word2), word3), (word4, word5)",
            "word0, (((word1, word2), word3)), (word4)",
            "word0, (((word1, word2))), ((word4, word5)))"
        ])
        expected = pd.Series([True, True, False, False, False])

        self.base_find_matching(series, query_text, expected)

    def test_incorrect_single_delimiter(self):
        query_text = "word0, ((word1)), word2"
        series = pd.Series([
            "word0, ((word1)), word2",
            "(word0, ((word1)), word2)",
            "word0, ((word1), word2)",
            "word0, (word1)), word2"
        ])
        expected = pd.Series([True, True, False, False])
        self.base_find_matching(series, query_text, expected)

    def test_mismatched_parentheses2(self):
        query_text = "word0, ((word1)), (word2, word3)"
        series = pd.Series([
            "word0, ((word1)), (word2, word3)",
            "(word2, word3), word0, ((word1))",
            "word0, someExtraText, ((word1)), someMoreText, (word2, word3)",
            "word0, ((word1), (word2, word3))",
            "word0, ((word1), ((word2, word3)"
        ])
        expected = pd.Series([True, True, True, False, False])
        self.base_find_matching(series, query_text, expected)

    def test_negative_words(self):
        series = pd.Series([
            "word0, word1",
            "word0, word2",
            "word0, word2, word3",
            "word0, (word1), word2",
            "word0, (word2, word3), word1",
            "word0, word1suffix",
        ])

        # 1. Basic Negative Test Case
        search_string1 = "~word1, word0"
        expected1 = pd.Series([False, True, True, False, False, True])

        # 2. Two Negative Words
        search_string2 = "~word1, ~word3, word0"
        expected2 = pd.Series([False, True, False, False, False, True])

        # 3. Combination of Negative and Mandatory Words
        search_string3 = "@word2, ~word1, word0"
        expected3 = pd.Series([False, True, True, False, False, False])

        # 4. Negative Words with Wildcards
        search_string4 = "word0, ~word1*"
        expected4 = pd.Series([False, True, True, False, False, False])

        # Running tests
        self.base_find_matching(series, search_string1, expected1)
        self.base_find_matching(series, search_string2, expected2)
        self.base_find_matching(series, search_string3, expected3)
        self.base_find_matching(series, search_string4, expected4)

    def test_negative_words_group(self):
        series = pd.Series([
            "word0, (word1, (word2))",
            "word0, (word1, (word2)), word3",
            "word0, (word1, (word2), word3)",
            "word0, (word1, (word2, word3))",
            ])
        search_string = "word0, (word1, (word2))"
        expected = pd.Series([True, True, True, True])
        self.base_find_matching(series, search_string, expected)

        search_string = "word0, (word1, (word2)), ~word3"
        expected = pd.Series([True, False, False, False])
        self.base_find_matching(series, search_string, expected)

        search_string = "word0, (word1, (word2), ~word3)"
        expected = pd.Series([True, False, False, False])
        self.base_find_matching(series, search_string, expected)
