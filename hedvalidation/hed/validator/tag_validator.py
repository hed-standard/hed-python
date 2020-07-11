"""
This module is used to validate the HED tags as strings.

"""

import re
import time
import inflect
from hed.validator import error_reporter
from hed.validator import warning_reporter

pluralize = inflect.engine()
pluralize.defnoun("hertz", "hertz")


class TagValidator:
    CAMEL_CASE_EXPRESSION = r'([A-Z-]+\s*[a-z-]*)+'
    CHARACTER_ERROR_TYPE = 'invalidCharacter'
    CLOCK_TIME_UNIT_CLASS = 'clockTime'
    COMMA_ERROR_TYPE = 'commaMissing'
    COMMA_VALID_ERROR_TYPE = 'extraCommaOrInvalid'
    DEFAULT_UNIT_ATTRIBUTE = 'default'
    DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE = 'defaultUnits'
    DIGIT_EXPRESSION = r'^-?[\d.]+(?:e-?\d+)?$'
    DUPLICATE_ERROR_TYPE = 'duplicateTag'
    EXTENSION_ALLOWED_ATTRIBUTE = 'extensionAllowed'
    INVALID_CHARS = '[]{}'
    PARENTHESES_ERROR_TYPE = 'parentheses'
    REQUIRE_CHILD_ERROR_TYPE = 'childRequired'
    REQUIRE_CHILD_TYPE = 'requireChild'
    REQUIRED_ERROR_TYPE = 'requiredPrefixMissing'
    REQUIRED_PREFIX_TYPE = 'required'
    TAG_DICTIONARY_KEY = 'tags'
    TAKES_VALUE_ATTRIBUTE = 'takesValue'
    TILDE_ERROR_TYPE = 'tooManyTildes'
    TIME_UNIT_CLASS = 'time'
    UNIQUE_ERROR_TYPE = 'multipleUniqueTags'
    UNIQUE_TAG_TYPE = 'unique'
    UNIT_CLASS_ATTRIBUTE = 'unitClass'
    UNIT_CLASS_UNITS_ELEMENT = 'units'
    UNIT_SYMBOL_TYPE = 'unitSymbol'
    UNITS_ELEMENT = 'units'
    VALID_ERROR_TYPE = 'invalidTag'
    OPENING_GROUP_CHARACTER = '('
    CLOSING_GROUP_CHARACTER = ')'
    DOUBLE_QUOTE = '"'
    COMMA = ','
    TILDE = '~'
    SI_UNIT_MODIFIER_KEY = 'SIUnitModifier'
    SI_UNIT_SYMBOL_MODIFIER_KEY = 'SIUnitSymbolModifier'

    def __init__(self, hed_dictionary=None, check_for_warnings=False, run_semantic_validation=True):
        """Constructor for the Tag_Validator class.

        Parameters
        ----------
        hed_dictionary: HedDictionary
            A Hed_Dictionary object.

        Returns
        -------
        TagValidator
            A Tag_Validator object.

        """
        self._hed_dictionary = hed_dictionary
        if hed_dictionary:
            self._hed_dictionary_dictionaries = hed_dictionary.get_dictionaries()
        else:
            self._hed_dictionary_dictionaries = None
        self._check_for_warnings = check_for_warnings
        self._issue_count = 0
        self._error_count = 0
        self._warning_count = 0
        self._run_semantic_validation = run_semantic_validation

    def _increment_issue_count(self, is_error=True):
        """Increments the validation issue count

         Parameters
         ----------
         is_error: bool
            True if the issue is an error, False if it is not.
         Returns
         -------

         """
        self._issue_count += 1
        if is_error:
            self._error_count += 1
        else:
            self._warning_count += 1

    def get_issue_count(self):
        """Gets the issue count

         Parameters
         ----------

         Returns
         -------
         int
            The issue count
         """
        return self._issue_count

    def get_warning_count(self):
        """Gets the warning count

         Parameters
         ----------

         Returns
         -------
         int
            The warning count
         """
        return self._warning_count

    def get_error_count(self):
        """Gets the error count

         Parameters
         ----------

         Returns
         -------
         int
            The error count
         """
        return self._error_count

    def run_individual_tag_validators(self, original_tag, formatted_tag, previous_original_tag='',
                                      previous_formatted_tag=''):
        """Runs the validators on the individual tags in a HED string.

         Parameters
         ----------
         original_tag: str
            A original tag.
         formatted_tag: str
            A format tag.
         previous_original_tag: str
            The previous original tag.
         previous_formatted_tag: str
            The previous format tag.
         Returns
         -------
         list
             The validation issues associated with the top-level in the HED string.

         """
        validation_issues = []
        if self._run_semantic_validation:
            validation_issues += self.tag_exist_in_schema(original_tag, formatted_tag, previous_original_tag,
                                                          previous_formatted_tag)
            validation_issues += self.check_if_tag_unit_class_units_are_valid(original_tag, formatted_tag)
            validation_issues += self.check_if_tag_requires_child(original_tag, formatted_tag)
            if self._check_for_warnings:
                validation_issues += self.check_if_tag_unit_class_units_exist(original_tag, formatted_tag)
        if self._check_for_warnings:
            validation_issues += self.check_capitalization(original_tag, formatted_tag)
        return validation_issues

    def run_tag_group_validators(self, tag_group, tag_group_string):
        """Runs the validators on the groups in a HED string.

         Parameters
         ----------
         tag_group: list
            A list containing the tags in a group.
         tag_group_string: str
            A string of the tag group.
         Returns
         -------
         list
             The validation issues associated with the groups in a HED string.

         """
        validation_issues = []
        validation_issues += self.check_number_of_group_tildes(tag_group, tag_group_string)
        return validation_issues

    def run_hed_string_validators(self, hed_string):
        """Runs the validators on the HED string. If this is passed then all the other validators are run on the tags
           and groups in the HED string.

         Parameters
         ----------
         hed_string: str
            A HED string.
         Returns
         -------
         list
             The validation issues associated with a HED string.

         """
        validation_issues = []
        validation_issues += self.find_invalid_character_issues(hed_string)
        validation_issues += self.count_tag_group_parentheses(hed_string)
        validation_issues += self.find_delimiter_issues_in_hed_string(hed_string)
        return validation_issues

    def run_tag_level_validators(self, original_tag_list, formatted_tag_list):
        """Runs the validators on tags at each level in a HED string. This pertains to the top-level, all groups,
           and nested groups.

         Parameters
         ----------
         original_tag_list: list
            A list containing the original tags.
         formatted_tag_list: list
            A list containing formatted tags.
         Returns
         -------
         list
             The validation issues associated with each level in a HED string.

         """
        validation_issues = []
        if self._run_semantic_validation:
            validation_issues += self.check_if_multiple_unique_tags_exist(original_tag_list, formatted_tag_list)
        validation_issues += self.check_if_duplicate_tags_exist(original_tag_list, formatted_tag_list)
        return validation_issues

    def run_top_level_validators(self, formatted_top_level_tags):
        """Runs the validators on tags at the top-level in a HED string.

         Parameters
         ----------
         formatted_top_level_tags: list
            A list containing the top-level tags in a HED string.
         Returns
         -------
         list
             The validation issues associated with the top-level in a HED string.

         """
        validation_issues = []
        if self._check_for_warnings and self._run_semantic_validation:
            validation_issues += self.check_for_required_tags(formatted_top_level_tags)
        return validation_issues

    def tag_exist_in_schema(self, original_tag, formatted_tag, previous_original_tag='', previous_formatted_tag=''):
        """Reports a validation error if the tag provided is not a valid tag or doesn't take a value.

        Parameters
        ----------
        original_tag: str
            The original tag that is used to report the error.
        formatted_tag: str
            The tag that is used to do the validation.
        previous_original_tag: str
            The previous original tag that is used to report the error.
        previous_formatted_tag: str
            The previous tag that is used to do the validation.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        is_extension_tag = self.is_extension_allowed_tag(formatted_tag)
        if self._hed_dictionary_dictionaries[TagValidator.TAG_DICTIONARY_KEY].get(formatted_tag) or \
                self.tag_takes_value(formatted_tag) or formatted_tag == TagValidator.TILDE:
            return validation_issues

        if not is_extension_tag and self.tag_takes_value(previous_formatted_tag):
            validation_issues += error_reporter.report_error_type(TagValidator.COMMA_VALID_ERROR_TYPE,
                                                                   tag=original_tag,
                                                                   previous_tag=previous_original_tag)
            self._increment_issue_count()
        elif not is_extension_tag:
            validation_issues += error_reporter.report_error_type(TagValidator.VALID_ERROR_TYPE, tag=original_tag)
            self._increment_issue_count()
        return validation_issues

    def tag_exists_in_schema(self, formatted_tag):
        """Checks to see if the tag is a valid HED tag.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag is a valid HED tag. False, if otherwise.

        """
        return self._hed_dictionary_dictionaries[TagValidator.TAG_DICTIONARY_KEY].get(formatted_tag) is not None

    def check_capitalization(self, original_tag, formatted_tag):
        """Reports a validation warning if the tag isn't correctly capitalized.

        Parameters
        ----------
        original_tag: str
            The original tag that is used to report the warning.
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        tag_names = original_tag.split("/")
        if self.tag_takes_value(formatted_tag):
            tag_names = tag_names[:-1]
        for tag_name in tag_names:
            correct_tag_name = tag_name.capitalize()
            if tag_name != correct_tag_name and not re.search(self.CAMEL_CASE_EXPRESSION, tag_name):
                validation_issues += warning_reporter.report_warning_type("capitalization", tag=original_tag)
                self._increment_issue_count(is_error=False)
                break
        return validation_issues

    def is_extension_allowed_tag(self, formatted_tag):
        """Checks to see if the tag has the 'extensionAllowed' attribute. It will strip the tag until there are no more
        slashes to check if its ancestors have the attribute.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'extensionAllowed' attribute. False, if otherwise.

        """
        tag_slash_indices = self.get_tag_slash_indices(formatted_tag)
        for tag_slash_index in tag_slash_indices:
            tag_substring = self.get_tag_substring_by_end_index(formatted_tag, tag_slash_index)
            if self._hed_dictionary.tag_has_attribute(tag_substring,
                                                      TagValidator.EXTENSION_ALLOWED_ATTRIBUTE):
                return True
        return False

    def tag_takes_value(self, formatted_tag):
        """Checks to see if the tag has the 'takesValue' attribute.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'takesValue' attribute. False, if otherwise.

        """
        takes_value_tag = self.replace_tag_name_with_pound(formatted_tag)
        return self._hed_dictionary.tag_has_attribute(takes_value_tag,
                                                      TagValidator.TAKES_VALUE_ATTRIBUTE)

    def is_unit_class_tag(self, formatted_tag):
        """Checks to see if the tag has the 'unitClass' attribute.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        bool
            True if the tag has the 'unitClass' attribute. False, if otherwise.

        """
        takes_value_tag = self.replace_tag_name_with_pound(formatted_tag)
        if not self._hed_dictionary.has_unit_classes:
            return False
        return self._hed_dictionary.tag_has_attribute(takes_value_tag,
                                                      TagValidator.UNIT_CLASS_ATTRIBUTE)

    def replace_tag_name_with_pound(self, formatted_tag):
        """Replaces the tag name with the pound sign.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        str
            A tag with the a pound sign in place of it's name.

        """
        pound_sign_tag = '#'
        last_tag_slash_index = formatted_tag.rfind('/')
        if last_tag_slash_index != -1:
            pound_sign_tag = formatted_tag[:last_tag_slash_index] + '/#'
        return pound_sign_tag

    def check_if_tag_unit_class_units_are_valid(self, original_tag, formatted_tag):
        """Reports a validation error if the tag provided has a unit class and the units are incorrect.

        Parameters
        ----------
        original_tag: str
            The original tag that is used to report the error.
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        if not self.tag_exists_in_schema(formatted_tag) and self.is_unit_class_tag(formatted_tag):
            tag_unit_classes = self.get_tag_unit_classes(formatted_tag)
            formatted_tag_unit_value = self.get_tag_name(formatted_tag)
            original_tag_unit_value = self.get_tag_name(original_tag)
            tag_unit_class_units = tuple(self.get_tag_unit_class_units(formatted_tag))
            if (TagValidator.CLOCK_TIME_UNIT_CLASS in
                    self._hed_dictionary_dictionaries[self.UNITS_ELEMENT]):
                if (TagValidator.CLOCK_TIME_UNIT_CLASS in tag_unit_classes
                        and TagValidator.is_clock_face_time(formatted_tag_unit_value)):
                    return validation_issues
            elif (TagValidator.TIME_UNIT_CLASS in
                  self._hed_dictionary_dictionaries[self.UNITS_ELEMENT]):
                if (TagValidator.TIME_UNIT_CLASS in tag_unit_classes
                        and TagValidator.is_clock_face_time(formatted_tag_unit_value)):
                    return validation_issues
            if re.search(TagValidator.DIGIT_EXPRESSION,
                           self.validate_units(original_tag_unit_value,
                                               formatted_tag_unit_value,
                                               tag_unit_class_units)):
                pass
            else:
                validation_issues += error_reporter.report_error_type('unitClassInvalidUnit', tag=original_tag,
                                                                       unit_class_units=','.join(
                                                                           sorted(tag_unit_class_units)))
                self._increment_issue_count()
        return validation_issues

    def get_valid_unit_plural(self, unit):
        """
        Parameters
        ----------
        unit: str
            unit to generate plural forms
        Returns
        -------
        list
            list of plural units
        """
        derivative_units = [unit]
        if self._hed_dictionary.has_unit_modifiers and \
                self._hed_dictionary_dictionaries[self.UNIT_SYMBOL_TYPE].get(unit) is None:
            derivative_units.append(pluralize.plural(unit))
        return derivative_units

    def _strip_off_units_if_valid(self, unit_value, unit, is_unit_symbol):
        """

        Parameters
        ----------
        unit_value      -value of unit
        unit            -what the unit is
        is_unit_symbol  -unit symbol bool

        Returns
        -------
        tuple of the found unit and the stripped value
        """
        found_unit = False
        stripped_value = ''

        if str(unit_value).startswith(unit):
            found_unit = True
            stripped_value = str(unit_value)[len(unit):].strip()
        elif str(unit_value).endswith(unit):
            found_unit = True
            stripped_value = str(unit_value)[0:-len(unit)].strip()

        if found_unit and self._hed_dictionary.has_unit_modifiers:
            modifierKey = ''
            if is_unit_symbol:
                modifierKey = self.SI_UNIT_SYMBOL_MODIFIER_KEY
            else:
                modifierKey = self.SI_UNIT_MODIFIER_KEY

            for unit_modifier in self._hed_dictionary_dictionaries[modifierKey]:
                if stripped_value.startswith(unit_modifier):
                    stripped_value = stripped_value[len(unit_modifier):].strip()
                elif stripped_value.endswith(unit_modifier):
                    stripped_value = stripped_value[0:-len(unit_modifier)].strip()
        return found_unit, stripped_value

    def validate_units(self, original_tag_unit_value, formatted_tag_unit_value, tag_unit_class_units):
        """Checks to see if the specified string has a valid unit, and removes it if so

        Parameters
        ----------
        original_tag_unit_value
            The unformatted value of the tag
        formatted_tag_unit_value
            The formatted value of the tag
        tag_unit_class_units
            A list of valid units for this tag
        Returns
        -------
        str
            A tag_unit_values with the valid unit removed, if one was present.
            Otherwise, returns tag_unit_values

        """
        tag_unit_class_units = sorted(tag_unit_class_units, key=len, reverse=True)
        for unit in tag_unit_class_units:
            derivative_units = self.get_valid_unit_plural(unit)
            for derivative_unit in derivative_units:
                if self._hed_dictionary.has_unit_modifiers and \
                        self._hed_dictionary_dictionaries[self.UNIT_SYMBOL_TYPE].get(unit):
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

    def check_if_tag_unit_class_units_exist(self, original_tag, formatted_tag):
        """Reports a validation warning if the tag provided has a unit class but no units are not specified.

        Parameters
        ----------
        original_tag: str
            The original tag that is used to report the error.
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        str
            A validation warning string. If no errors are found then an empty string is returned.

        """
        validation_issues = []
        if self.is_unit_class_tag(formatted_tag):
            tag_unit_values = self.get_tag_name(formatted_tag)
            if re.search(TagValidator.DIGIT_EXPRESSION, tag_unit_values):
                default_unit = self.get_unit_class_default_unit(formatted_tag)
                validation_issues += warning_reporter.report_warning_type('unitClassDefaultUsed', tag=original_tag,
                                                                           default_unit=default_unit)
                self._increment_issue_count(is_error=False)
        return validation_issues

    def get_tag_name(self, tag):
        """Gets the tag name from the tag path

        Parameters
        ----------
        tag: str
            A tag which is a path.
        Returns
        -------
        string
            The tag name.

        """
        tag_name = tag
        tag_slash_indices = self.get_tag_slash_indices(tag)
        if tag_slash_indices:
            tag_name = tag[tag_slash_indices[-1] + 1:]
        return tag_name

    def get_tag_unit_classes(self, formatted_tag):
        """Gets the unit classes associated with a particular tag.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        list
            A list containing the unit classes associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit classes associated with it.

        """
        unit_classes = []
        unit_class_tag = self.replace_tag_name_with_pound(formatted_tag)
        if self.is_unit_class_tag(formatted_tag):
            unit_classes = self._hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE][unit_class_tag]
            unit_classes = unit_classes.split(',')
        return unit_classes

    def get_tag_unit_class_units(self, formatted_tag):
        """Gets the unit class units associated with a particular tag.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        list
            A list containing the unit class units associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit class units associated with it.

        """
        units = []
        unit_class_tag = self.replace_tag_name_with_pound(formatted_tag)
        if self.is_unit_class_tag(formatted_tag):
            unit_classes = self._hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE][unit_class_tag]
            unit_classes = unit_classes.split(',')

            for unit_class in unit_classes:
                try:
                    units += (self._hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_UNITS_ELEMENT][unit_class])
                except:
                    continue
        return units

    def get_unit_class_default_unit(self, formatted_tag):
        """Gets the default unit class unit that is associated with the specified tag.

        Parameters
        ----------
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        string
            The default unit class unit associated with the specific tag. If the tag doesn't have a unit class then an
            empty string is returned.

        """
        default_unit = ''
        unit_class_tag = self.replace_tag_name_with_pound(formatted_tag)
        if self.is_unit_class_tag(formatted_tag):
            has_default_attribute = self._hed_dictionary.tag_has_attribute(unit_class_tag,
                                                                           TagValidator.DEFAULT_UNIT_ATTRIBUTE)
            if has_default_attribute:
                default_unit = self._hed_dictionary_dictionaries[TagValidator.DEFAULT_UNIT_ATTRIBUTE][unit_class_tag]
            elif unit_class_tag in self._hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE]:
                unit_classes = \
                    self._hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE][unit_class_tag].split(',')
                first_unit_class = unit_classes[0]
                default_unit = self._hed_dictionary_dictionaries[TagValidator.DEFAULT_UNITS_FOR_TYPE_ATTRIBUTE][
                    first_unit_class]
        return default_unit

    def check_number_of_group_tildes(self, tag_group, tag_group_string):
        """Reports a validation error if the tag group has too many tildes.

        Parameters
        ----------
        tag_group: list
            A list containing the tags in a group.
        tag_group_string: str
            A string of the tag group.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        if tag_group.count('~') > 2:
            validation_issues += error_reporter.report_error_type(TagValidator.TILDE_ERROR_TYPE, tag=tag_group_string)
            self._increment_issue_count()
        return validation_issues

    def check_if_tag_requires_child(self, original_tag, formatted_tag):
        """Reports a validation error if the tag provided has the 'requireChild' attribute.

        Parameters
        ----------
        original_tag: str
            The original tag that is used to report the error.
        formatted_tag: str
            The tag that is used to do the validation.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        if self._hed_dictionary_dictionaries[TagValidator.REQUIRE_CHILD_TYPE].get(formatted_tag):
            validation_issues += error_reporter.report_error_type(TagValidator.REQUIRE_CHILD_ERROR_TYPE,
                                                                   tag=original_tag)
            self._increment_issue_count()
        return validation_issues

    def check_for_required_tags(self, formatted_top_level_tags):
        """Reports a validation error if the required tags aren't present.

        Parameters
        ----------
        formatted_top_level_tags: list
            A list containing the top-level tags.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        required_tag_prefixes = self._hed_dictionary_dictionaries[TagValidator.REQUIRED_PREFIX_TYPE]
        for required_tag_prefix in required_tag_prefixes:
            capitalized_required_tag_prefix = \
                self._hed_dictionary_dictionaries[TagValidator.REQUIRED_PREFIX_TYPE][required_tag_prefix]
            if sum([x.startswith(required_tag_prefix) for x in formatted_top_level_tags]) < 1:
                validation_issues += warning_reporter.report_warning_type(TagValidator.REQUIRED_ERROR_TYPE,
                                                                           tag_prefix=capitalized_required_tag_prefix)
                self._increment_issue_count(is_error=False)
        return validation_issues

    def check_if_multiple_unique_tags_exist(self, original_tag_list, formatted_tag_list):
        """Reports a validation error if two or more tags start with a tag prefix that has the 'unique' attribute.

        Parameters
        ----------
        original_tag_list: list
            A list containing tags that are used to report the error.
        formatted_tag_list: list
            A list containing tags that are used to do the validation.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        unique_tag_prefixes = self._hed_dictionary_dictionaries[TagValidator.UNIQUE_TAG_TYPE]
        for unique_tag_prefix in unique_tag_prefixes:
            unique_tag_prefix_bool_mask = [x.startswith(unique_tag_prefix) for x in formatted_tag_list]
            if sum(unique_tag_prefix_bool_mask) > 1:
                validation_issues += error_reporter.report_error_type(
                    TagValidator.UNIQUE_ERROR_TYPE,
                    tag_prefix=self._hed_dictionary_dictionaries[TagValidator.UNIQUE_TAG_TYPE][unique_tag_prefix])
                self._increment_issue_count()
        return validation_issues

    def tag_has_unique_prefix(self, tag):
        """Checks to see if the tag starts with a prefix.

        Parameters
        ----------
        tag: str
            A tag.
        Returns
        -------
        bool
            True if the tag starts with a unique prefix. False if otherwise.

        """
        unique_tag_prefixes = self._hed_dictionary_dictionaries[TagValidator.UNIQUE_TAG_TYPE]
        for unique_tag_prefix in unique_tag_prefixes:
            if tag.lower().startswith(unique_tag_prefix):
                return True
        return False

    def check_if_duplicate_tags_exist(self, original_tag_list, formatted_tag_list):
        """Reports a validation error if two or more tags are the same.

        Parameters
        ----------
        original_tag_list: list
            A list containing tags that are used to report the error.
        formatted_tag_list: list
            A list containing tags that are used to do the validation.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        duplicate_indices = set([])
        for tag_index, tag in enumerate(formatted_tag_list):
            all_indices = range(len(formatted_tag_list))
            for duplicate_index in all_indices:
                if tag_index == duplicate_index:
                    continue
                if formatted_tag_list[tag_index] != TagValidator.TILDE and \
                        formatted_tag_list[tag_index] == formatted_tag_list[duplicate_index] and \
                        tag_index not in duplicate_indices and duplicate_index not in duplicate_indices:
                    duplicate_indices.add(tag_index)
                    duplicate_indices.add(duplicate_index)
                    validation_issues += error_reporter.report_error_type(TagValidator.DUPLICATE_ERROR_TYPE,
                                                                           tag=original_tag_list[tag_index])
                    self._increment_issue_count()
        return validation_issues

    def get_tag_slash_indices(self, tag, slash='/'):
        """Gets all of the indices in a tag that are slashes.

        Parameters
        ----------
        tag: str
            A tag.
        slash: str
            The slash character. By default it is a forward slash.
        Returns
        -------
        list
            A list containing the indices of the tag slashes.

        """
        return [s.start() for s in re.finditer(slash, tag)]

    def get_tag_substring_by_end_index(self, tag, end_index):
        """Gets a tag substring from the start until the end index.

        Parameters
        ----------
        tag: str
            A tag.
        end_index: int
            A index for the tag substring to end.
        Returns
        -------
        str
            A tag substring.

        """
        if end_index != 0:
            return tag[:end_index]
        return tag

    def find_delimiter_issues_in_hed_string(self, hed_string):
        """Reports a validation error if there are missing commas or commas in tags that take values.

        Parameters
        ----------
        hed_string: str
            A hed string.
        Returns
        -------
        list
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
            if TagValidator.character_is_delimiter(current_character):
                if current_tag.strip() == current_character:
                    issues += error_reporter.report_error_type('extraDelimiter',
                                                               character=current_character,
                                                               index=i,
                                                               hed_string=hed_string)
                    current_tag = ''
                    continue
                current_tag = ''
            elif current_character == self.OPENING_GROUP_CHARACTER:
                if current_tag.strip() == self.OPENING_GROUP_CHARACTER:
                    current_tag = ''
                else:
                    issues += error_reporter.report_error_type('invalidTag', tag=current_tag)
            elif TagValidator.comma_is_missing_after_closing_parentheses(last_non_empty_valid_character,
                                                                         current_character):
                issues += error_reporter.report_error_type('commaMissing', tag=current_tag[:-1])
                break
            last_non_empty_valid_character = current_character
            last_non_empty_valid_index = i
        if TagValidator.character_is_delimiter(last_non_empty_valid_character):
            issues += error_reporter.report_error_type('extraDelimiter',
                                                       character=last_non_empty_valid_character,
                                                       index=last_non_empty_valid_index,
                                                       hed_string=hed_string)
        return issues

    def skip_iterations(self, iterator, start, end):
        """Skips a number of iterations based on the start and end index.

        Parameters
        ----------
        iterator: iterator
            A iterator object.
        start: int
            The start position in the iterator to start skipping.
        end: int
            The end position in the iterator to stop skipping.
        Returns
        -------
        iterator
            An iterator with the iterations skipped.

        """
        iterations_to_skip = end - start
        for iteration in range(iterations_to_skip):
            next(iterator, None)
        return iterator

    @staticmethod
    def report_invalid_character_error(character, index, hed_string):
        """Reports a error that is related to an invalid character.

        Parameters
        ----------
        character: str
            The invalid character.
        index: int
            The index of the invalid character in the HED string.
        hed_string: str
            The HED string that caused the error.
        Returns
        -------
        list of dict
            A singleton list with a dictionary representing the error.

        """
        return error_reporter.report_error_type(TagValidator.CHARACTER_ERROR_TYPE, character=character, index=index,
                                                hed_string=hed_string)

    @staticmethod
    def comma_is_missing_after_closing_parentheses(last_non_empty_character, current_character):
        """Checks to see if a comma is missing after a closing parentheses in a HED string. This is a helper function for
           the find_missing_commas_in_hed_string function.

        Parameters
        ----------
        last_non_empty_character: character
            The last non-empty string in the HED string.
        current_character: str
            The current character in the HED string.
        Returns
        -------
        bool
            True if a comma is missing after a closing parentheses. False, if otherwise.

        """
        return last_non_empty_character == TagValidator.CLOSING_GROUP_CHARACTER and not \
            TagValidator.character_is_delimiter(current_character)

    @staticmethod
    def character_is_delimiter(character):
        """Checks to see if the character is a delimiter. A delimiter is a commma or a tilde.

        Parameters
        ----------
        character: character
            A string character.
        Returns
        -------
        string
            Returns true if the character is a delimiter. False, if otherwise. A delimiter is a comma or a tilde.

        """
        if character == TagValidator.COMMA or character == TagValidator.TILDE:
            return True
        return False

    def find_invalid_character_issues(self, hed_string):
        """Reports an error if it finds any invalid characters as defined by TagValidator.INVALID_CHARS

        Parameters
        ----------
        hed_string: str
            A hed string.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        for index, character in enumerate(hed_string):
            if character in TagValidator.INVALID_CHARS:
                validation_issues += TagValidator.report_invalid_character_error(character, index, hed_string)
                self._increment_issue_count()

        return validation_issues

    def count_tag_group_parentheses(self, hed_string):
        """Reports a validation error if there are an unequal number of opening or closing parentheses. This is the
         first check before the tags are parsed.

        Parameters
        ----------
        hed_string: str
            A hed string.
        Returns
        -------
        list
            A validation issues list. If no issues are found then an empty list is returned.

        """
        validation_issues = []
        number_of_opening_parentheses = hed_string.count('(')
        number_of_closing_parentheses = hed_string.count(')')
        if number_of_opening_parentheses != number_of_closing_parentheses:
            validation_issues += error_reporter.report_error_type(TagValidator.PARENTHESES_ERROR_TYPE,
                                                                   opening_parentheses_count=number_of_opening_parentheses,
                                                                   closing_parentheses_count=number_of_closing_parentheses)
            self._increment_issue_count()
        return validation_issues

    @staticmethod
    def is_clock_face_time(time_string):
        """Checks to see if the specified string is valid HH:MM time string.

        Parameters
        ----------
        time_string: str
            A time string.
        Returns
        -------
        string
            True if the time string is valid. False, if otherwise.

        """
        try:
            time.strptime(time_string, '%H:%M:%S')
        except ValueError:
            try:
                time.strptime(time_string, '%H:%M')
            except ValueError:
                return False
        return True


if __name__ == '__main__':
    song = ['always', 'look', 'on', 'the', 'bright', 'side', 'of', 'life']
    song_iter = iter(song)
    for sing in song_iter:
        print(sing)
