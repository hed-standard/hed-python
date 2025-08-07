""" Utilities supporting the validation of HED strings. """

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors


class StringValidator:
    """Runs checks on the raw string that depend on multiple characters, e.g. mismatched parentheses"""
    OPENING_GROUP_CHARACTER = '('
    CLOSING_GROUP_CHARACTER = ')'
    COMMA = ','

    def run_string_validator(self, hed_string_obj):
        validation_issues = []
        validation_issues += self.check_count_tag_group_parentheses(hed_string_obj.get_original_hed_string())
        validation_issues += self.check_delimiter_issues_in_hed_string(hed_string_obj.get_original_hed_string())
        return validation_issues

    @staticmethod
    def check_count_tag_group_parentheses(hed_string) -> list[dict]:
        """ Report unmatched parentheses.

        Parameters:
            hed_string (str): A HED string.

        Returns:
            list: A list of validation list. Each issue is a dictionary.
        """
        validation_issues = []
        number_open_parentheses = hed_string.count('(')
        number_closed_parentheses = hed_string.count(')')
        if number_open_parentheses != number_closed_parentheses:
            validation_issues += ErrorHandler.format_error(ValidationErrors.PARENTHESES_MISMATCH,
                                                           opening_parentheses_count=number_open_parentheses,
                                                           closing_parentheses_count=number_closed_parentheses)
        return validation_issues

    def check_delimiter_issues_in_hed_string(self, hed_string) -> list[dict]:
        """ Report missing commas or commas in value tags.

        Parameters:
            hed_string (str): A HED string.

        Returns:
            list: A validation issues list. Each issue is a dictionary.
        """
        last_non_empty_valid_character = ''
        last_non_empty_valid_index = 0
        current_tag = ''
        issues = []

        for i, current_character in enumerate(hed_string):
            current_tag += current_character
            if not current_character.strip():
                continue
            if self._character_is_delimiter(current_character):
                if current_tag.strip() == current_character:
                    issues += ErrorHandler.format_error(ValidationErrors.TAG_EMPTY, source_string=hed_string,
                                                        char_index=i)
                    current_tag = ''
                    continue
                current_tag = ''
            elif current_character == self.OPENING_GROUP_CHARACTER:
                if current_tag.strip() == self.OPENING_GROUP_CHARACTER:
                    current_tag = ''
                else:
                    issues += ErrorHandler.format_error(ValidationErrors.COMMA_MISSING, tag=current_tag)
            elif last_non_empty_valid_character == "," and current_character == self.CLOSING_GROUP_CHARACTER:
                issues += ErrorHandler.format_error(ValidationErrors.TAG_EMPTY, source_string=hed_string,
                                                    char_index=i)
            elif self._comma_is_missing_after_closing_parentheses(last_non_empty_valid_character,
                                                                  current_character):
                issues += ErrorHandler.format_error(ValidationErrors.COMMA_MISSING, tag=current_tag[:-1])
                break
            last_non_empty_valid_character = current_character
            last_non_empty_valid_index = i
        if self._character_is_delimiter(last_non_empty_valid_character):
            issues += ErrorHandler.format_error(ValidationErrors.TAG_EMPTY,
                                                char_index=last_non_empty_valid_index,
                                                source_string=hed_string)
        return issues

    @staticmethod
    def _comma_is_missing_after_closing_parentheses(last_non_empty_character, current_character):
        """ Checks if missing comma after a closing parentheses.

        Parameters:
            last_non_empty_character (str): The last non-empty string in the HED string.
            current_character (str): The current character in the HED string.

        Returns:
            bool: True if a comma is missing after a closing parentheses. False, if otherwise.

        Notes:
            - This is a helper function for the find_missing_commas_in_hed_string function.

        """
        return last_non_empty_character == StringValidator.CLOSING_GROUP_CHARACTER and \
            not (StringValidator._character_is_delimiter(current_character)
                 or current_character == StringValidator.CLOSING_GROUP_CHARACTER)

    @staticmethod
    def _character_is_delimiter(character):
        """ Checks if the character is a delimiter.

        Parameters:
            character (str): A string character.

        Returns:
            bool: Returns True if the character is a delimiter. False, if otherwise.

        Notes:
            -  A delimiter is a comma.

        """
        return character == StringValidator.COMMA
