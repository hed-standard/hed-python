'''
This module is used to validate the HED tags as strings.

Created on Oct 2, 2017

@author: Jeremy Cockfield

'''

import re;
import time;
from hedvalidation import error_reporter;
from hedvalidation import warning_reporter;


class TagValidator:
    BRACKET_ERROR_TYPE = 'bracket';
    COMMA_ERROR_TYPE = 'comma';
    CAMEL_CASE_EXPRESSION = r'([A-Z-]+\s*[a-z-]*)+';
    DEFAULT_UNIT_ATTRIBUTE = 'default';
    DIGIT_EXPRESSION = r'^\d+$';
    REQUIRE_CHILD_ERROR_TYPE = 'requireChild';
    REQUIRED_ERROR_TYPE = 'required';
    TAG_DICTIONARY_KEY = 'tags';
    TILDE_ERROR_TYPE = 'tilde';
    TIME_UNIT_CLASS = 'time';
    UNIQUE_ERROR_TYPE = 'unique';
    DUPLICATE_ERROR_TYPE = 'duplicate';
    VALID_ERROR_TYPE = 'valid';
    EXTENSION_ALLOWED_ATTRIBUTE = 'extensionAllowed';
    TAKES_VALUE_ATTRIBUTE = 'takesValue';
    IS_NUMERIC_ATTRIBUTE = 'isNumeric';
    UNIT_CLASS_ATTRIBUTE = 'unitClass';
    UNIT_CLASS_UNITS_ELEMENT = 'units';
    OPENING_GROUP_BRACKET = '(';
    CLOSING_GROUP_BRACKET = ')';
    DOUBLE_QUOTE = '"';
    COMMA = ',';
    TILDE = '~';
    hed_dictionary = None;
    hed_dictionary_dictionaries = None;

    def __init__(self, hed_dictionary):
        """Constructor for the Tag_Validator class.

        Parameters
        ----------
        hed_dictionary: Hed_Dictionary
            A Hed_Dictionary object.

        Returns
        -------
        TagValidator
            A Tag_Validator object.

        """
        self.hed_dictionary = hed_dictionary;
        self.hed_dictionary_dictionaries = hed_dictionary.get_dictionaries();
        self._issue_count = 0;
        self._error_count = 0;
        self._warning_count = 0;

    def increment_validation_issue(self, is_error):
        """Increments the validation issue count

         Parameters
         ----------
         is_error: boolean
            True if the issue is an error, False if it is not.
         Returns
         -------

         """
        self._issue_count += 1;
        if is_error:
            self._error_count += 1;
        else:
            self._warning_count += 1;

    def get_issue_count(self):
        """Gets the issue count

         Parameters
         ----------

         Returns
         -------
         integer
            The issue count
         """
        return self._issue_count;

    def get_warning_count(self):
        """Gets the warning count

         Parameters
         ----------

         Returns
         -------
         integer
            The warning count
         """
        return self._warning_count;

    def get_error_count(self):
        """Gets the error count

         Parameters
         ----------

         Returns
         -------
         integer
            The error count
         """
        return self._error_count;

    def run_individual_tag_validators(self, original_tag, formatted_tag, check_for_warnings=False):
        """Runs the validators on the individual tags in a HED string.

         Parameters
         ----------
         original_tag: string
            A original tag.
         formatted_tag: string
            A format tag.
         check_for_warnings: boolean
            True, if to include issues found from the warning validators. False, if otherwise.
         Returns
         -------
         string
             The validation issues associated with the top-level in the HED string.

         """
        validation_issues = '';
        validation_issues += self.check_if_tag_is_valid(original_tag, formatted_tag);
        validation_issues += self.check_if_tag_unit_class_units_are_valid(original_tag, formatted_tag);
        validation_issues += self.check_if_tag_requires_child(original_tag, formatted_tag);
        if check_for_warnings:
            validation_issues += self.check_if_tag_unit_class_units_exist(original_tag, formatted_tag);
            validation_issues += self.check_capitalization(original_tag, formatted_tag);
        return validation_issues;

    def run_tag_group_validators(self, tag_group):
        """Runs the validators on the groups in a HED string.

         Parameters
         ----------
         tag_group: list
            A list containing the tags in a group.
         Returns
         -------
         string
             The validation issues associated with the groups in a HED string.

         """
        validation_issues = '';
        validation_issues += self.check_number_of_group_tildes(tag_group);
        return validation_issues;

    def run_hed_string_validators(self, hed_string):
        """Runs the validators on the HED string. If this is passed then all the other validators are run on the tags
           and groups in the HED string.

         Parameters
         ----------
         hed_string: string
            A HED string.
         Returns
         -------
         string
             The validation issues associated with a HED string.

         """
        validation_issues = '';
        validation_issues += TagValidator.count_tag_group_brackets(hed_string);
        validation_issues += self.find_comma_issues_in_hed_string(hed_string);
        return validation_issues;

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
         string
             The validation issues associated with each level in a HED string.

         """
        validation_issues = '';
        validation_issues += self.check_if_multiple_unique_tags_exist(original_tag_list, formatted_tag_list);
        validation_issues += self.check_if_duplicate_tags_exist(original_tag_list, formatted_tag_list);
        return validation_issues;

    def run_top_level_validators(self, formatted_top_level_tags, check_for_warnings=False):
        """Runs the validators on tags at the top-level in a HED string.

         Parameters
         ----------
         formatted_top_level_tags: list
            A list containing the top-level tags in a HED string.
         check_for_warnings: boolean
            True, if to include issues found from the warning validators. False, if otherwise.
         Returns
         -------
         string
             The validation issues associated with the top-level in a HED string.

         """
        validation_issues = '';
        if check_for_warnings:
            validation_issues += self.check_for_required_tags(formatted_top_level_tags);
        return validation_issues;

    def check_if_tag_is_valid(self, original_tag, formatted_tag):
        """Reports a validation error if the tag provided is not a valid tag or doesn't take a value.

        Parameters
        ----------
        original_tag: string
            The original tag that is used to report the error.
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        if self.is_extension_allowed_tag(formatted_tag) or self.tag_takes_value(formatted_tag) or \
                formatted_tag == TagValidator.TILDE:
            pass;
        elif not self.hed_dictionary_dictionaries[TagValidator.TAG_DICTIONARY_KEY].get(formatted_tag):
            validation_error = error_reporter.report_error_type(TagValidator.VALID_ERROR_TYPE, tag=original_tag);
        return validation_error;

    def tag_is_valid(self, formatted_tag):
        """Checks to see if the tag is a valid HED tag.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        boolean
            True if the tag is a valid HED tag. False, if otherwise.

        """
        return self.hed_dictionary_dictionaries[TagValidator.TAG_DICTIONARY_KEY].get(formatted_tag);

    def check_capitalization(self, original_tag, formatted_tag):
        """Reports a validation warning if the tag isn't correctly capitalized.

        Parameters
        ----------
        original_tag: string
            The original tag that is used to report the warning.
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            A validation warning string. If no warnings are found then an empty string is returned.

        """
        validation_warning = '';
        tag_names = original_tag.split("/");
        if self.tag_takes_value(formatted_tag):
            tag_names = tag_names[:-1];
        for tag_name in tag_names:
            correct_tag_name = tag_name.capitalize();
            if tag_name != correct_tag_name and not re.search(self.CAMEL_CASE_EXPRESSION, tag_name):
                validation_warning = warning_reporter.report_warning_type("cap", tag=original_tag);
                break;
        return validation_warning;

    def is_extension_allowed_tag(self, formatted_tag):
        """Checks to see if the tag has the 'extensionAllowed' attribute. It will strip the tag until there are no more
        slashes to check if its ancestors have the attribute.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        boolean
            True if the tag has the 'extensionAllowed' attribute. False, if otherwise.

        """
        tag_slash_indices = self.get_tag_slash_indices(formatted_tag);
        for tag_slash_index in tag_slash_indices:
            tag_substring = self.get_tag_substring_by_end_index(formatted_tag, tag_slash_index);
            if self.hed_dictionary.tag_has_attribute(tag_substring,
                                                     TagValidator.EXTENSION_ALLOWED_ATTRIBUTE):
                return True;
        return False;

    def tag_takes_value(self, formatted_tag):
        """Checks to see if the tag has the 'takesValue' attribute.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        boolean
            True if the tag has the 'takesValue' attribute. False, if otherwise.

        """
        takes_value_tag = self.replace_tag_name_with_pound(formatted_tag);
        return self.hed_dictionary.tag_has_attribute(takes_value_tag,
                                                     TagValidator.TAKES_VALUE_ATTRIBUTE);

    def is_unit_class_tag(self, formatted_tag):
        """Checks to see if the tag has the 'unitClass' attribute.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        boolean
            True if the tag has the 'unitClass' attribute. False, if otherwise.

        """
        takes_value_tag = self.replace_tag_name_with_pound(formatted_tag);
        return self.hed_dictionary.tag_has_attribute(takes_value_tag,
                                                     TagValidator.UNIT_CLASS_ATTRIBUTE);

    def replace_tag_name_with_pound(self, formatted_tag):
        """Replaces the tag name with the pound sign.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            A tag with the a pound sign in place of it's name.

        """
        pound_sign_tag = '#';
        last_tag_slash_index = formatted_tag.rfind('/');
        if last_tag_slash_index != -1:
            pound_sign_tag = formatted_tag[:last_tag_slash_index] + '/#';
        return pound_sign_tag;

    def check_if_tag_unit_class_units_are_valid(self, original_tag, formatted_tag):
        """Reports a validation error if the tag provided has a unit class and the units are incorrect.

        Parameters
        ----------
        original_tag: string
            The original tag that is used to report the error.
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        if not self.tag_is_valid(formatted_tag) and self.is_unit_class_tag(formatted_tag):
            tag_unit_classes = self.get_tag_unit_classes(formatted_tag);
            tag_unit_values = self.get_tag_name(formatted_tag);
            tag_unit_class_units = tuple(self.get_tag_unit_class_units(formatted_tag));
            if TagValidator.TIME_UNIT_CLASS in tag_unit_classes and TagValidator.is_hh_mm_time(tag_unit_values):
                pass;
            elif not re.search(TagValidator.DIGIT_EXPRESSION, tag_unit_values) and \
                    not tag_unit_values.startswith(tag_unit_class_units) and \
                    not tag_unit_values.endswith(tag_unit_class_units):
                validation_error = error_reporter.report_error_type('unitClass', tag=original_tag,
                                                                    unit_class_units=','.join(tag_unit_class_units));
        return validation_error;

    def check_if_tag_unit_class_units_exist(self, original_tag, formatted_tag):
        """Reports a validation warning if the tag provided has a unit class but no units are not specified.

        Parameters
        ----------
        original_tag: string
            The original tag that is used to report the error.
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            A validation warning string. If no errors are found then an empty string is returned.

        """
        validation_warning = '';
        if self.is_unit_class_tag(formatted_tag):
            tag_unit_values = self.get_tag_name(formatted_tag);
            if re.search(TagValidator.DIGIT_EXPRESSION, tag_unit_values):
                default_unit = self.get_unit_class_default_unit(formatted_tag);
                validation_warning = warning_reporter.report_warning_type('unitClass', tag=original_tag,
                                                                          default_unit=default_unit);
        return validation_warning;

    def get_tag_name(self, tag):
        """Gets the tag name from the tag path

        Parameters
        ----------
        tag: string
            A tag which is a path.
        Returns
        -------
        string
            The tag name.

        """
        tag_name = tag;
        tag_slash_indices = self.get_tag_slash_indices(tag);
        if tag_slash_indices:
            tag_name = tag[tag_slash_indices[-1] + 1:]
        return tag_name;

    def get_tag_unit_classes(self, formatted_tag):
        """Gets the unit classes associated with a particular tag.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        list
            A list containing the unit classes associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit classes associated with it.

        """
        unit_classes = [];
        unit_class_tag = self.replace_tag_name_with_pound(formatted_tag);
        if self.is_unit_class_tag(formatted_tag):
            unit_classes = self.hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE][unit_class_tag];
            unit_classes = unit_classes.split(',');
        return unit_classes;

    def get_tag_unit_class_units(self, formatted_tag):
        """Gets the unit class units associated with a particular tag.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        list
            A list containing the unit class units associated with a particular tag. A empty list will be returned if
            the tag doesn't have unit class units associated with it.

        """
        units = [];
        unit_class_tag = self.replace_tag_name_with_pound(formatted_tag);
        if self.is_unit_class_tag(formatted_tag):
            unit_classes = self.hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE][unit_class_tag];
            unit_classes = unit_classes.split(',');
            for unit_class in unit_classes:
                try:
                    units += (self.hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_UNITS_ELEMENT][unit_class]);
                except:
                    continue;
        return list(map(str.lower, units));

    def get_unit_class_default_unit(self, formatted_tag):
        """Gets the default unit class unit that is associated with the specified tag.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            The default unit class unit associated with the specific tag. If the tag doesn't have a unit class then an
            empty string is returned.

        """
        default_unit = '';
        unit_class_tag = self.replace_tag_name_with_pound(formatted_tag);
        if self.is_unit_class_tag(formatted_tag):
            has_default_attribute = self.hed_dictionary.tag_has_attribute(formatted_tag,
                                                                          TagValidator.DEFAULT_UNIT_ATTRIBUTE);
            if has_default_attribute:
                default_unit = self.hed_dictionary_dictionaries[TagValidator.DEFAULT_UNIT_ATTRIBUTE][formatted_tag];
            elif unit_class_tag in self.hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE]:
                unit_classes = \
                    self.hed_dictionary_dictionaries[TagValidator.UNIT_CLASS_ATTRIBUTE][unit_class_tag].split(',');
                first_unit_class = unit_classes[0];
                default_unit = self.hed_dictionary_dictionaries[TagValidator.DEFAULT_UNIT_ATTRIBUTE][first_unit_class];
        return default_unit;

    def is_numeric_tag(self, formatted_tag):
        """Checks to see if the tag has the 'isNumeric' attribute.

        Parameters
        ----------
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        boolean
            True if the tag has the 'isNumeric' attribute. False, if otherwise.

        """
        last_tag_slash_index = formatted_tag.rfind('/');
        if last_tag_slash_index != -1:
            numeric_tag = formatted_tag[:last_tag_slash_index] + '/#';
            return self.hed_dictionary.tag_has_attribute(numeric_tag, TagValidator.IS_NUMERIC_ATTRIBUTE);
        return False;

    def check_number_of_group_tildes(self, tag_group):
        """Reports a validation error if the tag group has too many tildes.

        Parameters
        ----------
        tag_group: list
            A list containing the tags in a group.
        Returns
        -------
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        if tag_group.count('~') > 2:
            validation_error = error_reporter.report_error_type(TagValidator.TILDE_ERROR_TYPE, tag_group);
        return validation_error;

    def check_if_tag_requires_child(self, original_tag, formatted_tag):
        """Reports a validation error if the tag provided has the 'requireChild' attribute.

        Parameters
        ----------
        original_tag: string
            The original tag that is used to report the error.
        formatted_tag: string
            The tag that is used to do the validation.
        Returns
        -------
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        if self.hed_dictionary_dictionaries[TagValidator.REQUIRE_CHILD_ERROR_TYPE].get(formatted_tag):
            validation_error = error_reporter.report_error_type(TagValidator.REQUIRE_CHILD_ERROR_TYPE,
                                                                tag=original_tag);
        return validation_error;

    def check_for_required_tags(self, formatted_top_level_tags):
        """Reports a validation error if the required tags aren't present.

        Parameters
        ----------
        formatted_top_level_tags: list
            A list containing the top-level tags.
        Returns
        -------
        string
            A validation warning string. If no warnings are found then an empty string is returned.

        """
        validation_warning = '';
        required_tag_prefixes = self.hed_dictionary_dictionaries[TagValidator.REQUIRED_ERROR_TYPE];
        for required_tag_prefix in required_tag_prefixes:
            capitalized_required_tag_prefix = \
                self.hed_dictionary_dictionaries[TagValidator.REQUIRED_ERROR_TYPE][required_tag_prefix];
            if sum([x.startswith(required_tag_prefix) for x in formatted_top_level_tags]) < 1:
                validation_warning += warning_reporter.report_warning_type(TagValidator.REQUIRED_ERROR_TYPE,
                                                                           tag_prefix=capitalized_required_tag_prefix);
        return validation_warning;

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
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        unique_tag_prefixes = self.hed_dictionary_dictionaries[TagValidator.UNIQUE_ERROR_TYPE];
        for unique_tag_prefix in unique_tag_prefixes:
            unique_tag_prefix_boolean_mask = [x.startswith(unique_tag_prefix) for x in formatted_tag_list];
            if sum(unique_tag_prefix_boolean_mask) > 1:
                validation_error += error_reporter.report_error_type(
                    TagValidator.UNIQUE_ERROR_TYPE,
                    tag_prefix=self.hed_dictionary_dictionaries[TagValidator.UNIQUE_ERROR_TYPE][unique_tag_prefix]);
        return validation_error;

    def tag_has_unique_prefix(self, tag):
        """Checks to see if the tag starts with a prefix.

        Parameters
        ----------
        tag: string
            A tag.
        Returns
        -------
        boolean
            True if the tag starts with a unique prefix. False if otherwise.

        """
        unique_tag_prefixes = self.hed_dictionary_dictionaries[TagValidator.UNIQUE_ERROR_TYPE];
        for unique_tag_prefix in unique_tag_prefixes:
            if tag.lower().startswith(unique_tag_prefix):
                return True;
        return False;

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
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        duplicate_indices = set([]);
        for tag_index, tag in enumerate(formatted_tag_list):
            all_indices = range(len(formatted_tag_list));
            for duplicate_index in all_indices:
                if tag_index == duplicate_index:
                    continue;
                if formatted_tag_list[tag_index] != TagValidator.TILDE and \
                        formatted_tag_list[tag_index] == formatted_tag_list[duplicate_index] and \
                        tag_index not in duplicate_indices and duplicate_index not in duplicate_indices:
                    duplicate_indices.add(tag_index);
                    duplicate_indices.add(duplicate_index);
                    validation_error += error_reporter.report_error_type(TagValidator.DUPLICATE_ERROR_TYPE,
                                                                         tag=original_tag_list[tag_index]);
        return validation_error;

    def get_tag_slash_indices(self, tag, slash='/'):
        """Gets all of the indices in a tag that are slashes.

        Parameters
        ----------
        tag: string
            A tag.
        slash: string
            The slash character. By default it is a forward slash.
        Returns
        -------
        list
            A list containing the indices of the tag slashes.

        """
        return [s.start() for s in re.finditer(slash, tag)];

    def get_tag_substring_by_end_index(self, tag, end_index):
        """Gets a tag substring from the start until the end index.

        Parameters
        ----------
        tag: string
            A tag.
        end_index: int
            A index for the tag substring to end.
        Returns
        -------
        string
            A tag substring.

        """
        if end_index != 0:
            return tag[:end_index]
        return tag;

    def find_comma_issues_in_hed_string(self, hed_string):
        """Reports a validation error if there are missing commas or commas in tags that take values.

        Parameters
        ----------
        hed_string: string
            A hed string.
        Returns
        -------
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        current_tag = '';
        last_non_empty_character = '';
        character_indices_iterator = iter(range(len(hed_string)));
        for character_index in character_indices_iterator:
            character = hed_string[character_index];
            current_tag += character;
            if not character.isspace():
                if TagValidator.character_is_delimiter(character):
                    current_tag = '';
                if character == TagValidator.OPENING_GROUP_BRACKET and \
                        self._is_valid_tag_with_parentheses(hed_string, current_tag, character_index):
                    index_after_parentheses = self._get_index_at_end_of_parentheses(hed_string, current_tag,
                                                                                    character_index);
                    character_indices_iterator = self.skip_iterations(character_indices_iterator, character_index,
                                                                      index_after_parentheses);
                    current_tag = '';
                elif TagValidator.comma_is_missing_before_opening_bracket(last_non_empty_character, character):
                    validation_error = TagValidator.report_missing_comma_error(current_tag);
                    break;
                elif TagValidator.comma_is_missing_after_closing_bracket(last_non_empty_character, character):
                    validation_error = TagValidator.report_missing_comma_error(current_tag);
                    break;
                last_non_empty_character = character;
        return validation_error;

    def skip_iterations(self, iterator, start, end):
        """Skips a number of iterations based on the start and end index.

        Parameters
        ----------
        iterator: iterator
            A iterator object.
        start: integer
            The start position in the iterator to start skipping.
        end: integer
            The end position in the iterator to stop skipping.
        Returns
        -------
        iterator
            An iterator with the iterations skipped.

        """
        iterations_to_skip = end - start;
        for iteration in range(iterations_to_skip):
            next(iterator, None);
        return iterator;

    def _is_valid_tag_with_parentheses(self, hed_string, current_tag, character_index):
        """Checks to see if the current tag with the next set of parentheses in the HED string is valid. Some tags have
           parentheses and this function is implemented to avoid reporting a missing comma error.

        Parameters
        ----------
        hed_string: string
            A HED string.
        current_tag: string
            The current tag in the HED string.
        character_index: integer
            The index of the current character.
        Returns
        -------
        boolean
            True, if the current tag with the next set of parentheses in the HED string is valid. False, if otherwise.

        """
        current_tag = current_tag[:-1];
        rest_of_hed_string = hed_string[character_index:];
        current_tag_with_parentheses, _ = TagValidator.get_next_set_of_parentheses_in_hed_string(
            current_tag + rest_of_hed_string);
        current_tag_with_parentheses = current_tag_with_parentheses.lower();
        if self.tag_takes_value(current_tag_with_parentheses):
            return True;
        return self.tag_is_valid(current_tag_with_parentheses);

    def _get_index_at_end_of_parentheses(self, hed_string, current_tag, character_index):
        """Checks to see if the current tag with the next set of parentheses in the HED string is valid. Some tags have
           parentheses and this function is implemented to avoid reporting a missing comma error.

        Parameters
        ----------
        hed_string: string
            A HED string.
        current_tag: string
            The current tag in the HED string.
        character_index: integer
            The index of the current character.
        Returns
        -------
        integer
            The position at the end of the next set of parentheses.

        """
        current_tag = current_tag[:-1];
        rest_of_hed_string = hed_string[character_index:];
        _, parentheses_length = TagValidator.get_next_set_of_parentheses_in_hed_string(current_tag +
                                                                                       rest_of_hed_string);
        return parentheses_length;

    @staticmethod
    def report_missing_comma_error(error_tag):
        """Reports a error that is related with a missing comma.

        Parameters
        ----------
        error_tag: string
            The tag that caused the error.
        Returns
        -------
        string
            The error message associated with a missing comma.


        """
        error_tag = error_tag[:-1].strip();
        return error_reporter.report_error_type(TagValidator.COMMA_ERROR_TYPE, tag=error_tag);

    @staticmethod
    def comma_is_missing_before_opening_bracket(last_non_empty_character, current_character):
        """Checks to see if a comma is missing before a opening bracket in a HED string. This is a helper function for
           the find_missing_commas_in_hed_string function.

        Parameters
        ----------
        last_non_empty_character: character
            The last non-empty string in the HED string.
        current_character: string
            The current character in the HED string.
        Returns
        -------
        boolean
            True if a comma is missing before a opening bracket. False, if otherwise.

        """
        return last_non_empty_character and not TagValidator.character_is_delimiter(last_non_empty_character) and \
               current_character == TagValidator.OPENING_GROUP_BRACKET;

    @staticmethod
    def comma_is_missing_after_closing_bracket(last_non_empty_character, current_character):
        """Checks to see if a comma is missing after a closing bracket in a HED string. This is a helper function for
           the find_missing_commas_in_hed_string function.

        Parameters
        ----------
        last_non_empty_character: character
            The last non-empty string in the HED string.
        current_character: string
            The current character in the HED string.
        Returns
        -------
        boolean
            True if a comma is missing after a closing bracket. False, if otherwise.

        """
        return last_non_empty_character == TagValidator.CLOSING_GROUP_BRACKET and not \
            TagValidator.character_is_delimiter(current_character);

    @staticmethod
    def get_next_set_of_parentheses_in_hed_string(hed_string):
        """Gets the next set of parentheses in the provided HED string.

        Parameters
        ----------
        hed_string: string
            A HED string.
        Returns
        -------
        string
            A tuple containing the next set of parentheses in the HED string and the length of the string in the
            parentheses. If not found, then the entire HED string is returned.

        """
        parentheses_length = 0;
        set_of_parentheses = '';
        opening_parenthesis_found = False;
        for character in hed_string:
            set_of_parentheses += character
            if character == TagValidator.OPENING_GROUP_BRACKET:
                opening_parenthesis_found = True;
            if character == TagValidator.CLOSING_GROUP_BRACKET and opening_parenthesis_found:
                return set_of_parentheses, parentheses_length;
            parentheses_length += 1;
        return set_of_parentheses, parentheses_length;

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
            return True;
        return False;

    @staticmethod
    def count_tag_group_brackets(hed_string):
        """Reports a validation error if there are an unequal number of opening or closing parentheses. This is the
         first check before the tags are parsed.

        Parameters
        ----------
        hed_string: string
            A hed string.
        Returns
        -------
        string
            A validation error string. If no errors are found then an empty string is returned.

        """
        validation_error = '';
        number_of_opening_brackets = hed_string.count('(');
        number_of_closing_brackets = hed_string.count(')');
        if number_of_opening_brackets != number_of_closing_brackets:
            validation_error = error_reporter.report_error_type(TagValidator.BRACKET_ERROR_TYPE,
                                                                opening_bracket_count=number_of_opening_brackets,
                                                                closing_bracket_count=number_of_closing_brackets);
        return validation_error;

    @staticmethod
    def is_hh_mm_time(time_string):
        """Checks to see if the specified string is valid HH:MM time string.

        Parameters
        ----------
        time_string: string
            A time string.
        Returns
        -------
        string
            True if the time string is valid. False, if otherwise.

        """
        try:
            time.strptime(time_string, '%H:%M')
        except ValueError:
            return False;
        return True;


if __name__ == '__main__':
    song = ['always', 'look', 'on', 'the', 'bright', 'side', 'of', 'life']
    song_iter = iter(song)
    for sing in song_iter:
        print(sing)
