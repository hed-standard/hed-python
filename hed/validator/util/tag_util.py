""" Utilities supporting validation of HED tags as strings. """

import re
from hed.errors.error_reporter import ErrorHandler
from hed.schema.hed_schema_constants import HedKey
from hed.errors.error_types import ValidationErrors


class TagValidator:
    """ Validation for individual HED tags. """
    CAMEL_CASE_EXPRESSION = r'([A-Z]+\s*[a-z-]*)+'

    def run_individual_tag_validators(self, original_tag, allow_placeholders=False,
                                      is_definition=False) -> list[dict]:
        """ Runs the validators on the individual tags.

            This ignores most illegal characters except in extensions.

        Parameters:
            original_tag (HedTag): A original tag.
            allow_placeholders (bool): Allow value class or extensions to be placeholders rather than a specific value.
            is_definition (bool): This tag is part of a Definition, not a normal line.

        Returns:
            list: The validation issues associated with the tags. Each issue is dictionary.

         """
        validation_issues = []
        validation_issues += self.check_tag_exists_in_schema(original_tag)
        if not allow_placeholders:
            validation_issues += self.check_for_placeholder(original_tag, is_definition)
        validation_issues += self.check_tag_requires_child(original_tag)
        validation_issues += self.check_tag_is_deprecated(original_tag)
        validation_issues += self.check_capitalization(original_tag)
        return validation_issues

    # ==========================================================================
    # Mostly internal functions to check individual types of errors
    # =========================================================================+
    @staticmethod
    def check_tag_exists_in_schema(original_tag) -> list[dict]:
        """ Report invalid tag or doesn't take a value.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.is_basic_tag() or original_tag.is_takes_value_tag():
            return validation_issues

        is_extension_tag = original_tag.has_attribute(HedKey.ExtensionAllowed)
        if not is_extension_tag:
            actual_error = None
            if "#" in original_tag.extension:
                actual_error = ValidationErrors.PLACEHOLDER_INVALID
            validation_issues += ErrorHandler.format_error(ValidationErrors.TAG_EXTENSION_INVALID, tag=original_tag,
                                                           actual_error=actual_error)
        else:
            validation_issues += ErrorHandler.format_error(ValidationErrors.TAG_EXTENDED, tag=original_tag,
                                                           index_in_tag=len(original_tag.org_base_tag),
                                                           index_in_tag_end=None)
        return validation_issues

    @staticmethod
    def check_tag_requires_child(original_tag) -> list[dict]:
        """ Report if tag is a leaf with 'requiredTag' attribute.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.has_attribute(HedKey.RequireChild):
            validation_issues += ErrorHandler.format_error(ValidationErrors.TAG_REQUIRES_CHILD,
                                                           tag=original_tag)
        return validation_issues

    def check_capitalization(self, original_tag) -> list[dict]:
        """Report warning if incorrect tag capitalization.

        Parameters:
            original_tag (HedTag): The original tag used to report the warning.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        tag_names = original_tag.org_base_tag.split("/")
        for tag_name in tag_names:
            correct_tag_name = tag_name.capitalize()
            if tag_name != correct_tag_name and not re.search(self.CAMEL_CASE_EXPRESSION, tag_name):
                validation_issues += ErrorHandler.format_error(ValidationErrors.STYLE_WARNING,
                                                               tag=original_tag)
                break
        return validation_issues

    def check_tag_is_deprecated(self, original_tag) -> list[dict]:
        validation_issues = []
        if original_tag.has_attribute(HedKey.DeprecatedFrom):
            validation_issues += ErrorHandler.format_error(ValidationErrors.ELEMENT_DEPRECATED,
                                                           tag=original_tag)

        return validation_issues

    # ==========================================================================
    # Private utility functions
    # =========================================================================+

    @staticmethod
    def check_for_placeholder(original_tag, is_definition=False) -> list[dict]:
        """ Report invalid placeholder characters.

        Parameters:
            original_tag (HedTag):  The HedTag to be checked
            is_definition (bool): If True, placeholders are allowed.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - Invalid placeholder may appear in the extension/value portion of a tag.

        """
        validation_issues = []
        if not is_definition:
            starting_index = len(original_tag.org_base_tag) + 1
            for i, character in enumerate(original_tag.extension):
                if character == "#":
                    validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                   tag=original_tag,
                                                                   index_in_tag=starting_index + i,
                                                                   index_in_tag_end=starting_index + i + 1,
                                                                   actual_error=ValidationErrors.PLACEHOLDER_INVALID)

        return validation_issues
