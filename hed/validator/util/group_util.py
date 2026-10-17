"""Validation of the HED tags as strings."""

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import ValidationErrors
from hed.schema.hed_schema_constants import HedKey
from hed.validator.reserved_checker import ReservedChecker
from hed.validator.util.dup_util import DuplicateChecker


class GroupValidator:
    """Validation for attributes across groups HED tags.

    This is things like Required, Unique, top level tags, etc.
    """

    def __init__(self, hed_schema):
        """Constructor for GroupValidator

        Parameters:
            hed_schema (HedSchema): A HedSchema object.
        """
        if hed_schema is None:
            raise ValueError("HedSchema required for validation")
        self._hed_schema = hed_schema
        self._reserved_checker = ReservedChecker.get_instance()
        self._duplicate_checker = DuplicateChecker()

    def run_tag_level_validators(self, hed_string_obj) -> list[dict]:
        """Report invalid groups at each level.

        Parameters:
            hed_string_obj (HedString): A HedString object.

        Returns:
            list: Issues associated with each level in the HED string. Each issue is a dictionary.

        Notes:
            - This pertains to the top-level, all groups, and nested groups.
        """

        checks = [
            self._check_group_relationships,
            self._duplicate_checker.check_for_duplicates,
        ]

        for check in checks:
            issues = check(hed_string_obj)  # Call each function with `hed_string`
            if issues:
                return issues

        return []  # Return an empty list if no issues are found

    def run_all_tags_validators(self, hed_string_obj) -> list[dict]:
        """Report invalid the multi-tag properties in a HED string, e.g. required tags.

        Parameters:
           hed_string_obj (HedString): A HedString object.

        Returns:
           list: The issues associated with the tags in the HED string. Each issue is a dictionary.
        """
        validation_issues = []
        tags = hed_string_obj.get_all_tags()
        validation_issues += self._validate_tags_in_hed_string(tags)
        return validation_issues

    # ==========================================================================
    # Mostly internal functions to check individual types of errors
    # =========================================================================+

    def _check_group_relationships(self, hed_string_obj):
        """Check the group relationships

        Parameters:
            hed_string_obj (HedString): A HedString object.

        Returns:
            list: Issues associated with each level in the HED string. Each issue is a dictionary.

        Notes:
            - This pertains to the top-level, all groups, and nested groups.
        """

        for original_tag_group, is_top_level in hed_string_obj.get_all_groups(also_return_depth=True):
            is_group = original_tag_group.is_group

            # Check for empty group anywhere this is fatal
            if not original_tag_group and is_group:
                return ErrorHandler.format_error(ValidationErrors.HED_GROUP_EMPTY, tag=original_tag_group)

            # If a tag should be in a group. If not at the top level, a fatal error occurs.
            validation_issues = self.check_tag_level_issue(original_tag_group.tags(), is_top_level, is_group)
            if len(validation_issues) > 0:
                return validation_issues

            # If the reserved group requirements are not met, this is a fatal error.
            validation_issues = self._check_reserved_group_requirements(original_tag_group)
            if len(validation_issues) > 0:
                return validation_issues

        return []

    def _check_reserved_group_requirements(self, group):
        """Check a group against the row of its governing reserved tag (reserved_tags.json).

        Parameters:
            group (HedGroup) - the HED group to test for special tags.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        reserved_tags = self._reserved_checker.get_reserved(group)
        if len(reserved_tags) == 0:
            return []

        # Check for compatibility of the reserved tags within this string
        validation_issues = self._reserved_checker.check_reserved_compatibility(group, reserved_tags)
        if len(validation_issues) > 0:
            return validation_issues

        # Check for requires Def tags
        validation_issues += self._reserved_checker.check_tag_requirements(group, reserved_tags)
        if len(validation_issues) > 0:
            return validation_issues

        return validation_issues

    @staticmethod
    def check_tag_level_issue(original_tag_list, is_top_level, is_group) -> list:
        """Report tags incorrectly positioned in hierarchy.

        Parameters:
            original_tag_list (list of HedTag): HedTags containing the original tags.
            is_top_level (bool): If True, this group is a "top level tag group".
            is_group (bool): If True group should be contained by parenthesis.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - A tag is a tagGroup or topLevelTagGroup tag when its schema says so or its row in
              reserved_tags.json does: schemas 8.0.0 and 8.1.0 carry neither attribute on Delay and Duration,
              and the file supplies them (specification 3.2.8 rule 1).
        """
        validation_issues = GroupValidator._check_group_tag_attribute(original_tag_list, is_group)
        if len(validation_issues) > 0:
            return validation_issues

        reserved_checker = ReservedChecker.get_instance()
        top_level_tags = [
            tag
            for tag in original_tag_list
            if tag.base_tag_has_attribute(HedKey.TopLevelTagGroup)
            or tag.short_base_tag in reserved_checker.top_group_tags
        ]
        if not is_top_level:
            validation_issues += GroupValidator._check_no_top_tags(top_level_tags)
        return validation_issues

    @staticmethod
    def _check_no_top_tags(tag_list):
        """Check there are no tags with the top level tag group attribute are in this list.

        Parameters:
            tag_list (list of HedTag): List of HedTags in the group

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - A reserved tag is reported with its row's ERROR_CODE; TAG_GROUP_ERROR otherwise.
        """
        reserved_checker = ReservedChecker.get_instance()
        validation_issues = []
        for top_level_tag in tag_list:
            actual_code = reserved_checker.get_error_code(top_level_tag.short_base_tag)
            validation_issues += ErrorHandler.format_error(
                ValidationErrors.HED_TOP_LEVEL_TAG, tag=top_level_tag, actual_error=actual_code
            )
        return validation_issues

    @staticmethod
    def _check_group_tag_attribute(tag_list, is_group):
        """Check that any tags in a list are in a group if they have tag-group attribute.

        Parameters:
            tag_list (list of HedTag): List of HedTags in the group
            is_group (boolean):  True if the tags in tag_list are in parentheses at some level.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - The tagGroup attribute comes from the schema or from the tag's row in reserved_tags.json.
            - A reserved tag is reported with its row's ERROR_CODE; TAG_GROUP_ERROR otherwise.
        """
        if is_group:
            return []
        reserved_checker = ReservedChecker.get_instance()
        validation_issues = []
        for tag in tag_list:
            if tag.base_tag_has_attribute(HedKey.TagGroup) or tag.short_base_tag in reserved_checker.group_tags:
                validation_issues += ErrorHandler.format_error(
                    ValidationErrors.HED_TAG_GROUP_TAG,
                    tag=tag,
                    actual_error=reserved_checker.get_error_code(tag.short_base_tag),
                )
        return validation_issues

    def check_for_required_tags(self, tags) -> list:
        """Report missing required tags.

        Parameters:
            tags (list): HedTags containing the tags.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        """
        validation_issues = []
        required_prefixes = self._hed_schema.get_tags_with_attribute(HedKey.Required)
        for required_prefix in required_prefixes:
            if not any(tag.long_tag.casefold().startswith(required_prefix.casefold()) for tag in tags):
                validation_issues += ErrorHandler.format_error(
                    ValidationErrors.REQUIRED_TAG_MISSING, tag_namespace=required_prefix
                )
        return validation_issues

    def check_multiple_unique_tags_exist(self, tags) -> list:
        """Report if multiple identical unique tags exist

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
            unique_tag_prefix_bool_mask = [x.long_tag.casefold().startswith(unique_prefix.casefold()) for x in tags]
            if sum(unique_tag_prefix_bool_mask) > 1:
                validation_issues += ErrorHandler.format_error(
                    ValidationErrors.TAG_NOT_UNIQUE, tag_namespace=unique_prefix
                )
        return validation_issues

    def _validate_tags_in_hed_string(self, tags):
        """Validate the multi-tag properties in a HED string.

            Multi-tag properties include required tag, unique tag, etc.

        Parameters:
            tags (list): A list containing the HedTags in a HED string.

        Returns:
            list: The validation issues associated with the tags in a HED string. Each issue is a dictionary.
        """
        validation_issues = []
        validation_issues += self.check_for_required_tags(tags)
        validation_issues += self.check_multiple_unique_tags_exist(tags)
        return validation_issues
