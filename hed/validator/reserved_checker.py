import json
import os
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
        self.allow_two_level_value_tags = self._get_special_tags_by_property("allowTwoLevelValue")
        self.top_group_tags = self._get_special_tags_by_property("topLevelTagGroup")
        self.requires_def_tags = self._get_special_tags_by_property("requiresDef")
        self.group_tags = self._get_special_tags_by_property("tagGroup")
        self.exclusive_tags = self._get_special_tags_by_property("exclusive")
        self.timelineTags = self._get_special_tags_by_property("requiresTimeline")
        self.no_splice_in_group = self._get_special_tags_by_property("noSpliceInGroup")
        self.has_forbidden_subgroup_tags = {
            value["name"]
            for value in self.reserved_map.values()
            if len(value.get("forbiddenSubgroupTags", [])) > 0
        }

    def _get_special_tags_by_property(self, property_name):
        return {
            value["name"]
            for value in self.reserved_map.values()
            if value.get(property_name) is True
        }

    def check_hed_string(self, hed_string, full_check):
        checks = [
            lambda: self.splice_check(hed_string, full_check),
            lambda: self.check_unique(hed_string),
            lambda: self.check_tag_group_levels(hed_string, full_check),
            lambda: self.check_exclusive(hed_string),
            lambda: self.check_no_splice_in_group_tags(hed_string),
            lambda: self.check_top_group_requirements(hed_string, full_check),
            lambda: self.check_forbidden_groups(hed_string),
            lambda: self.check_non_top_groups(hed_string, full_check),
        ]
        for check in checks:
            issues = check()
            if issues:
                return issues
        return []

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
                return ErrorHandler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=incompatible_tag[0], group=group)
        return []

    def check_def_tag_requirements(self, group, reserved_tags):
        requires_defs = [tag for tag in reserved_tags if tag.short_base_tag in self.requires_def_tags]
        if len(requires_defs) > 1:
            return ErrorHandler.format_error(ValidationErrors.HED_RESERVED_TAG_REPEATED, tag=requires_defs[0],
                                             group=group)
        defs = group.find_def_tags(recursive=False, include_groups=1)
        if len(requires_defs) == 1 and len(defs) != 1:
            return ErrorHandler.format_error(TemporalErrors.ONSET_NO_DEF_TAG_FOUND, tag=requires_defs[0])
        if len(requires_defs) == 0 and len(defs) != 0:
            return ErrorHandler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=defs[0], group=group)

    def get_incompatible(self, tag, reserved_tags):
        """ Return the list of tags that cannot be in the same group with tag.

        Parameters:
            tag (HedTag) - reserved tag to be tested.
            reserved_tags (list of HedTag) - reserved tags (no duplicates)

        Returns:
            list of HedTag

        """
        requirements = self.reserved_map[tag.short_base_tag]
        other_allowed = requirements["otherAllowedNonDefTags"]
        incompatible = [this_tag for this_tag in reserved_tags if this_tag.short_base_tag not in other_allowed and this_tag != tag]
        return incompatible

    def splice_check(self, hed_string, full_check):
        return []

    def check_unique(self, hed_string):
        return [hed_string]

    def check_tag_group_levels(self, hed_string, full_check):
        return []

    def check_exclusive(self, hed_string):
        return []

    def check_no_splice_in_group_tags(self, hed_string):
        return []

    def check_top_group_requirements(self, hed_string, full_check):
        return []

    def check_forbidden_groups(self, hed_string):
        return []

    def check_non_top_groups(self, hed_string, full_check):
        return []


    # Additional methods for other checks should be implemented here following similar patterns.


if __name__ == "__main__":
    checker = ReservedChecker.get_instance()
    print("ReservedChecker initialized successfully.")
    print(checker.special_names)
