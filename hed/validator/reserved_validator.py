import json
from functools import lru_cache

class reserved_validator:
    _instance = None
    _reserved_map = {}

    def __init__(self):
        if reserved_validator._instance is not None:
            raise Exception("Use ReservedChecker.get_instance() to get an instance of this class.")
        self._initialize_special_tags()

    @staticmethod
    def get_instance():
        if reserved_validator._instance is None:
            reserved_validator._instance = reserved_validator()
        return reserved_validator._instance

    def _initialize_special_tags(self):
        reserved_validator._reserved_map = self._load_reserved_tags()
        self.special_names = set(reserved_validator._reserved_map.keys())
        self.require_value_tags = self._get_special_tags_by_property("requireValue")
        self.no_extension_tags = self._get_special_tags_by_property("noExtension")
        self.allow_two_level_value_tags = self._get_special_tags_by_property("allowTwoLevelValue")
        self.top_group_tags = self._get_special_tags_by_property("topLevelTagGroup")
        self.requires_def_tags = self._get_special_tags_by_property("requiresDef")
        self.group_tags = self._get_special_tags_by_property("tagGroup")
        self.exclusive_tags = self._get_special_tags_by_property("exclusive")
        self.temporal_tags = self._get_special_tags_by_property("isTemporalTag")
        self.no_splice_in_group = self._get_special_tags_by_property("noSpliceInGroup")
        self.has_forbidden_subgroup_tags = {
            value["name"]
            for value in reserved_validator._reserved_map.values()
            if len(value.get("forbiddenSubgroupTags", [])) > 0
        }

    @staticmethod
    @lru_cache
    def _load_reserved_tags():
        with open("../data/json/reservedTags.json", "r") as file:
            return json.load(file)

    def _get_special_tags_by_property(self, property_name):
        return {
            value["name"]
            for value in reserved_validator._reserved_map.values()
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

    def splice_check(self, hed_string, full_check):
        if not hed_string.column_splices:
            return []
        if full_check or any(tag.schema_tag.name in self.exclusive_tags for tag in hed_string.tags):
            return [self.generate_issue("curlyBracesNotAllowed", hed_string.hed_string)]
        return []

    def check_unique(self, hed_string):
        unique_tags = [tag for tag in hed_string.tags if tag.has_attribute("unique")]
        unique_names = set()
        for tag in unique_tags:
            if tag.schema_tag.name in unique_names:
                return [
                    self.generate_issue("multipleUniqueTags", hed_string.hed_string, tag.original_tag)
                ]
            unique_names.add(tag.schema_tag.name)
        return []

    @staticmethod
    def generate_issue(issue_type, hed_string, tag=None):
        return {
            "type": issue_type,
            "hed_string": hed_string,
            "tag": tag
        }

    # Additional methods for other checks should be implemented here following similar patterns.

if __name__ == "__main__":
    checker = reserved_validator.get_instance()
    print("ReservedChecker initialized successfully.")
