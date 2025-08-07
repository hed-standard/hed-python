import json
import os
import math
from threading import Lock
from collections import defaultdict
from hed.errors.error_types import ValidationErrors, TemporalErrors
from hed.errors.error_reporter import ErrorHandler

class ReservedChecker:
    _instance = None
    _lock = Lock()
    reserved_reqs_path = os.path.join(os.path.dirname(__file__), "data/reservedTags.json")

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ReservedChecker, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Load the JSON file during the first instantiation
        if not hasattr(self, "reserved_map"):
            with open(self.reserved_reqs_path, 'r') as file:
                self.reserved_map = json.load(file)
        self._initialize_special_tags()

    @staticmethod
    def get_instance():
        if ReservedChecker._instance is None:
            ReservedChecker._instance = ReservedChecker()
        return ReservedChecker._instance

    def _initialize_special_tags(self):
        self.special_names = set(self.reserved_map.keys())
        self.require_value_tags = self._get_special_tags_by_property("requireValue")
        self.no_extension_tags = self._get_special_tags_by_property("noExtension")
        self.top_group_tags = self._get_special_tags_by_property("topLevelTagGroup")
        self.requires_def_tags = self._get_special_tags_by_property("requiresDef")
        self.group_tags = self._get_special_tags_by_property("tagGroup")
        self.timelineTags = self._get_special_tags_by_property("requiresTimeline")
        self.no_splice_in_group = self._get_special_tags_by_property("noSpliceInGroup")

    def _get_special_tags_by_property(self, property_name):
        return {
            value["name"]
            for value in self.reserved_map.values()
            if value.get(property_name) is True
        }

    def get_reserved(self, group):
        reserved_tags = [tag for tag in group.tags() if tag.short_base_tag in self.special_names]
        return reserved_tags

    @staticmethod
    def _get_duplicates(tag_list):
        grouped_tags = defaultdict(list)
        for tag in tag_list:
            grouped_tags[tag.short_base_tag].append(tag)
        return grouped_tags

    def check_reserved_compatibility(self, group, reserved_tags):
        """ Check to make sure that the reserved tags can be used together and no duplicates.

        Parameters:
            group (HedTagGroup): A group to be checked.
            reserved_tags (list of HedTag): A list of reserved tags in this group.

        """
        # Make sure there are no duplicate reserved tags
        grouped = self._get_duplicates(reserved_tags)
        multiples = [key for key, items in grouped.items() if len(items) > 1]
        if len(multiples) > 0:
            return ErrorHandler.format_error(ValidationErrors.HED_RESERVED_TAG_REPEATED,
                                             tag=grouped[multiples[0]][1], group=group)
        # Test compatibility among the reserved tags
        for tag in reserved_tags:
            incompatible_tag = self.get_incompatible(tag, reserved_tags)
            if incompatible_tag:
                return ErrorHandler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=incompatible_tag[0],
                                                 group=group)
        return []

    def check_tag_requirements(self, group, reserved_tags):
        """ Check the tag requirements within the group.

        Parameters:
            group (HedTagGroup): A group to be checked.
            reserved_tags (list of HedTag): A list of reserved tags in this group.

        Notes:  This is only called when there are some reserved incompatible tags.
        """
        [requires_defs, defs] = self.get_def_information(group, reserved_tags)
        if len(requires_defs) > 1:
            return ErrorHandler.format_error(ValidationErrors.HED_RESERVED_TAG_REPEATED, tag=requires_defs[0],
                                             group=group)
        if len(requires_defs) == 1 and len(defs) != 1:
            return ErrorHandler.format_error(TemporalErrors.ONSET_NO_DEF_TAG_FOUND, tag=requires_defs[0])

        if len(requires_defs) == 0 and len(defs) != 0:
            return ErrorHandler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=reserved_tags[0], group=group)

        other_tags = [tag for tag in group.tags() if tag not in reserved_tags and tag not in defs]
        if len(other_tags) > 0:
            return ErrorHandler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=other_tags[0], group=group)

        # Check the subgroup requirements
        other_groups = [group for group in group.groups() if group not in defs]
        min_allowed, max_allowed = self.get_group_requirements(reserved_tags)
        if not math.isinf(max_allowed) and len(other_groups) > max_allowed:
            return ErrorHandler.format_error(ValidationErrors.HED_RESERVED_TAG_GROUP_ERROR, group=group,
                                             group_count=str(len(other_groups)), tag_list=reserved_tags)
        if group.is_group and not math.isinf(max_allowed) and min_allowed > len(other_groups):
            return ErrorHandler.format_error(ValidationErrors.HED_RESERVED_TAG_GROUP_ERROR, group=group,
                                             group_count=str(len(other_groups)), tag_list=reserved_tags)
        return []

    def get_group_requirements(self, reserved_tags) -> tuple[float, float]:
        """ Returns the maximum and minimum number of groups required for these reserved tags.

        Parameters:
            reserved_tags (list of HedTag): The reserved tags to be checked.

        Returns:
            tuple[float, float]: the maximum required and the minimum required.

        """
        max_allowed = float('inf')
        min_allowed = float('-inf')
        for tag in reserved_tags:
            requirements = self.reserved_map[tag.short_base_tag]
            this_min = requirements['minNonDefSubgroups']
            if this_min is not None and this_min > min_allowed:
                min_allowed = this_min
            this_max = requirements['maxNonDefSubgroups']
            if this_max is not None and this_max < max_allowed:
                max_allowed = this_max
        if max_allowed < min_allowed and len(reserved_tags) > 1:
            min_allowed = max_allowed
        return min_allowed, max_allowed

    def get_def_information(self, group, reserved_tags) -> list[list]:
        """Get definition information for reserved tags.

        Parameters:
            group (HedGroup): The HED group to check.
            reserved_tags (list of HedTag): The reserved tags to process.

        Returns:
            list[list]: A list containing [requires_defs, defs].
        """
        requires_defs = [tag for tag in reserved_tags if tag.short_base_tag in self.requires_def_tags]
        defs = group.find_def_tags(recursive=False, include_groups=1)
        return [requires_defs, defs]

    def get_incompatible(self, tag, reserved_tags) -> list:
        """ Return the list of tags that cannot be in the same group with tag.

        Parameters:
            tag (HedTag): Reserved tag to be tested.
            reserved_tags (list of HedTag): Reserved tags (no duplicates).

        Returns:
            list[HedTag]: List of incompatible tags.

        """
        requirements = self.reserved_map[tag.short_base_tag]
        other_allowed = requirements["otherAllowedNonDefTags"]
        incompatible = [this_tag for this_tag in reserved_tags
                        if this_tag.short_base_tag not in other_allowed and this_tag != tag]
        return incompatible

    # Additional methods for other checks should be implemented here following similar patterns.


if __name__ == "__main__":
    checker = ReservedChecker.get_instance()
    print("ReservedChecker initialized successfully.")
    print(checker.special_names)
