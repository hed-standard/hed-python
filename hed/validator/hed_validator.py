"""
This module contains the HedValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, and .xlsx. To get the validation issues after creating a HedValidator class call
the get_validation_issues() function.

"""

from hed.errors.error_types import ValidationErrors, DefinitionErrors
from hed.errors.error_reporter import ErrorHandler, check_for_any_errors

from hed.models.hed_string import HedString
from hed.models import HedTag
from hed.validator.tag_validator import TagValidator
from hed.validator.def_validator import DefValidator
from hed.validator.onset_validator import OnsetValidator


class HedValidator:
    """ Top level validation of HED strings. """

    def __init__(self, hed_schema=None, def_dicts=None, run_full_onset_checks=True, definitions_allowed=False):
        """ Constructor for the HedValidator class.

        Parameters:
            hed_schema (HedSchema or HedSchemaGroup): HedSchema object to use for validation.
            def_dicts(DefinitionDict or list or dict): the def dicts to use for validation
            run_full_onset_checks(bool): If True, check for matching onset/offset tags
            definitions_allowed(bool): If False, flag definitions found as errors
        """
        super().__init__()
        self._tag_validator = None
        self._hed_schema = hed_schema

        self._tag_validator = TagValidator(hed_schema=self._hed_schema)
        self._def_validator = DefValidator(def_dicts, hed_schema)
        self._onset_validator = OnsetValidator(def_dict=self._def_validator,
                                               run_full_onset_checks=run_full_onset_checks)
        self._definitions_allowed = definitions_allowed

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
        issues += self._tag_validator.run_hed_string_validators(hed_string, allow_placeholders)
        if check_for_any_errors(issues):
            return issues
        if hed_string == "n/a" or not self._hed_schema:
            return issues
        issues += hed_string.convert_to_canonical_forms(self._hed_schema)
        if check_for_any_errors(issues):
            return issues
        # This is required so it can validate the tag a tag expands into
        # e.g. checking units when a definition placeholder has units
        self._def_validator.construct_def_tags(hed_string)
        issues += self._validate_individual_tags_in_hed_string(hed_string, allow_placeholders=allow_placeholders)
        issues += self._def_validator.validate_def_tags(hed_string, self._tag_validator)
        return issues

    def run_full_string_checks(self, hed_string):
        issues = []
        issues += self._validate_tags_in_hed_string(hed_string)
        issues += self._validate_groups_in_hed_string(hed_string)
        issues += self._onset_validator.validate_onset_offset(hed_string)
        return issues

    def _validate_groups_in_hed_string(self, hed_string_obj):
        """ Report invalid groups at each level.

        Parameters:
            hed_string_obj (HedString): A HedString object.

        Returns:
            list: Issues associated with each level in the HED string. Each issue is a dictionary.

        Notes:
            - This pertains to the top-level, all groups, and nested groups.

        """
        validation_issues = []
        for original_tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            is_group = original_tag_group.is_group
            if not original_tag_group and is_group:
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_GROUP_EMPTY,
                                                               tag=original_tag_group)
            validation_issues += self._tag_validator.run_tag_level_validators(original_tag_group.tags(), is_top_level,
                                                                              is_group)

        validation_issues += self._check_for_duplicate_groups(hed_string_obj)
        return validation_issues

    def _check_for_duplicate_groups_recursive(self, sorted_group, validation_issues):
        prev_child = None
        for child in sorted_group:
            if child == prev_child:
                if isinstance(child, HedTag):
                    error_code = ValidationErrors.HED_TAG_REPEATED
                    validation_issues += ErrorHandler.format_error(error_code, child)
                else:
                    error_code = ValidationErrors.HED_TAG_REPEATED_GROUP
                    found_group = child
                    base_steps_up = 0
                    while isinstance(found_group, list):
                        found_group = found_group[0]
                        base_steps_up += 1
                    for _ in range(base_steps_up):
                        found_group = found_group._parent
                    validation_issues += ErrorHandler.format_error(error_code, found_group)
            if not isinstance(child, HedTag):
                self._check_for_duplicate_groups_recursive(child, validation_issues)
            prev_child = child

    def _check_for_duplicate_groups(self, original_group):
        sorted_group = original_group.sorted()
        validation_issues = []
        self._check_for_duplicate_groups_recursive(sorted_group, validation_issues)
        return validation_issues

    def _validate_tags_in_hed_string(self, hed_string_obj):
        """ Report invalid the multi-tag properties in a hed string, e.g. required tags..

         Parameters:
            hed_string_obj (HedString): A HedString object.

         Returns:
            list: The issues associated with the tags in the HED string. Each issue is a dictionary.
        """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        validation_issues += self._tag_validator.run_all_tags_validators(tags)
        return validation_issues

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
                #         validation_issues += self._tag_validator. \
                #             run_individual_tag_validators(tag, allow_placeholders=allow_placeholders,
                #                                           is_definition=is_definition)
                # else:
                validation_issues += self._tag_validator. \
                    run_individual_tag_validators(hed_tag,
                                                  allow_placeholders=allow_placeholders,
                                                  is_definition=is_definition)

        return validation_issues
