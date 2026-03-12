"""Defined constants for definitions, def labels, and expanded labels."""

from enum import IntEnum


class TopTagReturnType(IntEnum):
    """Return-type selector for :meth:`~hed.models.HedString.find_top_level_tags`.

    Attributes:
        TAGS: Return only the anchor :class:`~hed.models.HedTag` objects.
        GROUPS: Return only the top-level :class:`~hed.models.HedGroup` objects.
        BOTH: Return ``(tag, group)`` pairs (default).
    """

    TAGS = 0
    GROUPS = 1
    BOTH = 2


class DefTagNames:
    """Source names for definitions, def labels, and expanded labels."""

    DEF_KEY = "Def"
    DEF_EXPAND_KEY = "Def-expand"
    DEFINITION_KEY = "Definition"

    ONSET_KEY = "Onset"
    OFFSET_KEY = "Offset"
    INSET_KEY = "Inset"
    DURATION_KEY = "Duration"
    DELAY_KEY = "Delay"

    TEMPORAL_KEYS = {ONSET_KEY, OFFSET_KEY, INSET_KEY}
    DURATION_KEYS = {DURATION_KEY, DELAY_KEY}

    ALL_TIME_KEYS = TEMPORAL_KEYS.union(DURATION_KEYS)
    TIMELINE_KEYS = {ONSET_KEY, OFFSET_KEY, INSET_KEY, DELAY_KEY}
