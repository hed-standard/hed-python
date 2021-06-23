"""
This module is used to validate the HED tags as strings.

"""

import datetime
import re
import inflect

from hed.errors import error_reporter
from hed.schema import HedKey
from hed.errors.error_types import ValidationErrors, ValidationWarnings

pluralize = inflect.engine()
pluralize.defnoun("hertz", "hertz")


class TagValidator:
    CAMEL_CASE_EXPRESSION = r'([A-Z-]+\s*[a-z-]*)+'
    DIGIT_OR_POUND_EXPRESSION = r'^(-?[\d.]+(?:e-?\d+)?|#)$'
    INVALID_STRING_CHARS = '[]{}~'
    OPENING_GROUP_CHARACTER = '('
    CLOSING_GROUP_CHARACTER = ')'
    COMMA = ','
    CLOCK_TIME_UNIT_CLASS = 'clockTime'
    DATE_TIME_UNIT_CLASS = 'dateTime'
    TIME_UNIT_CLASS = 'time'

    def __init__(self, hed_schema=None, check_for_warnings=False, run_semantic_validation=True,
                 allow_numbers_to_be_pound_sign=False, error_handler=None):
        """Constructor for the Tag_Validator class.

        Parameters
        ----------
        hed_schema: HedSchema
            A HedSchema object.
        allow_numbers_to_be_pound_sign: bool
            If true, considers # equal to a number for validation purposes.  This is so it can validate templates.
        error_handler : ErrorHandler or None
            Used to report errors.  Uses a default one if none passed in.
        Returns
        -------
        TagValidator
            A Tag_Validator object.

        """
        if error_handler is None:
            error_handler = error_reporter.ErrorHandler()
        self._error_handler = error_handler
        self._hed_schema = hed_schema
        self._check_for_warnings = check_for_warnings
        self._run_semantic_validation = run_semantic_validation
        if hed_schema:
            self._hed_schema_dictionaries = hed_schema.dictionaries
        else:
            self._hed_schema_dictionaries = {}
            self._run_semantic_validation = False
        self._placeholders_allowed_in_strings = allow_numbers_to_be_pound_sign

        self.UNIT_CLASS_TYPE_DICT = {
            self.DATE_TIME_UNIT_CLASS: self._is_date_time,
            self.CLOCK_TIME_UNIT_CLASS: self._is_clock_face_time,
            self.TIME_UNIT_CLASS: self._is_clock_face_time,
        }

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

    def run_individual_tag_validators(self, original_tag):
        """Runs the validators on the individual tags in a HED string.

         Parameters
         ----------
         original_tag: HedTag
            A original tag.
         Returns
         -------
         []
             The validation issues associated with the top-level in the HED string.
         """
        validation_issues = []
        if self._run_semantic_validation:
            validation_issues += self.check_tag_exists_in_schema(original_tag)
            validation_issues += self.check_tag_unit_class_units_are_valid(original_tag)
            validation_issues += self.check_tag_requires_child(original_tag)
            if self._check_for_warnings:
                validation_issues += self.check_tag_unit_class_units_exist(original_tag)
        if self._check_for_warnings:
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

    def run_all_tags_validators(self, tags):
        """Validates the multi-tag properties in a hed string, eg required tags.

         Parameters
         ----------
         tags: [HedTag]
            A list containing the tags in a HED string.
         Returns
         -------
         []
             The validation issues associated with the tags in a HED string.
         """
        validation_issues = []
        if self._run_semantic_validation:
            if self._check_for_warnings:
                validation_issues += self.check_for_required_tags(tags)
            validation_issues += self.check_multiple_unique_tags_exist(tags)
        return validation_issues

    # ==========================================================================
    # Basic public facing attribute getters for tags
    # =========================================================================+
    def is_extension_allowed_tag(self, original_tag):
        """Checks to see if the tag has the 'extensionAllowed' attribute. It will strip the tag until there are no more
        slashes to check if its ancestors have the attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        tag_takes_extension: bool
            True if the tag has the 'extensionAllowed' attribute. False, if otherwise.
        """
        base_tag = original_tag.base_tag.lower()
        return self._hed_schema.tag_has_attribute(base_tag, HedKey.ExtensionAllowedPropagated)

    def is_takes_value_tag(self, original_tag):
        """Checks to see if the tag has the 'takesValue' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'takesValue' attribute. False, if otherwise.

        """
        return self._value_tag_has_attribute(original_tag, HedKey.TakesValue)

    def is_unit_class_tag(self, original_tag):
        """Checks to see if the tag has the 'unitClass' attribute.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'unitClass' attribute. False, if otherwise.

        """
        return self._value_tag_has_attribute(original_tag, HedKey.UnitClass)

    def get_tag_unit_classes(self, original_tag):
        """Gets the unit classes associated with a particular tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        []
            A list containing the unit classes associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit classes associated with it.

        """
        unit_classes = self._value_tag_has_attribute(original_tag, HedKey.UnitClass, return_value=True)
        if unit_classes:
            unit_classes = unit_classes.split(',')
        else:
            unit_classes = []
        return unit_classes

    def get_tag_unit_class_units(self, original_tag):
        """Gets the unit class units associated with a particular tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        []
            A list containing the unit class units associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit class units associated with it.

        """
        units = []
        unit_classes = self.get_tag_unit_classes(original_tag)
        for unit_class in unit_classes:
            units += (self._hed_schema_dictionaries[HedKey.UnitClasses][unit_class])
        return units

    def get_unit_class_default_unit(self, original_tag):
        """Gets the default unit class unit that is associated with the specified tag.

        Parameters
        ----------
        original_tag: HedTag
            The tag that is used to do the validation.
        Returns
        -------
        str
            The default unit class unit associated with the specific tag. If the tag doesn't have a unit class then an
            empty string is returned.

        """
        default_unit = ''
        unit_classes = self.get_tag_unit_classes(original_tag)
        if unit_classes:
            first_unit_class = unit_classes[0]
            default_unit = self._hed_schema_dictionaries[HedKey.DefaultUnits][first_unit_class]

        return default_unit

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
        number_of_opening_parentheses = hed_string.count('(')
        number_of_closing_parentheses = hed_string.count(')')
        if number_of_opening_parentheses != number_of_closing_parentheses:
            validation_issues += self._error_handler.format_error(ValidationErrors.PARENTHESES,
                                                                  opening_parentheses_count=number_of_opening_parentheses,
                                                                  closing_parentheses_count=number_of_closing_parentheses)
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

        for i in range(len(hed_string)):
            current_character = hed_string[i]
            current_tag += current_character
            if not current_character.strip():
                continue
            if TagValidator._character_is_delimiter(current_character):
                if current_tag.strip() == current_character:
                    issues += self._error_handler.format_error(ValidationErrors.EMPTY_TAG, source_string=hed_string,
                                                               char_index=i)
                    current_tag = ''
                    continue
                current_tag = ''
            elif current_character == self.OPENING_GROUP_CHARACTER:
                if current_tag.strip() == self.OPENING_GROUP_CHARACTER:
                    current_tag = ''
                else:
                    issues += self._error_handler.format_error(ValidationErrors.COMMA_MISSING, tag=current_tag)
            elif TagValidator._comma_is_missing_after_closing_parentheses(last_non_empty_valid_character,
                                                                          current_character):
                issues += self._error_handler.format_error(ValidationErrors.COMMA_MISSING, tag=current_tag[:-1])
                break
            last_non_empty_valid_character = current_character
            last_non_empty_valid_index = i
        if TagValidator._character_is_delimiter(last_non_empty_valid_character):
            issues += self._error_handler.format_error(ValidationErrors.EMPTY_TAG,
                                                       char_index=last_non_empty_valid_index,
                                                       source_string=hed_string)
        return issues

    pattern_doubleslash = re.compile(r"([ \t/]{2,}|^/|/$)")

    def check_tag_formatting(self, original_tag):
        validation_issues = []
        for match in self.pattern_doubleslash.finditer(str(original_tag)):
            validation_issues += self._error_handler.format_error(ValidationErrors.EXTRA_SLASHES_OR_SPACES,
                                                                  tag=original_tag,
                                                                  index_in_tag=match.start(),
                                                                  index_in_tag_end=match.end())

        return validation_issues

    def check_tag_exists_in_schema(self, original_tag):
        """Reports a validation error if the tag provided is not a valid tag or doesn't take a value.

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
        formatted_tag = original_tag.lower()
        if self._hed_schema_dictionaries[HedKey.AllTags].get(formatted_tag) or \
                self.is_takes_value_tag(original_tag):
            return validation_issues

        is_extension_tag = self.is_extension_allowed_tag(original_tag)
        if not is_extension_tag:
            validation_issues += self._error_handler.format_error(ValidationErrors.INVALID_EXTENSION, tag=original_tag)
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
        formatted_tag = original_tag.lower()
        if self.is_unit_class_tag(original_tag):
            tag_unit_classes = self.get_tag_unit_classes(original_tag)
            original_tag_unit_value = original_tag.extension_or_value_portion
            formatted_tag_unit_value = original_tag_unit_value.lower()
            # Check for special known types with extra validation, like clock face or dates.
            for unit_class_type in self.UNIT_CLASS_TYPE_DICT:
                if unit_class_type in self._hed_schema_dictionaries[HedKey.UnitClasses] \
                        and unit_class_type in tag_unit_classes \
                        and self.UNIT_CLASS_TYPE_DICT[unit_class_type](formatted_tag_unit_value):
                    return validation_issues

            tag_unit_class_units = self.get_tag_unit_class_units(original_tag)
            if re.search(self.DIGIT_OR_POUND_EXPRESSION,
                         self._validate_units(original_tag_unit_value,
                                              formatted_tag_unit_value,
                                              tag_unit_class_units)):
                pass
            else:
                validation_issues += self._error_handler.format_error(ValidationErrors.UNIT_CLASS_INVALID_UNIT,
                                                                      original_tag,
                                                                      unit_class_units=tag_unit_class_units)

        if not self._placeholders_allowed_in_strings and "#" in formatted_tag:
            pound_index = original_tag.org_tag.find("#")
            validation_issues += self._error_handler.format_error(ValidationErrors.INVALID_TAG_CHARACTER,
                                                                  tag=original_tag, index_in_tag=pound_index,
                                                                  index_in_tag_end=pound_index + 1)

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
        if self._hed_schema_dictionaries[HedKey.RequireChild].get(original_tag.lower()):
            validation_issues += self._error_handler.format_error(ValidationErrors.REQUIRE_CHILD, tag=original_tag)
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
        if self.is_unit_class_tag(original_tag):
            tag_unit_values = original_tag.extension_or_value_portion
            if re.search(self.DIGIT_OR_POUND_EXPRESSION, tag_unit_values):
                default_unit = self.get_unit_class_default_unit(original_tag)
                validation_issues += self._error_handler.format_error(ValidationWarnings.UNIT_CLASS_DEFAULT_USED,
                                                                      tag=original_tag,
                                                                      default_unit=default_unit)
        return validation_issues

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
        if self.is_takes_value_tag(original_tag):
            tag_names = tag_names[:-1]
        for tag_name in tag_names:
            correct_tag_name = tag_name.capitalize()
            if tag_name != correct_tag_name and not re.search(self.CAMEL_CASE_EXPRESSION, tag_name):
                validation_issues += self._error_handler.format_error(ValidationWarnings.CAPITALIZATION,
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
                validation_issues += self._error_handler.format_error(ValidationErrors.DUPLICATE, tag=tag)
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
                              self._hed_schema.tag_has_attribute(tag.base_tag.lower(), HedKey.TopLevelTagGroup)]
            tag_group_tags = [tag for tag in original_tag_list if
                              self._hed_schema.tag_has_attribute(tag.base_tag.lower(), HedKey.TagGroup)]
            for tag_group_tag in tag_group_tags:
                if not is_group:
                    validation_issues += self._error_handler.format_error(ValidationErrors.HED_TAG_GROUP_TAG,
                                                                          tag=tag_group_tag)
            for top_level_tag in top_level_tags:
                if not is_top_level:
                    validation_issues += self._error_handler.format_error(ValidationErrors.HED_TOP_LEVEL_TAG,
                                                                          tag=top_level_tag)

            if is_top_level and len(top_level_tags) > 1:
                validation_issues += self._error_handler.format_error(ValidationErrors.HED_MULTIPLE_TOP_TAGS,
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
        required_tag_prefixes = self._hed_schema_dictionaries[HedKey.RequiredPrefix]
        for required_tag_prefix in required_tag_prefixes:
            capitalized_required_tag_prefix = \
                self._hed_schema_dictionaries[HedKey.RequiredPrefix][required_tag_prefix]
            if sum([x.lower().startswith(required_tag_prefix) for x in tags]) < 1:
                validation_issues += self._error_handler.format_error(ValidationWarnings.REQUIRED_PREFIX_MISSING,
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
        unique_tag_prefixes = self._hed_schema_dictionaries[HedKey.Unique]
        for unique_tag_prefix in unique_tag_prefixes:
            unique_tag_prefix_bool_mask = [x.lower().startswith(unique_tag_prefix) for x in original_tag_list]
            if sum(unique_tag_prefix_bool_mask) > 1:
                validation_issues += self._error_handler.format_error(ValidationErrors.MULTIPLE_UNIQUE,
                                                                      tag_prefix=unique_tag_prefixes[unique_tag_prefix])
        return validation_issues

    # ==========================================================================
    # Private utility functions
    # =========================================================================+
    def _get_valid_unit_plural(self, unit):
        """
        Parameters
        ----------
        unit: str
            unit to generate plural forms
        Returns
        -------
        [str]
            list of plural units
        """
        derivative_units = [unit]
        if self._hed_schema.has_unit_modifiers and \
                self._hed_schema_dictionaries[HedKey.UnitSymbol].get(unit) is None:
            derivative_units.append(pluralize.plural(unit))
        return derivative_units

    def _validate_units(self, original_tag_unit_value, formatted_tag_unit_value, tag_unit_class_units):
        """Checks to see if the specified string has a valid unit, and removes it if so.

        Parameters
        ----------
        original_tag_unit_value: str
            The unformatted value of the tag
        formatted_tag_unit_value: str
            The formatted value of the tag
        tag_unit_class_units: [str]
            A list of valid units for this tag
        Returns
        -------
        str
            A tag_unit_values with the valid unit removed, if one was present.
            Otherwise, returns tag_unit_values

        """
        tag_unit_class_units = sorted(tag_unit_class_units, key=len, reverse=True)
        for unit in tag_unit_class_units:
            derivative_units = self._get_valid_unit_plural(unit)
            for derivative_unit in derivative_units:
                if self._hed_schema.has_unit_modifiers and \
                        self._hed_schema_dictionaries[HedKey.UnitSymbol].get(unit):
                    found_unit, stripped_value = self._strip_off_units_if_valid(original_tag_unit_value,
                                                                                derivative_unit,
                                                                                True)
                else:
                    found_unit, stripped_value = self._strip_off_units_if_valid(formatted_tag_unit_value,
                                                                                derivative_unit,
                                                                                False)
                if found_unit:
                    return stripped_value

        return formatted_tag_unit_value

    @staticmethod
    def _is_clock_face_time(time_string):
        """Checks to see if the specified string is a valid HH:MM time string.

        Parameters
        ----------
        time_string: str
            A time string.
        Returns
        -------
        bool
            True if the time string is valid. False, if otherwise.

        """
        try:
            time_obj = datetime.time.fromisoformat(time_string)
            return not time_obj.tzinfo and not time_obj.microsecond
        except ValueError:
            return False

    @staticmethod
    def _is_date_time(date_time_string):
        """Checks to see if the specified string is a valid ISO 8601 datetime string.

        Parameters
        ----------
        date_time_string: str
            A datetime string.
        Returns
        -------
        bool
            True if the datetime string is valid. False, if otherwise.

        """
        try:
            date_time_obj = datetime.datetime.fromisoformat(date_time_string)
            return not date_time_obj.tzinfo
        except ValueError:
            return False

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
        error_type = ValidationErrors.INVALID_CHARACTER
        character = hed_string[index]
        if character == "~":
            error_type = ValidationErrors.TILDES_NOT_SUPPORTED
        return self._error_handler.format_error(error_type, char_index=index,
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
        """Checks to see if the character is a delimiter. A delimiter is a commma

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

    def _strip_off_units_if_valid(self, unit_value, unit, is_unit_symbol):
        """Validates and strips units from a value.

        Parameters
        ----------
        unit_value: str
            The value to validate.
        unit: str
            The unit to strip.
        is_unit_symbol: bool
            Whether the unit is a symbol.
        Returns
        -------
        tuple
            The found unit and the stripped value.
        """
        found_unit = False
        stripped_value = ''

        should_be_prefix = self._hed_schema_dictionaries[HedKey.UnitPrefix].get(unit, False)
        if should_be_prefix and str(unit_value).startswith(unit):
            found_unit = True
            stripped_value = str(unit_value)[len(unit):].strip()
        elif not should_be_prefix and str(unit_value).endswith(unit):
            found_unit = True
            stripped_value = str(unit_value)[0:-len(unit)].strip()

        if found_unit and self._hed_schema.has_unit_modifiers:
            if is_unit_symbol:
                modifier_key = HedKey.SIUnitSymbolModifier
            else:
                modifier_key = HedKey.SIUnitModifier

            for unit_modifier in self._hed_schema_dictionaries[modifier_key]:
                if stripped_value.startswith(unit_modifier):
                    stripped_value = stripped_value[len(unit_modifier):].strip()
                elif stripped_value.endswith(unit_modifier):
                    stripped_value = stripped_value[0:-len(unit_modifier)].strip()
        return found_unit, stripped_value

    def _value_tag_has_attribute(self, original_tag, key=HedKey.ExtensionAllowedPropagated,
                                 return_value=False):
        """
            Will return if original tag has the specified attribute, or False if original tag is not a takes value tag.

        Parameters
        ----------
        original_tag : HedTag

        key : str
            A HedKey value to check for
        return_value : bool
            If true, returns the value of the attribute, rather than True/False

        Returns
        -------
        attribute_name_or_value: bool or str
            Returns the name or value of the specified attribute
        """
        if key not in self._hed_schema_dictionaries:
            return False
        value_class_tag = original_tag.base_tag.lower() + "/#"

        value = self._hed_schema_dictionaries[key].get(value_class_tag, False)
        if return_value:
            return value
        return bool(value)
