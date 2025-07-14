""" Top level validation of HED strings. """

import re
from hed.errors.error_types import ValidationErrors, DefinitionErrors
from hed.errors import error_reporter

from hed.validator.def_validator import DefValidator
from hed.validator.util import UnitValueValidator, CharRexValidator, StringValidator, TagValidator, GroupValidator
from hed.schema.hed_schema import HedSchema


class HedValidator:
    """ Top level validation of HED strings.

    This module contains the HedValidator class which is used to validate the tags in a HED string or a file.
    The file types include .tsv, .txt, and .xlsx. To get the validation issues after creating a
    HedValidator class call the get_validation_issues() function.
    """

    def __init__(self, hed_schema, def_dicts=None, definitions_allowed=False):
        """ Constructor for the HedValidator class.

        Parameters:
            hed_schema (HedSchema or HedSchemaGroup): HedSchema object to use for validation.
            def_dicts (DefinitionDict or list or dict): the def dicts to use for validation
            definitions_allowed (bool): If False, flag definitions found as errors
        """
        if hed_schema is None:
            raise ValueError("HedSchema required for validation")

        self._hed_schema = hed_schema

        self._def_validator = DefValidator(def_dicts, hed_schema)
        self._definitions_allowed = definitions_allowed

        self._validate_characters = hed_schema.schema_83_props

        self._unit_validator = UnitValueValidator(modern_allowed_char_rules=self._validate_characters)
        self._char_validator = CharRexValidator(modern_allowed_char_rules=self._validate_characters)
        self._string_validator = StringValidator()
        self._tag_validator = TagValidator()
        self._group_validator = GroupValidator(hed_schema)

    def validate(self, hed_string, allow_placeholders, error_handler=None) -> list[dict]:
        """ Validate the HED string object using the schema.

        Parameters:
            hed_string (HedString): the string to validate.
            allow_placeholders (bool): allow placeholders in the string.
            error_handler (ErrorHandler or None): the error handler to use, creates a default one if none passed.

        Returns:
            list[dict]: A list of issues for HED string.
        """
        if not error_handler:
            error_handler = error_reporter.ErrorHandler()
        issues = []
        issues += self.run_basic_checks(hed_string, allow_placeholders=allow_placeholders)
        error_handler.add_context_and_filter(issues)
        if error_reporter.check_for_any_errors(issues):
            return issues
        issues += self.run_full_string_checks(hed_string)
        error_handler.add_context_and_filter(issues)
        return issues

    def run_basic_checks(self, hed_string, allow_placeholders) -> list[dict]:
        """Run basic validation checks on a HED string.

        Parameters:
            hed_string (HedString): The HED string to validate.
            allow_placeholders (bool): Whether placeholders are allowed in the HED string.

        Returns:
            list[dict]: A list of issues found during validation. Each issue is represented as a dictionary.

        Notes:
            - This method performs initial validation checks on the HED string, including character validation and tag validation.
            - It checks for invalid characters, calculates canonical forms, and validates individual tags.
            - If any issues are found during these checks, the method stops and returns the issues immediately.
            - The method also validates definition tags if applicable.

        """
        issues = []
        issues += self._run_hed_string_validators(hed_string, allow_placeholders)
        if error_reporter.check_for_any_errors(issues):
            return issues
        if hed_string == "n/a":
            return issues
        for tag in hed_string.get_all_tags():
            issues += self._run_validate_tag_characters(tag, allow_placeholders=allow_placeholders)
        issues += hed_string._calculate_to_canonical_forms(self._hed_schema)
        if error_reporter.check_for_any_errors(issues):
            return issues
        issues += self._validate_individual_tags_in_hed_string(hed_string, allow_placeholders=allow_placeholders)
        issues += self._def_validator.validate_def_tags(hed_string, self)
        return issues

    def run_full_string_checks(self, hed_string) -> list[dict]:
        """Run all full-string validation checks on a HED string.

        Parameters:
            hed_string (HedString): The HED string to validate.

        Returns:
            list[dict]: A list of issues found during validation. Each issue is represented as a dictionary.

        Notes:
            - This method iterates through a series of validation checks defined in the `checks` list.
            - Each check is a callable function that takes `hed_string` as input and returns a list of issues.
            - If any check returns issues, the method stops and returns those issues immediately.
            - If no issues are found, an empty list is returned.

        """
        checks = [
            self._group_validator.run_all_tags_validators,
            self._group_validator.run_tag_level_validators,
            self._def_validator.validate_onset_offset,
        ]

        for check in checks:
            issues = check(hed_string)  # Call each function with `hed_string`
            if issues:
                return issues

        return []  # Return an empty list if no issues are found

    # Todo: mark semi private/actually private below this
    def _run_validate_tag_characters(self, original_tag, allow_placeholders) -> list[dict]:
        """ Basic character validation of tags

        Parameters:
            original_tag (HedTag): A original tag.
            allow_placeholders (bool): Allow value class or extensions to be placeholders rather than a specific value.

        Returns:
            list[dict]: The validation issues associated with the characters. Each issue is dictionary.

        """
        return self._char_validator.check_tag_invalid_chars(original_tag, allow_placeholders)

    def _run_hed_string_validators(self, hed_string_obj, allow_placeholders=False) -> list[dict]:
        """Basic high level checks of the HED string for illegal characters

           Catches fully banned characters, out of order parentheses, commas, repeated slashes, etc.

        Parameters:
            hed_string_obj (HedString): A HED string.
            allow_placeholders (bool): Allow placeholder and curly brace characters

        Returns:
            list[dict]: The validation issues associated with a HED string. Each issue is a dictionary.
         """
        validation_issues = []
        validation_issues += self._char_validator.check_invalid_character_issues(
            hed_string_obj.get_original_hed_string(), allow_placeholders)
        validation_issues += self._string_validator.run_string_validator(hed_string_obj)
        for original_tag in hed_string_obj.get_all_tags():
            validation_issues += self.check_tag_formatting(original_tag)
        return validation_issues

    pattern_doubleslash = re.compile(r"([ \t/]{2,}|^/|/$)")

    def check_tag_formatting(self, original_tag) -> list[dict]:
        """ Report repeated or erroneous slashes.

        Parameters:
            original_tag (HedTag): The original tag that is used to report the error.

        Returns:
            list[dict]: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
        for match in self.pattern_doubleslash.finditer(original_tag.org_tag):
            validation_issues += error_reporter.ErrorHandler.format_error(ValidationErrors.NODE_NAME_EMPTY,
                                                                          tag=original_tag,
                                                                          index_in_tag=match.start(),
                                                                          index_in_tag_end=match.end())

        return validation_issues

    def validate_units(self, original_tag, validate_text=None, report_as=None, error_code=None,
                       index_offset=0) -> list[dict]:
        """Validate units and value classes

        Parameters:
            original_tag (HedTag): The source tag
            validate_text (str): the text we want to validate, if not the full extension.
            report_as (HedTag): Report the error tag as coming from a different one.
                               Mostly for definitions that expand.
            error_code (str): The code to override the error as.  Again mostly for def/def-expand tags.
            index_offset (int): Offset into the extension validate_text starts at

        Returns:
            list[dict]: Issues found from units
        """
        if validate_text is None:
            validate_text = original_tag.extension
        issues = []
        if validate_text == '#':
            return []
        if original_tag.is_unit_class_tag():
            issues += self._unit_validator.check_tag_unit_class_units_are_valid(original_tag,
                                                                                validate_text,
                                                                                report_as=report_as,
                                                                                error_code=error_code)
        elif original_tag.is_value_class_tag():
            issues += self._unit_validator.check_tag_value_class_valid(original_tag,
                                                                       validate_text,
                                                                       report_as=report_as)
        elif original_tag.extension:
            issues += self._char_validator.check_for_invalid_extension_chars(original_tag,
                                                                             validate_text,
                                                                             index_offset=index_offset)

        return issues

    def _validate_individual_tags_in_hed_string(self, hed_string_obj, allow_placeholders=False) -> list[dict]:
        """ Validate individual tags in a HED string.

         Parameters:
            hed_string_obj (HedString): A HedString  object.
            allow_placeholders (bool): Allow placeholders in the tags.

         Returns:
            list[dict]: The issues associated with the individual tags. Each issue is a dictionary.

         """
        from hed.models.definition_dict import DefTagNames
        validation_issues = []
        definition_groups = hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY},
                                                               include_groups=1)
        all_definition_groups = [group for sub_group in definition_groups for group in sub_group.get_all_groups()]
        for group in hed_string_obj.get_all_groups():
            is_definition = group in all_definition_groups
            for hed_tag in group.tags():
                if not self._definitions_allowed and hed_tag.short_base_tag == DefTagNames.DEFINITION_KEY:
                    validation_issues += error_reporter.ErrorHandler.format_error(
                        DefinitionErrors.BAD_DEFINITION_LOCATION, hed_tag)
                validation_issues += \
                    self._tag_validator.run_individual_tag_validators(hed_tag, allow_placeholders=allow_placeholders,
                                                                      is_definition=is_definition)
                if (hed_tag.short_base_tag == DefTagNames.DEF_KEY or
                        hed_tag.short_base_tag == DefTagNames.DEF_EXPAND_KEY):
                    validation_issues += (
                        self._def_validator.validate_def_value_units(hed_tag,
                                                                     self, allow_placeholders=allow_placeholders))
                elif (hed_tag.short_base_tag == DefTagNames.DEFINITION_KEY) and hed_tag.extension.endswith("/#"):
                    validation_issues += self.validate_units(hed_tag, hed_tag.extension[:-2])
                elif not (allow_placeholders and '#' in hed_tag.extension):
                    validation_issues += self.validate_units(hed_tag)

        return validation_issues
