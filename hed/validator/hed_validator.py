"""
This module contains the HedValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, and .xlsx. To get the validation issues after creating a HedValidator class call
the get_validation_issues() function.

"""
import re
from hed.errors.error_types import ValidationErrors, DefinitionErrors
from hed.errors.error_reporter import ErrorHandler, check_for_any_errors

from hed.validator.def_validator import DefValidator
from hed.validator.tag_util import UnitValueValidator, CharValidator, StringValidator, TagValidator, GroupValidator
from hed.schema.schema_validation_util import schema_version_greater_equal
from hed.schema import HedSchema


class HedValidator:
    """ Top level validation of HED strings. """

    def __init__(self, hed_schema, def_dicts=None, definitions_allowed=False):
        """ Constructor for the HedValidator class.

        Parameters:
            hed_schema (HedSchema or HedSchemaGroup): HedSchema object to use for validation.
            def_dicts(DefinitionDict or list or dict): the def dicts to use for validation
            definitions_allowed(bool): If False, flag definitions found as errors
        """
        if hed_schema is None:
            raise ValueError("HedSchema required for validation")

        self._hed_schema = hed_schema

        self._def_validator = DefValidator(def_dicts, hed_schema)
        self._definitions_allowed = definitions_allowed

        self._validate_characters = schema_version_greater_equal(hed_schema, "8.3.0")

        self._unit_validator = UnitValueValidator(modern_allowed_char_rules=self._validate_characters)
        self._char_validator = CharValidator(modern_allowed_char_rules=self._validate_characters)
        self._string_validator = StringValidator()
        self._tag_validator = TagValidator()
        self._group_validator = GroupValidator(hed_schema)

    def validate(self, hed_string, allow_placeholders, error_handler=None):
        """
        Validate the string using the schema

        Parameters:
            hed_string(HedString): the string to validate
            allow_placeholders(bool): allow placeholders in the string
            error_handler(ErrorHandler or None): the error handler to use, creates a default one if none passed
        Returns:
            issues (list of dict): A list of issues for hed string
        """
        if not error_handler:
            error_handler = ErrorHandler()
        issues = []
        issues += self.run_basic_checks(hed_string, allow_placeholders=allow_placeholders)
        error_handler.add_context_and_filter(issues)
        if check_for_any_errors(issues):
            return issues
        issues += self.run_full_string_checks(hed_string)
        error_handler.add_context_and_filter(issues)
        return issues

    def run_basic_checks(self, hed_string, allow_placeholders):
        issues = []
        issues += self._run_hed_string_validators(hed_string, allow_placeholders)
        if check_for_any_errors(issues):
            return issues
        if hed_string == "n/a":
            return issues
        for tag in hed_string.get_all_tags():
            issues += self._run_validate_tag_characters(tag, allow_placeholders=allow_placeholders)
        issues += hed_string._calculate_to_canonical_forms(self._hed_schema)
        if check_for_any_errors(issues):
            return issues
        issues += self._validate_individual_tags_in_hed_string(hed_string, allow_placeholders=allow_placeholders)
        issues += self._def_validator.validate_def_tags(hed_string, self)
        return issues

    def run_full_string_checks(self, hed_string):
        issues = []
        issues += self._group_validator.run_all_tags_validators(hed_string)
        issues += self._group_validator.run_tag_level_validators(hed_string)
        issues += self._def_validator.validate_onset_offset(hed_string)
        return issues

    # Todo: mark semi private/actually private below this
    def _run_validate_tag_characters(self, original_tag, allow_placeholders):
        """ Basic character validation of tags

        Parameters:
            original_tag (HedTag): A original tag.
            allow_placeholders (bool): Allow value class or extensions to be placeholders rather than a specific value.

        Returns:
            list: The validation issues associated with the characters. Each issue is dictionary.

        """
        return self._char_validator.check_tag_invalid_chars(original_tag, allow_placeholders)

    def _run_hed_string_validators(self, hed_string_obj, allow_placeholders=False):
        """Basic high level checks of the hed string for illegal characters

           Catches fully banned characters, out of order parentheses, commas, repeated slashes, etc.

        Parameters:
            hed_string_obj (HedString): A HED string.
            allow_placeholders: Allow placeholder and curly brace characters

        Returns:
            list: The validation issues associated with a HED string. Each issue is a dictionary.
         """
        validation_issues = []
        validation_issues += self._char_validator.check_invalid_character_issues(
            hed_string_obj.get_original_hed_string(), allow_placeholders)
        validation_issues += self._string_validator.run_string_validator(hed_string_obj)
        for original_tag in hed_string_obj.get_all_tags():
            validation_issues += self.check_tag_formatting(original_tag)
        return validation_issues

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
            validation_issues += ErrorHandler.format_error(ValidationErrors.NODE_NAME_EMPTY,
                                                           tag=original_tag,
                                                           index_in_tag=match.start(),
                                                           index_in_tag_end=match.end())

        return validation_issues

    def validate_units(self, original_tag, validate_text=None, report_as=None, error_code=None,
                       index_offset=0):
        """Validate units and value classes

        Parameters:
            original_tag(HedTag): The source tag
            validate_text (str): the text we want to validate, if not the full extension.
            report_as(HedTag): Report the error tag as coming from a different one.
                               Mostly for definitions that expand.
            error_code(str): The code to override the error as.  Again mostly for def/def-expand tags.
            index_offset(int): Offset into the extension validate_text starts at

        Returns:
            issues(list): Issues found from units
        """
        if validate_text is None:
            validate_text = original_tag.extension
        issues = []
        if original_tag.is_unit_class_tag():
            issues += self._unit_validator.check_tag_unit_class_units_are_valid(original_tag,
                                                                                validate_text,
                                                                                report_as=report_as,
                                                                                error_code=error_code,
                                                                                index_offset=index_offset)
        elif original_tag.is_value_class_tag():
            issues += self._unit_validator.check_tag_value_class_valid(original_tag,
                                                                       validate_text,
                                                                       report_as=report_as,
                                                                       error_code=error_code,
                                                                       index_offset=index_offset)
        elif original_tag.extension:
            issues += self._char_validator.check_for_invalid_extension_chars(original_tag,
                                                                             validate_text,
                                                                             index_offset=index_offset)

        return issues

    def _validate_individual_tags_in_hed_string(self, hed_string_obj, allow_placeholders=False):
        """ Validate individual tags in a HED string.

         Parameters:
            hed_string_obj (HedString): A HedString  object.

         Returns:
            list: The issues associated with the individual tags. Each issue is a dictionary.

         """
        from hed.models.definition_dict import DefTagNames
        validation_issues = []
        definition_groups = hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY},
                                                               include_groups=1)
        all_definition_groups = [group for sub_group in definition_groups for group in sub_group.get_all_groups()]
        for group in hed_string_obj.get_all_groups():
            is_definition = group in all_definition_groups
            for hed_tag in group.tags():
                if not self._definitions_allowed and hed_tag.short_base_tag == DefTagNames.DEFINITION_ORG_KEY:
                    validation_issues += ErrorHandler.format_error(DefinitionErrors.BAD_DEFINITION_LOCATION, hed_tag)
                # todo: unclear if this should be restored at some point
                # if hed_tag.expandable and not hed_tag.expanded:
                #     for tag in hed_tag.expandable.get_all_tags():
                #         validation_issues += self._group_validator. \
                #             run_individual_tag_validators(tag, allow_placeholders=allow_placeholders,
                #                                           is_definition=is_definition)
                # else:
                validation_issues += self._tag_validator. \
                    run_individual_tag_validators(hed_tag,
                                                  allow_placeholders=allow_placeholders,
                                                  is_definition=is_definition)
                if (hed_tag.short_base_tag == DefTagNames.DEF_ORG_KEY or
                        hed_tag.short_base_tag == DefTagNames.DEF_EXPAND_ORG_KEY):
                    validation_issues += self._def_validator.validate_def_value_units(hed_tag, self)
                else:
                    validation_issues += self.validate_units(hed_tag)

        return validation_issues
