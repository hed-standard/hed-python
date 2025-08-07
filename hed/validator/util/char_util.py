""" Classes responsible for basic character validation of a string or tag."""
import json
import re
import os

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors

CLASS_REX_FILENAME = '../data/class_regex.json'


class CharValidator:
    """Class responsible for basic character level validation of a string or tag."""

    # # sign is allowed by default as it is specifically checked for separately.
    DEFAULT_ALLOWED_PLACEHOLDER_CHARS = ".+-^ _#"
    # Placeholder characters are checked elsewhere, but by default allowed
    TAG_ALLOWED_CHARS = "-_/"

    INVALID_STRING_CHARS = '[]{}~'
    INVALID_STRING_CHARS_PLACEHOLDERS = '[]~'

    def __init__(self, modern_allowed_char_rules=False):
        """Does basic character validation for HED strings/tags

        Parameters:
            modern_allowed_char_rules(bool): If True, use 8.3 style rules for unicode characters.
        """
        self._validate_characters = modern_allowed_char_rules

    def check_invalid_character_issues(self, hed_string, allow_placeholders) -> list[dict]:
        """ Report invalid characters.

        Parameters:
            hed_string (str): A HED string.
            allow_placeholders (bool): Allow placeholder and curly brace characters.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - Invalid tag characters are defined by self.INVALID_STRING_CHARS or
                                                    self.INVALID_STRING_CHARS_PLACEHOLDERS
        """
        validation_issues = []
        invalid_dict = self.INVALID_STRING_CHARS
        if allow_placeholders:
            invalid_dict = self.INVALID_STRING_CHARS_PLACEHOLDERS
        for index, character in enumerate(hed_string):
            if self._validate_characters:
                if character in invalid_dict or not character.isprintable():
                    validation_issues += self._report_invalid_character_error(hed_string, index)
            else:
                if character in invalid_dict or ord(character) > 127:
                    validation_issues += self._report_invalid_character_error(hed_string, index)

        return validation_issues

    def check_tag_invalid_chars(self, original_tag, allow_placeholders) -> list[dict]:
        """ Report invalid characters in the given tag.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            allow_placeholders (bool): Allow placeholder characters(#) if True.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = self._check_invalid_prefix_issues(original_tag)
        allowed_chars = self.TAG_ALLOWED_CHARS
        if allow_placeholders:
            allowed_chars += "#"
        validation_issues += self._check_invalid_chars(original_tag.org_base_tag, allowed_chars, original_tag)
        return validation_issues

    def check_for_invalid_extension_chars(self, original_tag, validate_text, error_code=None, index_offset=0) -> list[dict]:
        """Report invalid characters in extension/value.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            validate_text (str): the text we want to validate, if not the full extension.
            error_code (str): The code to override the error as.  Again mostly for def/def-expand tags.
            index_offset (int): Offset into the extension validate_text starts at.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        allowed_chars = self.TAG_ALLOWED_CHARS
        allowed_chars += self.DEFAULT_ALLOWED_PLACEHOLDER_CHARS
        allowed_chars += " "
        return self._check_invalid_chars(validate_text, allowed_chars, original_tag,
                                         starting_index=len(original_tag.org_base_tag) + 1 + index_offset,
                                         error_code=error_code)

    @staticmethod
    def _check_invalid_chars(check_string, allowed_chars, source_tag, starting_index=0, error_code=None):
        """ Helper for checking for invalid characters.

        Parameters:
            check_string (str): String to be checked for invalid characters.
            allowed_chars (str): Characters allowed in string.
            source_tag (HedTag): Tag from which the string came from.
            starting_index (int): Starting index of check_string within the tag.
            error_code (str): The code to override the error as.  Again mostly for def/def-expand tags.

        Returns:
            list:  List of dictionaries with validation issues.
        """
        validation_issues = []
        for i, character in enumerate(check_string):
            if character.isalnum():
                continue
            if character in allowed_chars:
                continue
            # Todo: Remove this patch when clock times and invalid characters are more properly checked
            if character == ":":
                continue
            validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_TAG_CHARACTER,
                                                           tag=source_tag, index_in_tag=starting_index + i,
                                                           index_in_tag_end=starting_index + i + 1,
                                                           actual_error=error_code)
        return validation_issues

    @staticmethod
    def _check_invalid_prefix_issues(original_tag):
        """Check for invalid schema namespace.

        Parameters:
            original_tag (HedTag): Tag to look


        Returns:
            list:  List of dictionaries with validation issues.

        """
        issues = []
        schema_namespace = original_tag.schema_namespace
        if schema_namespace and not schema_namespace[:-1].isalpha():
            issues += ErrorHandler.format_error(ValidationErrors.TAG_NAMESPACE_PREFIX_INVALID,
                                                tag=original_tag, tag_namespace=schema_namespace)
        return issues

    @staticmethod
    def _report_invalid_character_error(hed_string, index):
        """ Report an invalid character.

        Parameters:
            hed_string (str): The HED string that caused the error.
            index (int): The index of the invalid character in the HED string.

        Returns:
            list: A singleton list with a dictionary representing the error.

        """
        error_type = ValidationErrors.CHARACTER_INVALID
        character = hed_string[index]
        if character == "~":
            error_type = ValidationErrors.TILDES_UNSUPPORTED
        return ErrorHandler.format_error(error_type, char_index=index,
                                         source_string=hed_string)


class CharRexValidator(CharValidator):
    """Class responsible for basic character level validation of a string or tag."""

    def __init__(self, modern_allowed_char_rules=False):
        """Does basic character validation for HED strings/tags

        Parameters:
            modern_allowed_char_rules(bool): If True, use 8.3 style rules for Unicode characters.
        """
        super().__init__(modern_allowed_char_rules)
        self._rex_dict = self._get_rex_dict()

    def get_problem_chars(self, in_str, cname):

        # List to store problem indices and characters
        bad_indices = []

        # Retrieve the allowed character classes for the given class_name
        allowed_classes = self._rex_dict["class_chars"].get(cname, [])
        if not allowed_classes:
            return bad_indices
        # Combine the corresponding regular expressions from the char_regex section
        allowed_regex_parts = [self._rex_dict["char_regex"][char_class] for char_class in allowed_classes]

        # Create one combined regex that matches any of the allowed character classes
        combined_regex = "|".join(allowed_regex_parts)

        # Compile the combined regular expression
        compiled_regex = re.compile(combined_regex)

        # Iterate through the input string, checking each character
        for index, char in enumerate(in_str):
            # If the character doesn't match the combined regex, it's a problem
            if not compiled_regex.match(char):
                bad_indices.append((index, char))

        return bad_indices

    def is_valid_value(self, in_string, cname):
        # Retrieve the allowed character classes for the given class_name
        class_regex = self._rex_dict["class_words"].get(cname, [])
        if not class_regex:
            return True
        match = re.match(class_regex, in_string)
        match = match if match else False
        return match

    @staticmethod
    def _get_rex_dict():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.realpath(os.path.join(current_dir, CLASS_REX_FILENAME))
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)


if __name__ == "__main__":
    # Example input string
    input_string = "Hello World123"

    # Class name (e.g., "nameClass" or "testClass")
    class_name = "nameClass"

    # Call the function and print the result
    # problem_indices = get_problem_chars(input_string, class_name, json_data)
    # print(problem_indices)
