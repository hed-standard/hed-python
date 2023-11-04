from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors


class CharValidator:
    """Class responsible for basic character level validation of a string or tag."""

    # # sign is allowed by default as it is specifically checked for separately.
    DEFAULT_ALLOWED_PLACEHOLDER_CHARS = ".+-^ _#"
    # Placeholder characters are checked elsewhere, but by default allowed
    TAG_ALLOWED_CHARS = "-_/"

    INVALID_STRING_CHARS = '[]{}~'
    INVALID_STRING_CHARS_PLACEHOLDERS = '[]~'

    def check_invalid_character_issues(self, hed_string, allow_placeholders):
        """ Report invalid characters.

        Parameters:
            hed_string (str): A hed string.
            allow_placeholders: Allow placeholder and curly brace characters

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
            if character in invalid_dict or ord(character) > 127:
                validation_issues += self._report_invalid_character_error(hed_string, index)

        return validation_issues

    def check_tag_invalid_chars(self, original_tag, allow_placeholders):
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

    def check_for_invalid_extension_chars(self, original_tag):
        """Report invalid characters in extension/value.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        allowed_chars = self.TAG_ALLOWED_CHARS
        allowed_chars += self.DEFAULT_ALLOWED_PLACEHOLDER_CHARS
        allowed_chars += " "
        return self._check_invalid_chars(original_tag.extension, allowed_chars, original_tag,
                                         starting_index=len(original_tag.org_base_tag) + 1)
    
    @staticmethod
    def _check_invalid_chars(check_string, allowed_chars, source_tag, starting_index=0):
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
                                                           index_in_tag_end=starting_index + i + 1)
        return validation_issues

    @staticmethod
    def _check_invalid_prefix_issues(original_tag):
        """Check for invalid schema namespace."""
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
