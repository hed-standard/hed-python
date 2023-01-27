"""
This module contains the HedValidator class which is used to validate the tags in a HED string or a file. The file
types include .tsv, .txt, and .xlsx. To get the validation issues after creating a HedValidator class call
the get_validation_issues() function.

"""

from hed.errors.error_types import ValidationErrors
from hed.errors.error_reporter import ErrorHandler

from hed.models.hed_string import HedString
from hed.models import HedTag
from hed.validator.tag_validator import TagValidator
from functools import partial
from hed.models.hed_ops import HedOps


class HedValidator(HedOps):
    """ Top level validation of HED strings. """

    def __init__(self, hed_schema=None, run_semantic_validation=True):
        """ Constructor for the HedValidator class.

        Parameters:
            hed_schema (HedSchema or HedSchemaGroup): HedSchema object to use for validation.
            run_semantic_validation (bool): True if the validator should check the HED data against a schema.
        """
        super().__init__()
        self._tag_validator = None
        self._hed_schema = hed_schema

        self._tag_validator = TagValidator(hed_schema=self._hed_schema,
                                           run_semantic_validation=run_semantic_validation)
        self._run_semantic_validation = run_semantic_validation

    def __get_tag_funcs__(self, **kwargs):
        string_funcs = []
        allow_placeholders = kwargs.get("allow_placeholders")
        check_for_warnings = kwargs.get("check_for_warnings")
        string_funcs.append(self._tag_validator.run_hed_string_validators)
        string_funcs.append(
            partial(HedString.convert_to_canonical_forms, hed_schema=self._hed_schema))
        string_funcs.append(partial(self._validate_individual_tags_in_hed_string,
                                    allow_placeholders=allow_placeholders,
                                    check_for_warnings=check_for_warnings))
        return string_funcs

    def __get_string_funcs__(self, **kwargs):
        check_for_warnings = kwargs.get("check_for_warnings")
        string_funcs = [partial(self._validate_tags_in_hed_string, check_for_warnings=check_for_warnings),
                        self._validate_groups_in_hed_string]
        return string_funcs

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

    def _validate_tags_in_hed_string(self, hed_string_obj, check_for_warnings=False):
        """ Report invalid the multi-tag properties.

         Parameters:
            hed_string_obj (HedString): A HedString object.

         Returns:
            list: The issues associated with the tags in the HED string. Each issue is a dictionary.

        Notes:
            - in a hed string, eg required tags.

         """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        validation_issues += self._tag_validator.run_all_tags_validators(tags, check_for_warnings=check_for_warnings)
        return validation_issues

    def _validate_individual_tags_in_hed_string(self, hed_string_obj, allow_placeholders=False,
                                                check_for_warnings=False):
        """ Validate individual tags in a HED string.

         Parameters:
            hed_string_obj (HedString): A HedString  object.

         Returns:
            list: The issues associated with the individual tags. Each issue is a dictionary.

         """
        from hed.models.definition_dict import DefTagNames
        validation_issues = []
        def_groups = hed_string_obj.find_top_level_tags(anchor_tags={DefTagNames.DEFINITION_KEY}, include_groups=1)
        all_def_groups = [group for sub_group in def_groups for group in sub_group.get_all_groups()]
        for group in hed_string_obj.get_all_groups():
            is_definition = group in all_def_groups
            for hed_tag in group.tags():
                validation_issues += \
                    self._tag_validator.run_individual_tag_validators(hed_tag, allow_placeholders=allow_placeholders,
                                                                      check_for_warnings=check_for_warnings,
                                                                      is_definition=is_definition)

        return validation_issues
