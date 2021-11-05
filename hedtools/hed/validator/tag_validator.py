"""
This module is used to validate the HED tags as strings.

"""

import re
from hed.errors.error_reporter import ErrorHandler
from hed.schema import HedKey
from hed.errors.error_types import ValidationErrors
from hed.validator import tag_validator_util


class TagValidator:
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

        Parameters
        ----------
        hed_schema: HedSchema
            A HedSchema object.
        Returns
        -------
        TagValidator
            A Tag_Validator object.

        """
        self._hed_schema = hed_schema
        self._run_semantic_validation = run_semantic_validation
        if not self._hed_schema:
            self._run_semantic_validation = False

    # ==========================================================================
    # Top level validator functions
    # =========================================================================+
    def run_hed_string_validators(self, hed_string_obj):
        """Do the most basic high level checks of the hed string, for basic invalid characters or bad delimiters

         Parameters
         ----------
         hed_string_obj: HedString
            A HED string.
         Returns
         -------
         []
             The validation issues associated with a HED string.

         """
        validation_issues = []
        validation_issues += self.check_invalid_character_issues(hed_string_obj.get_original_hed_string())
        validation_issues += self.check_count_tag_group_parentheses(hed_string_obj.get_original_hed_string())
        validation_issues += self.check_delimiter_issues_in_hed_string(hed_string_obj.get_original_hed_string())
        for tag in hed_string_obj.get_all_tags():
            validation_issues += self.check_tag_formatting(tag)
        return validation_issues

    def run_individual_tag_validators(self, original_tag, check_for_warnings, allow_placeholders=False):
        """Runs the validators on the individual tags in a HED string.

         Parameters
         ----------
         original_tag: HedTag
            A original tag.
         check_for_warnings: bool
             If True, also check for warnings.
         allow_placeholders: bool
             Allow value class or extensions to be placeholders rather than a specific value.
         Returns
         -------
         []
             The validation issues associated with the top-level in the HED string.
         """
        validation_issues = []
        validation_issues += self.check_tag_invalid_chars(original_tag, allow_placeholders)
        if self._run_semantic_validation:
            validation_issues += self.check_tag_exists_in_schema(original_tag, check_for_warnings)
            if self._hed_schema.is_unit_class_tag(original_tag):
                validation_issues += self.check_tag_unit_class_units_are_valid(original_tag)
                if check_for_warnings:
                    validation_issues += self.check_tag_unit_class_units_exist(original_tag)
            elif self._hed_schema.is_value_class_tag(original_tag):
                validation_issues += self.check_tag_value_class_valid(original_tag)
            elif original_tag.extension_or_value_portion:
                validation_issues += self.check_for_invalid_extension_chars(original_tag)

            if not allow_placeholders:
                # if not self._allow_pound_signs_as_numbers:
                validation_issues += self.check_for_placeholder(original_tag)
            validation_issues += self.check_tag_requires_child(original_tag)
        if check_for_warnings:
            validation_issues += self.check_capitalization(original_tag)
        return validation_issues

    def run_tag_level_validators(self, original_tag_list, is_top_level, is_group):
        """Runs the validators on tags at each level in a HED string. This pertains to the top-level, all groups,
           and nested groups.

        Parameters
        ----------
        original_tag_list: [HedTag]
           A list containing the original tags.
        is_top_level: bool
            If True, this group is a "top level tag group", that can contain definitions, Onset, etc tags.
        is_group: bool
            If true, group is contained by parenthesis
        Returns
        -------
        []
            The validation issues associated with each level in a HED string.
        """
        validation_issues = []
        validation_issues += self.check_duplicate_tags_exist(original_tag_list)
        validation_issues += self.check_tag_level_issue(original_tag_list, is_top_level, is_group)
        return validation_issues

    def run_all_tags_validators(self, tags, check_for_warnings):
        """Validates the multi-tag properties in a hed string, eg required tags.

        Parameters
        ----------
        tags: [HedTag]
          A list containing the tags in a HED string.
        check_for_warnings: bool
            If True, also check for warnings.
        Returns
        -------
        []
            The validation issues associated with the tags in a HED string.
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
        """Reports an error if it finds any invalid characters as defined by TagValidator.INVALID_STRING_CHARS

        Parameters
        ----------
        hed_string: str
            A hed string.
        Returns
        -------
        list
            A validation issues []. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        for index, character in enumerate(hed_string):
            if character in TagValidator.INVALID_STRING_CHARS:
                validation_issues += self._report_invalid_character_error(hed_string, index)

        return validation_issues

    def check_count_tag_group_parentheses(self, hed_string):
        """Reports a validation error if there are an unequal number of opening or closing parentheses. This is the
         first check before the tags are parsed.

        Parameters
        ----------
        hed_string: str
            A hed string.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.

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
        """Reports a validation error if there are missing commas or commas in tags that take values.

        Parameters
        ----------
        hed_string: str
            A hed string.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.

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
        """Reports a validation errors for any repeated or erroneous slashes

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        validation_issues = []
        for match in self.pattern_doubleslash.finditer(original_tag.org_tag):
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_NODE_NAME_EMPTY,
                                                           tag=original_tag,
                                                           index_in_tag=match.start(),
                                                           index_in_tag_end=match.end())

        return validation_issues

    def check_tag_invalid_chars(self, original_tag, allow_placeholders):
        """Reports a validation errors for any invalid characters in the given tag.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        allow_placeholders: bool
            Allow placeholder characters(#) if True
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        allowed_chars = self.TAG_ALLOWED_CHARS
        if not self._hed_schema or not self._hed_schema.is_hed3_schema:
            allowed_chars += " "
        if allow_placeholders:
            allowed_chars += "#"
        return self._check_invalid_chars(original_tag.org_base_tag, allowed_chars, original_tag)

    def check_tag_exists_in_schema(self, original_tag, check_for_warnings=False):
        """Reports a validation error if the tag provided is not a valid tag or doesn't take a value.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        check_for_warnings: bool
            If True, also check for warnings.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        validation_issues = []
        if self._hed_schema.is_basic_tag(original_tag) or self._hed_schema.is_takes_value_tag(original_tag):
            return validation_issues

        is_extension_tag = self._hed_schema.is_extension_allowed_tag(original_tag)
        if not is_extension_tag:
            validation_issues += ErrorHandler.format_error(ValidationErrors.INVALID_EXTENSION, tag=original_tag)
        elif check_for_warnings:
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_EXTENDED, tag=original_tag,
                                                           index_in_tag=len(original_tag.org_base_tag),
                                                           index_in_tag_end=None)
        return validation_issues

    def check_tag_unit_class_units_are_valid(self, original_tag):
        """Reports a validation error if the tag provided has a unit class and the units are incorrect.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        if self._hed_schema.is_unit_class_tag(original_tag):
            stripped_value = self._hed_schema.get_stripped_unit_value(original_tag)
            if not self._validate_value_class_portion(original_tag, stripped_value):
                tag_unit_class_units = self._hed_schema.get_tag_unit_class_units(original_tag)
                if tag_unit_class_units:
                    validation_issues += ErrorHandler.format_error(ValidationErrors.HED_UNITS_INVALID,
                                                                   original_tag,
                                                                   unit_class_units=tag_unit_class_units)
        return validation_issues

    def check_tag_value_class_valid(self, original_tag):
        """Reports a validation error if the tag provided has has an invalid value portion

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        Returns
        -------
        error_list: []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        validation_issues = []
        if not self._validate_value_class_portion(original_tag, original_tag.extension_or_value_portion):
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_VALUE_INVALID,
                                                           original_tag)

        return validation_issues

    def check_tag_requires_child(self, original_tag):
        """Reports a validation error if the tag provided has the 'requireChild' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        if self._hed_schema.tag_has_attribute(original_tag, HedKey.RequireChild):
            validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_REQUIRES_CHILD,
                                                           tag=original_tag)
        return validation_issues

    def check_tag_unit_class_units_exist(self, original_tag):
        """Reports a validation warning if the tag provided has a unit class but no units are not specified.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        Returns
        -------
        []
            A list validation error dicts.  Returns empty list if no issues found
        """
        validation_issues = []
        if self._hed_schema.is_unit_class_tag(original_tag):
            tag_unit_values = original_tag.extension_or_value_portion
            if tag_validator_util.validate_numeric_value_class(tag_unit_values):
                default_unit = self._hed_schema.get_unit_class_default_unit(original_tag)
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_UNITS_DEFAULT_USED,
                                                               tag=original_tag,
                                                               default_unit=default_unit)
        return validation_issues

    def check_for_invalid_extension_chars(self, original_tag):
        """Reports a validation errors for any invalid characters in the given extension/value portion.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the error.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        allowed_chars = self.TAG_ALLOWED_CHARS
        allowed_chars += self.DEFAULT_ALLOWED_PLACEHOLDER_CHARS
        allowed_chars += " "
        return self._check_invalid_chars(original_tag.extension_or_value_portion, allowed_chars, original_tag,
                                         starting_index=len(original_tag.org_base_tag) + 1)

    def check_capitalization(self, original_tag):
        """Reports a validation warning if the tag isn't correctly capitalized.

        Parameters
        ----------
        original_tag: HedTag
            The original tag that is used to report the warning.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        validation_issues = []
        tag_names = str(original_tag).split("/")
        # Cut off the # sign tag if it exists
        if self._hed_schema and self._hed_schema.is_takes_value_tag(original_tag):
            tag_names = tag_names[:-1]
        for tag_name in tag_names:
            correct_tag_name = tag_name.capitalize()
            if tag_name != correct_tag_name and not re.search(self.CAMEL_CASE_EXPRESSION, tag_name):
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_STYLE_WARNING,
                                                               tag=original_tag)
                break
        return validation_issues

    def check_duplicate_tags_exist(self, original_tag_list):
        """Reports a validation error if two or more tags are the same.

        This only tracks exact matches, it will not catch two identical  value tags with different values.
        Parameters
        ----------
        original_tag_list: [HedTag]
            A list containing tags that are used to report the error.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        tag_set = set()
        for tag in original_tag_list:
            formatted_tag = tag.lower()
            if formatted_tag in tag_set:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_REPEATED, tag=tag)
                continue
            tag_set.add(formatted_tag)

        return validation_issues

    def check_tag_level_issue(self, original_tag_list, is_top_level, is_group):
        """
            Checks all tags in the group to verify they are correctly positioned in the hierarchy

        Parameters
        ----------
        original_tag_list: [HedTag]
           A list containing the original tags.
        is_top_level: bool
            If True, this group is a "top level tag group", that can contain definitions, Onset, etc tags.
        is_group: bool
            If true, group is contained by parenthesis
        Returns
        -------
        []
            The validation issues associated with each level in a HED string.
        """
        validation_issues = []
        if self._run_semantic_validation:
            top_level_tags = [tag for tag in original_tag_list if
                              self._hed_schema.base_tag_has_attribute(tag, HedKey.TopLevelTagGroup)]
            tag_group_tags = [tag for tag in original_tag_list if
                              self._hed_schema.base_tag_has_attribute(tag, HedKey.TagGroup)]
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
        """Reports a validation error if the required tags aren't present.

        Parameters
        ----------
        tags: [HedTag]
            A list containing the tags.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        validation_issues = []
        required_tag_prefixes = self._hed_schema.get_all_tags_with_attribute(HedKey.RequiredPrefix)
        for capitalized_required_tag_prefix in required_tag_prefixes:
            required_tag_prefix = capitalized_required_tag_prefix.lower()
            if sum([x.lower().startswith(required_tag_prefix) for x in tags]) < 1:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_REQUIRED_TAG_MISSING,
                                                               tag_prefix=capitalized_required_tag_prefix)
        return validation_issues

    def check_multiple_unique_tags_exist(self, original_tag_list):
        """Reports a validation error if two or more tags start with a tag prefix that has the 'unique' attribute.

        Parameters
        ----------
        original_tag_list: [HedTag]
            A list containing tags that are used to report the error.
        Returns
        -------
        []
            A validation issues list. If no issues are found then an empty list is returned.
        """
        validation_issues = []
        unique_tag_prefixes = self._hed_schema.get_all_tags_with_attribute(HedKey.Unique)
        for capitalized_unique_tag_prefix in unique_tag_prefixes:
            unique_tag_prefix = capitalized_unique_tag_prefix.lower()
            unique_tag_prefix_bool_mask = [x.lower().startswith(unique_tag_prefix) for x in original_tag_list]
            if sum(unique_tag_prefix_bool_mask) > 1:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TAG_NOT_UNIQUE,
                                                               tag_prefix=capitalized_unique_tag_prefix)
        return validation_issues

    # ==========================================================================
    # Private utility functions
    # =========================================================================+
    def _validate_value_class_portion(self, original_tag, portion_to_validate):
        if portion_to_validate is None:
            return False

        # Fallback code for no value classes
        if not self._hed_schema.value_classes:
            unit_class_types = self._hed_schema.get_tag_unit_classes(original_tag)
            if tag_validator_util.validate_value_class_type(portion_to_validate, unit_class_types):
                return True
            return tag_validator_util.validate_numeric_value_class(portion_to_validate)
        if not self._hed_schema.is_value_class_tag(original_tag):
            return False

        value_class_types = self._hed_schema.get_tag_value_classes(original_tag)
        return tag_validator_util.validate_value_class_type(portion_to_validate, value_class_types)

    def _report_invalid_character_error(self, hed_string, index):
        """Reports a error that is related to an invalid character.

        Parameters
        ----------
        hed_string: str
            The HED string that caused the error.
        index: int
            The index of the invalid character in the HED string.
        Returns
        -------
        [{}]
            A singleton list with a dictionary representing the error.

        """
        error_type = ValidationErrors.HED_CHARACTER_INVALID
        character = hed_string[index]
        if character == "~":
            error_type = ValidationErrors.HED_TILDES_UNSUPPORTED
        return ErrorHandler.format_error(error_type, char_index=index,
                                         source_string=hed_string)

    @staticmethod
    def _comma_is_missing_after_closing_parentheses(last_non_empty_character, current_character):
        """
        Checks to see if a comma is missing after a closing parentheses in a HED string.

        This is a helper function for the find_missing_commas_in_hed_string function.

        Parameters
        ----------
        last_non_empty_character: str
            The last non-empty string in the HED string.
        current_character: str
            The current character in the HED string.
        Returns
        -------
        bool
            True if a comma is missing after a closing parentheses. False, if otherwise.

        """
        return last_non_empty_character == TagValidator.CLOSING_GROUP_CHARACTER and \
            not (TagValidator._character_is_delimiter(current_character)
                 or current_character == TagValidator.CLOSING_GROUP_CHARACTER)

    @staticmethod
    def _character_is_delimiter(character):
        """Checks to see if the character is a delimiter. A delimiter is a comma

        Parameters
        ----------
        character: str
            A string character.
        Returns
        -------
        bool
            Returns true if the character is a delimiter. False, if otherwise. A delimiter is a comma

        """
        return character == TagValidator.COMMA

    def check_for_placeholder(self, original_tag):
        """
            Checks for a placeholder character in the extension/value portion of a tag, unless they are allowed.

        Parameters
        ----------
        original_tag : HedTag

        Returns
        -------
        error_list: [{}]
        """
        validation_issues = []
        if not original_tag.is_definition:
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
