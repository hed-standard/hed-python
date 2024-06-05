"""
Utilities to support HED searches based on strings.
"""
import re
from itertools import combinations, product
from collections import defaultdict
import pandas as pd


def find_matching(series, search_string, regex=False):
    """ Find lines in the series that match the search string and returns a mask.

    Syntax Rules:
        - '@': Prefixing a term in the search string means the term must appear anywhere within a line.
        - '~': Prefixing a term in the search string means the term must NOT appear within a line.
        - Parentheses: Elements within parentheses must appear in the line with the same level of nesting.
                e.g.: Search string: "(A), (B)" will match "(A), (B, C)", but not "(A, B)", since they don't
                      start in the same group.
        - "LongFormTag*": A * will match any remaining word(anything but a comma or parenthesis)
        - An individual term can be arbitrary regex, but it is limited to single continuous words.

    Notes:
        - Specific words only care about their level relative to other specific words, not overall.
              e.g. "(A, B)" will find: "A, B", "(A, B)", (A, (C), B)", or ((A, B))"
        - If you have no grouping or anywhere words in the search, it assumes all terms are anywhere words.
        - The format of the series should match the format of the search string, whether it's in short or long form.
        - To enable support for matching parent tags, ensure that both the series and search string are in long form.

    Parameters:
        series (pd.Series): A Pandas Series object containing the lines to be searched.
        search_string (str): The string to search for in each line of the series.
        regex (bool): By default, translate any * wildcard characters to .*? regex.
                      If True, do no translation and pass the words as is. Due to how it's setup, you must not include
                      the following characters: (),

    Returns:
        mask (pd.Series): A Boolean mask Series of the same length as the input series.
                          The mask has `True` for lines that match the search string and `False` otherwise.
    """
    if not regex:
        # Replace *'s with a reasonable value for people who don't know regex
        search_string = re.sub(r'(?<!\.)\*', '.*?', search_string)
    anywhere_words, negative_words, specific_words = find_words(search_string)
    # If we have no nesting or anywhere words, assume they don't care about level
    if "(" not in search_string and "@" not in search_string:
        anywhere_words += specific_words
        specific_words = []
    delimiter_map = construct_delimiter_map(search_string, specific_words)
    candidate_indexes = _verify_basic_words(series, anywhere_words, negative_words)

    # do a basic check for all specific words(this doesn't verify word delimiters)
    for word in specific_words:
        matches = series.str.contains(word, regex=True)
        current_word_indexes = set(matches[matches].index.tolist())

        candidate_indexes &= current_word_indexes

        if not candidate_indexes:
            break

    candidate_indexes = sorted(candidate_indexes)

    full_mask = pd.Series(False, index=series.index, dtype=bool)

    if candidate_indexes:
        if specific_words:
            candidate_series = series[candidate_indexes]
            mask = candidate_series.apply(verify_search_delimiters, args=(specific_words, delimiter_map))
            full_mask.loc[candidate_indexes] = mask
        else:
            full_mask.loc[candidate_indexes] = True

    return full_mask


def _get_word_indexes(series, word):
    pattern = r'(?:[ ,()]|^)' + word + r'(?:[ ,()]|$)'
    matches = series.str.contains(pattern, regex=True)
    return set(matches[matches].index.tolist())


def _verify_basic_words(series, anywhere_words, negative_words):
    candidate_indexes = set(series.index)
    for word in anywhere_words:
        current_word_indexes = _get_word_indexes(series, word)
        candidate_indexes &= current_word_indexes

    for word in negative_words:
        current_word_indexes = _get_word_indexes(series, word)
        candidate_indexes -= current_word_indexes
    return candidate_indexes


def find_words(search_string):
    """ Extract words in the search string based on their prefixes.

    Parameters:
        search_string (str): The search query string to parse.
                             Words can be prefixed with '@' or '~'.

    Returns:
        list: A list containing three lists:
            - Words prefixed with '@'
            - Words prefixed with '~'
            - Words with no prefix
    """
    # Match sequences of characters that are not commas or parentheses.
    pattern = r'[^,()]+'
    words = re.findall(pattern, search_string)

    # Remove any extraneous whitespace from each word
    words = [word.strip() for word in words if word.strip()]

    at_words = [word[1:] for word in words if word.startswith("@")]
    tilde_words = [word[1:] for word in words if word.startswith("~")]
    no_prefix_words = [word for word in words if not word.startswith("~") and not word.startswith("@")]

    return [at_words, tilde_words, no_prefix_words]


def check_parentheses(text):
    """ Check for balanced parentheses in the given text and returns the unbalanced ones.

    Parameters:
        text (str): The text to be checked for balanced parentheses.

    Returns:
        str: A string containing the unbalanced parentheses in their original order.

    Notes:
        - The function only considers the characters '(' and ')' for balancing.
        - Balanced pairs of parentheses are removed, leaving behind only the unbalanced ones.

    """
    # Extract all parentheses from the text
    all_parentheses = ''.join(re.findall('[()]', text))

    stack = []
    remaining_parentheses = []

    # Loop through all parentheses and find balanced ones
    for p in all_parentheses:
        if p == '(':
            stack.append(p)
        elif p == ')' and stack:
            stack.pop()
        else:
            remaining_parentheses.append(p)

    # Add unbalanced ( back to remaining parentheses
    remaining_parentheses.extend(stack)

    return ''.join(remaining_parentheses)


def reverse_and_flip_parentheses(s):
    """ Reverse a string and flips the parentheses.

        Parameters:
            s (str): The string to be reversed and have its parentheses flipped.

        Returns:
            str: The reversed string with flipped parentheses.

        Notes:
            - The function takes into account only the '(' and ')' characters for flipping.
    """
    # Reverse the string
    reversed_s = s[::-1]

    # Flip the parentheses directly in the reversed string
    flipped_s = reversed_s.translate(str.maketrans("()", ")("))
    return flipped_s


def construct_delimiter_map(text, words):
    """ Based on an input search query and list of words, return the parenthetical delimiters between them.

    Parameters:
        text (str): The search query.
        words(list): A list of words we want to map between from the query.

    Returns:
        dict: The two-way delimiter map.
    """
    locations = {}
    # Find the locations of each word in the text
    for word in words:
        for match in re.finditer(r'(?:[ ,()]|^)(' + word + r')(?:[ ,()]|$)', text):
            start_index = match.start(1)
            end_index = match.end(1)
            match_length = end_index - start_index
            locations[start_index] = (word, match_length)

    sorted_locations = sorted(locations.items())

    delimiter_map = {}
    # Use combinations to get every combination of two words in order
    for (start1, (word1, length1)), (start2, (word2, length2)) in combinations(sorted_locations, 2):
        end1 = start1 + length1
        delimiter_text = text[end1:start2]
        delimiter_map[(word1, word2)] = check_parentheses(delimiter_text)

    # Add the reversed version of the above
    reverse_map = {(word2, word1): reverse_and_flip_parentheses(delimiter_text) for ((word1, word2), delimiter_text) in
                   delimiter_map.items()}
    delimiter_map.update(reverse_map)

    return delimiter_map


def verify_search_delimiters(text, specific_words, delimiter_map):
    """ Verify that the text contains specific words with expected delimiters between them.

    Parameters:
        text (str): The text to search in.
        specific_words (list of str): Words that must appear relative to other words in the text.
        delimiter_map (dict): A dictionary specifying expected delimiters between pairs of specific words.

    Returns:
        bool: True if all conditions are met, otherwise False.
    """
    locations = defaultdict(list)

    # Find all locations for each word in the text
    for word in specific_words:
        for match in re.finditer(r'(?:[ ,()]|^)(' + word + r')(?:[ ,()]|$)', text):
            start_index = match.start(1)
            matched_word = match.group(1)
            locations[word].append((start_index, len(matched_word), word))

    if len(locations) != len(specific_words):
        return False

    # Generate all possible combinations of word sequences
    # this covers cases where the same tag is found twice, and you need to check both
    for sequence in product(*locations.values()):
        sorted_sequence = sorted(sequence)

        # Check if the delimiters for this sequence match the expected delimiters
        valid = True
        for i in range(len(sorted_sequence) - 1):
            start1, len1, word1 = sorted_sequence[i]
            start2, len2, word2 = sorted_sequence[i + 1]

            end1 = start1 + len1
            delimiter_text = text[end1:start2]

            found_delimiter = check_parentheses(delimiter_text)
            expected_delimiter = delimiter_map.get((word1, word2), None)

            if found_delimiter != expected_delimiter:
                valid = False
                break

        if valid:
            return True  # Return True if any sequence is valid

    return False  # Return False if no valid sequence is found
