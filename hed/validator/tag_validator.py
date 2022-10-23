"""
This module is used to validate the HED tags as strings.

"""

import re
from hed.errors.error_reporter import ErrorHandler
from hed.schema import HedKey
from hed.errors.error_types import ValidationErrors
from hed.validator import tag_validator_util


class TagValidator:
    """ Validation for individual HED tags. """

    CAMEL_CASE_EXPRESSION = r'([A-Z-]+\s*[a-z-]*)+'
    INVALID_STRING_CHARS = '[]{}~'
    OPENING_GROUP_CHARACTER = '('
    CLOSING_GROUP_CHARACTER = ')'
    COMMA = ','

    # # sign is allowed by default as it is specifically checked for separately.
    DEFAULT_ALLOWED_PLACEHOLDER_CHARS = ".+-^ _#"
    # Placeholder characters are checked elsewhere, but by default allowed
    TAG_ALLOWED_CHARS = "-_/"

    def __init__(self, hed_schema=None, run_semantic_validation=True):
        """Constructor for the Tag_Validator class.

        Parameters:
            hed_schema (HedSchema): A HedSchema object.
            run_semantic_validation (bool): True if the validator should check the HED data against a schema.

        Returns:
            TagValidator: A Tag_Validator object.

        """
        self._hed_schema = hed_schema
        self._run_semantic_validation = run_semantic_validation
        if not self._hed_schema:
            self._run_semantic_validation = False

        # Dict contains all the value portion validators for value class.  e.g. "is this a number?"
        self._value_unit_validators = self._register_default_value_validators()

    # ==========================================================================
    # Top level validator functions
    # =========================================================================+
    def run_hed_string_validators(self, hed_string_obj):
        """Basic high level checks of the hed string

        Parameters:
            hed_string_obj (HedString): A HED string.

        Returns:
            list: The validation issues associated with a HED string. Each issue is a dictionary.

        Notes:
            - Used for basic invalid characters or bad delimiters.

         """
        validation_issues = []
        validation_issues += self.check_invalid_character_issues(hed_string_obj.get_original_hed_string())
        validation_issues += self.check_count_tag_group_parentheses(hed_string_obj.get_original_hed_string())
        validation_issues += self.check_delimiter_issues_in_hed_string(hed_string_obj.get_original_hed_string())
        for tag in hed_string_obj.get_all_tags():
            validation_issues += self.check_tag_formatting(tag)
        return validation_issues

    def run_individual_tag_validators(self, original_tag, check_for_warnings, allow_placeholders=False,
                                      is_definition=False):
        """ Runs the hed_ops on the individual tags.

        Parameters:
            original_tag (HedTag): A original tag.
            check_for_warnings (bool): If True, also check for warnings.
            allow_placeholders (bool): Allow value class or extensions to be placeholders rather than a specific value.
            is_definition (bool): This tag is part of a Definition, not a normal line.

        Returns:
            list: The validation issues associated with the top-level tags. Each issue is dictionary.

         """
        validation_issues = []
        validation_issues += self.check_tag_invalid_chars(original_tag, allow_placeholders)
        if self._run_semantic_validation:
            validation_issues += self.check_tag_exists_in_schema(original_tag, check_for_warnings)
            if original_tag.is_unit_class_tag():
                validation_issues += self.check_tag_unit_class_units_are_valid(original_tag, check_for_warnings)
            elif original_tag.is_value_class_tag():
                validation_issues += self.check_tag_value_class_valid(original_tag)
            elif original_tag.extension_or_value_portion:
                validation_issues += self.check_for_invalid_extension_chars(original_tag)

            if not allow_placeholders:
                validation_issues += self.check_for_placeholder(original_tag, is_definition)
            validation_issues += self.check_tag_requires_child(original_tag)
        if check_for_warnings:
            validation_issues += self.check_capitalization(original_tag)
        return validation_issues

    def run_tag_level_validators(self, original_tag_list, is_top_level, is_group):
        """ Run hed_ops at each level in a HED string.

        Parameters:
            original_tag_list (list): A list containing the original HedTags.
            is_top_level (bool): If True, this group is a "top level tag group".
            is_group (bool): If true, group is contained by parenthesis.

        Returns:
            list: The validation issues associated with each level in a HED string.

        Notes:
            - This is for the top-level, all groups, and nested groups.
            - This can contain definitions, Onset, etc tags.

        """
        validation_issues = []
        validation_issues += self.check_tag_level_issue(original_tag_list, is_top_level, is_group)
        return validation_issues

    def run_all_tags_validators(self, tags, check_for_warnings):
        """ Validate the multi-tag properties in a hed string.

        Parameters:
            tags (list): A list containing the HedTags in a HED string.
            check_for_warnings (bool): If True, also check for warnings.

        Returns:
            list: The validation issues associated with the tags in a HED string. Each issue is a dictionary.

        Notes:
            - Multi-tag properties include required tags.

        """
        validation_issues = []
        if self._run_semantic_validation:
            if check_for_warnings:
                validation_issues += self.check_for_required_tags(tags)
            validation_issues += self.check_multiple_unique_tags_exist(tags)
        return validation_issues

    # ==========================================================================
    # Mostly internal functions to check individual types of errors
    # =========================================================================+
    def check_invalid_character_issues(self, hed_string):
        """ Report invalid characters.

        Parameters:
            hed_string (str): A hed string.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - Invalid tag characters are defined by TagValidator.INVALID_STRING_CHARS.
        """
        validation_issues = []
        for index, character in enumerate(hed_string):
            if character in TagValidator.INVALID_STRING_CHARS:
                validation_issues += self._report_invalid_character_error(hed_string, index)

        return validation_issues

    def check_count_tag_group_parentheses(self, hed_string):
        """ Report unmatched parentheses.

        Parameters:
            hed_string (str): A hed string.

        Returns:
            list: A list of validation list. Each issue is a dictionary.
        """
        validation_issues = []
        number_open_parentheses = hed_string.count('(')
        number_closed_parentheses = hed_string.count(')')
        if number_open_parentheses != number_closed_parentheses:
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_PARENTHESES_MISMATCH,
                                                           opening_parentheses_count=number_open_parentheses,
                                                           closing_parentheses_count=number_closed_parentheses)
        return validation_issues

    def check_delimiter_issues_in_hed_string(self, hed_string):
        """ Report missing commas or commas in value tags.

        Parameters:
            hed_string (str): A hed string.

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
            if TagValidator._character_is_delimiter(current_character):
                if current_tag.strip() == current_character:
                    issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_EMPTY, source_string=hed_string,
                                                        char_index=i)
                    current_tag = ''
                    continue
                current_tag = ''
            elif current_character == self.OPENING_GROUP_CHARACTER:
                if current_tag.strip() == self.OPENING_GROUP_CHARACTER:
                    current_tag = ''
                else:
                    issues += ErrorHandler.format_error(ValidationErrors.HED_COMMA_MISSING, tag=current_tag)
            elif TagValidator._comma_is_missing_after_closing_parentheses(last_non_empty_valid_character,
                                                                          current_character):
                issues += ErrorHandler.format_error(ValidationErrors.HED_COMMA_MISSING, tag=current_tag[:-1])
                break
            last_non_empty_valid_character = current_character
            last_non_empty_valid_index = i
        if TagValidator._character_is_delimiter(last_non_empty_valid_character):
            issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_EMPTY,
                                                char_index=last_non_empty_valid_index,
                                                source_string=hed_string)
        return issues

    pattern_doubleslash = re.compile(r"([ \t/]{2,}|^/|/$)")

    def check_tag_formatting(self, original_tag):
        """ Report repeated or erroneous slashes.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        for match in self.pattern_doubleslash.finditer(original_tag.org_tag):
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                           tag=original_tag,
                                                           index_in_tag=match.start(),
                                                           index_in_tag_end=match.end())

        return validation_issues

    def check_tag_invalid_chars(self, original_tag, allow_placeholders):
        """ Report invalid characters in the given tag.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            allow_placeholders (bool): Allow placeholder characters(#) if True.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        allowed_chars = self.TAG_ALLOWED_CHARS
        if not self._hed_schema or not self._hed_schema.is_hed3_schema:
            allowed_chars += " "
        if allow_placeholders:
            allowed_chars += "#"
        return self._check_invalid_chars(original_tag.org_base_tag, allowed_chars, original_tag)

    def check_tag_exists_in_schema(self, original_tag, check_for_warnings=False):
        """ Report invalid tag or doesn't take a value.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            check_for_warnings (bool): If True, also check for warnings.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.is_basic_tag() or original_tag.is_takes_value_tag():
            return validation_issues

        is_extension_tag = original_tag.is_extension_allowed_tag()
        if not is_extension_tag:
            validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_EXTENSION, tag=original_tag)
        elif check_for_warnings:
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_EXTENDED, tag=original_tag,
                                                           index_in_tag=len(original_tag.org_base_tag),
                                                           index_in_tag_end=None)
        return validation_issues

    def check_tag_unit_class_units_are_valid(self, original_tag, check_for_warnings):
        """ Report incorrect unit class or units.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.
            check_for_warnings (bool): Indicates whether to check for warnings.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.is_unit_class_tag():
            stripped_value, unit = original_tag.get_stripped_unit_value()
            if not unit:
                if self._validate_value_class_portion(original_tag, stripped_value):
                    if check_for_warnings:
                        # only suggest a unit is missing if this is a valid number
                        if tag_validator_util.validate_numeric_value_class(stripped_value):
                            default_unit = original_tag.get_unit_class_default_unit()
                            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_UNITS_DEFAULT_USED,
                                                                           tag=original_tag,
                                                                           default_unit=default_unit)
                else:
                    tag_unit_class_units = original_tag.get_tag_unit_class_units()
                    if tag_unit_class_units:
                        validation_issues += ErrorHandler.format_error(ValidationErrors.HED_UNITS_INVALID,
                                                                       original_tag,
                                                                       unit_class_units=tag_unit_class_units)
        return validation_issues

    def check_tag_value_class_valid(self, original_tag):
        """ Report an invalid value portion.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues.
        """
        validation_issues = []
        if not self._validate_value_class_portion(original_tag, original_tag.extension_or_value_portion):
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_VALUE_INVALID,
                                                           original_tag)

        return validation_issues

    def check_tag_requires_child(self, original_tag):
        """ Report if tag is a leaf with 'requiredTag' attribute.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        if original_tag.has_attribute(HedKey.RequireChild):
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_REQUIRES_CHILD,
                                                           tag=original_tag)
        return validation_issues

    def check_tag_unit_class_units_exist(self, original_tag):
        """ Report warning if tag has a unit class tag with no units.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list: Validation issues.  Each issue is a dictionary.

        """
        validation_issues = []
        if original_tag.is_unit_class_tag():
            tag_unit_values = original_tag.extension_or_value_portion
            if tag_validator_util.validate_numeric_value_class(tag_unit_values):
                default_unit = original_tag.get_unit_class_default_unit()
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_UNITS_DEFAULT_USED,
                                                               tag=original_tag,
                                                               default_unit=default_unit)
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
        return self._check_invalid_chars(original_tag.extension_or_value_portion, allowed_chars, original_tag,
                                         starting_index=len(original_tag.org_base_tag) + 1)

    def check_capitalization(self, original_tag):
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
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_STYLE_WARNING,
                                                               tag=original_tag)
                break
        return validation_issues

    def check_tag_level_issue(self, original_tag_list, is_top_level, is_group):
        """ Report tags incorrectly positioned in hierarchy.

        Parameters:
            original_tag_list (list): HedTags containing the original tags.
            is_top_level (bool): If True, this group is a "top level tag group"
            is_group (bool): If true group should be contained by parenthesis

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - Top-level groups can contain definitions, Onset, etc tags.
        """
        validation_issues = []
        if self._run_semantic_validation:
            top_level_tags = [tag for tag in original_tag_list if
                              tag.base_tag_has_attribute(HedKey.TopLevelTagGroup)]
            tag_group_tags = [tag for tag in original_tag_list if
                              tag.base_tag_has_attribute(HedKey.TagGroup)]
            for tag_group_tag in tag_group_tags:
                if not is_group:
                    validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_GROUP_TAG,
                                                                   tag=tag_group_tag)
            for top_level_tag in top_level_tags:
                if not is_top_level:
                    validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TOP_LEVEL_TAG,
                                                                   tag=top_level_tag)

            if is_top_level and len(top_level_tags) > 1:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS,
                                                               tag=top_level_tags[0],
                                                               multiple_tags=top_level_tags[1:])

        return validation_issues

    def check_for_required_tags(self, tags):
        """ Report missing required tags.

        Parameters:
            tags (list): HedTags containing the tags.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        """
        validation_issues = []
        required_prefixes = self._hed_schema.get_tags_with_attribute(HedKey.Required)
        for required_prefix in required_prefixes:
            if not any(tag.long_tag.lower().startswith(required_prefix.lower()) for tag in tags):
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                                               tag_prefix=required_prefix)
        return validation_issues

    def check_multiple_unique_tags_exist(self, tags):
        """ Report if multiple identical unique tags exist

            A unique Term can only appear once in a given HedString.
            Unique terms are terms with the 'unique' property in the schema.

        Parameters:
            tags (list): HedTags containing the tags.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        unique_prefixes = self._hed_schema.get_tags_with_attribute(HedKey.Unique)
        for unique_prefix in unique_prefixes:
            unique_tag_prefix_bool_mask = [x.long_tag.lower().startswith(unique_prefix.lower()) for x in tags]
            if sum(unique_tag_prefix_bool_mask) > 1:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_NOT_UNIQUE,
                                                               tag_prefix=unique_prefix)
        return validation_issues

    # ==========================================================================
    # Private utility functions
    # =========================================================================+
    def _validate_value_class_portion(self, original_tag, portion_to_validate):
        if portion_to_validate is None:
            return False

        value_class_types = original_tag.value_classes
        return self.validate_value_class_type(portion_to_validate, value_class_types)

    def _report_invalid_character_error(self, hed_string, index):
        """ Report an invalid character.

        Parameters:
            hed_string (str): The HED string that caused the error.
            index (int): The index of the invalid character in the HED string.

        Returns:
            list: A singleton list with a dictionary representing the error.

        """
        error_type = ValidationErrors.HED_CHARACTER_INVALID
        character = hed_string[index]
        if character == "~":
            error_type = ValidationErrors.HED_TILDES_UNSUPPORTED
        return ErrorHandler.format_error(error_type, char_index=index,
                                         source_string=hed_string)

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
        return last_non_empty_character == TagValidator.CLOSING_GROUP_CHARACTER and \
            not (TagValidator._character_is_delimiter(current_character)
                 or current_character == TagValidator.CLOSING_GROUP_CHARACTER)

    @staticmethod
    def _character_is_delimiter(character):
        """ Checks if the character is a delimiter.

        Parameters:
            character (str): A string character.

        Returns:
            bool: Returns true if the character is a delimiter. False, if otherwise.

        Notes:
            -  A delimiter is a comma.

        """
        return character == TagValidator.COMMA

    def check_for_placeholder(self, original_tag, is_definition=False):
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
            for i, character in enumerate(original_tag.extension_or_value_portion):
                if character == "#":
                    validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                   tag=original_tag,
                                                                   index_in_tag=starting_index + i,
                                                                   index_in_tag_end=starting_index + i + 1,
                                                                   actual_error=ValidationErrors.HED_VALUE_INVALID)

        return validation_issues

    def _check_invalid_chars(self, check_string, allowed_chars, source_tag, starting_index=0):
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
    def _register_default_value_validators():
        validator_dict = {
            tag_validator_util.DATE_TIME_VALUE_CLASS: tag_validator_util.is_date_time,
            tag_validator_util.NUMERIC_VALUE_CLASS: tag_validator_util.validate_numeric_value_class,
            tag_validator_util.TEXT_VALUE_CLASS: tag_validator_util.validate_text_value_class,
            tag_validator_util.NAME_VALUE_CLASS: tag_validator_util.validate_text_value_class
        }

        return validator_dict

    def validate_value_class_type(self, unit_or_value_portion, valid_types):
        """ Report invalid unit or valid class values.

        Parameters:
            unit_or_value_portion (str): The value portion to validate.
            valid_types (list): The names of value class or unit class types (e.g. dateTime or dateTimeClass).

        Returns:
            type_valid (bool): True if this is one of the valid_types validators.

        """
        for unit_class_type in valid_types:
            valid_func = self._value_unit_validators.get(unit_class_type)
            if valid_func:
                if valid_func(unit_or_value_portion):
                    return True
        return False
