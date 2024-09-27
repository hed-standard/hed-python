""" Validation of the HED tags as strings. """

from hed.errors.error_reporter import ErrorHandler
from hed.models.model_constants import DefTagNames
from hed.schema.hed_schema_constants import HedKey
from hed.models.hed_tag import HedTag
from hed.errors.error_types import ValidationErrors, TemporalErrors


class GroupValidator:
    """ Validation for attributes across groups HED tags.

        This is things like Required, Unique, top level tags, etc.
     """
    def __init__(self, hed_schema):
        """ Constructor for GroupValidator

        Parameters:
            hed_schema (HedSchema): A HedSchema object.
        """
        if hed_schema is None:
            raise ValueError("HedSchema required for validation")
        self._hed_schema = hed_schema

    def run_tag_level_validators(self, hed_string_obj):
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
            validation_issues += self.check_tag_level_issue(original_tag_group.tags(), is_top_level, is_group)

        validation_issues += self._check_for_duplicate_groups(hed_string_obj)
        validation_issues += self.validate_duration_tags(hed_string_obj)
        return validation_issues

    def run_all_tags_validators(self, hed_string_obj):
        """ Report invalid the multi-tag properties in a HED string, e.g. required tags.

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

    @staticmethod
    def check_tag_level_issue(original_tag_list, is_top_level, is_group):
        """ Report tags incorrectly positioned in hierarchy.

            Top-level groups can contain definitions, Onset, etc. tags.

        Parameters:
            original_tag_list (list): HedTags containing the original tags.
            is_top_level (bool): If True, this group is a "top level tag group".
            is_group (bool): If True group should be contained by parenthesis.

        Returns:
            list: Validation issues. Each issue is a dictionary.
        """
        validation_issues = []
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
                actual_code = None
                if top_level_tag.short_base_tag == DefTagNames.DEFINITION_KEY:
                    actual_code = ValidationErrors.DEFINITION_INVALID
                elif top_level_tag.short_base_tag in DefTagNames.ALL_TIME_KEYS:
                    actual_code = ValidationErrors.TEMPORAL_TAG_ERROR  # May split this out if we switch error

                if actual_code:
                    validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TOP_LEVEL_TAG,
                                                                   tag=top_level_tag,
                                                                   actual_error=actual_code)
                validation_issues += ErrorHandler.format_error(ValidationErrors.HED_TOP_LEVEL_TAG,
                                                               tag=top_level_tag)

        if is_top_level and len(top_level_tags) > 1:
            validation_issue = False
            short_tags = {tag.short_base_tag for tag in top_level_tags}
            # Verify there's no duplicates, and that if there's two tags they are a delay and temporal tag.
            if len(short_tags) != len(top_level_tags):
                validation_issue = True
            elif DefTagNames.DELAY_KEY not in short_tags or len(short_tags) != 2:
                validation_issue = True
            else:
                short_tags.remove(DefTagNames.DELAY_KEY)
                other_tag = next(iter(short_tags))
                if other_tag not in DefTagNames.ALL_TIME_KEYS:
                    validation_issue = True

            if validation_issue:
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
            if not any(tag.long_tag.casefold().startswith(required_prefix.casefold()) for tag in tags):
                validation_issues += ErrorHandler.format_error(ValidationErrors.REQUIRED_TAG_MISSING,
                                                               tag_namespace=required_prefix)
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
            unique_tag_prefix_bool_mask = [x.long_tag.casefold().startswith(unique_prefix.casefold()) for x in tags]
            if sum(unique_tag_prefix_bool_mask) > 1:
                validation_issues += ErrorHandler.format_error(ValidationErrors.TAG_NOT_UNIQUE,
                                                               tag_namespace=unique_prefix)
        return validation_issues

    @staticmethod
    def validate_duration_tags(hed_string_obj):
        """ Validate Duration/Delay tag groups

        Parameters:
            hed_string_obj (HedString): The hed string to check.

        Returns:
            list: Issues found in validating durations (i.e., extra tags or groups present, or a group missing)
        """
        duration_issues = []
        for top_tag, group in hed_string_obj.find_top_level_tags(anchor_tags=DefTagNames.DURATION_KEYS):
            top_level_tags = [tag.short_base_tag for tag in group.get_all_tags()
                              if tag.base_tag_has_attribute(HedKey.TopLevelTagGroup)]
            # Skip onset/inset/offset
            if any(tag in DefTagNames.TEMPORAL_KEYS for tag in top_level_tags):
                continue
            # This implicitly validates the duration/delay tag, as they're the only two allowed in the same group
            # It should be impossible to have > 2 tags, but it's a good stopgap.
            if len(top_level_tags) != len(group.tags()):
                for tag in group.tags():
                    if tag.short_base_tag not in top_level_tags:
                        duration_issues += ErrorHandler.format_error(TemporalErrors.DURATION_HAS_OTHER_TAGS,
                                                                     tag=tag)
                continue
            if len(group.groups()) != 1:
                duration_issues += ErrorHandler.format_error(TemporalErrors.DURATION_WRONG_NUMBER_GROUPS,
                                                             top_tag,
                                                             hed_string_obj.groups())
                continue

        return duration_issues

    def _validate_tags_in_hed_string(self, tags):
        """ Validate the multi-tag properties in a HED string.

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
        sorted_group = original_group._sorted()
        validation_issues = []
        self._check_for_duplicate_groups_recursive(sorted_group, validation_issues)
        return validation_issues
