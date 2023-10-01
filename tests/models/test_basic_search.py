import unittest
import pandas as pd
from hed import load_schema_version

import os
from hed import TabularInput
from hed.models import df_util, basic_search
from hed.models.basic_search import find_words, check_parentheses, reverse_and_flip_parentheses, \
    construct_delimiter_map, verify_search_delimiters, find_matching
import numpy as np


class TestNewSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bids_root_path = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                                       '../data/bids_tests/eeg_ds003645s_hed'))
        sidecar1_path = os.path.realpath(os.path.join(bids_root_path, 'task-FacePerception_events.json'))
        cls.events_path = os.path.realpath(
            os.path.join(bids_root_path, 'sub-002/eeg/sub-002_task-FacePerception_run-1_events.tsv'))
        cls.base_input = TabularInput(cls.events_path, sidecar1_path)
        cls.schema = load_schema_version()
        cls.df = cls.base_input.series_filtered

    def test_find_matching_results(self):
        result1 = basic_search.find_matching(self.df, "(Face, Item-interval/1)")
        result2 = basic_search.find_matching(self.df, "(Face, Item-interval/1*)")

        # Add assertions
        self.assertTrue(np.sum(result1) > 0, "result1 should have some true values")
        self.assertTrue(np.sum(result2) > 0, "result2 should have some true values")
        self.assertTrue(np.sum(result1) < np.sum(result2), "result1 should have fewer true values than result2")


class TestFindWords(unittest.TestCase):
    def test_basic(self):
        search_string = "@global (local1, local2)"
        anywhere_words, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['global'])
        self.assertEqual(specific_words, ['local1', 'local2'])

    def test_no_anywhere_words(self):
        search_string = "(local1, local2)"
        anywhere_words, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, [])
        self.assertEqual(specific_words, ['local1', 'local2'])

    def test_no_specific_words(self):
        search_string = "@global1, @global2"
        anywhere_words, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['global1', 'global2'])
        self.assertEqual(specific_words, [])

    def test_empty_string(self):
        search_string = ""
        anywhere_words, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, [])
        self.assertEqual(specific_words, [])

    def test_mixed_words(self):
        search_string = "@global (local1, local2), @another_global"
        anywhere_words, specific_words = find_words(search_string)
        self.assertEqual(anywhere_words, ['global', 'another_global'])
        self.assertEqual(specific_words, ['local1', 'local2'])

    def test_whitespace(self):
        search_string = " @Global ,  ( local1 , local2 ) "
        anywhere_words, specific_words = find_words(search_string)
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
    def base_verify_func(self, query_text, text, anywhere_words, specific_words, expected_result):
        delimiter_map = construct_delimiter_map(query_text, specific_words)
        actual_result = verify_search_delimiters(text, anywhere_words, specific_words, delimiter_map)
        self.assertEqual(actual_result, expected_result)

    def test_all_conditions_met(self):
        query_text = "word0,((word1),word2)"
        specific_words = ["word0", "word1", "word2"]
        text = "word0,((word1),word2)"
        self.base_verify_func(query_text, text, [], specific_words, True)
        text = "((word1),word2), word0"
        self.base_verify_func(query_text, text, [], specific_words, True)
        text = "word0,(word2, (word1))"
        self.base_verify_func(query_text, text, [], specific_words, True)
        text = "word0,((word1),(ExtraGroup),word2)"
        self.base_verify_func(query_text, text, [], specific_words, True)
        text = "word0,((word2),word1)"
        self.base_verify_func(query_text, text, [], specific_words, False)
        text = "((word1),word0), word2"
        self.base_verify_func(query_text, text, [], specific_words, False)
        text = "word0,((word1))"
        self.base_verify_func(query_text, text, [], specific_words, False)
        text = "(word1),(ExtraGroup),word2)"
        self.base_verify_func(query_text, text, [], specific_words, False)

    def test_complex_case_with_word_identifiers(self):
        query_text = "word0,((word1),@word2,@word3,word4)"
        specific_words = ["word0", "word1", "word4"]
        anywhere_words = ["word2", "word3"]
        text = "word0,((word1),word2,word3,word4)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)
        text = "word2,word0,((word1),word3,word4)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)
        text = "word3,((word1),word2,word4),word0"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)
        text = "word0,((word1),word4),word2,word3"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)
        text = "word0,word1,word4,word2"  # Incorrect delimiters
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)
        text = "word2,word3"  # Missing specific words
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

    def test_very_complex_case_with_word_identifiers(self):
        query_text = "word0,(((word1,word2),@word3)),((word4,word5)))"
        specific_words = ["word0", "word1", "word2", "word4", "word5"]
        anywhere_words = ["word3"]

        # Test case where all conditions are met
        text = "word0,(((word1,word2),word3)),((word4,word5)))"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Test case with anywhere words out of specific context but still in the string
        text = "word3,word0,(((word1,word2))),((word4,word5)))"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Test case with correct specific words but incorrect delimiters
        text = "word0,((word1,word2),word3),(word4,word5)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

        # Test case missing one specific word
        text = "word0,(((word1,word2),word3)),(word4))"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

        # Test case missing anywhere word
        text = "word0,(((word1,word2))),((word4,word5)))"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

    def test_incorrect_single_delimiter(self):
        query_text = "word0,((word1)),word2"
        specific_words = ["word0", "word1", "word2"]
        anywhere_words = []

        # Positive case 1: Exact match
        text = "word0,((word1)),word2"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Positive case 2: Additional parentheses around the entire sequence
        text = "(word0,((word1)),word2)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Single closing parenthesis missing between word1 and word2
        text = "word0,((word1),word2)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

        # Single opening parenthesis missing between word0 and word1
        text = "word0,(word1)),word2"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

    def test_mismatched_parentheses(self):
        query_text = "word0,((word1)),(word2,word3)"
        specific_words = ["word0", "word1", "word2", "word3"]
        anywhere_words = []

        # Positive case 1: Exact match
        text = "word0,((word1)),(word2,word3)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Positive case 2: Reordered sequence with the same delimiters
        text = "(word2,word3),word0,((word1))"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Positive case 3: Additional text in between but the delimiters remain the same
        text = "word0,someExtraText,((word1)),someMoreText,(word2,word3)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, True)

        # Extra closing parenthesis between word2 and word3
        text = "word0,((word1),(word2,word3))"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

        # Extra opening parenthesis between word1 and word2
        text = "word0,((word1),((word2,word3)"
        self.base_verify_func(query_text, text, anywhere_words, specific_words, False)

    def test_wildcard_matching_verify_delimiters(self):
        query_text = "word0, ((word1.*?)), word2.*?"
        delimiter_map = construct_delimiter_map(query_text, ["word0", "word1.*?", "word2.*?"])

        # Positive test cases
        text = "((word1)), word0, word2X"
        self.assertTrue(verify_search_delimiters(text, [], ["word0", "word1.*?", "word2.*?"], delimiter_map))

        text = "word0, ((word1Y)), word2Z"
        self.assertTrue(verify_search_delimiters(text, [], ["word0", "word1.*?", "word2.*?"], delimiter_map))

        # Negative test cases
        text = "word0, (word1), word2"
        self.assertFalse(verify_search_delimiters(text, [], ["word0", "word1.*?", "word2.*?"], delimiter_map))

class TestFindMatching(unittest.TestCase):
    def base_find_matching(self, series, search_string, expected):
        mask = find_matching(series, search_string)
        self.assertTrue(all(mask == expected), f"Expected {expected}, got {mask}")

    def test_basic_matching(self):
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
            "word0, (word1), word2"
        ])
        search_string = "word0, ((word1*)), word2*"
        expected = pd.Series([True, True, False])
        self.base_find_matching(series, search_string, expected)
