"""Singleton checker that validates reserved HED tag usage rules loaded from reserved_tags.json.

``hed/validator/data/reserved_tags.json`` is a verbatim copy of ``reserved_tags.json`` as published by the HED
specification (section 3.2.8, defined in Appendix A.6). The ``reserved_tags.yaml`` workflow fails when the copy
drifts from hed-specification main. Every row of the file applies in every standard schema version >= 8.0.0
(hed-specification decision 2026-10-15): its ``requireValue``, ``tagGroup`` and ``topLevelTagGroup`` fields
supply what the 8.0.0 to 8.2.0 schemas lack on ``Delay`` and ``Duration``, so no check here takes a version.
"""

import json
import os
from collections import defaultdict
from threading import Lock

from hed.errors.error_reporter import ErrorHandler
from hed.errors.error_types import TemporalErrors, ValidationErrors


class ReservedChecker:
    """Thread-safe singleton that loads reserved tag rules and checks groups for compliance."""

    _instance = None
    _lock = Lock()
    reserved_reqs_path = os.path.join(os.path.dirname(__file__), "data", "reserved_tags.json")

    # The ten reserved tags that carry no rule beyond their schema attributes (specification 3.2.8, second
    # paragraph). reserved_tags.json lists only the structural tags, so these are written out here rather than
    # read from a bundled schema, whose contents could change between releases.
    ORGANIZATIONAL_TAGS = frozenset(
        {
            "Collection",
            "Condition-variable",
            "Control-variable",
            "Event-stream",
            "Experimental-intertrial",
            "Experimental-trial",
            "Indicator-variable",
            "Recording",
            "Task",
            "Time-block",
        }
    )

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Load the JSON file during the first instantiation
        if not hasattr(self, "reserved_map"):
            with open(self.reserved_reqs_path, encoding="utf-8") as file:
                data = json.load(file)
            self.reserved_map = data["tags"]
            self.value_forms = data["valueForms"]
        self._initialize_special_tags()

    @staticmethod
    def get_instance():
        """Return the singleton ReservedChecker instance, creating it on first call.

        Returns:
            ReservedChecker: The shared singleton instance.

        """
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
        self.timeline_tags = self._get_special_tags_by_property("requiresTimeline")
        self.allow_splice_in_group = self._get_special_tags_by_property("allowSpliceInGroup")
        # The nine structural reserved tags: the rows plus the two-part tags Def and Def-expand.
        self.structural_names = frozenset(self.special_names | set(self.value_forms))
        self.reserved_names = self.structural_names | self.ORGANIZATIONAL_TAGS

    def _get_special_tags_by_property(self, property_name):
        return {value["name"] for value in self.reserved_map.values() if value.get(property_name) is True}

    def get_error_code(self, tag_name) -> str | None:
        """Return the ERROR_CODE of the row for a tag name, or None if the name is not a row.

        Parameters:
            tag_name (str): The short base tag name.

        Returns:
            str or None: The row's error code (specification 3.2.8 rule 6).
        """
        row = self.reserved_map.get(tag_name)
        return row["ERROR_CODE"] if row else None

    def get_reserved(self, group):
        """Return the list of reserved tags found directly within the given HED group.

        Parameters:
            group (HedGroup): The group to inspect.

        Returns:
            list[HedTag]: Tags in the group whose short base tag is a reserved name.

        """
        reserved_tags = [tag for tag in group.tags() if tag.short_base_tag in self.special_names]
        return reserved_tags

    def get_governing_tag(self, reserved_tags):
        """Return the tag whose row gives the group rules, or None if the reserved tags cannot share a group.

        Parameters:
            reserved_tags (list of HedTag): The reserved tags of one group, without duplicates.

        Returns:
            HedTag or None: The only tag, or, for two tags of which one lists the other in its ``secondaryWith``,
                that other tag (specification 3.2.8 rule 3). None for any other combination.
        """
        if len(reserved_tags) == 1:
            return reserved_tags[0]
        if len(reserved_tags) == 2:
            first, second = reserved_tags
            if second.short_base_tag in self.reserved_map[first.short_base_tag].get("secondaryWith", []):
                return second
            if first.short_base_tag in self.reserved_map[second.short_base_tag].get("secondaryWith", []):
                return first
        return None

    @staticmethod
    def _get_duplicates(tag_list):
        grouped_tags = defaultdict(list)
        for tag in tag_list:
            grouped_tags[tag.short_base_tag].append(tag)
        return grouped_tags

    def check_reserved_compatibility(self, group, reserved_tags):
        """Check to make sure that the reserved tags can be used together and no duplicates.

        Parameters:
            group (HedTagGroup): A group to be checked.
            reserved_tags (list of HedTag): A list of reserved tags in this group.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - These are placement errors, reported as TAG_GROUP_ERROR (specification 3.2.8 rule 6).
        """
        # Make sure there are no duplicate reserved tags
        grouped = self._get_duplicates(reserved_tags)
        multiples = [key for key, items in grouped.items() if len(items) > 1]
        if len(multiples) > 0:
            return ErrorHandler.format_error(
                ValidationErrors.HED_RESERVED_TAG_REPEATED, tag=grouped[multiples[0]][1], group=group
            )
        # Test compatibility among the reserved tags
        if self.get_governing_tag(reserved_tags) is None:
            return ErrorHandler.format_error(
                ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=self._first_incompatible(reserved_tags), group=group
            )
        return []

    def _first_incompatible(self, reserved_tags):
        """Return the first tag that a reserved tag of the group does not allow beside it, to name in the error."""
        for tag in reserved_tags:
            allowed = self.reserved_map[tag.short_base_tag]["otherAllowedNonDefTags"]
            for other in reserved_tags:
                if other is not tag and other.short_base_tag not in allowed:
                    return other
        return reserved_tags[-1]

    def check_tag_requirements(self, group, reserved_tags):
        """Check the group against the row of its governing tag.

        Parameters:
            group (HedTagGroup): A group to be checked.
            reserved_tags (list of HedTag): A list of reserved tags in this group.

        Returns:
            list: Validation issues. Each issue is a dictionary.

        Notes:
            - Call this only after check_reserved_compatibility found no issue, so a governing tag exists.
            - A missing or extra anchor and a wrong number of inner groups are content errors, reported with the
              row's ERROR_CODE; a top-level tag the row does not allow is a placement error, reported as
              TAG_GROUP_ERROR (specification 3.2.8 rule 6).
            - An anchor is a Def tag or a Def-expand group; neither counts as an other tag or an inner group.
        """
        governing_tag = self.get_governing_tag(reserved_tags)
        row = self.reserved_map[governing_tag.short_base_tag]
        error_code = row["ERROR_CODE"]
        anchors = group.find_def_tags(recursive=False, include_groups=1)
        if row["requiresDef"] and len(anchors) != 1:
            return ErrorHandler.format_error(
                TemporalErrors.ONSET_NO_DEF_TAG_FOUND, tag=governing_tag, actual_error=error_code
            )
        if not row["requiresDef"] and anchors:
            return ErrorHandler.format_error(
                ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=governing_tag, group=group, actual_error=error_code
            )

        allowed = {governing_tag.short_base_tag, *row["otherAllowedNonDefTags"]}
        other_tags = [tag for tag in group.tags() if tag not in anchors and tag.short_base_tag not in allowed]
        if other_tags:
            return ErrorHandler.format_error(ValidationErrors.HED_TAGS_NOT_ALLOWED, tag=other_tags[0], group=group)

        # Check the subgroup requirements
        inner_groups = [subgroup for subgroup in group.groups() if subgroup not in anchors]
        min_allowed = row["minNonDefSubgroups"]
        max_allowed = row["maxNonDefSubgroups"]
        if len(inner_groups) < min_allowed or (max_allowed is not None and len(inner_groups) > max_allowed):
            return ErrorHandler.format_error(
                ValidationErrors.HED_RESERVED_TAG_GROUP_ERROR,
                group=group,
                group_count=str(len(inner_groups)),
                tag_list=reserved_tags,
                actual_error=error_code,
            )
        return []
